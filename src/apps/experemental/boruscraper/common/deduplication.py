import os
import imagehash
from PIL import Image
from loguru import logger
from typing import Optional, List, Dict, Tuple

class DeduplicationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.hash_cache = None # List of dicts: {'hash_obj': ImageHash, 'data': dict}

    def calculate_dhash(self, image_path: str) -> Optional[str]:
        """Calculates the dhash of an image."""
        try:
            with Image.open(image_path) as img:
                return str(imagehash.dhash(img))
        except Exception as e:
            logger.error(f"Failed to calculate dhash for {image_path}: {e}")
            return None

    def _ensure_cache(self, current_project_id: int):
        """Loads all hashes from OTHER projects into memory if not loaded."""
        # For simplicity in this 'fast' implementation, we reload or update?
        # If we share the manager, checking different projects concurrently might be slightly racy if we filter by 'other' in the SQL.
        # Better: Fetch ALL hashes once, store with project_id.
        if self.hash_cache is None:
            raw_data = self.db_manager.get_all_other_hashes(-1) # -1 to get ALL
            self.hash_cache = []
            for row in raw_data:
                try:
                    h_obj = imagehash.hex_to_hash(row['dhash'])
                    self.hash_cache.append({'h': h_obj, 'd': row})
                except Exception:
                    pass # Invalid hash in DB?

    def check_is_duplicate(self, dhash_str: str, current_project_id: int, threshold: int = 0) -> Tuple[bool, List[Dict], float]:
        """
        Checks if the dhash exists in OTHER projects.
        Returns (is_duplicate, list_of_conflicts, min_distance).
        """
        if not dhash_str:
            return False, [], float('inf')

        # 1. Exact Match (Fast DB Query) - OPTIONAL optimization
        # We now prefer to ALWAYS calculate min_dist for user feedback.
        # Since _ensure_cache loads all hashes anyway (for now), the loop covers exact matches (dist=0).
        # if threshold == 0:
        #    conflicts = self.db_manager.check_dhash_exists(dhash_str, -1)
        #    if conflicts:
        #        return True, conflicts, 0.0
        #    return False, [], float('inf')

        # 2. Smart Match (Hamming Distance)
        self._ensure_cache(current_project_id)
        
        target_hash = imagehash.hex_to_hash(dhash_str)
        conflicts = []
        min_dist = float('inf')
        
        # We need to manually add any NEW hashes found during this session to the cache?
        # For now, we rely on the pre-loaded cache + DB. 
        # CAUTION: If we don't update cache, we might miss dupes within the same run if they were JUST added?
        # But per requirements: "dhash exists in OTHER projects". Usually previously scraped ones.
        # If we scrape concurrently, we might need to append to cache.

        for item in self.hash_cache:
            # We now ALLOW same project checks (User Request)
            # if item['d']['project_id'] == current_project_id:
            #     continue

            dist = item['h'] - target_hash
            if dist < min_dist:
                min_dist = dist
                
            if dist <= threshold:
                # Add distance info to conflict data
                c_data = item['d'].copy()
                c_data['distance'] = dist
                conflicts.append(c_data)

        if conflicts:
            conflicts.sort(key=lambda x: x['distance'])
            return True, conflicts, min_dist
            
        return False, [], min_dist

    def add_to_cache(self, dhash_str: str, data: Dict):
        """Update cache with new item to ensure immediate consistency."""
        if self.hash_cache is not None:
             try:
                h_obj = imagehash.hex_to_hash(dhash_str)
                self.hash_cache.append({'h': h_obj, 'd': data})
             except: pass
