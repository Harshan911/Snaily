<p align="center">
  <br />
  <span style="font-size: 64px;">🐉</span>
  <br />
  <h1 align="center">Blue Dragon AI Hub</h1>
  <p align="center">
    <strong>Your local-first AI connector — private, fast, yours.</strong>
  </p>
  <p align="center">
    Not another AI software. A connector that contexts SLMs + skills + memory + web search into one thing.
  </p>
  <p align="center">
    <a href="#-quick-start"><strong>Quick Start »</strong></a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#-features">Features</a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#-skill-files">Skill Files</a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#-hardware-guide">Hardware Guide</a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#-contributing">Contributing</a>
  </p>
  <br />
  <p align="center">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" />
    <img src="https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+" />
    <img src="https://img.shields.io/badge/fastapi-0.100+-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/tauri-2.x-FFC131.svg?logo=tauri&logoColor=white" alt="Tauri 2.x" />
    <img src="https://img.shields.io/badge/ollama-latest-000000.svg" alt="Ollama" />
  </p>
</p>

<br />

---

## 🧐 What Is This?

**Blue Dragon AI Hub** is an open-source, local-first desktop application that connects Small Language Models (SLMs) with a modular skill system, persistent memory, and live web search — all running on **your** machine with **zero telemetry**.

Think of it as a personal AI workbench: you pick the brain (local SLM or cloud API), load skill files to specialize it, and it remembers your conversations across sessions. Everything works offline after initial setup. No data ever leaves your machine.

### Who is it for?

Everyone. Old laptops, machines with no GPU, Raspberry Pi 5 — if it runs Python, it runs Blue Dragon.

<br />

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **SLM Runtime** | Run models locally via [Ollama](https://ollama.com) — Qwen, Llama, Mistral, Phi, and more |
| 📄 **Skill Files** | Drop `.md` / `.yaml` files to give your AI new abilities — no code required |
| 💾 **Persistent Memory** | Cross-session RAG memory powered by ChromaDB + Sentence Transformers |
| 🔍 **Web Search** | Live DuckDuckGo search — the AI decides when to look things up |
| ☁️ **Tier System** | Seamlessly switch between local inference and cloud APIs (OpenAI / Claude / Gemini) |
| 📥 **Model Portal** | Browse, download, and switch models with one click |
| 🔒 **Zero Telemetry** | No data leaves your machine. Ever. |
| ⚡ **Lightweight** | Total install < 4 GB including model. No GPU required. |

<br />

## 🏗️ Architecture

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

<br />

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | [Download](https://www.python.org/downloads/) |
| **Ollama** | Latest | [Download](https://ollama.com/download) — for local SLM inference |
| **Node.js** | 18+ | [Download](https://nodejs.org/) — for Tauri frontend build |
| **Rust** | Latest | [Install](https://rustup.rs/) — for Tauri desktop shell |

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/blue-dragon-ai-hub.git
cd blue-dragon-ai-hub
```

### 2. Set Up the Backend

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Pull a Model via Ollama

```bash
# Pull the recommended lightweight model
ollama pull qwen3:4b

# Or try other models
ollama pull llama3.2:3b
ollama pull phi4-mini
```

### 4. Start the Backend Server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API server starts at `http://localhost:8000`. The frontend is served automatically at the same address.

### 5. Open the App

Navigate to **http://localhost:8000** in your browser — or build the Tauri desktop app:

```bash
cd frontend
npm install
npm run tauri dev
```

<br />

## 📂 Project Structure

```
project-slm/
├── BLUEPRINT.md                    # Detailed build plan & spec
├── README.md                       # ← You are here
│
├── backend/                        # Python FastAPI backend
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── agent/                      # Core agent loop
│   │   ├── loop.py                 # Reason → tool → observe → respond
│   │   └── prompt_builder.py       # System prompt assembly + skill injection
│   │
│   ├── models/                     # SLM management
│   │   ├── manager.py              # List / download / switch models via Ollama
│   │   └── config.py               # Model configs (quant levels, RAM estimates)
│   │
│   ├── skills/                     # Skill file system
│   │   ├── parser.py               # Parse .md/.yaml skill files → structured data
│   │   ├── validator.py            # Validate skill format (security sandbox)
│   │   └── dock/                   # Drop skill files here
│   │       └── example-skill.md    # Ships with one example
│   │
│   ├── memory/                     # Persistent cross-chat memory
│   │   ├── store.py                # ChromaDB wrapper (add / query / delete)
│   │   ├── embedder.py             # Sentence Transformers embeddings
│   │   └── data/                   # ChromaDB persistent storage (auto-created)
│   │
│   ├── tools/                      # Agent tools
│   │   ├── web_search.py           # DuckDuckGo search tool
│   │   ├── memory_query.py         # Query memory tool
│   │   └── registry.py             # Tool registration for agent loop
│   │
│   └── tiers/                      # Cloud / Local tier management
│       ├── local.py                # Ollama local inference
│       └── cloud.py                # Cloud API inference (OpenAI / Claude / Gemini)
│
└── frontend/                       # Tauri frontend
    └── src/                        # Web UI
        ├── index.html              # Main page
        ├── styles/
        │   └── main.css            # All styles
        └── js/
            ├── app.js              # Main app logic
            ├── chat.js             # Chat interface
            ├── sidebar.js          # Sidebar (models, skills, memory)
            ├── settings.js         # Settings & tier switching
            └── api.js              # Backend API calls
```

<br />

## 📄 Skill Files

Skill files are the heart of Blue Dragon. They're simple `.md` files with YAML frontmatter that teach the AI new behaviors — **no code, no plugins, no risk**.

### How They Work

1. You write (or generate) a `.md` skill file
2. Drop it into the skill dock (drag & drop or file picker)
3. The app validates it, parses the YAML metadata, and injects the markdown body into the system prompt
4. The AI now follows those instructions when triggered

### Skill File Format

```yaml
---
name: "research-analysis"
description: "Deep research and analysis with web verification"
version: "1.0"
triggers:
  - "research"
  - "analyze"
  - "investigate"
requires:
  web_search: true
  memory: true
---

## Guardrails
- ALWAYS verify facts with web search before stating as true
- NEVER fabricate data, statistics, or sources

## Workflow
1. Understand the query — break into sub-questions if complex
2. Check memory for relevant past research
3. Search the web for current, reliable information
4. Synthesize into a clear, structured response

## Output Format
- Start with a one-line summary answer
- Use bullet points for key findings
- End with sources and confidence level

## Examples
User: "What's the latest on quantum computing?"
Agent: **Summary:** Quantum computing has reached [X milestone]...
```

### Key Principles

- **Text only** — skill files are never executed, only parsed and injected
- **Sandboxed** — validator rejects anything suspicious
- **Composable** — activate multiple skills simultaneously
- **Shareable** — share `.md` files with anyone

<br />

## ⚡ Inference Tiers

Same app. Same skills. Same memory. Only the brain source changes.

| Tier | Brain | Requirements | Best For |
|---|---|---|---|
| 💻 **Local Lite** | Ollama + Q4_K_M SLM | 6+ GB RAM, no GPU | Old laptops, offline use |
| 🚀 **Local Power** | Ollama + Q5/Q8 SLM | 16+ GB RAM or GPU | Powerful machines |
| ☁️ **Cloud** | OpenAI / Claude / Gemini API | Internet + API key | No local hardware, best quality |
| 🍓 **Pi Server** | Ollama + Q4_K_M on Pi 5 | Pi 5 8GB, always-on | Home AI server |

Switch tiers instantly in the sidebar — no restart required.

<br />

## 💻 Hardware Guide

### Minimum Requirements

| Spec | Minimum | Recommended |
|---|---|---|
| **RAM** | 6 GB | 8 GB+ |
| **Disk** | 5 GB free | 10 GB free |
| **CPU** | Any x64 with AVX2 | Ryzen 5000+ / Intel 10th gen+ |
| **GPU** | Not required | Nice to have |
| **OS** | Windows 10+ / Linux / macOS | Any |
| **Disk type** | HDD works (slower) | SSD preferred |

### Recommended Models by Hardware

| Your Hardware | Recommended Model | Size | Notes |
|---|---|---|---|
| 4–6 GB RAM | `qwen3:1.7b` | ~1 GB | Fast, basic tasks |
| 6–8 GB RAM | `qwen3:4b` (Q4_K_M) | ~2.5 GB | **Best balance** — recommended default |
| 8–16 GB RAM | `llama3.2:8b` | ~4.7 GB | Stronger reasoning |
| 16+ GB RAM / GPU | `qwen3:8b` (Q8) | ~8 GB | Near cloud-level quality |

<br />

## 🔌 API Reference

The backend exposes a full REST API at `http://localhost:8000`. Interactive docs are available at `/docs` (Swagger UI).

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message, get a response |
| `POST` | `/api/chat/stream` | Streaming chat via Server-Sent Events |
| `GET` | `/api/health` | Health check & system status |

### Skills

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/skills` | List all available skill files |
| `POST` | `/api/skills/activate` | Activate a skill by filename |
| `POST` | `/api/skills/deactivate` | Deactivate a skill |
| `POST` | `/api/skills/validate` | Validate a skill file |
| `POST` | `/api/skills/upload` | Upload a skill file (drag & drop) |

### Memory

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/memory/stats` | Memory statistics (count, size) |
| `POST` | `/api/memory/query` | Query memory for relevant context |
| `DELETE` | `/api/memory/clear` | Clear all memory entries |

### Models

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/models/available` | List models available for download |
| `GET` | `/api/models/installed` | List locally installed models |
| `GET` | `/api/models/active` | Get currently active model |
| `POST` | `/api/models/switch` | Switch to a different model |
| `POST` | `/api/models/download` | Download a model via Ollama |

### Settings

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/settings/tier` | Get current inference tier |
| `POST` | `/api/settings/tier` | Switch inference tier |

<br />

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend Shell** | Tauri 2.x (Rust + HTML/CSS/JS) | Tiny binary (~5 MB), cross-platform |
| **Frontend UI** | Vanilla HTML + CSS + JS | No framework bloat, works everywhere |
| **Backend API** | Python 3.11+ / FastAPI | Best AI ecosystem, async, fast |
| **SLM Runtime** | Ollama (wraps llama.cpp) | One-command install, model management built-in |
| **Memory / RAG** | ChromaDB (SQLite backend) | Persistent, lightweight, local |
| **Embeddings** | all-MiniLM-L6-v2 (Sentence Transformers) | ~90 MB, runs on CPU, good quality |
| **Web Search** | DuckDuckGo Search | Free, no API key, no rate limits |
| **IPC** | Tauri ↔ FastAPI via localhost REST | Clean separation of concerns |

<br />

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Contribution Ideas

- 🌍 New skill files for specific use cases
- 🎨 UI/UX improvements
- 🧪 Test coverage
- 📖 Documentation improvements
- 🐛 Bug fixes
- 🔧 Performance optimizations

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/blue-dragon-ai-hub.git
cd blue-dragon-ai-hub

# Backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt

# Run backend with hot reload
cd backend
uvicorn main:app --reload --port 8000
```

<br />

## 🎯 Design Principles

| # | Principle | Description |
|---|---|---|
| 1 | **Local First** | Everything works offline after initial setup |
| 2 | **CPU First** | GPU is a bonus, never a requirement |
| 3 | **Zero Telemetry** | No data leaves the machine — ever |
| 4 | **Skill Files Are Text** | Never executed, only parsed and injected |
| 5 | **Google Forms Easy** | If a setting needs code, redesign it |
| 6 | **Open Source (MIT)** | Free forever, fork freely |
| 7 | **Small Footprint** | Total install < 4 GB including model |
| 8 | **Tier Flexible** | Cloud ↔ Local ↔ Pi — skills and memory follow |

<br />

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

<br />

## 🙏 Acknowledgments

- [Ollama](https://ollama.com) — for making local LLM inference dead simple
- [FastAPI](https://fastapi.tiangolo.com) — the backbone of our API layer
- [ChromaDB](https://www.trychroma.com) — lightweight, embeddable vector database
- [Sentence Transformers](https://sbert.net) — efficient CPU-friendly embeddings
- [Tauri](https://tauri.app) — for tiny, fast, cross-platform desktop apps
- [DuckDuckGo](https://duckduckgo.com) — privacy-respecting search with no API keys

---

<p align="center">
  <strong>🐉 Built with love for everyone — old laptops, no GPU, minimum specs.</strong>
  <br />
  <sub>Open source. Free will. Your data stays yours.</sub>
</p>
