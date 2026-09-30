"""FastAPI app - GoTec Design Engine"""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

from .config import FRONTEND_URL, GENERATED_DIR
from .schemas import PromptRequest, GenerateResponse
from .llm_parser import parse_prompt_with_llm
from .image_generator import generate_2d_image
from .model_3d import generate_3d_from_image

app = FastAPI(
    title="GoTec Design Engine",
    description="AI-powered floor plan generator (text -> 2D -> 3D)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files (images, 3D models)
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")


@app.get("/")
def root():
    return {
        "name": "GoTec Design Engine",
        "version": "0.1.0",
        "status": "running",
        "endpoints": ["/api/generate", "/api/health", "/docs"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gotec-design"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate_design(req: PromptRequest):
    """Full pipeline: prompt -> spec -> 2D image -> 3D model."""
    start = time.time()

    # Stage 1: LLM parses prompt into structured spec
    spec = parse_prompt_with_llm(req.prompt)

    # Stage 2: Generate 2D floor plan image
    image_url = generate_2d_image(spec)
    image_path = GENERATED_DIR / Path(image_url).name

    # Stage 3: Generate 3D model from 2D image
    model_url = generate_3d_from_image(image_path)

    elapsed = round(time.time() - start, 2)
    return GenerateResponse(
        success=True,
        spec=spec,
        image_2d_url=image_url,
        model_3d_url=model_url,
        processing_time_sec=elapsed,
        message=f"Generated {spec.bhk}BHK, {int(spec.total_area_sqft)} sqft design.",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": str(exc)},
    )
