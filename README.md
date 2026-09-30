# 🏗️ GoTec.AI — Design Engine (POC)

> **AI-powered floor plan generator for Indian real estate.**
> Prompt → 2D plan → 3D model, in seconds. Built on open-source models.

[![Status](https://img.shields.io/badge/status-POC-yellow)]()
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## ✨ Features

- 🧠 **LLM-powered prompt parsing** — Mistral-7B extracts structured specs from natural language
- 📐 **Text → 2D floor plan** — Stable Diffusion XL renders architectural blueprints
- 🧊 **2D → 3D model** — TripoSR reconstructs 3D geometry, viewed live in browser
- 🕉️ **Vastu-aware** — Room zones (NE pooja, SW master bedroom, SE kitchen) baked into spec
- 🌏 **Indian-first** — City-specific bylaws support (Mumbai DCR, Delhi MPD ready)
- ⚡ **Zero cost** — Runs on HuggingFace free tier + open-source models

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS, Three.js (R3F) |
| Backend | FastAPI (Python 3.11), Pydantic |
| LLM | `mistralai/Mistral-7B-Instruct-v0.3` |
| 2D Image | `stabilityai/stable-diffusion-xl-base-1.0` |
| 3D Model | `stabilityai/TripoSR` |
| Hosting (planned) | Vercel (frontend) + Railway (backend) |

---

## 📁 Project Structure

```
GoTech.AI/
├── backend/                      # FastAPI + HuggingFace
│   ├── app/
│   │   ├── main.py              # API entry point
│   │   ├── llm_parser.py        # Mistral prompt → spec
│   │   ├── image_generator.py   # SDXL → 2D PNG
│   │   ├── model_3d.py          # TripoSR → 3D GLB
│   │   ├── schemas.py           # Pydantic models
│   │   └── config.py            # Env + paths
│   ├── requirements.txt
│   ├── .env.example             # Template (commit this)
│   ├── start.bat                # Windows launcher
│   └── start.sh                 # Git Bash launcher
│
├── frontend/gotec-web/           # Next.js 16 website
│   ├── app/
│   │   ├── page.tsx             # Landing page
│   │   └── design/page.tsx      # Design studio
│   ├── components/
│   │   ├── Viewer3D.tsx         # Three.js 3D viewer
│   │   └── SpecPanel.tsx        # Spec display
│   ├── lib/api.ts               # Backend client
│   └── package.json
│
├── docs/                          # Screenshots & assets
├── .gitignore                    # Excludes .env, venv, node_modules, etc.
├── README.md
├── start.bat                     # Windows: launch both servers
└── start-all.sh                  # Git Bash: launch both servers
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** + npm
- **Git** (for cloning)

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/gotec-ai.git
cd gotec-ai
```

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Windows (PowerShell / CMD)
.\venv\Scripts\activate
# Git Bash
source venv/Scripts/activate

pip install -r requirements.txt
cp .env.example .env        # macOS/Linux
copy .env.example .env      # Windows
```

**Edit `backend/.env` and add your HuggingFace token:**
```env
HF_TOKEN=hf_your_token_here
FRONTEND_URL=http://localhost:3000
```

> 🔑 **Get a free HF token:** https://huggingface.co/settings/tokens  
> Create token → Type: **Fine-grained** → Preset: **Inference**

```bash
uvicorn app.main:app --reload --port 8000
```

✅ Backend live at: **http://localhost:8000**  
📖 Swagger docs: **http://localhost:8000/docs**

### 3. Frontend setup

```bash
cd frontend/gotec-web
npm install
npm run dev
```

✅ Frontend live at: **http://localhost:3000**

### 4. Try it!

1. Open **http://localhost:3000**
2. Click **"Try Demo"** → goes to **/design**
3. Type or pick an example prompt:
   > *"3BHK in Mumbai, 1200 sqft, north facing, Vastu compliant, with pooja room"*
4. Click **"Generate Design"**
5. View **2D plan** + **3D model** side by side 🎉

---

## 🎯 One-Click Launchers

| OS | Script | Action |
|----|--------|--------|
| **Windows (CMD)** | `start.bat` (root) | Opens both servers in separate windows |
| **Git Bash / MINGW64** | `./start-all.sh` | Opens both servers in separate windows |
| **Windows Backend only** | `backend/start.bat` | Starts FastAPI |
| **Windows Frontend only** | `frontend/gotec-web/start.bat` | Starts Next.js |

---

## 📸 Demo

![Landing Page](docs/landing.png)
![Design Studio](docs/design-studio.png)

---

## 🔌 API Reference

### `POST /api/generate`

Full pipeline: prompt → spec → 2D → 3D

**Request:**
```json
{
  "prompt": "3BHK, 1200 sqft, north facing, Vastu compliant"
}
```

**Response:**
```json
{
  "success": true,
  "spec": {
    "bhk": 3,
    "total_area_sqft": 1200,
    "facing": "north",
    "vastu_compliant": true,
    "rooms": [
      {"type": "master_bedroom", "area_sqft": 200, "vastu_zone": "south_west"}
    ]
  },
  "image_2d_url": "/generated/plan_xxx.png",
  "model_3d_url": "/generated/model_xxx.glb",
  "processing_time_sec": 2.4,
  "message": "Generated 3BHK, 1200 sqft design."
}
```

### `GET /api/health`
Health check → `{"status":"ok"}`

### `GET /docs`
Interactive Swagger UI

---

## 💡 How It Works

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  User Prompt     │ →  │  Mistral-7B LLM  │ →  │  Structured Spec │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                          ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Three.js Viewer │ ←  │  TripoSR         │ ←  │  SDXL 2D Image   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

1. **Parse**: Mistral extracts BHK, area, facing, rooms, Vastu zones from natural language
2. **Generate 2D**: SDXL renders an architectural floor plan based on the spec
3. **Generate 3D**: TripoSR reconstructs 3D geometry from the 2D image
4. **Display**: Three.js shows the interactive 3D model in the browser

---

## 🛡️ Without HF Token (Fallback Mode)

If `HF_TOKEN` is not set, the backend uses built-in mocks:
- LLM → rule-based parser (regex)
- 2D → PIL-generated placeholder plan
- 3D → empty GLB shell (Three.js builds procedurally)

This lets you develop and demo the **full pipeline UI** without burning HF credits.

---

## 🗺️ Roadmap

### Phase 1 — POC (current)
- [x] Text → JSON spec via LLM
- [x] 2D plan via SDXL
- [x] 3D model via TripoSR
- [x] Beautiful Next.js demo UI
- [x] Three.js interactive viewer

### Phase 2 — Validation Engine (next 4-6 weeks)
- [ ] Vastu compliance validator (per-room zones)
- [ ] City-specific bylaws: Mumbai DCR, Delhi MPD, Bangalore BDA
- [ ] Min/max room dimension enforcement
- [ ] Adjacency rule checker

### Phase 3 — Customization (month 2-3)
- [ ] Real floor plan training data (5000+ scraped layouts)
- [ ] ML layout generator (replace rule-based)
- [ ] Editable UI (drag walls, resize rooms)

### Phase 4 — Full Platform (month 4+)
- [ ] Land data scraper (RERA, MagicBricks, 99acres)
- [ ] BOQ + material cost estimator
- [ ] Multi-floor support
- [ ] Pilot with 2-3 builder clients

---

## 🧪 Testing the API

```bash
# Health check
curl http://localhost:8000/api/health

# Generate design
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"3BHK in Mumbai, 1200 sqft, north facing, Vastu compliant, with pooja room"}'
```

---

## 🤝 Contributing

This is a private POC for the GoTec.AI founding team. Collaboration is internal.

---

## 📜 License

MIT (or whatever you choose — change this line)

---

## 👥 Team

Built with ❤️ for the Indian real estate ecosystem.
