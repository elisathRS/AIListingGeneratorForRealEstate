# ListPro — Implementation Plan

**Version:** 1.0
**Project:** ListPro — AI-Powered Real Estate Listing Generator

> **How to use this checklist:** Mark each item `[x]` when complete. Every phase delivers a working, testable product increment — you never need to wait until the end to see results.

---

## Phase 1 — Project Foundation & Working Form
> **Goal:** A running local server with a complete, styled web form that submits data and returns a placeholder response. Agents can open the app and fill out the form on day one.

### 1.1 Project Scaffold
- [ ] Create the full folder structure as defined in the PRD (`backend/`, `frontend/`, `video/`, `docs/`)
- [ ] Create `backend/requirements.txt` with all Python dependencies
- [ ] Create `backend/.env.example` with `GEMINI_API_KEY` and `UPLOADPOST_API_KEY` placeholders
- [ ] Create `backend/.env` (copied from `.env.example`, not committed to git)
- [ ] Create `backend/services/__init__.py` (empty, marks folder as Python package)
- [ ] Create `backend/uploads/` directory (with a `.gitkeep` so it's tracked)

### 1.2 FastAPI Backend — Server & Routing
- [ ] Create `backend/main.py` with FastAPI app instance
- [ ] Add CORS middleware (allow all origins for local development)
- [ ] Mount `frontend/` as static file directory
- [ ] Add `GET /` route → serves `frontend/index.html`
- [ ] Add `GET /results` route → serves `frontend/results.html`
- [ ] Add `GET /health` route → returns `{"status": "ok"}` (used for smoke testing)
- [ ] Add stub `POST /api/generate` route → accepts multipart form, returns hardcoded JSON placeholder
- [ ] Configure Uvicorn to run on `localhost:8000`

### 1.3 Frontend — Form Page (`index.html`)
- [ ] Create HTML page with ListPro header and brand color `#1B4F8A`
- [ ] Add all form fields per PRD §4.1:
  - [ ] Property Type (select: House, Apartment, Land, Penthouse)
  - [ ] Operation (radio: Sale / Rent)
  - [ ] Address / Location (text)
  - [ ] City (text)
  - [ ] State (select with all 50 U.S. states + DC)
  - [ ] Price in USD (number)
  - [ ] Bedrooms (number 0–10)
  - [ ] Bathrooms (number 0–10)
  - [ ] Built Area in sq ft (number)
  - [ ] Land Area in sq ft (number, optional)
  - [ ] Parking Spaces (number)
  - [ ] Amenities (10 checkboxes per PRD §4.1.1)
  - [ ] Agent Notes (textarea)
  - [ ] Cover Photo (file input, required, single image)
  - [ ] Additional Photos (file input, multiple)
  - [ ] Agent Name, Phone, Email
- [ ] Add "✨ Generate Listing" submit button
- [ ] Add loading spinner overlay (hidden by default, shown on submit)
- [ ] Add client-side required-field validation before submit

### 1.4 Frontend — Results Page (`results.html`)
- [ ] Create HTML page with ListPro header
- [ ] Add placeholder card for "Professional Description"
- [ ] Add placeholder card for "Instagram Caption"
- [ ] Add four action buttons (disabled for now): Download PDF, Download Image, Post to Instagram, Generate Video
- [ ] Add "← Generate another listing" back link to `index.html`

### 1.5 Frontend — Styles & JavaScript
- [ ] Create `frontend/static/css/styles.css` with:
  - [ ] CSS variables for brand colors (`#1B4F8A`, `#27AE60`, `#F39C12`)
  - [ ] Responsive grid layout (mobile-first)
  - [ ] Form input and button styles
  - [ ] Card component with shadow
  - [ ] Loading spinner animation
  - [ ] Toast notification styles
- [ ] Create `frontend/static/js/app.js` with:
  - [ ] Form submission via `fetch` using `FormData`
  - [ ] Show/hide loading spinner on submit
  - [ ] Save API response to `localStorage`
  - [ ] Redirect to `results.html` on success
  - [ ] On results page: read `localStorage`, populate description and caption cards
  - [ ] Copy-to-clipboard function for both text cards

---

### Phase 1 — Developer Testing
- [ ] Run `pip install -r requirements.txt` — confirm no errors
- [ ] Start server: `uvicorn main:app --reload` from `backend/` — confirm it starts on port 8000
- [ ] `GET http://localhost:8000/health` → expect `{"status": "ok"}`
- [ ] `POST http://localhost:8000/api/generate` with sample multipart form data (use curl or Postman) → expect placeholder JSON response
- [ ] Verify no Python import errors in console on startup

### Phase 1 — Functional Testing (You)
- [ ] Open `http://localhost:8000` in browser → form page loads with ListPro branding
- [ ] Try submitting the form with missing required fields → browser validation blocks submission and highlights missing fields
- [ ] Fill all required fields, attach a cover photo, click "✨ Generate Listing" → loading spinner appears
- [ ] After stub response: page redirects to `http://localhost:8000/results` → placeholder text appears in both cards
- [ ] Click "Copy" on the description card → text copies to clipboard (paste to verify)
- [ ] Open the form on a phone browser → layout is readable and usable without horizontal scrolling

---

## Phase 2 — AI Content Generation (Core Value)
> **Goal:** Real Gemini-generated descriptions and Instagram captions. After Phase 2, agents can use the tool daily to generate all the text content they need.

### 2.1 Gemini AI Service
- [ ] Add `google-generativeai` to `requirements.txt`
- [ ] Create `backend/services/ai_service.py`
- [ ] Load `GEMINI_API_KEY` from `.env` using `python-dotenv`
- [ ] Initialize Gemini client with model `gemini-2.5-pro` (closest available to Gemini Pro 3.1)
- [ ] Write `async def generate_description(property_data: dict) -> str`:
  - [ ] Build a detailed prompt from all property fields (type, operation, price, beds, baths, sq ft, amenities, agent notes, city, state)
  - [ ] Request 3–4 professional paragraphs in English with a call to action at the end
  - [ ] Return generated text string
- [ ] Write `async def generate_instagram_caption(property_data: dict, description: str) -> str`:
  - [ ] Build prompt requesting engaging caption with key stats
  - [ ] Include instruction for 20–30 U.S. real estate hashtags (city-specific where possible)
  - [ ] Return generated caption string
- [ ] Add error handling — if Gemini call fails, raise `HTTPException` with clear message

### 2.2 Wire AI into `/api/generate` Endpoint
- [ ] Replace stub in `main.py` with real logic:
  - [ ] Parse all form fields from multipart request
  - [ ] Generate `listing_id` using `uuid4()`
  - [ ] Create directory `backend/uploads/{listing_id}/`
  - [ ] Save cover photo to `uploads/{listing_id}/cover.jpg`
  - [ ] Save additional photos to `uploads/{listing_id}/photo_1.jpg`, `photo_2.jpg`, etc.
  - [ ] Call `ai_service.generate_description(property_data)`
  - [ ] Call `ai_service.generate_instagram_caption(property_data, description)`
  - [ ] Store all data in in-memory dict: `listings[listing_id] = {...}`
  - [ ] Return JSON: `{listing_id, description, instagram_caption, property_data}`

### 2.3 Results Page — Display Real Content
- [ ] Update `app.js` to display real description and caption from API response
- [ ] Format description with paragraph breaks
- [ ] Format Instagram caption preserving line breaks and hashtags
- [ ] Show property title in page header (e.g., "3-Bed House for Sale — Austin, TX")
- [ ] Enable the four action buttons (they will call their endpoints in Phases 3 & 4)

---

### Phase 2 — Developer Testing
- [ ] Unit test `generate_description()` directly: call function with sample property dict, print output, verify it returns a non-empty string with 3+ paragraphs
- [ ] Unit test `generate_instagram_caption()`: verify output contains at least 15 hashtags starting with `#`
- [ ] `POST /api/generate` via curl/Postman with real image file and all fields — confirm `listing_id`, `description`, and `instagram_caption` in response
- [ ] Confirm `uploads/{listing_id}/` directory is created with photos saved correctly
- [ ] Check server logs for any Gemini API errors or rate limits

### Phase 2 — Functional Testing (You)
- [ ] Fill out the form completely with a real property (use any test address and upload a real photo)
- [ ] Submit → loading spinner shows → results page loads within 15 seconds
- [ ] Read the generated description → verify it is professional, mentions the correct property type, city, price range, and amenities you selected
- [ ] Read the Instagram caption → verify it includes the price, bed/bath count, and at least 15 hashtags relevant to U.S. real estate
- [ ] Click "Copy" on both cards → paste each into a text editor to verify full content copied correctly
- [ ] Submit two different properties back-to-back → verify each generates distinct, unique content
- [ ] Try submitting with only required fields (no amenities, no agent notes) → verify AI still generates sensible output

---

## Phase 3 — PDF, Instagram Image & Auto-Posting
> **Goal:** Agents can download a print-ready PDF flyer, a social media image, and post directly to Instagram from the results page — all in one click.

### 3.1 PDF Generation Service
- [ ] Create `backend/services/pdf_service.py`
- [ ] Import ReportLab (`reportlab.platypus`, `reportlab.lib`)
- [ ] Write `def generate_pdf(listing_id, property_data, photo_paths, description) -> str`:
  - [ ] Create PDF with letter-size page, 0.5-inch margins
  - [ ] **Header:** Full-width colored banner (`#1B4F8A`), white "ListPro" text left, property title right
  - [ ] **Cover photo:** Full-width image, ~4 inches tall
  - [ ] **Key stats row:** 5 colored boxes side-by-side — Price (`$`), Beds, Baths, Sq Ft, Parking
  - [ ] **Additional photos:** 2-column grid, each ~2 inches tall (skip if none)
  - [ ] **Description section:** Heading "Property Description", then full AI text with line wrapping
  - [ ] **Amenities section:** Two-column checklist with checkmark character (✓)
  - [ ] **Agent contact footer:** Horizontal rule, then Name | Phone | Email
  - [ ] Save PDF to `uploads/{listing_id}/listing.pdf`
  - [ ] Return file path

### 3.2 Instagram Image Generation Service
- [ ] Create `backend/services/image_service.py`
- [ ] Import Pillow (`PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`)
- [ ] Write `def generate_instagram_image(listing_id, property_data, cover_photo_path) -> str`:
  - [ ] Open cover photo, resize/crop to exactly 1080×1080 (center crop)
  - [ ] Create dark gradient overlay (numpy array or manual pixel loop): transparent at top, 80% black at bottom 60%
  - [ ] Draw badge top-left: rounded rectangle, blue `#1B4F8A` for Sale, green `#27AE60` for Rent, white text "FOR SALE" or "FOR RENT"
  - [ ] Draw price: large white bold text, centered, lower-middle area
  - [ ] Draw location: medium white text below price (`City, State`)
  - [ ] Draw details row: "🛏 {beds}  🚿 {baths}  📐 {sqft} sq ft" centered, smaller text
  - [ ] Draw bottom strip: semi-transparent dark bar, agent name and phone in white
  - [ ] Save to `uploads/{listing_id}/instagram.jpg` at quality 95
  - [ ] Return file path
- [ ] Add font fallback: try to load a system bold font, fall back to Pillow default if not found

### 3.3 Wire PDF & Image into `/api/generate`
- [ ] Call `pdf_service.generate_pdf(...)` after AI generation
- [ ] Call `image_service.generate_instagram_image(...)` after AI generation
- [ ] Store file paths in `listings[listing_id]` dict
- [ ] Add `has_pdf: true` and `has_image: true` to API response

### 3.4 Download Endpoints
- [ ] Add `GET /api/pdf/{listing_id}` → return `FileResponse` for `listing.pdf`
- [ ] Add `GET /api/image/{listing_id}` → return `FileResponse` for `instagram.jpg`
- [ ] Add 404 handling if listing_id not found

### 3.5 Instagram Auto-Posting Service
- [ ] Create `backend/services/instagram_service.py`
- [ ] Load `UPLOADPOST_API_KEY` from `.env`
- [ ] Write `async def post_to_instagram(image_path, caption) -> dict`:
  - [ ] Open image file in binary mode
  - [ ] Build multipart form: `user=listapro`, `platform[]=instagram`, `image=<file>`, `title=<caption>`
  - [ ] Set header `Authorization: Apikey {UPLOADPOST_API_KEY}`
  - [ ] POST to `https://api.upload-post.com/api/upload` using `httpx.AsyncClient`
  - [ ] Return `{"success": True, "message": "Posted successfully"}` on 2xx
  - [ ] Return `{"success": False, "message": "<error detail>"}` on failure

### 3.6 Instagram Post Endpoint & Frontend
- [ ] Add `POST /api/instagram/{listing_id}` endpoint in `main.py`
- [ ] Call `instagram_service.post_to_instagram(...)` and return result
- [ ] Update `app.js`:
  - [ ] "Download PDF" button → opens `/api/pdf/{listing_id}` in new tab
  - [ ] "Download Image" button → opens `/api/image/{listing_id}` in new tab
  - [ ] "Post to Instagram" button → calls `POST /api/instagram/{listing_id}`, shows green toast on success, red toast on failure, disables button after posting

---

### Phase 3 — Developer Testing
- [ ] Call `generate_pdf()` directly with sample data and a real photo path — open the output PDF, verify layout: header color, photo, stat boxes, description text, agent info visible
- [ ] Call `generate_instagram_image()` directly — open the output JPG, verify: photo fills canvas, gradient visible, badge correct color, all text readable
- [ ] `GET /api/pdf/{listing_id}` → browser downloads a valid, openable PDF file
- [ ] `GET /api/image/{listing_id}` → browser downloads a valid 1080×1080 JPG
- [ ] `POST /api/instagram/{listing_id}` with a real `UPLOADPOST_API_KEY` → check response JSON; if key is not yet available, verify the error is handled gracefully (no server crash)
- [ ] Test with no additional photos → PDF still generates without the grid section crashing

### Phase 3 — Functional Testing (You)
- [ ] Generate a listing and click "Download PDF" → PDF opens/downloads, verify it looks professional with the property photo, price box, description, and agent info
- [ ] Click "Download Instagram Image" → JPG downloads, open it and verify: property photo as background, gradient overlay, "FOR SALE"/"FOR RENT" badge in correct color, price is large and readable, your test location and details are shown
- [ ] Verify badge color: Sale listing → blue badge; Rent listing → green badge
- [ ] Click "Post to Instagram" → toast notification appears (success or error message — both are acceptable, what matters is no silent failure)
- [ ] Try downloading PDF for an invalid listing ID (type a fake URL) → expect a 404 message, not a server error

---

## Phase 4 — Video Reel Generation
> **Goal:** Agents can generate a 20–30 second vertical video reel with smooth photo transitions, animated text, and agent branding — ready to post on Instagram Reels and TikTok.

### 4.1 Remotion Project Setup
- [ ] From project root, create `video/` folder
- [ ] Create `video/package.json` with Remotion 4.x dependencies (`remotion`, `@remotion/cli`, `react`, `react-dom`, TypeScript types)
- [ ] Create `video/remotion.config.ts` with output settings: 1080×1920, 30fps
- [ ] Create `video/public/` directory (will hold per-render `data.json` and `music.mp3`)
- [ ] Add placeholder `video/public/music.mp3` instruction in README (user provides their own MP3)
- [ ] Run `npm install` inside `video/` — confirm no errors

### 4.2 Remotion Components
- [ ] Create `video/src/PropertyReel/PropertyReel.tsx`:
  - [ ] Accept props: `photos` (string[]), `price`, `location`, `bedrooms`, `bathrooms`, `area`, `agentName`, `agentPhone`, `agentEmail`, `operation`
  - [ ] Load `data.json` from `staticFile('data.json')` if props not passed directly
  - [ ] **Photo segments (per photo, 100 frames / ~3.3 sec each):**
    - [ ] Display photo as full-bleed background using `<Img>`
    - [ ] Apply Ken Burns effect: `scale` from 1.0 → 1.08 using `interpolate(frame, [0, durationInFrames], [1, 1.08])`
    - [ ] Fade in from previous photo: opacity `interpolate(frame, [0, 15], [0, 1])`
  - [ ] **Text overlays (each uses `spring()` entrance):**
    - [ ] Photo 1: Price overlay — large white text, dark pill background
    - [ ] Photo 2: Location overlay — city, state
    - [ ] Photo 3: Details row — bed / bath / sq ft icons
    - [ ] Photo 4: CTA — "Schedule a Visit Today"
  - [ ] **Final contact screen (150 frames / 5 sec):**
    - [ ] Solid `#1B4F8A` background
    - [ ] "ListPro" wordmark fades in at top
    - [ ] Agent name, phone, email spring in sequentially
    - [ ] Brand tagline at bottom
  - [ ] **Audio:** `<Audio src={staticFile('music.mp3')} volume={0.4} />`
- [ ] Create `video/src/Root.tsx`: register `PropertyReel` composition (id: `"PropertyReel"`, 1080×1920, 30fps, durationInFrames: 750)
- [ ] Create `video/src/index.ts`: call `registerRoot(Root)`

### 4.3 Backend — Video Render Endpoint
- [ ] Add in-memory `video_jobs` dict to track render status per `listing_id`
- [ ] Add `POST /api/video/{listing_id}` endpoint:
  - [ ] Retrieve listing data from `listings[listing_id]`
  - [ ] Copy photo files to `video/public/photos/` with predictable names
  - [ ] Write `video/public/data.json` with all property data and photo paths
  - [ ] Set `video_jobs[listing_id] = "rendering"`
  - [ ] Launch `npx remotion render PropertyReel output/{listing_id}.mp4` as async subprocess (`asyncio.create_subprocess_exec`)
  - [ ] On subprocess completion: set `video_jobs[listing_id] = "done"` and save mp4 path
  - [ ] On subprocess error: set `video_jobs[listing_id] = "error"`
  - [ ] Return `{"status": "rendering", "listing_id": listing_id}` immediately (non-blocking)
- [ ] Add `GET /api/video/status/{listing_id}` → return `{"status": "rendering"|"done"|"error"}`
- [ ] Add `GET /api/video/download/{listing_id}` → return `FileResponse` for the `.mp4`

### 4.4 Frontend — Video Generation UI
- [ ] Update `app.js`:
  - [ ] "Generate Video" button → calls `POST /api/video/{listing_id}`
  - [ ] Show animated progress bar and "Rendering your reel… this takes ~30 seconds"
  - [ ] Poll `GET /api/video/status/{listing_id}` every 3 seconds
  - [ ] On status `"done"`: hide progress bar, show "✅ Video ready!" + "⬇️ Download Reel" button
  - [ ] On status `"error"`: show red error message
  - [ ] "Download Reel" button → opens `/api/video/download/{listing_id}`

---

### Phase 4 — Developer Testing
- [ ] `cd video && npm install` → no errors
- [ ] `npx remotion studio` inside `video/` → browser opens Remotion Studio, composition visible
- [ ] Place 2–4 test photos in `video/public/photos/` and write a sample `data.json`, then render manually: `npx remotion render PropertyReel test_output.mp4` → mp4 file created, playable
- [ ] Ken Burns effect visible on at least one photo in the rendered output
- [ ] All text overlays appear on correct photo segments
- [ ] Contact screen appears in final 5 seconds
- [ ] `POST /api/video/{listing_id}` → returns `{"status": "rendering"}` immediately without blocking
- [ ] Poll `GET /api/video/status/{listing_id}` every few seconds → status transitions from `"rendering"` → `"done"`
- [ ] `GET /api/video/download/{listing_id}` → `.mp4` file downloads and plays correctly

### Phase 4 — Functional Testing (You)
- [ ] Generate a full listing (fill the form, submit)
- [ ] On the results page, click "Generate Video" → progress bar appears immediately
- [ ] Wait ~30 seconds → progress bar disappears and "✅ Video ready!" message + download button appear
- [ ] Click "Download Reel" → `.mp4` file downloads
- [ ] Open the video and verify:
  - [ ] Correct property photos appear in sequence
  - [ ] Each photo has a slow zoom (Ken Burns) effect
  - [ ] Price text appears on the first photo
  - [ ] Location appears on the second photo
  - [ ] Bed/bath/sq ft details appear on the third photo
  - [ ] "Schedule a Visit Today" CTA appears on the fourth photo
  - [ ] Final screen shows agent name, phone, and email on a blue background
  - [ ] Background music is audible (if `music.mp3` was placed in `video/public/`)
- [ ] Upload the downloaded `.mp4` directly to Instagram Reels (manual) → verify the 9:16 aspect ratio fits the Reels format correctly

---

## Summary Checklist by Phase

| Phase | Deliverable | Testable On Day |
|-------|-------------|-----------------|
| 1 | Running server + complete styled form | Day 1 |
| 2 | AI-generated descriptions + Instagram captions | Day 2–3 |
| 3 | PDF download + Instagram image + auto-posting | Day 4–5 |
| 4 | Video reel generation + download | Day 6–8 |

---

## Environment Setup Checklist (Do First)
- [ ] Install Python 3.11+ (`python --version`)
- [ ] Install Node.js 18+ (`node --version`)
- [ ] Create and activate a Python virtual environment: `python -m venv venv && source venv/bin/activate`
- [ ] Install Python dependencies: `pip install -r backend/requirements.txt`
- [ ] Copy `.env.example` to `.env` and fill in your API keys
- [ ] Install Node dependencies for video: `cd video && npm install`
