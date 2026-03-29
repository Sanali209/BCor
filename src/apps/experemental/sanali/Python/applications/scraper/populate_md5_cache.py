import os
import glob
from tqdm import tqdm
from loguru import logger

from SLM.appGlue.helpers import ImageHelper
# Assuming ws4_s1 is in the same directory and contains the necessary classes
from ws4_s1 import ProjectConfig, CacheManager


CONFIG_FILE = "reverse1.json"
PROCESSED_FILES_CACHE_NAME = ".processed_md5_files_cache"
SUPPORTED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "bmp"]

# --- LOGGING ---
logger.add(
    "../md5_populator_{time}.log",
    rotation="10 MB",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
)

def populate_md5_cache():

    logger.info("--- Starting MD5 Cache Population ---")

    try:
        config = ProjectConfig.load_from_file(CONFIG_FILE)
    except Exception as e:
        logger.critical(f"Failed to load configuration file {CONFIG_FILE}: {e}")
        return

    # --- Initialize Caches ---
    md5_cache_path = os.path.join(config.save_path, config.md5_cache_path)
    processed_files_cache_path = os.path.join(config.save_path, PROCESSED_FILES_CACHE_NAME)
    
    logger.info(f"Using MD5 cache at: {md5_cache_path}")
    logger.info(f"Using processed files cache at: {processed_files_cache_path}")

    md5_cache = CacheManager(md5_cache_path, config.cache_size_gb)
    processed_files_cache = CacheManager(processed_files_cache_path, config.cache_size_gb)

    # --- Find all image files ---
    resource_path = os.path.join(config.save_path, "resources")
    if not os.path.isdir(resource_path):
        logger.error(f"Resource directory not found at: {resource_path}")
        return
        
    logger.info(f"Scanning for images in: {resource_path}")
    
    all_image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        # The pattern '/**/' makes the search recursive
        pattern = os.path.join(resource_path, '**', f'*.{ext}')
        all_image_files.extend(glob.glob(pattern, recursive=True))

    if not all_image_files:
        logger.warning("No image files found to process.")
        return

    logger.info(f"Found {len(all_image_files)} total image files.")

    # --- Process Files ---
    new_hashes = 0
    for file_path in tqdm(all_image_files, desc="Calculating MD5 Hashes"):
        try:
            # Check if file has already been processed
            if file_path in processed_files_cache:
                logger.trace(f"Skipping already processed file: {file_path}")
                continue
            
            pil_image = ImageHelper.image_load_pil(file_path)
            md5_hash = ImageHelper.content_md5(pil_image)

            if md5_hash:
                if md5_hash not in md5_cache:
                    md5_cache.add(md5_hash, True)
                    new_hashes += 1
                
                # Mark file as processed regardless of whether the hash was new
                processed_files_cache.add(file_path, True)
            else:
                logger.warning(f"Could not generate MD5 for: {file_path}")

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")

    # --- Finalize ---
    md5_cache.close()
    processed_files_cache.close()
    logger.success(f"--- MD5 Cache Population Complete ---")
    logger.info(f"Added {new_hashes} new unique MD5 hashes to the cache.")
    logger.info(f"Total unique images in cache: {len(md5_cache)}")

if __name__ == "__main__":
    populate_md5_cache()
