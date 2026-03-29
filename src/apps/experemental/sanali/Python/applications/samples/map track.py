import cv2
import numpy as np
from sklearn.cluster import DBSCAN

from SLM.vision.window_capture import WindowCapture


class ClusterFlowTracker:
    def __init__(self, fb_thresh=1.0, max_corners=1200, eps=3, min_samples=5):
        """
        fb_thresh   : порог forward-backward ошибки
        max_corners : макс. число точек для трекинга
        eps         : радиус кластера для DBSCAN
        min_samples : мин. точек для кластера
        """
        self.prev_gray = None
        self.prev_pts = None
        self.fb_thresh = fb_thresh
        self.max_corners = max_corners
        self.global_shift = np.array([0.0, 0.0])  # глобальная позиция игрока
        self.dbscan_eps = eps
        self.dbscan_min_samples = min_samples

    def _forward_backward_check(self, prev_gray, gray, p0, fb_thresh=1.0):
        """Проверка точек методом forward-backward consistency."""
        lk_params = dict(winSize=(15, 15),
                         maxLevel=2,
                         criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        # прямой проход
        p1, st, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, p0, None, **lk_params)
        # обратный проход
        p0r, st_back, _ = cv2.calcOpticalFlowPyrLK(gray, prev_gray, p1, None, **lk_params)

        fb = np.linalg.norm(p0 - p0r, axis=2).reshape(-1)
        st = st.reshape(-1).astype(bool)
        st_back = st_back.reshape(-1).astype(bool)

        good = (fb < fb_thresh) & st & st_back
        return p0[good], p1[good]

    def _cluster_shifts(self, p0_ok, p1_ok):
        """Кластеризация смещений и выбор главного кластера."""
        if len(p0_ok) == 0:
            return np.array([0.0, 0.0])

        shifts = p1_ok - p0_ok
        shifts = shifts.reshape(-1, 2)

        clustering = DBSCAN(eps=self.dbscan_eps, min_samples=self.dbscan_min_samples).fit(shifts)
        labels = clustering.labels_

        # -1 = шум, берём самый большой кластер != -1
        unique, counts = np.unique(labels[labels >= 0], return_counts=True)
        if len(unique) == 0:
            return np.array([0.0, 0.0])

        main_cluster = unique[np.argmax(counts)]
        main_shifts = shifts[labels == main_cluster]

        return np.mean(main_shifts, axis=0)

    def step(self, frame_bgr):
        """Обработка одного кадра. Возвращает (глобальная_позиция, сдвиг_кадра)."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, maxCorners=self.max_corners,
                                                    qualityLevel=0.01, minDistance=7, blockSize=7)
            return self.global_shift, np.array([0.0, 0.0])

        if self.prev_pts is None or len(self.prev_pts) < 10:
            self.prev_pts = cv2.goodFeaturesToTrack(self.prev_gray, mask=None, maxCorners=self.max_corners,
                                                    qualityLevel=0.01, minDistance=7, blockSize=7)

        # forward-backward check
        p0_ok, p1_ok = self._forward_backward_check(self.prev_gray, gray,
                                                    self.prev_pts.astype(np.float32),
                                                    fb_thresh=self.fb_thresh)

        # кластеризация смещений
        shift = self._cluster_shifts(p0_ok, p1_ok)
        self.global_shift += shift

        # обновляем состояние
        self.prev_gray = gray
        self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, maxCorners=self.max_corners,
                                                qualityLevel=0.01, minDistance=7, blockSize=7)

        return self.global_shift.copy(), shift.copy()


if __name__ == "__main__":
    cap =WindowCapture("Titan Quest Anniversary Edition")
    tracker = ClusterFlowTracker()

    while True:
        frame = cap.get_screenshot()


        global_pos, frame_shift = tracker.step(frame)
        print("Сдвиг кадра:", frame_shift, "  Глобальная позиция:", global_pos)



    cap.release()
