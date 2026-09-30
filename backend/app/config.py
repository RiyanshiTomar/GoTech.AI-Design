"""Configuration & environment setup"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# HuggingFace API key (free tier: https://huggingface.co/settings/tokens)
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Output folders
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

# CORS (frontend URL)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Model IDs (HF Inference API compatible)
MODELS = {
    "llm": "mistralai/Mistral-7B-Instruct-v0.3",
    "text_to_2d": "stabilityai/stable-diffusion-xl-base-1.0",
    # HF Spaces (image -> GLB), tried in order. Runs on HF_TOKEN only.
    "image_to_3d_spaces": [
        "trellis-community/TRELLIS",
        "JeffreyXiang/TRELLIS",
    ],
}
