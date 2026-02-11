import sys
import os
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.core.controller import MainController
from app.utils.logging_setup import setup_logging

def main():
    # Setup Logging
    # This returns the SignalHandler instance which emits signals on log events
    log_handler = setup_logging()

    # Initialize Application
    app = QApplication(sys.argv)
    app.setApplicationName("MigrationApp")

    # Load Styles
    # Assuming main.py is in app/ directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(base_dir, "ui", "styles.qss")

    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {style_path}")

    # Initialize Controller
    controller = MainController()

    # Initialize Main Window
    window = MainWindow(controller)

    # Connect Logging Handler to UI
    # We connect directly so any logger.info() updates the UI LogWidget
    log_handler.log_signal.connect(window.log_widget.append_log)

    # Also connect controller explicit log messages if any
    controller.log_message.connect(window.log_widget.append_log)

    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
