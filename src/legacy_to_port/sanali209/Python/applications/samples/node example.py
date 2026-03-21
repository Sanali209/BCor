#!/usr/bin/python
# -*- coding: utf-8 -*-
import signal
from pathlib import Path



from NodeGraphQtPy import NodeGraph,  PropertiesBinWidget, NodesTreeWidget, NodesPaletteWidget, BaseNode

# import example nodes from the "nodes" sub-package

from qtpy import QtWidgets, QtCore

BASE_PATH = Path(__file__).parent.resolve()

class FooNode(BaseNode):
    __identifier__ = 'nodes.custom'
    NODE_NAME = 'Foo Node'

    def __init__(self):
        super(FooNode, self).__init__()


        # add custom ports
        self.add_input('input1', color=(180,80,0))
        self.add_output('output1', )


def main():
    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication([])

    # create graph controller.
    graph = NodeGraph()

    # set up context menu for the node graph.


    # registered example nodes.
    graph.register_nodes([
        FooNode
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)
    graph_widget.show()

    # create node with custom text color and disable it.
    node_a = graph.create_node('nodes.custom.FooNode', 'a')
    node_b = graph.create_node('nodes.custom.FooNode', 'b')
    node_a.set_output(0, node_b.get_input(0))


    # auto layout nodes.
    graph.auto_layout_nodes()



    # fit nodes to the viewer.
    graph.clear_selection()
    graph.fit_to_selection()

    # Custom builtin widgets from NodeGraphQt
    # ---------------------------------------

    # create a node properties bin widget.
    properties_bin = PropertiesBinWidget(node_graph=graph)
    properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # example show the node properties bin widget when a node is double-clicked.
    def display_properties_bin(node):
        if not properties_bin.isVisible():
            properties_bin.show()

    # wire function to "node_double_clicked" signal.
    graph.node_double_clicked.connect(display_properties_bin)

    # create a nodes tree widget.
    nodes_tree = NodesTreeWidget(node_graph=graph)
    nodes_tree.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_tree.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_tree.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_tree.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_tree.set_category_label('nodes.group', 'Group Nodes')
    # nodes_tree.show()

    # create a node palette widget.
    nodes_palette = NodesPaletteWidget(node_graph=graph)
    nodes_palette.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_palette.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_palette.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_palette.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_palette.set_category_label('nodes.group', 'Group Nodes')
    # nodes_palette.show()

    app.exec()


if __name__ == '__main__':
    main()