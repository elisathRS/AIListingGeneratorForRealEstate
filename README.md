# ListPro — AI Listing Generator for Real Estate

## Scenario

Real estate agents spend hours each week manually writing property descriptions, designing flyers, creating social media posts, and editing videos — for every single listing. This repetitive work is time-consuming and inconsistent.

**ListPro** solves this by automating the entire content pipeline. An agent fills out one form with property details and uploads photos, and the system generates everything automatically: professional descriptions, Instagram captions, PDF flyers, square images, and vertical video reels — ready to publish in minutes.

---

## What You Build

A full-stack AI-powered marketing content generator for real estate agents, including:

| Output | Description |
|---|---|
| AI Property Description | Professional text generated via Google Gemini |
| Instagram Caption | Optimized copy with hashtags |
| PDF Flyer | Downloadable marketing document |
| Instagram Image | 1080×1080px visual card |
| Video Reel | 1080×1920px vertical video for Reels/TikTok |
| Instagram Auto-Post | Direct publishing via Upload-Post API |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| AI | Google Gemini API (`gemini-2.5-flash`) |
| PDF | ReportLab |
| Images | Pillow |
| Video | Remotion (React + TypeScript) |
| Frontend | Vanilla HTML/CSS/JS |
| Instagram | Upload-Post API |

---

## Walkthrough

<img src='videoWT.gif' title='Video Walkthrough' width='' alt='Video Walkthrough' />

1. Agent opens the web form at `http://localhost:8000`
2. Fills in property details (address, price, beds, baths, type, description)
3. Uploads property photos
4. Clicks **Generate** — the backend:
   - Sends details to Gemini → receives description + Instagram caption
   - Generates a PDF flyer and Instagram image in parallel
   - Saves everything under a unique listing ID
5. Results page displays generated content with download buttons for PDF, image, and video
6. Agent clicks **Post to Instagram** to auto-publish
7. Agent requests **video render** — Remotion runs in the background, MP4 available to download when ready

---

## Environment Variables

Create a `backend/.env` file with the following:

```env
GEMINI_API_KEY=your_google_gemini_api_key
UPLOADPOST_API_KEY=your_uploadpost_api_key
UPLOADPOST_USER=your_uploadpost_username
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Get it at [Google AI Studio](https://aistudio.google.com) |
| `UPLOADPOST_API_KEY` | Yes | Required only for Instagram auto-posting |
| `UPLOADPOST_USER` | Yes | Your Upload-Post account username |

---

## Installation Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd AIListingGeneratorForRealEstate
```

### 2. Set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in your API keys
```

### 4. Set up the video module

```bash
cd ../video
npm install
```

### 5. Run the app

```bash
cd ../backend
python main.py
```

Open `http://localhost:8000` in your browser.

### Optional — Video Studio Preview

```bash
cd video
npm run studio
```
