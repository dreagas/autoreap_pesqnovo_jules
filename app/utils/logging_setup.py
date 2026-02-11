import logging
from PySide6.QtCore import QObject, Signal

class SignalHandler(QObject, logging.Handler):
    """
    Custom logging handler that emits a signal with the log message.
    This allows the UI to update in real-time safely.
    """
    log_signal = Signal(str)

    def __init__(self):
        # Initialize both parent classes
        # QObject must be initialized first or via super() if consistent MRO
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

def setup_logging(log_file="app.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Could not setup file logging: {e}")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Signal Handler (for UI)
    signal_handler = SignalHandler()
    signal_handler.setFormatter(formatter)
    logger.addHandler(signal_handler)

    return signal_handler
