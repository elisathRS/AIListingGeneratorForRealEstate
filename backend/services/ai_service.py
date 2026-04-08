import os
import asyncio
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------
_api_key = os.getenv("GEMINI_API_KEY", "")
if _api_key:
    genai.configure(api_key=_api_key)

# Model name — google-generativeai 0.8.x model string for Gemini 2.5 Pro
MODEL_NAME = "gemini-2.5-flash"


def _get_model() -> genai.GenerativeModel:
    if not _api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to backend/.env and restart the server."
        )
    return genai.GenerativeModel(MODEL_NAME)


_RETRY_DELAYS = [30, 60, 120]  # seconds between attempts


def _generate_sync(model: genai.GenerativeModel, prompt: str, max_retries: int = 4) -> str:
    """Blocking call to Gemini with retry on 429. Run via run_in_executor."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            msg = str(e)
            if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                if attempt < max_retries - 1:
                    m = re.search(r"retry in (\d+)(?:\.\d+)?s", msg, re.IGNORECASE)
                    idx = min(attempt, len(_RETRY_DELAYS) - 1)
                    wait = int(m.group(1)) + 2 if m else _RETRY_DELAYS[idx]
                    time.sleep(wait)
                    continue
            raise
    raise RuntimeError("Gemini rate limit: max retries exceeded")


async def _generate_with_retry(model: genai.GenerativeModel, prompt: str) -> str:
    """Run the blocking Gemini call in a thread so the event loop stays free."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _generate_sync, model, prompt)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _format_price(price: float) -> str:
    return f"${price:,.0f}"


def _amenities_text(amenities: list) -> str:
    if not amenities:
        return "modern finishes and quality construction throughout"
    if len(amenities) == 1:
        return amenities[0]
    return ", ".join(amenities[:-1]) + f", and {amenities[-1]}"


# ---------------------------------------------------------------------------
# Property Description
# ---------------------------------------------------------------------------
async def generate_description(property_data: dict) -> str:
    """
    Generate a professional 3–4 paragraph property description using Gemini.
    """
    pd = property_data
    op = "for sale" if pd.get("operation", "").lower() == "sale" else "for rent"
    amenities = _amenities_text(pd.get("amenities", []))
    land_line = (
        f"  - Land area: {pd['land_area']:,.0f} sq ft\n" if pd.get("land_area") else ""
    )
    notes_line = (
        f"\nAgent notes to highlight: {pd['agent_notes']}\n"
        if pd.get("agent_notes", "").strip()
        else ""
    )

    prompt = f"""You are a professional real estate copywriter. Write a compelling, professional property listing description in English for the following property.

PROPERTY DETAILS:
- Type: {pd.get('property_type')}
- Operation: {op.title()}
- Address: {pd.get('address')}, {pd.get('city')}, {pd.get('state')}
- Price: {_format_price(pd.get('price', 0))} USD
- Bedrooms: {pd.get('bedrooms')}
- Bathrooms: {pd.get('bathrooms')}
- Built area: {pd.get('built_area', 0):,.0f} sq ft
{land_line}- Parking spaces: {pd.get('parking')}
- Amenities: {amenities}
{notes_line}
INSTRUCTIONS:
- Write exactly 3 to 4 paragraphs. No headers, no bullet points — flowing prose only.
- Paragraph 1: Hook the reader with the property's best feature and location appeal.
- Paragraph 2: Describe the interior layout, space, and quality in detail.
- Paragraph 3: Highlight the amenities and lifestyle benefits.
- Paragraph 4: Strong call to action — invite the reader to schedule a visit.
- Tone: warm, professional, aspirational. Avoid clichés like "must-see" or "won't last long".
- Do NOT include the agent's name or contact info — that goes on the PDF separately.
- Output only the description text. No intro, no labels, no markdown.
"""

    try:
        model = _get_model()
        return await _generate_with_retry(model, prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini description generation failed: {e}")


# ---------------------------------------------------------------------------
# Instagram Caption
# ---------------------------------------------------------------------------
async def generate_instagram_caption(property_data: dict, description: str) -> str:
    """
    Generate an Instagram-optimized caption with U.S. real estate hashtags.
    """
    pd = property_data
    op_label = "For Sale" if pd.get("operation", "").lower() == "sale" else "For Rent"
    city = pd.get("city", "")
    state = pd.get("state", "")
    city_tag = city.lower().replace(" ", "")
    state_tag = state.lower().replace(" ", "")

    prompt = f"""You are a real estate social media expert. Write an engaging Instagram caption for this property listing.

PROPERTY:
- {pd.get('property_type')} {op_label}
- {pd.get('address')}, {city}, {state}
- Price: {_format_price(pd.get('price', 0))} USD
- {pd.get('bedrooms')} beds · {pd.get('bathrooms')} baths · {pd.get('built_area', 0):,.0f} sq ft
- {pd.get('parking')} parking space(s)
- Amenities: {', '.join(pd.get('amenities', [])) or 'N/A'}

PROFESSIONAL DESCRIPTION (for context):
{description[:400]}...

INSTRUCTIONS:
- Start with 1–2 attention-grabbing lines (can use 1–2 emojis naturally).
- Include key stats: price, beds, baths, sq ft on their own line using emojis (🛏 🚿 📐).
- Mention the city and state.
- End with a call to action (DM or comment to schedule a showing).
- Add a blank line, then 25–30 relevant hashtags on the last line.
- Include city-specific tags like #{city_tag}realestate #{city_tag}homes #{state_tag}realestate
- Also include general tags: #realestate #realtor #newlisting #justlisted #homesofinstagram #luxuryhomes #dreamhome #househunting #homebuying #realestateinvesting #propertylistings #homeforsale #realestateagent #openhouse
- Output only the caption text. No labels, no markdown, no explanation.
"""

    try:
        model = _get_model()
        return await _generate_with_retry(model, prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini caption generation failed: {e}")
