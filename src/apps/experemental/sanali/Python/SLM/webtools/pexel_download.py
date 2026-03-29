
from loguru import logger

from SLM.webtools.pexel_api import PexelsAPI

if __name__ == '__main__':
    # Configure Loguru logger
    logger.add("pexels_api.log", rotation="10 MB", retention="7 days", level="INFO")
    # You can also remove the default handler to prevent duplicate console output if desired
    # logger.remove()
    # logger.add(sys.stderr, level="INFO")
API_KEY = "fWR0eYyjy9EY2hu9b9bsADZSOQhexk0hgGlVSYnrs53Dq0AQNqNhxyML"


pexels_client = PexelsAPI(api_key=API_KEY)

logger.info("--- Starting Pexels API example usage ---")


# 4. Download search results (e.g., 3 photos of "cats")

downloaded_cat_photos = pexels_client.download_search_results(
    search_type="photos",
    query="3d render",
    num_items_to_download=10000,
    folder_path=r"E:\rawimagedb\repository\safe repo\presort\3d render"
)
logger.info(f"Downloaded files: {downloaded_cat_photos}")
logger.info(f"Rate limit status after downloads: {pexels_client.get_rate_limit_status()}")


