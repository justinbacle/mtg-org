import logging

from widgets.logviewer import LogHistoryHandler, LogViewerDialog


def makeRecord(message: str) -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, __file__, 1, message, None, None)


def test_log_history_handler_captures_and_clears():
    history = LogHistoryHandler(capacity=2)
    history.setFormatter(logging.Formatter("%(message)s"))

    history.emit(makeRecord("one"))
    history.emit(makeRecord("two"))
    history.emit(makeRecord("three"))

    assert history.text() == "two\nthree"

    history.clear()
    assert history.text() == ""


def test_log_viewer_dialog_refreshes(qtApp):
    history = LogHistoryHandler()
    history.setFormatter(logging.Formatter("%(message)s"))
    history.emit(makeRecord("hello"))
    dialog = LogViewerDialog(history)

    assert "hello" in dialog.text.toPlainText()
    assert dialog.refreshTimer.isActive()

    history.emit(makeRecord("world"))
    dialog.refresh()
    assert "world" in dialog.text.toPlainText()

    dialog.on_clearClicked()
    assert dialog.text.toPlainText() == ""
    dialog.accept()
    assert not dialog.refreshTimer.isActive()
