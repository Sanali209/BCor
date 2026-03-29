import asyncio
import time
import os
import sys
from loguru import logger

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.modules.assets.infrastructure.handlers.ollama import OllamaHandler

async def test_ollama_speed():
    IMG_PATH = r"D:\image_db\safe repo\ddsearch\kim_possible\kim_possible_1.webp"
    
    print("\n⏱️  OLLAMA INFERENCE SPEED TEST")
    print(f"File: {os.path.basename(IMG_PATH)}")
    
    if not os.path.exists(IMG_PATH):
        print(f"❌ Error: File not found at {IMG_PATH}")
        return

    # 1. Test Vision (VLM)
    print("\n[1/2] Testing Vision (Moondream)...")
    start = time.time()
    description = await OllamaHandler.describe_image(f"file://{IMG_PATH}")
    end = time.time()
    
    if description:
        print(f"✅ Success! Latency: {end - start:.2f}s")
        print(f"   Result: {description[:100]}...")
    else:
        print("❌ Vision Failed.")

    # 2. Test Embedding
    print("\n[2/2] Testing Embedding (Nomic)...")
    test_text = "A cartoon girl with red hair fighting crime."
    start = time.time()
    embedding = await OllamaHandler.get_embeddings(test_text)
    end = time.time()
    
    if embedding:
        print(f"✅ Success! Latency: {end - start:.2f}s")
        print(f"   Dimensions: {len(embedding)}")
    else:
        print("❌ Embedding Failed.")

    print("\n🏁 Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_ollama_speed())
