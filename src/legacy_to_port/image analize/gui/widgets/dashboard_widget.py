import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QScrollArea, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from analytics.plotly_chart_builder import PlotlyChartBuilder
from analytics.analytics_engine import AnalyticsEngine
from gui.utils import format_size, format_number

logger = logging.getLogger(__name__)

class StatCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            StatCard {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #58a6ff; font-size: 13px; font-weight: bold;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: bold;")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
    def update_value(self, value):
        self.lbl_value.setText(str(value))

class AnalyticsTab(QWidget):
    def __init__(self, analytics: AnalyticsEngine, parent=None):
        super().__init__(parent)
        self.analytics = analytics
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content.setStyleSheet("background-color: #1a1a2e;")
        self.layout = QVBoxLayout(content)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Header
        header = QLabel("Collection Overview")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff;")
        self.layout.addWidget(header)
        
        # 2. Stats Grid
        self.stats_grid = QGridLayout()
        self.card_total = StatCard("Total Images", "0")
        self.card_size = StatCard("Total Size", "0 B")
        self.card_formats = StatCard("Unique Formats", "0")
        # Change order or add row? 4 items fit nicely.
        # Let's replace "Avg File Size" with "Space Cleared"? Or add 5th?
        # User explicitly asked for "clined space on delete file add record to graphics"
        # I will add "Space Cleared" as 4th card, move Avg Size or Keep Avg Size.
        # Let's make it 5 cards flow? Or 6 (2 rows of 3).
        # Currently 1 row of 4.
        # Let's do: Total | Size | Formats | Space Saved | Avg Size (maybe drop avg or move)
        # I'll just add it to the end.
        self.card_saved = StatCard("Space Cleared", "0 B")
        self.card_saved.lbl_value.setStyleSheet("color: #59a14f; font-size: 26px; font-weight: bold;") # Green for savings
        
        self.stats_grid.addWidget(self.card_total, 0, 0)
        self.stats_grid.addWidget(self.card_size, 0, 1)
        self.stats_grid.addWidget(self.card_formats, 0, 2)
        self.stats_grid.addWidget(self.card_saved, 0, 3)
        
        self.layout.addLayout(self.stats_grid)
        
        # 3. Charts Area (2x2 Grid -> maybe 3 rows?)
        # User wants "realtime graphics on dashboard".
        # I'll add the Savings chart as a full-width chart at the bottom or top.
        
        self.charts_grid = QGridLayout()
        self.layout.addLayout(self.charts_grid)
        
        # Viewers
        self.chart_format_dist = QWebEngineView()
        self.chart_res_dist = QWebEngineView()
        self.chart_size_total = QWebEngineView()
        self.chart_savings = QWebEngineView() # New Chart
        
        # Min height
        for chart in [self.chart_format_dist, self.chart_res_dist, self.chart_size_total, self.chart_savings]:
            chart.setMinimumHeight(400)
            chart.setStyleSheet("background: transparent;")
            chart.page().setBackgroundColor(Qt.transparent)

        self.charts_grid.addWidget(self.chart_format_dist, 0, 0)
        self.charts_grid.addWidget(self.chart_res_dist, 0, 1)
        self.charts_grid.addWidget(self.chart_size_total, 1, 0)
        self.charts_grid.addWidget(self.chart_savings, 1, 1) # Savings chart instead of avg size
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def refresh(self):
        # 1. Summary Stats
        stats = self.analytics.get_collection_summary()
        savings_stats = self.analytics.get_savings_stats() # New
        
        total_images = stats.get('total_images', 0)
        total_size = stats.get('total_size_bytes', 0)
        formats = stats.get('formats', {})
        total_saved = savings_stats.get('total_saved_bytes', 0)
        
        self.card_total.update_value(format_number(total_images))
        self.card_size.update_value(format_size(total_size))
        self.card_formats.update_value(len(formats))
        self.card_saved.update_value(format_size(total_saved))
        
        # 2. Charts
        raw_data = self.analytics.get_raw_data_for_charts()
        ext_stats = self.analytics.get_extension_stats()
        history = savings_stats.get('history', [])
        
        # Donut: Formats
        html_donut = PlotlyChartBuilder.create_format_donut(formats)
        self.chart_format_dist.setHtml(html_donut)
        
        # Hist: Resolutions
        html_res = PlotlyChartBuilder.create_resolution_hist(raw_data.get('resolutions_by_ext', {}))
        self.chart_res_dist.setHtml(html_res)
        
        # Bar: Total Size
        html_size = PlotlyChartBuilder.create_size_bar(ext_stats)
        self.chart_size_total.setHtml(html_size)
        
        # Line: Savings
        html_savings = PlotlyChartBuilder.create_savings_chart(history)
        self.chart_savings.setHtml(html_savings)

class TopFilesTab(QWidget):
    def __init__(self, analytics: AnalyticsEngine, parent=None):
        super().__init__(parent)
        self.analytics = analytics
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setStyleSheet("background-color: #1a1a2e;")
        
        header = QLabel("Top 100 Largest Files")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #58a6ff; margin-bottom: 10px;")
        layout.addWidget(header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Filename", "Extension", "Resolution", "Size", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) # Path stretches
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0d1117;
                alternate-background-color: #16213e;
                gridline-color: #16213e;
                color: #e0e0e0;
                border: 1px solid #0f3460;
            }
            QHeaderView::section {
                background-color: #16213e;
                color: #58a6ff;
                padding: 5px;
                border: 1px solid #0f3460;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
    def refresh(self):
        top_files = self.analytics.get_top_large_images(100)
        
        self.table.setRowCount(0)
        for row, img in enumerate(top_files):
            self.table.insertRow(row)
            
            name_item = QTableWidgetItem(img['filename'])
            ext_item = QTableWidgetItem(img['extension'])
            res_item = QTableWidgetItem(f"{img['width']} x {img['height']}")
            
            # Use raw size for sorting, text for display if we subclass QTableWidgetItem, 
            # but for simplicity now just string. To sort correctly we'd need a custom item.
            # Assuming pre-sorted from DB query (which it is: ORDER BY size_bytes DESC).
            size_str = format_size(img['size_bytes'])
            size_item = QTableWidgetItem(size_str)
            
            path_item = QTableWidgetItem(img['path'])
            path_item.setToolTip(img['path'])
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, ext_item)
            self.table.setItem(row, 2, res_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, path_item)

class DashboardWidget(QWidget):
    def __init__(self, analytics_engine: AnalyticsEngine, parent=None):
        super().__init__(parent)
        self.analytics = analytics_engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.tab_overview = AnalyticsTab(self.analytics)
        self.tab_top_files = TopFilesTab(self.analytics)
        
        self.tabs.addTab(self.tab_overview, "Overview")
        self.tabs.addTab(self.tab_top_files, "Top 100 Files")
        
    def refresh_data(self):
        """Propagate refresh to tabs."""
        self.tab_overview.refresh()
        self.tab_top_files.refresh()
