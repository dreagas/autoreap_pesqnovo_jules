from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QPlainTextEdit, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QWheelEvent

class NoScrollComboBox(QComboBox):
    """
    A QComboBox that ignores wheel events unless the widget has explicit focus.
    This prevents accidental changes when scrolling the page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class NoScrollSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class StyledButton(QPushButton):
    """Standard Styled Button."""
    def __init__(self, text="", parent=None, variant="default", icon=None):
        super().__init__(text, parent)
        if variant == "primary":
            self.setObjectName("primary")
        elif variant == "danger":
            self.setObjectName("danger")

        self.setCursor(Qt.PointingHandCursor)
        if icon:
            self.setIcon(icon)

class LogWidget(QPlainTextEdit):
    """Read-only log widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("log_widget")
        self.setPlaceholderText("Aguardando logs...")
        self.setMaximumHeight(150)

    def append_log(self, message):
        self.appendPlainText(message)
        # Auto scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class StatusIndicator(QFrame):
    """Shows current status (Ready, Running, Error)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("PRONTO")
        self.label.setObjectName("status_ready")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def set_status(self, status_code, text=None):
        """
        status_code: 'ready', 'running', 'error'
        """
        if text:
            self.label.setText(text.upper())

        if status_code == "ready":
            self.label.setObjectName("status_ready")
        elif status_code == "running":
            self.label.setObjectName("status_running")
        elif status_code == "error":
            self.label.setObjectName("status_error")
        else:
            self.label.setObjectName("status_ready")

        # Refresh style
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)

class Card(QFrame):
    """Container with background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
