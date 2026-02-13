from PySide6.QtWidgets import (
    QComboBox, QSpinBox, QDoubleSpinBox, QWidget, QHBoxLayout, QPushButton,
    QDialog, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QWheelEvent, QIcon
from core.constants import BROWSER_CHROME, BROWSER_EDGE, IMG_DIR
import os

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class ModernMessageBox(QDialog):
    def __init__(self, title, message, icon_type="INFO", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        layout.addWidget(frame)
        
        inner = QVBoxLayout(frame)
        inner.setSpacing(15)
        inner.setContentsMargins(20, 20, 20, 20)
        
        # Icon Color
        color = "#38BDF8" # Info Blue
        if icon_type == "WARNING": color = "#FACC15"
        elif icon_type == "ERROR": color = "#EF4444"
        elif icon_type == "SUCCESS": color = "#10B981"
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900; background: transparent;")
        inner.addWidget(title_lbl)
        
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #E2E8F0; font-size: 13px; background: transparent;")
        inner.addWidget(msg_lbl)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #000000;
                font-weight: bold;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: white;
            }}
        """)
        btn_box.addWidget(self.btn_ok)
        
        if icon_type in ["WARNING", "ERROR"] and "cancel" not in title.lower():
             # Opcional: Adicionar botão cancelar se necessário no futuro
             pass

        inner.addLayout(btn_box)

    def exec(self):
        return super().exec()

class BrowserSwitch(QWidget):
    browserChanged = Signal(str)

    def __init__(self, current_browser=BROWSER_CHROME):
        super().__init__()
        self.current_browser = current_browser
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Chrome Option
        self.btn_chrome = self.create_option_btn(BROWSER_CHROME, "img_chrome.png")
        self.btn_chrome.clicked.connect(lambda: self.set_browser(BROWSER_CHROME))
        layout.addWidget(self.btn_chrome)

        # Edge Option
        self.btn_edge = self.create_option_btn(BROWSER_EDGE, "img_edge.png")
        self.btn_edge.clicked.connect(lambda: self.set_browser(BROWSER_EDGE))
        layout.addWidget(self.btn_edge)

        self.update_style()

    def create_option_btn(self, browser_id, icon_name):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)

        icon_path = os.path.join(IMG_DIR, icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
        else:
            btn.setText(browser_id.capitalize())
            
        return btn

    def set_browser(self, browser):
        if browser != self.current_browser:
            self.current_browser = browser
            self.update_style()
            self.browserChanged.emit(browser)

    def update_style(self):
        # Apply styles based on selection
        active_style = """
            QPushButton {
                background-color: #0284C7;
                border: 2px solid #38BDF8;
                border-radius: 8px;
            }
        """
        inactive_style = """
            QPushButton {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """

        if self.current_browser == BROWSER_CHROME:
            self.btn_chrome.setStyleSheet(active_style)
            self.btn_edge.setStyleSheet(inactive_style)
            self.btn_chrome.setChecked(True)
            self.btn_edge.setChecked(False)
        else:
            self.btn_chrome.setStyleSheet(inactive_style)
            self.btn_edge.setStyleSheet(active_style)
            self.btn_chrome.setChecked(False)
            self.btn_edge.setChecked(True)
