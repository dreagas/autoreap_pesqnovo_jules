import logging
import queue
import os

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

def setup_logging(log_file, version=""):
    log_queue = queue.Queue()
    logger = logging.getLogger("REAP_GUI")
    logger.setLevel(logging.INFO)

    # Check if handlers already exist to avoid duplication if called multiple times
    # However, since we return a new queue, we might want to attach a new queue handler?
    # Or assuming this is called once at startup.
    # If called once, we are fine.

    # Clear existing handlers to be safe if re-initialized?
    # Better not to mess with global logger if possible, but here it is a specific logger.
    if logger.hasHandlers():
        logger.handlers.clear()

    queue_handler = QueueHandler(log_queue)
    queue_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M')
    queue_handler.setFormatter(queue_formatter)
    logger.addHandler(queue_handler)

    try:
        # Ensure directory exists for log file
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try: os.makedirs(log_dir)
            except: pass

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        if version:
            logger.info("="*50)
            logger.info(f"NOVA SESSÃO INICIADA: {version}")
            logger.info(f"Log gravando em: {log_file}")
            logger.info("="*50)
    except Exception as e:
        print(f"ERRO CRÍTICO AO CRIAR ARQUIVO DE LOG: {e}")

    return logger, log_queue
