import os
import httpx
from dotenv import load_dotenv

load_dotenv()

UPLOAD_POST_URL = "https://api.upload-post.com/api/upload"


async def post_to_instagram(image_path: str, caption: str) -> dict:
    api_key = os.getenv("UPLOADPOST_API_KEY", "")

    if not api_key or api_key.startswith("your_"):
        return {
            "success": False,
            "message": "UPLOADPOST_API_KEY is not configured in backend/.env",
        }

    try:
        user = os.getenv("UPLOADPOST_USER", "").strip()
        if not user:
            return {"success": False, "message": "UPLOADPOST_USER is not set in backend/.env"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(image_path, "rb") as img_file:
                response = await client.post(
                    UPLOAD_POST_URL,
                    headers={"Authorization": f"Apikey {api_key}"},
                    files={
                        "user":       (None, user),
                        "platform[]": (None, "instagram"),
                        "title":      (None, caption),
                        "video":      ("instagram.jpg", img_file, "image/jpeg"),
                    },
                )

        if response.status_code in (200, 201):
            return {"success": True, "message": "Posted to Instagram successfully!"}

        return {
            "success": False,
            "message": f"Upload failed ({response.status_code}): {response.text[:300]}",
        }

    except httpx.TimeoutException:
        return {"success": False, "message": "Request timed out. Please try again."}
    except FileNotFoundError:
        return {"success": False, "message": "Instagram image not found. Generate the listing first."}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
