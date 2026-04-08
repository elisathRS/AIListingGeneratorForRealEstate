# Required External Resources & APIs

To smoothly execute the implementation plan and build **ListPro**, you will need to gather API keys, set up accounts, and prepare a few assets for the following external services.

You can use this document as a checklist to ensure you have everything ready before we begin Phase 1.

---

## 1. Intelligence: AI Text Generation — Google Gemini API

This is the core intelligence engine that powers ListPro. It takes the property form data and generates the professional listing description and Instagram caption automatically.

**What you need:** A Google Gemini API Key.

**Where to get it:** [Google AI Studio](https://aistudio.google.com)

**Model used:** `gemini-3.1-pro`

**Cost:** Free tier available — generous daily limits, more than enough for development, testing, and regular agent usage.

**Environment variable:** `GEMINI_API_KEY`

- [ ] Go to [aistudio.google.com](https://aistudio.google.com), sign in with a Google account
- [ ] Click **"Get API Key"** → **"Create API key"**
- [ ] Save the key securely — you will paste it into your `.env` file

---

## 2. Social Publishing: Instagram Auto-Posting — Upload-Post API

This service handles posting the generated Instagram image directly to an Instagram account with one click from the results page.

**What you need:** An Upload-Post account and API Key. You must also connect your Instagram account inside their dashboard.

**Where to get it:** [upload-post.com](https://upload-post.com)

**Endpoint used:** `POST https://api.upload-post.com/api/upload`

**Cost:** Paid service — check their website for current plan pricing.

**Environment variable:** `UPLOADPOST_API_KEY`

- [ ] Create an account at [upload-post.com](https://upload-post.com)
- [ ] Subscribe to a plan that includes Instagram posting
- [ ] Connect your Instagram account inside the Upload-Post dashboard
- [ ] Copy your API Key from the dashboard and save it securely

> **Note:** This is the only paid external service in the project. If you want to start testing without it, you can leave `UPLOADPOST_API_KEY` blank — the app will show an error message on that button but everything else will work normally.

---

## 3. Libraries & Open Source Packages (No Keys Required)

The following resources will be integrated via `pip` and `npm` during development. You do not need to sign up for any of these — they are free and open source.

**Python packages** (installed via `pip install -r requirements.txt`):
- **FastAPI + Uvicorn** — web framework and local server
- **google-generativeai** — official Google SDK for calling the Gemini API
- **ReportLab** — generates the downloadable PDF property flyer
- **Pillow** — generates the 1080×1080 Instagram square image
- **httpx** — async HTTP client for calling the Upload-Post API
- **python-multipart** — handles photo file uploads from the form
- **python-dotenv** — loads API keys from the `.env` file

**Node.js packages** (installed via `npm install` inside the `video/` folder):
- **Remotion + @remotion/cli** — generates the 1080×1920 vertical video reel
- **React + React-DOM** — required by Remotion for component rendering
- **TypeScript** — Remotion components are written in `.tsx`

---

## 4. System Requirements (Install on Your Machine)

These are the two runtimes the project depends on. Check what you already have before installing.

**Python 3.11 or higher**
- Check: run `python3 --version` in your terminal
- Download: [python.org/downloads](https://www.python.org/downloads)
- [ ] Installed and confirmed: `python3 --version` shows 3.11+

**Node.js 18 LTS or higher**
- Check: run `node --version` in your terminal
- Download: [nodejs.org](https://nodejs.org) — choose the LTS version
- [ ] Installed and confirmed: `node --version` shows v18+

---

## 5. Assets You Need to Provide

These are files the project expects but cannot generate automatically.

**Background music for the video reel**
- The video generator expects an MP3 file at `video/public/music.mp3`
- Use a royalty-free track to avoid copyright issues on Instagram and TikTok
- Recommended free sources:
  - [Pixabay Music](https://pixabay.com/music) — free, no attribution required
  - [YouTube Audio Library](https://studio.youtube.com) → Audio Library
  - [Free Music Archive](https://freemusicarchive.org)
- [ ] MP3 file selected, renamed to `music.mp3`, ready to place in `video/public/`

**Test property photos**
- Have at least one real property photo ready to test the form
- Any common format works: JPG, PNG, WEBP — the app handles resizing automatically
- [ ] At least one test photo ready

---

## 6. Deployment & Hosting (Optional — For When You Go Live)

ListPro runs entirely on `localhost:8000` for now. When you are ready to share it with agents or deploy it to a server, here are the recommended options for a Python FastAPI app:

**Railway** *(Recommended for FastAPI)*: [railway.app](https://railway.app) — simple Python deployments, free tier available

**Render**: [render.com](https://render.com) — free tier for web services, straightforward FastAPI support

**Fly.io**: [fly.io](https://fly.io) — fast deploys, generous free tier

- [ ] (Optional) Create a free account on Railway or Render to prepare for future deployment

---

## Local Setup Preparation

Once you have your keys, create the `.env` file inside the `backend/` folder:

```
GEMINI_API_KEY=your_gemini_key_here
UPLOADPOST_API_KEY=your_uploadpost_key_here
```

- [ ] `GEMINI_API_KEY` obtained and saved in `backend/.env`
- [ ] `UPLOADPOST_API_KEY` obtained and saved in `backend/.env` *(or skipped for now)*
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] `music.mp3` ready to place in `video/public/`
- [ ] At least one test property photo ready

**You are ready to begin Phase 1.**
