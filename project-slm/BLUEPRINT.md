# Snaily — Full Build Plan

> **What it is:** Not an AI software. A connector that contexts SLMs + skills + memory + web search into one thing.
> **Who it's for:** Everyone — old laptops, no GPU, minimum specs. Open source. Free will.
> **Core UX rule:** Every endpoint connection = as easy as filling Google Forms.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Tauri)                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Minimal Chat UI (GPT-like)                       │  │
│  │  ├── Chat input + conversation history            │  │
│  │  ├── Sidebar: Model selector (dropdown)           │  │
│  │  ├── Sidebar: Skill dock (drag-drop zone)         │  │
│  │  ├── Sidebar: Memory stats                        │  │
│  │  ├── Sidebar: Settings (tier switch)              │  │
│  │  └── Connection forms (Google Forms-style modals) │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (localhost)
┌──────────────────────▼──────────────────────────────────┐
│                 BACKEND (Python FastAPI)                  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Agent Loop   │  │ Skill Parser│  │ Memory Manager  │ │
│  │ (Orchestrate)│◄►│ (.md/.yaml) │  │ (Chroma + RAG)  │ │
│  └──────┬───────┘  └─────────────┘  └────────┬────────┘ │
│         │                                     │          │
│  ┌──────▼───────┐  ┌─────────────┐  ┌────────▼────────┐ │
│  │ SLM Runtime  │  │ Web Search  │  │ Embeddings      │ │
│  │ (Ollama /    │  │ (DuckDuckGo │  │ (Sentence       │ │
│  │  llama.cpp)  │  │  / Tavily)  │  │  Transformers)  │ │
│  └──────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Tech | Why |
|---|---|---|
| Frontend shell | Tauri 2.x (Rust + HTML/CSS/JS) | Tiny binary (~5 MB), cross-platform, Pi-friendly |
| Frontend UI | Vanilla HTML + CSS + JS | No framework bloat, works everywhere |
| Backend API | Python 3.11+ FastAPI | Best AI ecosystem, async, fast enough |
| SLM runtime | Ollama (wraps llama.cpp) | One-command install, model management built-in |
| Memory/RAG | ChromaDB (SQLite backend) | Persistent, lightweight, local |
| Embeddings | all-MiniLM-L6-v2 (Sentence Transformers) | ~90 MB, runs on CPU, good quality |
| Web search | DuckDuckGo Search (duckduckgo-search lib) | Free, no API key, no rate limits |
| Skill parsing | Python markdown/yaml parser | Simple, reliable |
| IPC | Tauri ↔ FastAPI via localhost REST | Clean separation |

---

## 3. Folder Structure

```
project-slm/
├── BLUEPRINT.md                    # This file
├── README.md                       # User-facing docs
├── LICENSE                         # MIT
│
├── backend/                        # Python FastAPI backend
│   ├── main.py                     # FastAPI app entry
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── agent/                      # Core agent loop
│   │   ├── __init__.py
│   │   ├── loop.py                 # Reason → tool → observe → respond
│   │   └── prompt_builder.py       # System prompt assembly (base + skill injection)
│   │
│   ├── models/                     # SLM management
│   │   ├── __init__.py
│   │   ├── manager.py              # List/download/switch models via Ollama API
│   │   └── config.py               # Model configs (quant levels, RAM estimates)
│   │
│   ├── skills/                     # Skill file system
│   │   ├── __init__.py
│   │   ├── parser.py               # Parse .md/.yaml skill files → structured data
│   │   ├── validator.py            # Validate skill file format (security sandbox)
│   │   └── dock/                   # User drops skill files here
│   │       └── example-skill.md    # Ships with one example
│   │
│   ├── memory/                     # Persistent cross-chat memory
│   │   ├── __init__.py
│   │   ├── store.py                # ChromaDB wrapper (add/query/delete)
│   │   ├── embedder.py             # Sentence Transformers embedding
│   │   └── data/                   # ChromaDB persistent storage (auto-created)
│   │
│   ├── tools/                      # Agent tools
│   │   ├── __init__.py
│   │   ├── web_search.py           # DuckDuckGo search tool
│   │   ├── memory_query.py         # Query memory tool
│   │   └── registry.py             # Tool registration for agent loop
│   │
│   └── tiers/                      # Cloud/Local tier management
│       ├── __init__.py
│       ├── local.py                # Ollama local inference
│       └── cloud.py                # API-based inference (Claude/Gemini/OpenAI)
│
├── frontend/                       # Tauri frontend
│   ├── src-tauri/                  # Rust/Tauri config
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── src/
│   │       └── main.rs
│   │
│   └── src/                        # Web UI
│       ├── index.html              # Main page
│       ├── styles/
│       │   └── main.css            # All styles
│       └── js/
│           ├── app.js              # Main app logic
│           ├── chat.js             # Chat interface
│           ├── sidebar.js          # Sidebar (model selector, skill dock, memory)
│           ├── settings.js         # Settings & tier switching
│           └── api.js              # Backend API calls
│
└── docs/                           # Documentation
    ├── skill-file-spec.md          # Skill file format specification
    ├── setup-guide.md              # Installation for users
    └── hardware-guide.md           # Which hardware = which tier
```

---

## 4. Skill File Spec (Format the app parses)

> NOTE: The meta-prompt to GENERATE these files comes last. This is just the spec.

```yaml
---
name: "skill-name-here"
description: "One line — what this skill does"
version: "1.0"
triggers:
  - "keyword or phrase that activates this skill"
requires:
  web_search: true/false
  memory: true/false
---

## Guardrails
- Rule 1 (NEVER violate)
- Rule 2

## Workflow
1. Step one
2. Step two
3. Step three

## Output Format
- How to structure the response

## Examples
User: "example input"
Agent: "example output"
```

App parses YAML frontmatter → extracts metadata + triggers.
Markdown body → injected into system prompt when skill is active.

---

## 5. Three Tiers (User picks in settings)

| Tier | Brain | Needs | Best for |
|---|---|---|---|
| ☁️ Cloud | Claude/Gemini/OpenAI API | Internet + API key | No hardware, just browser |
| 💻 Local Lite | Ollama + Q4_K_M SLM | 6+ GB RAM, no GPU | Old laptops |
| 🚀 Local Power | Ollama + Q5/Q8 SLM | 16+ GB RAM or GPU | Good machines |
| 🍓 Pi Server | Ollama + Q4_K_M on Pi 5 | Pi 5 8GB, always-on | Home AI server |

Same app, same skills, same memory. Only brain source changes.

---

## 6. Build Checklist (in order)

### Phase 1: Core Backend (Week 1)
- [ ] Set up Python project (`backend/`) with FastAPI
- [ ] Install & configure Ollama + pull Qwen3-4B Q4_K_M
- [ ] Build `/api/chat` endpoint — send message → get SLM response (streaming)
- [ ] Build agent loop (reason → tool call → observe → respond)
- [ ] Build skill file parser (.md with YAML frontmatter)
- [ ] Build skill validator (text-only, no exec, sandbox)
- [ ] Build prompt builder (base system prompt + inject active skill)
- [ ] Ship one example skill file

### Phase 2: Memory System (Week 2)
- [ ] Set up ChromaDB with SQLite persistence
- [ ] Integrate Sentence Transformers embedder (all-MiniLM-L6-v2)
- [ ] Auto-embed every conversation turn
- [ ] Build `/api/memory/query` — retrieve relevant past context
- [ ] Inject top-K memory results into prompt before SLM call
- [ ] Build `/api/memory/stats` — count, size, oldest/newest

### Phase 3: Web Search Tool (Week 2)
- [ ] Integrate duckduckgo-search library
- [ ] Build web search as agent tool (SLM decides when to call)
- [ ] Parse search results → inject as context
- [ ] Add offline fallback (skip gracefully if no internet)

### Phase 4: Tier System (Week 3)
- [ ] Build local inference adapter (Ollama API)
- [ ] Build cloud inference adapter (OpenAI-compatible API)
- [ ] Build tier switcher — same interface, swap backend
- [ ] `/api/settings/tier` — get/set current tier
- [ ] Auto-detect hardware on first launch → recommend tier

### Phase 5: Frontend (Week 3-4)
- [ ] Init Tauri project
- [ ] Build chat interface (input, send, conversation history, streaming response)
- [ ] Build sidebar — model selector dropdown
- [ ] Build sidebar — skill dock (list active skills, drag-drop zone)
- [ ] Build sidebar — memory stats display
- [ ] Build settings page — tier switch, model download
- [ ] Build connection modals (Google Forms-style — dropdowns, checkboxes)
- [ ] Dark mode, clean minimal design

### Phase 6: Model Portal (Week 4)
- [ ] `/api/models/available` — list downloadable models from Ollama
- [ ] `/api/models/download` — trigger download with progress
- [ ] `/api/models/active` — get/set active model
- [ ] Frontend: model browser with size, RAM needed, recommended label
- [ ] Show: "Qwen3-4B Q4_K_M — 2.5 GB — Recommended for old laptops"

### Phase 7: Skill Meta-Prompt (Last)
- [ ] Design the meta-prompt (USER provides this)
- [ ] Add to app: "Generate Skill" button → shows prompt to copy
- [ ] User pastes prompt into any LLM → gets .md file → drops into dock
- [ ] Validate on import → activate

### Phase 8: Polish & Ship (Week 5)
- [ ] Error handling everywhere (graceful, user-friendly messages)
- [ ] Test on: old laptop (4-8 GB RAM), Ryzen 7000, Pi 5
- [ ] Output validation layer (completeness check, format check)
- [ ] README + setup guide + hardware guide
- [ ] MIT License
- [ ] GitHub repo — open source launch

---

## 7. Minimum Hardware Targets

| Spec | Minimum | Recommended |
|---|---|---|
| RAM | 6 GB | 8 GB |
| Disk | 5 GB free | 10 GB free |
| CPU | Any x64 with AVX2 | Ryzen 5000+ / Intel 10th+ |
| GPU | Not required | Nice to have |
| OS | Windows 10+ / Linux / macOS | Any |
| Disk type | HDD works (slower) | SSD preferred |

---

## 8. Key Design Principles

1. **Local first** — everything works offline after initial setup
2. **CPU first** — GPU is a bonus, never a requirement
3. **Zero telemetry** — no data leaves the machine ever
4. **Skill files are text** — never executed, only parsed and injected
5. **Google Forms easy** — if a setting needs code, redesign it
6. **Open source (MIT)** — free forever, fork freely
7. **Small footprint** — total install < 4 GB including model
8. **Tier flexible** — cloud ↔ local ↔ Pi, skills and memory follow

---

## 9. Dependencies (Exact)

### Backend (Python)
```
fastapi
uvicorn[standard]
ollama
chromadb
sentence-transformers
duckduckgo-search
pyyaml
python-frontmatter
pydantic
```

### Frontend (Tauri)
```
@tauri-apps/cli v2
@tauri-apps/api v2
```

### Runtime
```
Ollama (latest)
Python 3.11+
Rust (for Tauri build)
Node.js 18+ (for Tauri frontend build)
```

---

*Last updated: 2026-02-25*
*Status: Ready to build Phase 1*
