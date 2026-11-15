import logging
import threading
from collections import deque

from PySide6 import QtCore, QtWidgets


class LogHistoryHandler(logging.Handler):
    """Keep the most recent formatted log messages in memory."""

    def __init__(self, capacity: int = 5000):
        super().__init__()
        self.records = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord):
        message = self.format(record)
        with self._lock:
            self.records.append(message)

    def text(self) -> str:
        with self._lock:
            return "\n".join(self.records)

    def clear(self):
        with self._lock:
            self.records.clear()


class ClickableStatusBar(QtWidgets.QStatusBar):
    clicked = QtCore.Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class LogViewerDialog(QtWidgets.QDialog):
    def __init__(self, history: LogHistoryHandler, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("Logs")
        self.resize(900, 500)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        self.mainLayout.addWidget(self.text)

        buttons = QtWidgets.QHBoxLayout()
        self.clearPB = QtWidgets.QPushButton("Clear")
        self.clearPB.clicked.connect(self.on_clearClicked)
        buttons.addWidget(self.clearPB)
        self.closePB = QtWidgets.QPushButton("Close")
        self.closePB.clicked.connect(self.accept)
        buttons.addWidget(self.closePB)
        self.mainLayout.addLayout(buttons)

        self.refresh()
        self.refreshTimer = QtCore.QTimer(self)
        self.refreshTimer.timeout.connect(self.refresh)
        self.refreshTimer.start(1000)

    def refresh(self):
        scrollBar = self.text.verticalScrollBar()
        atBottom = scrollBar.value() >= scrollBar.maximum() - 4
        self.text.setPlainText(self.history.text())
        if atBottom:
            scrollBar.setValue(scrollBar.maximum())

    def on_clearClicked(self):
        self.history.clear()
        self.refresh()

    def accept(self):
        self.refreshTimer.stop()
        super().accept()

    def reject(self):
        self.refreshTimer.stop()
        super().reject()
