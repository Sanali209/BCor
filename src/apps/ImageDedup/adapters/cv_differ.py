"""ImageDedup adapter: OpenCV Differ.

Implements IImageDiffer using CV2 absolute difference.
"""
import cv2
import numpy as np
from PIL import Image

from src.apps.ImageDedup.domain.interfaces.i_image_differ import IImageDiffer


class OpenCVDiffer(IImageDiffer):
    """Concrete implementation of image similarity using OpenCV."""

    def __init__(self, resize_dim: tuple[int, int] = (720, 720)) -> None:
        self.resize_dim = resize_dim

    def compute_difference(self, path_a: str, path_b: str) -> float:
        """Calculate similarity score [0.0 - 1.0].
        
        0.0 means identical, 1.0 means completely different.
        """
        try:
            # We use PIL to load to ensure same loading logic as other parts of BCor
            img_a = Image.open(path_a).convert("RGB")
            img_b = Image.open(path_b).convert("RGB")

            # Convert to CV2 format (BGR)
            cv_a = cv2.cvtColor(np.array(img_a), cv2.COLOR_RGB2BGR)
            cv_b = cv2.cvtColor(np.array(img_b), cv2.COLOR_RGB2BGR)

            # Resize to standardized dimensions for comparison
            cv_a_res = cv2.resize(cv_a, self.resize_dim)
            cv_b_res = cv2.resize(cv_b, self.resize_dim)

            # Absolute difference
            diff = cv2.absdiff(cv_a_res, cv_b_res)
            
            # Normalizing the difference to [0.0, 1.0]
            # mean of absolute differences across all pixels and channels
            mean_diff = np.mean(diff)
            score = mean_diff / 255.0

            return float(score)
        except Exception:
            # If images can't be loaded or compared, return maximum difference
            return 1.0

    def get_diff_highlight(self, path_a: str, path_b: str) -> np.ndarray:
        """Returns an image (numpy array) with differences highlighted.
        
        Used by UI to show visual comparison.
        """
        img_a = Image.open(path_a).convert("RGB")
        img_b = Image.open(path_b).convert("RGB")
        cv_a = cv2.cvtColor(np.array(img_a), cv2.COLOR_RGB2BGR)
        cv_b = cv2.cvtColor(np.array(img_b), cv2.COLOR_RGB2BGR)

        cv_a_res = cv2.resize(cv_a, self.resize_dim)
        cv_b_res = cv2.resize(cv_b, self.resize_dim)

        diff = cv2.absdiff(cv_a_res, cv_b_res)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 10 and h > 10:
                cv2.rectangle(cv_a_res, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        return cv_a_res
