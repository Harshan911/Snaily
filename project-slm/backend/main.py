"""
Snaily — Backend Entry Point
FastAPI server that orchestrates SLM, skills, memory, and tools.
Also serves the frontend at http://localhost:8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Optional, List
from pathlib import Path
import json
import asyncio
import shutil
import logging
import re

from agent.loop import AgentLoop
from agent.prompt_builder import PromptBuilder
from models.manager import ModelManager
from models.config import ModelConfig
from skills.parser import SkillParser
from skills.validator import SkillValidator
from memory.store import MemoryStore
from memory.embedder import Embedder
from tools.registry import ToolRegistry
from tools.web_search import WebSearchTool
from tools.memory_query import MemoryQueryTool
from tiers.local import LocalInference
from tiers.cloud import CloudInference

# ── Logging ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────

MAX_SKILL_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-][a-zA-Z0-9_\-. ]{0,100}\.(md|yaml|yml)$')

# ── Shared State ──────────────────────────────────────────

model_manager = ModelManager()
skill_parser = SkillParser()
skill_validator = SkillValidator()
embedder = Embedder()
memory_store = MemoryStore(embedder)
prompt_builder = PromptBuilder()

# Tools
web_search_tool = WebSearchTool()
memory_query_tool = MemoryQueryTool(memory_store)

tool_registry = ToolRegistry()
tool_registry.register(web_search_tool)
tool_registry.register(memory_query_tool)

# Inference tiers
local_inference = LocalInference()
cloud_inference = CloudInference()

# Agent
agent_loop = AgentLoop(
    prompt_builder=prompt_builder,
    tool_registry=tool_registry,
    local_inference=local_inference,
    cloud_inference=cloud_inference,
    memory_store=memory_store,
    model_manager=model_manager,
)

# ── Lifespan ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on server start, cleanup on shutdown."""
    await memory_store.initialize()
    skill_parser.load_all_skills()
    logger.info("🐉 Blue Dragon AI Hub — Backend Ready")
    logger.info(f"   Active skills: {len(skill_parser.active_skills)}")
    logger.info(f"   Memory entries: {await memory_store.count()}")
    print("🐉 Blue Dragon AI Hub — Backend Ready")
    print(f"   Active skills: {len(skill_parser.active_skills)}")
    print(f"   Memory entries: {await memory_store.count()}")
    yield
    # Shutdown cleanup (if needed in future)
    logger.info("🐉 Blue Dragon AI Hub — Shutting down.")

# ── App Init ──────────────────────────────────────────────

app = FastAPI(
    title="Blue Dragon AI Hub",
    description="Local-first AI connector — contexts SLMs + skills + memory + search into one thing.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ───────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    web_search: Optional[bool] = False
    use_memory: Optional[bool] = True

    @field_validator('message')
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 32000:
            raise ValueError('Message too long (max 32000 characters)')
        return v.strip()

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tools_used: List[str] = []

class TierSetting(BaseModel):
    tier: str  # "local" | "cloud"
    api_key: Optional[str] = None
    api_provider: Optional[str] = None  # "openai" | "anthropic" | "google"

class SkillDockRequest(BaseModel):
    filename: str

    @field_validator('filename')
    @classmethod
    def filename_must_be_safe(cls, v: str) -> str:
        """Prevent path traversal in filenames."""
        # Strip any path components — only keep the filename
        v = Path(v).name
        if not v or '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        if not SAFE_FILENAME_PATTERN.match(v):
            raise ValueError('Filename must be alphanumeric with .md, .yaml, or .yml extension')
        return v

class ModelDownloadRequest(BaseModel):
    model_name: str



# ── Chat Endpoint ─────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — send message, get SLM response."""
    try:
        result = await agent_loop.run(
            user_message=request.message,
            conversation_id=request.conversation_id,
            active_skills=skill_parser.active_skills,
            web_search=request.web_search,
            use_memory=request.use_memory,
        )
        return ChatResponse(
            reply=result["reply"],
            conversation_id=result["conversation_id"],
            tools_used=result.get("tools_used", []),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint — tokens sent as server-sent events."""
    async def event_generator():
        async for chunk in agent_loop.run_stream(
            user_message=request.message,
            conversation_id=request.conversation_id,
            active_skills=skill_parser.active_skills,
            web_search=request.web_search,
            use_memory=request.use_memory,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Skills Endpoints ──────────────────────────────────────

@app.get("/api/skills")
async def list_skills():
    """List all available skill files in the dock."""
    return {
        "skills": skill_parser.list_skills(),
        "active": [s["name"] for s in skill_parser.active_skills],
    }

@app.post("/api/skills/activate")
async def activate_skill(request: SkillDockRequest):
    """Activate a skill file from the dock."""
    try:
        skill = skill_parser.activate(request.filename)
        return {"status": "activated", "skill": skill}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Skill file '{request.filename}' not found in dock")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/skills/deactivate")
async def deactivate_skill(request: SkillDockRequest):
    """Deactivate a skill."""
    skill_parser.deactivate(request.filename)
    return {"status": "deactivated", "filename": request.filename}

@app.delete("/api/skills/{filename}")
async def delete_skill(filename: str):
    """Delete a skill file from the dock."""
    # Sanitize filename
    safe_name = Path(filename).name
    if not safe_name or '..' in safe_name or '/' in safe_name or '\\' in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not SAFE_FILENAME_PATTERN.match(safe_name):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    filepath = Path(__file__).parent / "skills" / "dock" / safe_name
    try:
        filepath.resolve().relative_to((Path(__file__).parent / "skills" / "dock").resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Filename escapes skill dock directory")

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Skill file '{safe_name}' not found")

    try:
        # Deactivate first if active
        skill_parser.deactivate(safe_name)
        filepath.unlink()
        skill_parser.load_all_skills()
        return {"status": "deleted", "filename": safe_name}
    except Exception as e:
        logger.exception(f"Skill delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/skills/validate")
async def validate_skill(request: SkillDockRequest):
    """Validate a skill file before activation."""
    result = skill_validator.validate_file(request.filename)
    return result


# ── Memory Endpoints ──────────────────────────────────────

@app.get("/api/memory/stats")
async def memory_stats():
    """Get memory store statistics."""
    return {
        "total_entries": await memory_store.count(),
        "size_mb": await memory_store.size_mb(),
    }

@app.post("/api/memory/query")
async def query_memory(request: ChatRequest):
    """Query memory for relevant past context."""
    results = await memory_store.query(request.message, top_k=5)
    return {"results": results}

@app.delete("/api/memory/clear")
async def clear_memory():
    """Clear all memory entries."""
    await memory_store.clear()
    return {"status": "cleared"}


# ── Model Endpoints ───────────────────────────────────────

@app.get("/api/models/available")
async def list_available_models():
    """List models available for download."""
    return {"models": ModelConfig.RECOMMENDED_MODELS}

@app.get("/api/models/installed")
async def list_installed_models():
    """List locally installed models."""
    models = await model_manager.list_installed()
    return {"models": models}

@app.get("/api/models/active")
async def get_active_model():
    """Get currently active model."""
    return {"model": model_manager.active_model}

@app.post("/api/models/switch")
async def switch_model(request: ModelDownloadRequest):
    """Switch to a different installed model."""
    try:
        await model_manager.switch(request.model_name)
        return {"status": "switched", "model": request.model_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/models/download")
async def download_model(request: ModelDownloadRequest):
    """Download a model via Ollama."""
    try:
        await model_manager.download(request.model_name)
        return {"status": "downloading", "model": request.model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Settings/Tier Endpoints ───────────────────────────────

@app.get("/api/settings/tier")
async def get_tier():
    """Get current inference tier."""
    return {"tier": agent_loop.current_tier}

@app.post("/api/settings/tier")
async def set_tier(setting: TierSetting):
    """Switch inference tier (local / cloud)."""
    try:
        agent_loop.set_tier(
            tier=setting.tier,
            api_key=setting.api_key,
            api_provider=setting.api_provider,
        )
        return {"status": "updated", "tier": setting.tier}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SearchSetting(BaseModel):
    firecrawl_api_key: str

@app.get("/api/settings/search")
async def get_search_settings():
    """Get web search configuration status."""
    return web_search_tool.get_config_status()

@app.post("/api/settings/search")
async def set_search_settings(setting: SearchSetting):
    """Save Firecrawl Search credentials."""
    if not setting.firecrawl_api_key or not setting.firecrawl_api_key.strip():
        raise HTTPException(status_code=400, detail="Firecrawl API key is required")

    web_search_tool.save_config(setting.firecrawl_api_key)
    return {"status": "saved", "configured": True}

@app.get("/api/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "tier": agent_loop.current_tier,
        "model": model_manager.active_model,
        "skills_active": len(skill_parser.active_skills),
    }


# ── Skill Upload Endpoint ─────────────────────────────────

@app.post("/api/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    """Upload a skill file to the dock via drag-and-drop."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Sanitize filename — prevent path traversal
    safe_name = Path(file.filename).name
    if not safe_name or '..' in safe_name or '/' in safe_name or '\\' in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not SAFE_FILENAME_PATTERN.match(safe_name):
        raise HTTPException(status_code=400, detail="Only .md, .yaml, .yml files allowed with safe characters")

    # Read with size limit BEFORE writing to disk
    content = await file.read()
    if len(content) > MAX_SKILL_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(content) // 1024} KB). Max allowed: {MAX_SKILL_UPLOAD_BYTES // 1024} KB"
        )

    dest = Path(__file__).parent / "skills" / "dock" / safe_name
    try:
        with open(dest, "wb") as f:
            f.write(content)
        # Validate the new skill
        result = skill_validator.validate_file(safe_name)
        if not result["valid"]:
            dest.unlink(missing_ok=True)  # Delete invalid file
            raise HTTPException(status_code=400, detail=f"Invalid skill: {result['errors']}")
        # Reload skills
        skill_parser.load_all_skills()
        return {"status": "uploaded", "filename": safe_name}
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)  # Clean up on error
        logger.exception(f"Skill upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Frontend Static Files ────────────────────────────────

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "src"


@app.get("/")
async def serve_index():
    """Serve the frontend HTML."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Snaily API. Frontend not found at expected path."}


# Mount static assets (CSS, JS) — MUST be after API routes
if FRONTEND_DIR.exists():
    app.mount("/styles", StaticFiles(directory=str(FRONTEND_DIR / "styles")), name="styles")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


# ── Run ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n🐌 Starting Snaily...")
    print("   Open: http://127.0.0.1:8000\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
