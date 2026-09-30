"""2D floor plan -> real 3D model (GLB) using TRELLIS on a Hugging Face Space.

Runs with only HF_TOKEN (uses the free ZeroGPU quota of your HF account).
If the Space is busy or out of quota, returns None and the frontend falls
back to a 3D layout built from the design spec.
"""
import shutil
import traceback
import uuid
from pathlib import Path
from typing import Optional

from .config import MODELS, HF_TOKEN, GENERATED_DIR


LAST_ERROR: Optional[str] = None


def _find_glb(result) -> Optional[str]:
    """Pick the .glb path out of whatever the Space returned."""
    items = result if isinstance(result, (tuple, list)) else [result]
    for it in items:
        if isinstance(it, dict):
            it = it.get("value") or it.get("path") or it.get("url")
        if isinstance(it, str) and it.lower().endswith(".glb") and Path(it).exists():
            return it
    return None


def _try_space(space: str, image_path: Path) -> Optional[str]:
    from gradio_client import Client, handle_file

    client = Client(space, token=HF_TOKEN, verbose=False)
    endpoints = client.view_api(return_format="dict", print_info=False).get("named_endpoints", {})
    print(f"[3D] {space} endpoints: {list(endpoints)}")
    img = handle_file(str(image_path))

    # The Space keeps a per-session temp folder; it must be created first.
    if "/start_session" in endpoints:
        try:
            client.predict(api_name="/start_session")
        except Exception as e:
            print(f"[3D] start_session skipped: {e!r}")
    # Same background-removal / crop step the Space runs in its own UI.
    if "/preprocess_image" in endpoints:
        try:
            name = endpoints["/preprocess_image"]["parameters"][0]["parameter_name"]
            out = client.predict(api_name="/preprocess_image", **{name: img})
            if isinstance(out, str) and Path(out).exists():
                img = handle_file(out)
            elif isinstance(out, dict) and out.get("path"):
                img = handle_file(out["path"])
        except Exception as e:
            print(f"[3D] preprocess_image skipped: {e!r}")
    values = dict(
        image=img, multiimages=None, is_multiimage=False, seed=0,
        ss_guidance_strength=7.5, ss_sampling_steps=12,
        slat_guidance_strength=3, slat_sampling_steps=12,
        multiimage_algo="stochastic", mesh_simplify=0.95, texture_size=1024,
    )

    def call(api_name: str):
        # Only pass the parameters this Space's endpoint really accepts.
        params = endpoints[api_name].get("parameters", [])
        names = [p.get("parameter_name") for p in params]
        print(f"[3D] {api_name} params: {names}")
        kwargs = {n: values[n] for n in names if n in values}
        # first image-like param gets the picture even if it has another name
        for p in params:
            n = p.get("parameter_name")
            if n not in values and "image" in n and "multi" not in n:
                kwargs[n] = img
        return client.predict(api_name=api_name, **kwargs)

    if "/generate_and_extract_glb" in endpoints:  # one-call Spaces
        return _find_glb(call("/generate_and_extract_glb"))

    # two-step Spaces: image -> latent, then latent -> GLB
    call("/image_to_3d")
    return _find_glb(call("/extract_glb"))


def generate_3d_from_image(image_path: Path) -> Optional[str]:
    """Return /generated/<file>.glb, or None if real 3D generation failed."""
    global LAST_ERROR
    LAST_ERROR = None
    if not HF_TOKEN:
        LAST_ERROR = "HF_TOKEN missing in backend/.env"
        print("[3D] HF_TOKEN missing -> using spec-based 3D in frontend")
        return None
    for space in MODELS["image_to_3d_spaces"]:
        try:
            glb = _try_space(space, image_path)
            if glb and Path(glb).stat().st_size > 1024:
                filename = f"model_{uuid.uuid4().hex[:12]}.glb"
                shutil.copy(glb, GENERATED_DIR / filename)
                print(f"[3D] OK via {space}")
                return f"/generated/{filename}"
            LAST_ERROR = f"{space}: no GLB file in result"
            print(f"[3D] {space}: no GLB in result")
        except Exception as e:
            LAST_ERROR = f"{space}: {type(e).__name__}: {e}"[:300]
            print(f"[3D] {space} failed: {e!r}")
            traceback.print_exc()
    return None
