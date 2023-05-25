import logging
from pathlib import Path
from PySide6 import QtGui, QtWidgets, QtSvg, QtCore

from lib import system


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
