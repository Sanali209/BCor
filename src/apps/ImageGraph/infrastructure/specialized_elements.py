from __future__ import annotations
import os
from typing import List, Optional, Any
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QColor, QPen, QPainter
from PySide6.QtWidgets import QMenu, QGraphicsSceneContextMenuEvent, QStyleOptionGraphicsItem, QWidget
from .graph_engine import BaseNode, BaseEdge, BCorGraphScene
from ..domain.models import RelationRecord, RelationSubType

class ImageNode(BaseNode):
    def __init__(self, x: float, y: float, radius: float, file_record: Any) -> None:
        super().__init__(x, y, radius, file_record)
        self.file_record = file_record
        self.image: Optional[QPixmap] = None
        self.setToolTip(f"ID: {file_record.id}\nPath: {file_record.local_path}")
        
        # Load thumbnail if available
        if hasattr(file_record, 'full_path') and os.path.exists(file_record.full_path):
             self.set_image(file_record.full_path)

    def set_image(self, path: str) -> None:
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.image = pixmap
            self.update()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        if self.image:
            rect = self.rect()
            scaled = self.image.scaled(
                int(rect.width()), 
                int(rect.height()), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            x = rect.x() + (rect.width() - scaled.width()) / 2
            y = rect.y() + (rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            super().paint(painter, option, widget)

class TagNode(BaseNode):
    def __init__(self, x: float, y: float, radius: float, tag_record: Any) -> None:
        super().__init__(x, y, radius, tag_record)
        self.tag_record = tag_record
        self.setBrush(Qt.GlobalColor.yellow)
        self.setToolTip(f"Tag: {tag_record.name}")

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        super().paint(painter, option, widget)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.tag_record.name)

class PinNode(BaseNode):
    def __init__(self, x: float, y: float, radius: float, name: str) -> None:
        super().__init__(x, y, radius, name)
        self.name = name
        self.setBrush(Qt.GlobalColor.cyan)
        self.setToolTip(f"Pin: {name}")

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        super().paint(painter, option, widget)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.name)

class RelationEdge(BaseEdge):
    def __init__(self, node1: BaseNode, node2: BaseNode, relation: Optional[RelationRecord] = None) -> None:
        super().__init__(node1, node2, relation)
        self.relation = relation
        if relation:
            self.colorize(relation.sub_type)

    def colorize(self, sub_type: RelationSubType) -> None:
        colors = {
            RelationSubType.WRONG: Qt.GlobalColor.red,
            RelationSubType.SIMILAR: Qt.GlobalColor.green,
            RelationSubType.SIMILAR_STYLE: Qt.GlobalColor.blue,
            RelationSubType.MANUAL: Qt.GlobalColor.darkGreen,
            RelationSubType.NONE: Qt.GlobalColor.yellow
        }
        color = colors.get(sub_type, Qt.GlobalColor.black)
        self.setPen(QPen(color, 3))
