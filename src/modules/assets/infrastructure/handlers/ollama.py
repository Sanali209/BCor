import httpx
import base64
import pathlib
from typing import Any, Optional
from loguru import logger

class OllamaHandler:
    """Unified handler for local AI tasks via Ollama (VLM & Embeddings)."""
    
    API_URL = "http://127.0.0.1:11434"
    DEFAULT_VISION_MODEL = "moondream:latest"  # Full tag for Windows compatibility
    DEFAULT_EMBED_MODEL = "nomic-embed-text:latest"

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> Any:
        """Entry point for AGM Stored field recalculation.
        
        Supports:
        - field_name == 'description': Vision/VLM mode.
        - field_name == 'ollama_embedding': Embedding mode.
        """
        field_name = context.get("field_name") if context else None
        source_val = context.get("new_source_val")  # Uri for vision, Text for embedding
        
        if field_name == "description":
            return await OllamaHandler.describe_image(uri)
        
        if field_name == "ollama_embedding":
            if not source_val:
                return []
            return await OllamaHandler.get_embeddings(str(source_val))
            
        return None

    @staticmethod
    async def describe_image(uri: str, model: str = DEFAULT_VISION_MODEL) -> str:
        """Get image description from local VLM."""
        path = uri.replace("file://", "")
        p = pathlib.Path(path)
        if not p.exists():
            logger.error(f"[BCOR_AI:ERROR] File not found {path}")
            return ""

        try:
            from PIL import Image
            import io
            with Image.open(p) as img:
                # Resize if too large to prevent Ollama 500/OOM crashes
                # 768 is a good compromise for Moondream
                if max(img.size) > 768:
                    img.thumbnail((768, 768))
                
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            logger.info(f"[BCOR_AI:STARTED] model={model} task=describe file={p.name} (resized to stable resolution)")
            logger.info(f"[BCOR_AI:STARTED] model={model} task=describe file={p.name}")
            async with httpx.AsyncClient(timeout=180.0) as client:
                # Some Ollama versions on Windows prefer images as a list of base64 data
                payload = {
                    "model": model,
                    "prompt": "Describe this image in detail, focus on objects, colors, and context. Be concise but descriptive.",
                    "images": [img_base64],
                    "stream": False,
                    "options": {
                        "num_predict": 300,
                        "temperature": 0.2
                    }
                }
                response = await client.post(
                    f"{OllamaHandler.API_URL}/api/generate",
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"[BCOR_AI:ERROR] Ollama returned {response.status_code}: {response.text}")
                    response.raise_for_status()
                
                data = response.json()
                desc = data.get("response", "").strip()
                if desc:
                    logger.success(f"[BCOR_AI:FINISHED] task=describe length={len(desc)}")
                else:
                    logger.warning("[BCOR_AI:EMPTY] No description returned from model.")
                return desc
        except Exception as e:
            logger.error(f"[BCOR_AI:FAILED] task=describe error={e}")
            return ""

    @staticmethod
    async def get_embeddings(text: str, model: str = DEFAULT_EMBED_MODEL) -> list[float]:
        """Get text embeddings from local Ollama."""
        try:
            logger.info(f"[BCOR_AI:STARTED] model={model} task=embedding text_len={len(text)}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{OllamaHandler.API_URL}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                emb = data.get("embedding", [])
                logger.success(f"[BCOR_AI:FINISHED] task=embedding dims={len(emb)}")
                return emb
        except Exception as e:
            logger.error(f"[BCOR_AI:FAILED] task=embedding error={e}")
            return []
