# signal for when the list item is clicked
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QEvent
from bases import Box
from pydantic import BaseSettings


class BoxListWidget(QtWidgets.QDockWidget):
    def __init__(self, projectSettingsBoxes, parent=None):
        super(BoxListWidget, self).__init__(parent=parent)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.boxes = projectSettingsBoxes
        self.settingsWindow = None
        self.initUI()

    def initUI(self):
        # add name to the dock widget
        self.setWindowTitle("Box List")

        # create a new box button
        self.newBoxButton = QtWidgets.QPushButton("New Box")
        self.newBoxButton.clicked.connect(self.newBox)

        # create the box list
        self.listWidget = QtWidgets.QListWidget()
        # on item selection, BoxListItem signals clicked
        self.listWidget.itemClicked.connect(self.openBoxSettings)

        # set the layout and add the widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.newBoxButton)
        self.layout.addWidget(self.listWidget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # create a new widget for the layout
        self.newWidget = QtWidgets.QWidget()
        self.newWidget.setLayout(self.layout)

        # add the boxes to the list
        for box in self.boxes:
            # add the item to the list
            self.addBox(box)

        # show the dock widget
        self.setWidget(self.newWidget)
        self.show()

    def openBoxSettings(self, box: Box):
        # if there is a box settings window open, save the current box settings
        if self.settingsWindow.currentBox is not None:
            self.settingsWindow.saveCurrentBoxSettings()

        self.settingsWindow.showBoxSettings(box)

    # override closeEvent to hide the dock widget instead of closing it
    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def showEvent(self, event):
        self.update()
        event.accept()

    def newBox(self):
        # create a new box
        newBox = Box()
        # append the box to the list
        self.boxes.append(newBox)
        # add the box to the list
        self.addBox(newBox)

    def addBox(self, box: Box):
        pass
        # if box is None:
        #     return
        # # create a new list item
        # listItem = BoxListItem(box=box, parent=self.listWidget)
        # # bind the setSelected event to print
        # listItem.signals.clicked.connect(lambda: self.settingsWindow.showBoxSettings(listItem.box))

        # # make the list item checkable
        # listItem.setFlags(listItem.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        # # set the list item to unchecked
        # listItem.setCheckState(Qt.CheckState.Unchecked)
        # # set the list item text to the box name
        # listItem.setText(f"Box {box.box}")
        # # add the list item to the list
        # self.listWidget.addItem(listItem)

    def updateBoxes(self, boxes):
        self.boxes = boxes
        self.listWidget.clear()
        for box in self.boxes:
            self.addBox(box)
