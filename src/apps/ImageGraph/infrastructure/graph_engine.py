from __future__ import annotations
import math
import networkx as nx
from typing import List, Dict, Optional, Any, cast
from PySide6.QtCore import QPointF, Qt, QRectF, QObject, Signal, Slot
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, 
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem,
    QColorDialog, QMenu, QGraphicsSceneContextMenuEvent
)

class GraphEngine(QObject):
    """Bridge for BCor to use the ported Graph Editor core."""
    pass

class BaseNode(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, radius: float, data_context: Any = None) -> None:
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        self.radius = radius
        self.data_context = data_context
        self.edges: List[BaseEdge] = []
        self.setBrush(QColor("blue"))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

class BaseEdge(QGraphicsLineItem):
    def __init__(self, node1: BaseNode, node2: BaseNode, data_context: Any = None) -> None:
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        self.data_context = data_context
        self.setPen(QPen(QColor("black"), 3))
        node1.edges.append(self)
        node2.edges.append(self)
        self.setZValue(-1)
        self.update_position()

    def update_position(self) -> None:
        p1 = self.node1.scenePos()
        p2 = self.node2.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

class BCorGraphScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: List[BaseNode] = []
        self.edges: List[BaseEdge] = []

    def addItem(self, item: QGraphicsItem) -> None:
        super().addItem(item)
        if isinstance(item, BaseNode):
            self.nodes.append(item)
        elif isinstance(item, BaseEdge):
            self.edges.append(item)

    def removeItem(self, item: QGraphicsItem) -> None:
        super().removeItem(item)
        if item in self.nodes:
            self.nodes.remove(cast(BaseNode, item))
        elif item in self.edges:
            self.edges.remove(cast(BaseEdge, item))

    def clear_scene(self) -> None:
        super().clear()
        self.nodes.clear()
        self.edges.clear()

    def auto_arrange(self, algorithm: str = "spring") -> None:
        if not self.nodes:
            return
        
        G = nx.Graph()
        for node in self.nodes:
            G.add_node(node)
        for edge in self.edges:
            G.add_edge(edge.node1, edge.node2)

        if algorithm == "spring":
            pos = nx.spring_layout(G, k=1.0/math.sqrt(len(self.nodes))*200)
        elif algorithm == "circular":
            pos = nx.circular_layout(G, scale=500)
        else:
            pos = nx.spring_layout(G)

        for node, coord in pos.items():
            node.setPos(coord[0]*1000, coord[1]*1000)
            for edge in node.edges:
                edge.update_position()

class GraphView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: Any) -> None:
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)
        event.accept()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._isMiddleMousePressed = True
            self._lastPos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if hasattr(self, '_isMiddleMousePressed') and self._isMiddleMousePressed:
            delta = event.pos() - self._lastPos
            self._lastPos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._isMiddleMousePressed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
