import sys
from PySide6.QtWidgets import QDialog, QMessageBox

def get_system_theme():
    """
    Detects if the system is using Dark Mode or Light Mode.
    Returns 'Dark' or 'Light'.
    Defaults to 'Dark' if detection fails or on non-Windows systems (to match app theme).
    """
    try:
        if sys.platform == "win32":
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "Light" if value == 1 else "Dark"
    except Exception:
        pass

    # Fallback default
    return "Dark"

def apply_dialog_theme(dialog):
    """
    Applies a theme to a QDialog or QMessageBox based on the system theme.
    This ensures popups are adapted to the Windows theme (Light or Dark).
    """
    theme = get_system_theme()

    if theme == "Dark":
        # Windows Dark Theme approximation
        style = """
            QDialog, QMessageBox {
                background-color: #202020;
                color: #ffffff;
                font-family: "Segoe UI", "Roboto", sans-serif;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QCheckBox {
                color: #ffffff;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """
    else:
        # Windows Light Theme approximation
        style = """
            QDialog, QMessageBox {
                background-color: #f0f0f0;
                color: #000000;
                font-family: "Segoe UI", "Roboto", sans-serif;
            }
            QLabel {
                color: #000000;
            }
            QPushButton {
                background-color: #e1e1e1;
                color: #000000;
                border: 1px solid #adadad;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QCheckBox {
                color: #000000;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d9d9d9;
            }
        """

    dialog.setStyleSheet(style)
