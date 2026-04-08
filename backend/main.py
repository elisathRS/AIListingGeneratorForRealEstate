import os
import uuid
import json
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image as _PilImage
from dotenv import load_dotenv

load_dotenv()

from services.ai_service import generate_description, generate_instagram_caption
from services.pdf_service import generate_pdf
from services.image_service import generate_instagram_image
from services.instagram_service import post_to_instagram as _post_to_instagram

# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="ListPro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Security headers ─────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# In-memory store — survives the request but not a server restart.
# _get_listing() falls back to disk so restarts never cause 404s.
listings: dict = {}

# Video render job status: listing_id -> "rendering" | "done" | "error"
video_jobs: dict = {}

VIDEO_DIR = BASE_DIR.parent / "video"


# ── Security helpers ─────────────────────────────────────────
MAX_UPLOAD_BYTES = 15 * 1024 * 1024   # 15 MB per photo
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_PROPERTY_TYPES = {"House", "Apartment", "Land", "Penthouse"}
ALLOWED_OPERATIONS = {"Sale", "Rent"}


def _valid_listing_id(listing_id: str) -> bool:
    """Return True only if listing_id is a valid UUID4 and stays within UPLOADS_DIR."""
    try:
        uuid.UUID(listing_id, version=4)
    except ValueError:
        return False
    resolved = (UPLOADS_DIR / listing_id).resolve()
    return str(resolved).startswith(str(UPLOADS_DIR.resolve()))


async def _validate_image(upload: UploadFile) -> bytes:
    """Read upload, enforce size + type limits, verify it's a real image."""
    content = await upload.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"Image too large (max 15 MB): {upload.filename}")
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{suffix}'. Use JPG, PNG, or WebP.")
    try:
        import io
        img = _PilImage.open(io.BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail=f"File is not a valid image: {upload.filename}")
    return content


def _save_listing(listing_id: str, data: dict):
    """Persist listing to disk so it survives server restarts."""
    path = UPLOADS_DIR / listing_id / "data.json"
    with open(path, "w") as f:
        json.dump(data, f)


def _get_listing(listing_id: str) -> dict | None:
    """Return listing from memory, falling back to disk if needed."""
    if listing_id in listings:
        return listings[listing_id]
    data_file = UPLOADS_DIR / listing_id / "data.json"
    if data_file.exists():
        with open(data_file) as f:
            data = json.load(f)
        listings[listing_id] = data   # warm the cache
        return data
    return None


# ---------------------------------------------------------------------------
# HTML page routes
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/results")
async def serve_results():
    return FileResponse(str(FRONTEND_DIR / "results.html"))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Phase 1 stub — /api/generate
# Accepts the full form, saves photos, returns placeholder content.
# Real Gemini calls will replace the placeholder text in Phase 2.
# ---------------------------------------------------------------------------
@app.post("/api/generate")
async def generate_listing(
    # Property details
    property_type: str = Form(...),
    operation: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    price: float = Form(...),
    bedrooms: int = Form(...),
    bathrooms: int = Form(...),
    built_area: float = Form(...),
    land_area: Optional[float] = Form(None),
    parking: int = Form(...),
    # Amenities arrive as a comma-separated string from the frontend
    amenities: Optional[str] = Form(""),
    # Agent notes
    agent_notes: Optional[str] = Form(""),
    # Agent info
    agent_name: str = Form(...),
    agent_phone: str = Form(...),
    agent_email: str = Form(...),
    # Photos
    cover_photo: UploadFile = File(...),
    additional_photos: List[UploadFile] = File(default=[]),
):
    # ── Input validation ────────────────────────────────────────
    if property_type not in ALLOWED_PROPERTY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid property type.")
    if operation not in ALLOWED_OPERATIONS:
        raise HTTPException(status_code=400, detail="Invalid operation. Use Sale or Rent.")
    if not (0 < price < 1_000_000_000):
        raise HTTPException(status_code=400, detail="Price must be between $1 and $1,000,000,000.")
    if not (0 <= bedrooms <= 20):
        raise HTTPException(status_code=400, detail="Bedrooms must be between 0 and 20.")
    if not (0 <= bathrooms <= 20):
        raise HTTPException(status_code=400, detail="Bathrooms must be between 0 and 20.")
    if built_area <= 0:
        raise HTTPException(status_code=400, detail="Built area must be greater than 0.")
    if len(address) > 200 or len(city) > 100 or len(agent_name) > 100:
        raise HTTPException(status_code=400, detail="Text field exceeds maximum length.")
    if agent_notes and len(agent_notes) > 2000:
        raise HTTPException(status_code=400, detail="Agent notes exceed 2000 characters.")

    # ── Validate & save photos ──────────────────────────────────
    listing_id = str(uuid.uuid4())
    listing_dir = UPLOADS_DIR / listing_id
    listing_dir.mkdir(parents=True, exist_ok=True)

    cover_data = await _validate_image(cover_photo)
    cover_ext  = Path(cover_photo.filename).suffix.lower() or ".jpg"
    cover_path = listing_dir / f"cover{cover_ext}"
    cover_path.write_bytes(cover_data)

    photo_paths = []
    if additional_photos:
        for i, photo in enumerate(additional_photos):
            if photo.filename:
                data = await _validate_image(photo)
                ext  = Path(photo.filename).suffix.lower() or ".jpg"
                photo_path = listing_dir / f"photo_{i + 1}{ext}"
                photo_path.write_bytes(data)
                photo_paths.append(str(photo_path))

    amenities_list = [a.strip() for a in amenities.split(",") if a.strip()] if amenities else []

    property_data = {
        "property_type": property_type,
        "operation": operation,
        "address": address,
        "city": city,
        "state": state,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "built_area": built_area,
        "land_area": land_area,
        "parking": parking,
        "amenities": amenities_list,
        "agent_notes": agent_notes,
        "agent_name": agent_name,
        "agent_phone": agent_phone,
        "agent_email": agent_email,
        "cover_photo_path": str(cover_path),
        "additional_photo_paths": photo_paths,
    }

    # ------------------------------------------------------------------
    # Phase 2 — Gemini AI generation
    # ------------------------------------------------------------------
    try:
        description = await generate_description(property_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Description generation failed: {e}")

    try:
        instagram_caption = await generate_instagram_caption(property_data, description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {e}")

    # ------------------------------------------------------------------
    # Phase 3 — PDF + Instagram image generation (run in parallel threads)
    # ------------------------------------------------------------------
    loop = asyncio.get_event_loop()

    async def _run_pdf():
        try:
            await loop.run_in_executor(None, generate_pdf, listing_id, property_data, photo_paths, description)
            return True
        except Exception as e:
            print(f"[PDF] Generation failed: {e}")
            return False

    async def _run_image():
        try:
            await loop.run_in_executor(None, generate_instagram_image, listing_id, property_data, str(cover_path))
            return True
        except Exception as e:
            print(f"[Image] Generation failed: {e}")
            return False

    has_pdf, has_image = await asyncio.gather(_run_pdf(), _run_image())

    # Store in memory AND persist to disk
    record = {
        **property_data,
        "description": description,
        "instagram_caption": instagram_caption,
        "listing_id": listing_id,
        "has_pdf": has_pdf,
        "has_image": has_image,
    }
    listings[listing_id] = record
    _save_listing(listing_id, record)

    return JSONResponse({
        "listing_id": listing_id,
        "description": description,
        "instagram_caption": instagram_caption,
        "property_data": property_data,
        "has_pdf": has_pdf,
        "has_image": has_image,
    })


# ---------------------------------------------------------------------------
# Download routes — listing_id validated to prevent path traversal
# ---------------------------------------------------------------------------
@app.get("/api/pdf/{listing_id}")
async def get_pdf(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    pdf_path = UPLOADS_DIR / listing_id / "listing.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(str(pdf_path), media_type="application/pdf", filename="listing.pdf")


@app.get("/api/image/{listing_id}")
async def get_image(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    image_path = UPLOADS_DIR / listing_id / "instagram.jpg"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(str(image_path), media_type="image/jpeg", filename="instagram.jpg")


@app.post("/api/instagram/{listing_id}")
async def post_to_instagram(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    image_path = UPLOADS_DIR / listing_id / "instagram.jpg"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Instagram image not found")
    record  = _get_listing(listing_id)
    caption = record.get("instagram_caption", "") if record else ""
    result  = await _post_to_instagram(str(image_path), caption)
    return JSONResponse(result)


async def _render_video(listing_id: str, record: dict):
    """Run Remotion render as a background task."""
    try:
        # Use the locally installed remotion binary to avoid npx interactive prompts
        remotion_bin = VIDEO_DIR / "node_modules" / ".bin" / "remotion"
        if not remotion_bin.exists():
            print("[Video] ERROR: Remotion not installed. Run: cd video && npm install")
            video_jobs[listing_id] = "error"
            return

        # Copy photos into video/public/photos/{listing_id}/
        photos_dir = VIDEO_DIR / "public" / "photos" / listing_id
        photos_dir.mkdir(parents=True, exist_ok=True)

        all_sources = [record.get("cover_photo_path", "")] + record.get("additional_photo_paths", [])
        photo_keys = []
        for i, src in enumerate(all_sources):
            if src and Path(src).exists():
                dst = photos_dir / f"photo_{i}.jpg"
                shutil.copy2(src, str(dst))
                photo_keys.append(f"photos/{listing_id}/photo_{i}.jpg")

        if not photo_keys:
            print("[Video] ERROR: no photos found for this listing")
            video_jobs[listing_id] = "error"
            return

        output_path = UPLOADS_DIR / listing_id / "reel.mp4"

        props = {
            "photos":     photo_keys,
            "price":      record.get("price", 0),
            "city":       record.get("city", ""),
            "state":      record.get("state", ""),
            "bedrooms":   record.get("bedrooms", 0),
            "bathrooms":  record.get("bathrooms", 0),
            "built_area": record.get("built_area", 0),
            "operation":  record.get("operation", "Sale"),
            "agentName":  record.get("agent_name", ""),
            "agentPhone": record.get("agent_phone", ""),
            "agentEmail": record.get("agent_email", ""),
        }

        print(f"[Video] Starting render for {listing_id} …")
        proc = await asyncio.create_subprocess_exec(
            str(remotion_bin), "render",
            "src/index.ts", "PropertyReel",
            str(output_path),
            "--props", json.dumps(props),
            cwd=str(VIDEO_DIR),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode == 0:
            print(f"[Video] Render done → {output_path}")
            video_jobs[listing_id] = "done"
        else:
            err = stderr.decode()[:600]
            print(f"[Video] Render failed (exit {proc.returncode}):\n{err}")
            video_jobs[listing_id] = "error"

    except Exception as e:
        print(f"[Video] Exception: {e}")
        video_jobs[listing_id] = "error"


@app.post("/api/video/{listing_id}")
async def start_video(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    record = _get_listing(listing_id)
    if not record:
        raise HTTPException(status_code=404, detail="Listing not found")
    video_jobs[listing_id] = "rendering"
    asyncio.create_task(_render_video(listing_id, record))
    return JSONResponse({"status": "rendering", "listing_id": listing_id})


@app.get("/api/video/status/{listing_id}")
async def video_status(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    if not _get_listing(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    status = video_jobs.get(listing_id, "pending")
    return {"status": status}


@app.get("/api/video/download/{listing_id}")
async def download_video(listing_id: str):
    if not _valid_listing_id(listing_id):
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    video_path = UPLOADS_DIR / listing_id / "reel.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found. Generate it first.")
    return FileResponse(str(video_path), media_type="video/mp4", filename="listing_reel.mp4")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
