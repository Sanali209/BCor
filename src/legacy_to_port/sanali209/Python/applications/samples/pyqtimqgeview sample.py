import sys
import os

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, \
    QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon

from SLM.FuncModule import get_files


class ImageViewerApp(QMainWindow):
    def __init__(self, image_paths):
        super().__init__()
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.image_paths = image_paths

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(150, 150))
        self.list_widget.setResizeMode(QListWidget.Adjust)

        for path in self.image_paths:
            item = ImageListItem(path)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        self.central_widget.setLayout(layout)

        # Connect the resize signal to the custom slot
        self.list_widget.resizeEvent = self.handle_resize

    def handle_resize(self, event):
        self.list_widget.updateGeometries()
        super(QListWidget, self.list_widget).resizeEvent(event)

    #on resize event rearange list items
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.list_widget.update()


class ImageListItem(QListWidgetItem):
    def __init__(self, image_path):
        super().__init__()

        pixmap = QIcon(image_path)

        self.setIcon(pixmap)
        self.setText(os.path.basename(image_path))



def main(image_paths):
    app = QApplication(sys.argv)
    viewer = ImageViewerApp(image_paths)
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    image_paths = get_files(r"F:\rawimagedb\repository\nsfv repo\_by races\Alien x Predator\Alien", exts=['*.jpg', '*.png', '*.jpeg'])
    main(image_paths)
