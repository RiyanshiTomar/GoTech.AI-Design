"""2D floor plan image generator using HuggingFace SDXL."""
import uuid
import base64
from pathlib import Path
from huggingface_hub import InferenceClient
from .config import MODELS, HF_TOKEN, GENERATED_DIR
from .schemas import DesignSpec


def _build_prompt(spec: DesignSpec) -> str:
    rooms = ", ".join(r.type.replace("_", " ") for r in spec.rooms[:8])
    return (
        f"Architectural top-down 2D floor plan blueprint, {spec.bhk}BHK house, "
        f"{int(spec.total_area_sqft)} sqft, {spec.facing} facing, "
        f"rooms: {rooms}. Clean black line drawing on white background, "
        f"technical architectural style, no perspective, no 3D, "
        f"walls shown as thick black lines, doors as arcs, windows as parallel lines, "
        f"room labels visible, dimensions annotated. "
        f"Professional CAD-style blueprint, high contrast, vector quality."
    )


def generate_2d_image(spec: DesignSpec) -> str:
    """Generate 2D floor plan image, return URL path."""
    prompt = _build_prompt(spec)
    filename = f"plan_{uuid.uuid4().hex[:12]}.png"
    filepath = GENERATED_DIR / filename

    if HF_TOKEN:
        try:
            client = InferenceClient(token=HF_TOKEN)
            image = client.text_to_image(
                prompt=prompt,
                model=MODELS["text_to_2d"],
                width=1024,
                height=1024,
            )
            image.save(str(filepath))
            return f"/generated/{filename}"
        except Exception as e:
            print(f"[HF image gen failed] {e} -> falling back to mock")

    # Fallback: programmatic placeholder using PIL
    _make_mock_plan(filepath, spec)
    return f"/generated/{filename}"


def _make_mock_plan(filepath: Path, spec: DesignSpec):
    """Generate a clean SVG-style mock floor plan with PIL."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Outer boundary (plot)
    margin = 80
    plot_w = W - 2 * margin
    plot_h = H - 2 * margin
    draw.rectangle([margin, margin, margin + plot_w, margin + plot_h],
                   outline="black", width=6)

    # Divide plot into rooms based on spec
    n = max(1, len(spec.rooms))
    cols = (n + 1) // 2
    rows = 2 if n > cols else 1
    cell_w = plot_w / max(1, cols)
    cell_h = plot_h / max(1, rows)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
        small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        small = font

    for i, room in enumerate(spec.rooms[: n]):
        c = i % cols
        r = i // cols
        x1 = margin + c * cell_w
        y1 = margin + r * cell_h
        x2 = x1 + cell_w
        y2 = y1 + cell_h
        draw.rectangle([x1 + 2, y1 + 2, x2 - 2, y2 - 2], outline="#1f2937", width=3)
        label = room.type.replace("_", " ").title()
        if room.area_sqft:
            label += f"\n{int(room.area_sqft)} sqft"
        draw.text((x1 + 12, y1 + 12), label, fill="#111827", font=font)

    # Title block
    draw.text((margin, H - 60),
              f"GoTec.AI - {spec.bhk}BHK - {int(spec.total_area_sqft)} sqft - {spec.facing} facing",
              fill="#0f172a", font=font)
    draw.text((margin, H - 32),
              "Conceptual layout (AI-generated mock)",
              fill="#64748b", font=small)

    img.save(filepath)
