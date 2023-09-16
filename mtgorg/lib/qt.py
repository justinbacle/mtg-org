import logging
import typing
from pathlib import Path
from PySide6 import QtGui, QtWidgets, QtSvg, QtCore, QtCharts

from mtgorg.lib import system


def selectPalette(app):
    # Overriden by material
    try:
        palette = QtGui.QPalette()
        if system.isWin10Dark():  # Dark theme enabled

            # Force the style to be the same on all OSs:
            if "Fusion" in QtWidgets.QStyleFactory.keys():
                app.setStyle("Fusion")

            # Now use a palette to switch to dark colors:
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("white"))
            palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("red"))
            palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
            palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("black"))
            palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(200, 200, 200))
            palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor(50, 50, 50))
            palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(80, 80, 80))

        else:
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        app.setPalette(palette)
    except Exception as e:
        logging.error(e)


def svgPathToPixmap(svg_filename: str, width: int, height: int, color: QtGui.QColor) -> QtGui.QPixmap:
    renderer = QtSvg.QSvgRenderer(svg_filename)
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtGui.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setPen(QtGui.QPen(color))
    renderer.render(painter)
    painter.end()
    return pixmap


def fileData(path: str | Path) -> str:
    if isinstance(path, Path):
        stream = QtCore.QFile(path.as_posix())
    else:
        stream = QtCore.QFile(path)
    if stream.open(QtCore.QFile.ReadOnly):
        js = str(stream.readAll(), 'utf-8')
        stream.close()
    else:
        logging.error(stream.errorString())
    return js


class ResizingGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        if self.scene() is not None:
            bounds = self.scene().itemsBoundingRect()
            self.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
        return super().resizeEvent(event)


def findAttrInParents(object: QtCore.QObject, attr: str) -> typing.Any:
    parent = object.parent()
    try:
        while not hasattr(parent, attr):
            parent = parent.parent()
    except AttributeError as e:
        logging.error(f"{object=} raised {e=} when looking for parent")
        raise e
    return getattr(parent, attr)


class FlowLayout(QtWidgets.QLayout):
    """from : https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html"""
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


def getChartsTheme():
    theme = QtCharts.QChart.ChartTheme.ChartThemeDark
    return theme


class ExtendedComboBox(QtWidgets.QComboBox):
    """
    from
    https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input
    """
    def __init__(self, parent=None):
        super(ExtendedComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QtWidgets.QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            try:
                self.activated[str].emit(self.itemText(index))
            except IndexError:
                # Don't really know what's happening there
                ...

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)
