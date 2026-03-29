import requests
import os
import time
from loguru import logger

class PexelsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1/"
        self.rate_limit_limit = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None # Unix timestamp

    def _update_rate_limit_info(self, headers):
        """Updates rate limit information from response headers."""
        self.rate_limit_limit = int(headers.get('X-Ratelimit-Limit', self.rate_limit_limit or 0))
        self.rate_limit_remaining = int(headers.get('X-Ratelimit-Remaining', self.rate_limit_remaining or 0))
        self.rate_limit_reset = int(headers.get('X-Ratelimit-Reset', self.rate_limit_reset or 0))

    def _request(self, endpoint, params=None, method="GET"):
        """Makes a request to the Pexels API."""
        headers = {"Authorization": self.api_key}
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            self._update_rate_limit_info(response.headers)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.status_code} - {response.text}")
            if response.headers:
                 self._update_rate_limit_info(response.headers)
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred during request to {url}")
            return None

    def get_rate_limit_status(self):
        """Returns the current rate limit status."""
        if self.rate_limit_remaining is None:
            logger.info("Rate limit information not yet available. Make an API call first.")
            return {"message": "Rate limit information not yet available. Make an API call first."}
        
        reset_time_readable = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(self.rate_limit_reset)) if self.rate_limit_reset else "N/A"
        
        return {
            "limit": self.rate_limit_limit,
            "remaining": self.rate_limit_remaining,
            "reset_timestamp": self.rate_limit_reset,
            "reset_time_readable_utc": reset_time_readable
        }

    # --- API Methods ---
    def search_photos(self, query, per_page=15, page=1, **kwargs):
        """Searches for photos."""
        params = {"query": query, "per_page": per_page, "page": page, **kwargs}
        return self._request("search", params=params)

    def search_videos(self, query, per_page=15, page=1, **kwargs):
        """Searches for videos."""
        params = {"query": query, "per_page": per_page, "page": page, **kwargs}
        return self._request("videos/search", params=params)

    def curated_photos(self, per_page=15, page=1):
        """Gets curated photos."""
        params = {"per_page": per_page, "page": page}
        return self._request("curated", params=params)

    def get_photo(self, photo_id):
        """Gets a specific photo by its ID."""
        return self._request(f"photos/{photo_id}")

    def popular_videos(self, per_page=15, page=1, **kwargs):
        """Gets popular videos."""
        params = {"per_page": per_page, "page": page, **kwargs}
        return self._request("videos/popular", params=params)

    def get_video(self, video_id):
        """Gets a specific video by its ID."""
        return self._request(f"videos/videos/{video_id}")

    def collections(self, per_page=15, page=1):
        """Gets a list of featured collections."""
        params = {"per_page": per_page, "page": page}
        return self._request("collections/featured", params=params)

    def collection_media(self, collection_id, type="photos", per_page=15, page=1):
        """Gets media (photos or videos) from a specific collection."""
        params = {"type": type, "per_page": per_page, "page": page}
        return self._request(f"collections/{collection_id}", params=params)

    # --- Download Methods ---
    def _download_file(self, url, filepath, filename):
        """Downloads a file from a URL and saves it."""
        os.makedirs(filepath, exist_ok=True)
        full_path = os.path.join(filepath, filename)
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(full_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Successfully downloaded {filename} to {filepath}")
            return full_path
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
        except IOError as e:
            logger.error(f"Error saving file {full_path}: {e}")
            return None

    def download_photo_from_result(self, photo_object, folder_path="pexels_downloads"):
        """Downloads a photo from a photo API result object."""
        if not photo_object or 'src' not in photo_object or 'original' not in photo_object['src']:
            logger.warning("Invalid photo object or missing original source URL.")
            return None
        
        photo_id = photo_object.get('id', 'unknown_id')
        photographer = photo_object.get('photographer', 'unknown_photographer').replace(" ", "_")
        
        original_url = photo_object['src']['original']
        file_extension = os.path.splitext(original_url.split('?')[0])[-1]
        if not file_extension:
            file_extension = ".jpg"

        filename = f"pexels_{photo_id}_{photographer}{file_extension}"
        return self._download_file(original_url, folder_path, filename)

    def download_video_from_result(self, video_object, folder_path="pexels_downloads", quality="hd"):
        """Downloads a video from a video API result object."""
        if not video_object or 'video_files' not in video_object or not video_object['video_files']:
            logger.warning("Invalid video object or missing video files.")
            return None

        video_id = video_object.get('id', 'unknown_id')
        target_link = None
        available_qualities = {}
        for vf in video_object['video_files']:
            if vf.get('link'):
                q_label = vf.get('quality', f"{vf.get('width')}x{vf.get('height')}")
                available_qualities[q_label] = vf['link']
                if vf.get('quality') == quality:
                    target_link = vf['link']
                    break
        
        if not target_link:
            if 'hd' in available_qualities: target_link = available_qualities['hd']
            elif 'sd' in available_qualities: target_link = available_qualities['sd']
            elif available_qualities: target_link = list(available_qualities.values())[0]

        if not target_link:
            logger.warning(f"Could not find a suitable download link for video {video_id} with quality '{quality}'.")
            return None

        file_extension = os.path.splitext(target_link.split('?')[0])[-1]
        if not file_extension:
            file_extension = ".mp4"

        filename = f"pexels_video_{video_id}{file_extension}"
        return self._download_file(target_link, folder_path, filename)

    def download_search_results(self, search_type, query, num_items_to_download, folder_path="pexels_downloads", **search_kwargs):
        """Downloads a specified number of items (photos or videos) from search results."""
        if search_type not in ["photos", "videos"]:
            logger.error("Invalid search_type. Must be 'photos' or 'videos'.")
            return []

        downloaded_files = []
        items_retrieved = 0
        page = 1
        per_page = min(num_items_to_download - items_retrieved, 80) if num_items_to_download > 0 else 80

        while items_retrieved < num_items_to_download:
            if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 1:
                logger.warning("Approaching rate limit. Pausing downloads.")
                if self.rate_limit_reset:
                    wait_time = max(0, self.rate_limit_reset - time.time())
                    logger.info(f"Waiting for {wait_time:.0f} seconds until rate limit resets.")
                    time.sleep(wait_time + 5)
                else:
                    logger.warning("Rate limit reset time unknown. Stopping.")
                    break
            
            current_per_page = min(num_items_to_download - items_retrieved, per_page)
            if current_per_page <= 0: break

            logger.info(f"Requesting page {page} with {current_per_page} items for query '{query}'...")
            if search_type == "photos":
                results = self.search_photos(query, per_page=current_per_page, page=page, **search_kwargs)
                key_name = 'photos'
                download_func = self.download_photo_from_result
            else: # videos
                results = self.search_videos(query, per_page=current_per_page, page=page, **search_kwargs)
                key_name = 'videos'
                download_func = self.download_video_from_result
            
            if not results or key_name not in results or not results[key_name]:
                logger.info(f"No more {search_type} found for query '{query}' on page {page}.")
                break

            for item in results[key_name]:
                if items_retrieved >= num_items_to_download:
                    break
                
                if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
                    logger.warning("Rate limit reached during item processing. Stopping.")
                    return downloaded_files

                file_path = download_func(item, folder_path=folder_path)
                if file_path:
                    downloaded_files.append(file_path)
                    items_retrieved += 1
                time.sleep(0.1) 

            if items_retrieved >= num_items_to_download:
                break
            
            if not results.get('next_page'):
                logger.info("No more pages available.")
                break
            
            page += 1

        logger.info(f"Downloaded {len(downloaded_files)} files to {folder_path}.")
        return downloaded_files

if __name__ == '__main__':
    # Configure Loguru logger
    logger.add("pexels_api.log", rotation="10 MB", retention="7 days", level="INFO")
    # You can also remove the default handler to prevent duplicate console output if desired
    # logger.remove()
    # logger.add(sys.stderr, level="INFO")


    API_KEY = "fWR0eYyjy9EY2hu9b9bsADZSOQhexk0hgGlVSYnrs53Dq0AQNqNhxyML" 
    
    if not API_KEY or API_KEY == "YOUR_PEXELS_API_KEY":
        logger.error("Please replace 'YOUR_PEXELS_API_KEY' with your actual Pexels API key to run the example.")
    else:
        pexels_client = PexelsAPI(api_key=API_KEY)

        logger.info("--- Starting Pexels API example usage ---")

        # 1. Search for photos
        logger.info("--- Searching for photos of 'nature' ---")
        photos_data = pexels_client.search_photos(query="nature", per_page=2)
        if photos_data and 'photos' in photos_data:
            for photo in photos_data['photos']:
                logger.info(f"Photo ID: {photo['id']}, Photographer: {photo['photographer']}, URL: {photo['url']}")
        logger.info(f"Rate limit status: {pexels_client.get_rate_limit_status()}")

        # 2. Search for videos
        logger.info("--- Searching for videos of 'ocean' ---")
        videos_data = pexels_client.search_videos(query="ocean", per_page=2)
        if videos_data and 'videos' in videos_data:
            for video in videos_data['videos']:
                logger.info(f"Video ID: {video['id']}, Duration: {video['duration']}s, URL: {video['url']}")
        logger.info(f"Rate limit status: {pexels_client.get_rate_limit_status()}")

        # 3. Get curated photos
        logger.info("--- Getting curated photos ---")
        curated_data = pexels_client.curated_photos(per_page=2)
        if curated_data and 'photos' in curated_data:
            for photo in curated_data['photos']:
                logger.info(f"Curated Photo ID: {photo['id']}, Photographer: {photo['photographer']}")
        logger.info(f"Rate limit status: {pexels_client.get_rate_limit_status()}")
        
        # 4. Download search results (e.g., 3 photos of "cats")
        logger.info("--- Downloading 3 photos of 'cats' ---")
        downloaded_cat_photos = pexels_client.download_search_results(
            search_type="photos",
            query="cats",
            num_items_to_download=3,
            folder_path="pexels_cats"
        )
        logger.info(f"Downloaded files: {downloaded_cat_photos}")
        logger.info(f"Rate limit status after downloads: {pexels_client.get_rate_limit_status()}")

        # 5. Download search results (e.g., 2 videos of "fireworks")
        logger.info("--- Downloading 2 videos of 'fireworks' ---")
        downloaded_fireworks_videos = pexels_client.download_search_results(
            search_type="videos",
            query="fireworks",
            num_items_to_download=2,
            folder_path="pexels_fireworks",
            search_kwargs={'orientation': 'portrait', 'size': 'medium'}
        )
        logger.info(f"Downloaded files: {downloaded_fireworks_videos}")
        logger.info(f"Rate limit status after downloads: {pexels_client.get_rate_limit_status()}")

        # 6. Get featured collections
        logger.info("--- Getting featured collections ---")
        collections_data = pexels_client.collections(per_page=2)
        if collections_data and 'collections' in collections_data:
            for collection in collections_data['collections']:
                logger.info(f"Collection ID: {collection['id']}, Title: {collection['title']}, Photos: {collection['photos_count']}")
        logger.info(f"Rate limit status: {pexels_client.get_rate_limit_status()}")
        logger.info("--- Pexels API example usage finished ---")
