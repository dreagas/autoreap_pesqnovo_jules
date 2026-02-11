import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def load_stylesheet(app):
    try:
        # Resolve path relative to this file
        base_path = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(base_path, "ui", "theme.qss")
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Error loading stylesheet: {e}")

def main():
    app = QApplication(sys.argv)

    # Set app info if needed
    app.setApplicationName("Automação REAP")

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()