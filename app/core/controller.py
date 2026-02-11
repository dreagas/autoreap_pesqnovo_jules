from PySide6.QtCore import QObject, Signal, Slot
from app.config.settings import settings
from app.core.worker import Worker
import logging

class MainController(QObject):
    """
    Acts as the bridge between the UI and the backend services.
    Handles signals, starts workers, and manages application state.
    """
    # Signals to update UI
    log_message = Signal(str)
    update_status = Signal(str, str) # status_code ('ready', 'running', 'error'), message
    progress_update = Signal(int)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("AppController")
        self._is_running = False
        self.worker = None

    @Slot()
    def start_process(self):
        if self._is_running:
            self.logger.warning("Processo já em execução.")
            return

        self._is_running = True
        self.update_status.emit("running", "Executando...")
        self.logger.info("Iniciando processo principal...")

        # Example of starting a worker
        # self.worker = Worker(self.run_automation_task)
        # self.worker.signals.finished.connect(self.on_process_finished)
        # self.worker.signals.error.connect(self.on_process_error)
        # self.worker.start()

        # For now, just a placeholder log since we don't have the task logic yet
        self.logger.info("Automation task placeholder started.")

    @Slot()
    def stop_process(self):
        if not self._is_running:
            return

        self.logger.info("Solicitação de parada recebida.")
        # Logic to stop worker would go here
        self._is_running = False
        self.update_status.emit("ready", "Parado pelo usuário")

    def on_process_finished(self):
        self._is_running = False
        self.update_status.emit("ready", "Concluído com sucesso")
        self.logger.info("Processo finalizado.")

    def on_process_error(self, err_tuple):
        self._is_running = False
        self.update_status.emit("error", "Erro na execução")
        self.logger.error(f"Erro capturado no worker: {err_tuple[1]}")
