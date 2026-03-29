import asyncio
import os
import sys
from loguru import logger
from src.modules.agm.tasks import compute_stored_field

async def main():
    repo_dir = os.path.dirname(__file__)
    sample_path = os.path.join(repo_dir, "tests", "test_data", "images", "37948324394_38056398fb_b.webp")
    # 1. Compute Hash first
    try:
        await getattr(compute_stored_field, "coroutine", compute_stored_field)(
            node_id="regression-asset-1",
            field_name="content_hash",
            source_value=f"file://{sample_path}",
            mime_type="image/webp",
            handler="ContentHashHandler",
            model="ImageAsset"
        )
        print("compute_stored_field completed.")
    except Exception as e:
        print(f"Exception: {e}")

asyncio.run(main())
