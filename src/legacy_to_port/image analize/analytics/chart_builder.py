import matplotlib

matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Modern Dark Theme for Charts
plt.style.use("dark_background")
colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]


class ChartBuilder:
    @staticmethod
    def create_area_histogram(raw_areas: list[int], num_bins: int = 20) -> FigureCanvasQTAgg:
        """Create a histogram of image areas from raw data."""
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor("#1e1e1e")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2d2d2d")

        if raw_areas and len(raw_areas) > 0:
            areas = np.array(raw_areas)
            ax.hist(areas, bins=num_bins, color="#00a8e8", alpha=0.7, edgecolor="white")
            ax.set_title("Image Area Distribution", color="white", fontsize=10)
            ax.set_xlabel("Area (pixels)", color="gray", fontsize=8)
            ax.set_ylabel("Count", color="gray", fontsize=8)
            ax.tick_params(axis="x", colors="gray", labelsize=7)
            ax.tick_params(axis="y", colors="gray", labelsize=7)
            ax.grid(True, linestyle="--", alpha=0.1)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color="gray")

        fig.tight_layout()
        return FigureCanvasQTAgg(fig)

    @staticmethod
    def create_file_size_histogram(raw_sizes: list[int], num_bins: int = 20) -> FigureCanvasQTAgg:
        """Create a histogram of file sizes from raw data."""
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor("#1e1e1e")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2d2d2d")

        if raw_sizes and len(raw_sizes) > 0:
            sizes = np.array(raw_sizes) / 1024  # Convert to KB
            ax.hist(sizes, bins=num_bins, color="#f28e2b", alpha=0.7, edgecolor="white")
            ax.set_title("File Size Distribution", color="white", fontsize=10)
            ax.set_xlabel("Size (KB)", color="gray", fontsize=8)
            ax.set_ylabel("Count", color="gray", fontsize=8)
            ax.tick_params(axis="x", colors="gray", labelsize=7)
            ax.tick_params(axis="y", colors="gray", labelsize=7)
            ax.grid(True, linestyle="--", alpha=0.1)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color="gray")

        fig.tight_layout()
        return FigureCanvasQTAgg(fig)

    @staticmethod
    def create_format_pie(data: dict[str, int]) -> FigureCanvasQTAgg:
        """Create a donut chart of file formats."""
        fig = Figure(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor("#1e1e1e")
        ax = fig.add_subplot(111)

        labels = list(data.keys())
        sizes = list(data.values())

        if sizes:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.85,
                colors=colors[: len(labels)],
                textprops={"color": "white"},
            )

            centre_circle = plt.Circle((0, 0), 0.70, fc="#1e1e1e")
            fig.gca().add_artist(centre_circle)

            ax.axis("equal")
            plt.setp(autotexts, size=8, weight="bold", color="white")
            plt.setp(texts, size=8)
            ax.set_title("File Formats", color="white", fontsize=10)
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color="gray")

        fig.tight_layout()
        return FigureCanvasQTAgg(fig)
