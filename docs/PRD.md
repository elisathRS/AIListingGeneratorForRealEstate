# ListPro — Product Requirements Document

**Version:** 1.0
**Date:** 2026-03-26
**Product:** ListPro — AI-Powered Real Estate Listing Generator
**Target Market:** Real estate agents in the United States

---

## 1. Overview

ListPro is a web-based tool that allows real estate agents to fill out a structured form with property details and automatically generate professional, publication-ready content using AI. It eliminates the manual effort of writing descriptions, designing social media posts, creating PDFs, and producing video reels.

### 1.1 Problem Statement

Real estate agents at this U.S. residential agency publish 3–5 properties per week. Currently, all listing content (descriptions, social posts, flyers, videos) is created manually using Canva and Word — a slow, inconsistent, and time-consuming process.

### 1.2 Solution

A single web form that accepts property details and photos, then automatically generates:
- A professional property description (via Gemini)
- An Instagram-optimized caption with hashtags
- A downloadable PDF flyer
- A square Instagram image (1080×1080)
- A vertical video reel (1080×1920) for Instagram and TikTok

---

## 2. Scope — Version 1.0

### In Scope
- Web form (desktop + mobile browser)
- AI text generation (description + Instagram caption)
- PDF generation
- Instagram image generation
- Instagram auto-posting via Upload-Post API
- Vertical video reel generation via Remotion
- Local deployment (localhost)

### Out of Scope (future versions)
- User authentication / multi-agent accounts
- Listing database / history
- MLS integration
- WhatsApp / Facebook posting
- Custom branding per agent

---

## 3. User Persona

**Primary User:** Real estate agent
- Publishes 3–5 listings per week
- Non-technical; comfortable with web forms
- Needs fast, professional output without design skills
- Publishes on Instagram and sends PDF flyers to clients

---

## 4. Functional Requirements

### 4.1 Web Form

The main page presents a single-page form with the following fields:

| Field | Type | Required |
|-------|------|----------|
| Property Type | Select: House, Apartment, Land, Penthouse | Yes |
| Operation | Radio: Sale / Rent | Yes |
| Address / Location | Text | Yes |
| City | Text | Yes |
| State | Select (all U.S. states) | Yes |
| Price (USD) | Number | Yes |
| Bedrooms | Number (0–10) | Yes |
| Bathrooms | Number (0–10) | Yes |
| Built Area (sq ft) | Number | Yes |
| Land Area (sq ft) | Number | No |
| Parking Spaces | Number | Yes |
| Amenities | Checkboxes (see §4.1.1) | No |
| Agent Notes | Textarea (2–3 lines) | No |
| Cover Photo | File (image, single) | Yes |
| Additional Photos | File (images, multiple) | No |
| Agent Name | Text | Yes |
| Agent Phone | Text | Yes |
| Agent Email | Email | Yes |

#### 4.1.1 Amenities Checkboxes
- Pool
- Garden / Backyard
- 24h Security
- Gym / Fitness Center
- Playground
- Event Hall / Party Room
- Rooftop Terrace
- Service Room
- Storage Unit
- Elevator

### 4.2 AI Content Generation

**Model:** Gemini Pro 3.1
**Language:** English

#### 4.2.1 Property Description
- 3–4 paragraphs
- Professional and attractive tone
- Highlights key features: location, size, amenities
- Ends with a call to action

#### 4.2.2 Instagram Caption
- Engaging, conversational tone
- Includes key stats (price, beds, baths, sq ft)
- 20–30 relevant U.S. real estate hashtags
- Examples: #realestate #forsale #homesofinstagram #luxuryhomes #[city]realestate #realtor #dreamhome #newlisting

### 4.3 Results Page

Displays after form submission:
- AI-generated property description (with copy button)
- Instagram caption (with copy button)
- Download PDF button
- Download Instagram Image button
- Post to Instagram button (with success/error feedback)
- Generate Video Reel button (with progress indicator + download link)
- "← Generate another listing" back link

---

## 5. PDF Generation

**Library:** ReportLab (Python)

### Layout
1. **Header:** Colored banner (#1B4F8A) with "ListPro" branding + property title
2. **Cover Photo:** Full-width, large image
3. **Additional Photos:** Grid (2 per row), smaller
4. **Key Stats Row:** Colored boxes — Price, Beds, Baths, Sq Ft, Parking
5. **Description:** Full AI-generated text
6. **Amenities:** Checklist
7. **Agent Contact:** Name, phone, email at bottom

**Output:** Downloadable `.pdf` file
**Trigger:** Generated automatically on form submission; available via "Download PDF" button

---

## 6. Instagram Square Image (1080×1080)

**Library:** Pillow (Python)

### Design Spec
- **Background:** Cover photo, resized/cropped to 1080×1080
- **Overlay:** Dark gradient from transparent → 80% black (bottom 60%)
- **Badge (top-left):** "FOR SALE" or "FOR RENT" — blue (#1B4F8A) for sale, green (#27AE60) for rent
- **Price:** Large white bold text, centered lower area
- **Location:** Smaller white text below price
- **Details Row:** Icons + text — 🛏 X beds | 🚿 X baths | 📐 X sq ft
- **Bottom Strip:** Agent name and phone

**Output:** Downloadable `.jpg` file

---

## 7. Instagram Auto-Posting

**API:** Upload-Post (`https://api.upload-post.com/api/upload`)

### Request
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `user`: identifier string
  - `platform[]`: `"instagram"`
  - `image`: the generated 1080×1080 image file
  - `title`: the AI-generated Instagram caption
- Headers:
  - `Authorization: Apikey {UPLOADPOST_API_KEY}`

### Response Handling
- Success: Show green toast — "Posted to Instagram successfully!"
- Error: Show red toast — "Failed to post. Please try again."

**Environment Variable:** `UPLOADPOST_API_KEY`

---

## 8. Video Reel Generation (1080×1920)

**Framework:** Remotion (React + TypeScript)
**Location:** `video/` folder inside project root
**Output:** `.mp4` file, 1080×1920, 30fps, 20–30 seconds

### Video Structure

| Segment | Duration | Content |
|---------|----------|---------|
| Photo 1 | 3–4 sec | Cover photo with Ken Burns zoom, price overlay fades in |
| Photo 2 | 3–4 sec | Second photo with zoom, location overlay |
| Photo 3 | 3–4 sec | Third photo with zoom, bed/bath/sqft icons |
| Photo 4 | 3–4 sec | Fourth photo, "Schedule a Visit" CTA |
| Contact | 5 sec | Solid brand color, agent info animates in |

### Visual Effects
- **Ken Burns:** Slow scale from 1.0→1.08 using `interpolate()`
- **Fade transitions:** 0.3s cross-fade between photos
- **Text animations:** `spring()` entrance for all text overlays
- **Background music:** MP3 file placed at `video/public/music.mp3`

### Backend Integration
1. Frontend sends `POST /api/video/{listing_id}`
2. Backend writes a `data.json` config to `video/public/`
3. Backend runs `npx remotion render` as subprocess
4. Frontend polls for completion
5. Download link appears when `.mp4` is ready

---

## 9. Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| AI | Gemini Pro 3.1 (`google-generativeai` SDK) |
| PDF | ReportLab |
| Image | Pillow |
| Video | Remotion 4.x (React + TypeScript) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| HTTP Client | httpx (async) |
| Server | Uvicorn (local) |
| Environment | python-dotenv |

---

## 10. Architecture

```
[Browser] ←→ [FastAPI Server :8000]
                    ├── /api/generate      → AI + PDF + Image generation
                    ├── /api/pdf/{id}      → Serve PDF
                    ├── /api/image/{id}    → Serve Instagram image
                    ├── /api/instagram/{id}→ Post to Upload-Post API
                    └── /api/video/{id}    → Trigger Remotion render
```

- All files stored in `backend/uploads/{listing_id}/`
- In-memory dict stores listing data per session (no database)
- Frontend served as static files by FastAPI

---

## 11. File Structure

```
AIListingGeneratorForRealEstate/
├── docs/
│   └── PRD.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── uploads/               # Auto-created, stores per-listing files
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py
│       ├── pdf_service.py
│       ├── image_service.py
│       └── instagram_service.py
├── frontend/
│   ├── index.html
│   ├── results.html
│   └── static/
│       ├── css/styles.css
│       └── js/app.js
├── video/
│   ├── package.json
│   ├── remotion.config.ts
│   └── src/
│       ├── index.ts
│       ├── Root.tsx
│       └── PropertyReel/
│           ├── PropertyReel.tsx
│           └── index.ts
└── README.md
```

---

## 12. Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key for Gemini Pro 3.1 |
| `UPLOADPOST_API_KEY` | Upload-Post API key for Instagram posting |

---

## 13. Non-Functional Requirements

- **Performance:** Form submission + AI generation should complete in < 15 seconds
- **Local-only:** Runs entirely on `localhost:8000`; no cloud deployment required
- **Browsers:** Chrome, Firefox, Safari (latest versions)
- **Mobile:** Responsive layout for form completion on phones
- **Error handling:** All API errors surfaced to the user with clear messages

---

## 14. Future Roadmap (v2+)

- Agent login / multi-user support
- Listing history and dashboard
- Facebook + TikTok auto-posting
- WhatsApp flyer sharing
- Custom agent branding / logo upload
- MLS data import
- Batch listing generation
