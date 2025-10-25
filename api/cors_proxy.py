"""
CORS Proxy for Color Extraction
This module provides a simple CORS proxy to fetch images for color extraction
when the original images are blocked by CORS policies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import httpx
import asyncio
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CORS Proxy for Color Extraction")


@app.get("/proxy-image")
async def proxy_image(url: str):
    """
    Proxy an image URL to bypass CORS restrictions.

    Args:
        url: The URL of the image to proxy

    Returns:
        The image data with proper CORS headers
    """
    try:
        async with httpx.AsyncClient() as client:
            # Fetch the image
            response = await client.get(url, timeout=30.0)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch image: {response.status_code}",
                )

            # Return the image with CORS headers
            return Response(
                content=response.content,
                media_type=response.headers.get("content-type", "image/png"),
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=400, detail=f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cors-proxy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
