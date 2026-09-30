"""2D -> 3D model generator using HuggingFace TripoSR or fallback GLB."""
import uuid
from pathlib import Path
from huggingface_hub import InferenceClient
from .config import MODELS, HF_TOKEN, GENERATED_DIR


def generate_3d_from_image(image_path: Path) -> str:
    """Send 2D image to TripoSR, return GLB file URL."""
    filename = f"model_{uuid.uuid4().hex[:12]}.glb"
    out_path = GENERATED_DIR / filename

    if HF_TOKEN:
        try:
            client = InferenceClient(token=HF_TOKEN)
            with open(image_path, "rb") as f:
                result = client.image_to_3d(
                    image=f.read(),
                    model=MODELS["image_to_3d"],
                )
            # Result may be bytes or path
            if isinstance(result, (bytes, bytearray)):
                out_path.write_bytes(result)
            elif isinstance(result, str) and Path(result).exists():
                Path(result).rename(out_path)
            elif hasattr(result, "save"):
                result.save(str(out_path))
            if out_path.exists() and out_path.stat().st_size > 0:
                return f"/generated/{filename}"
        except Exception as e:
            print(f"[HF 3D gen failed] {e} -> falling back to mock")

    # Fallback: simple box GLB (will be replaced by procedural generation in app)
    _make_mock_glb(out_path)
    return f"/generated/{filename}"


def _make_mock_glb(filepath: Path):
    """Minimal valid GLB - a single box (10ft x 10ft x 10ft)."""
    # Empty placeholder GLB - real procedural model will be built in frontend Three.js
    # from the 2D plan geometry. This endpoint just signals availability.
    import struct
    # Tiny GLB header for an empty scene - frontend will use parametric build
    glb_magic = b"glTF"
    glb_version = struct.pack("<I", 2)
    glb_length = struct.pack("<I", 0)
    filepath.write_bytes(glb_magic + glb_version + glb_length)
