from PySide6.QtCore import QObject, Signal, QThread, QTimer
from core.automation import AutomationLogic
from services.config_manager import ConfigManager
from services.logger import setup_logging
from core.constants import LOG_FILE, VERSION, TODOS_MESES_ORDENADOS
import threading
import queue
import time
import re
import ctypes
from selenium.webdriver.common.by import By

class WorkerThread(QThread):
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.target(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Thread error: {e}")

class AppController(QObject):
    log_signal = Signal(str, str) # msg, tag
    status_signal = Signal(str, str) # msg, color
    browser_connected = Signal()
    search_result = Signal(list) # List of dicts: {index, year, status, text}
    search_error = Signal(str)
    year_finished = Signal(str) # year
    execution_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.logger, self.log_queue = setup_logging(LOG_FILE, VERSION)
        self.stop_event = threading.Event()
        self.automation = None

        # Timer to poll log queue
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.process_log_queue)
        self.log_timer.start(100)

        self.current_worker = None

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = self.logger.handlers[0].format(record)
                tag = "INFO"
                if hasattr(record, 'tags'): tag = record.tags
                elif record.levelno == 30: tag = "WARNING"
                elif record.levelno == 40: tag = "ERROR"
                self.log_signal.emit(msg, tag)
        except queue.Empty:
            pass

    def start_browser(self):
        self.stop_event.clear()
        self.status_signal.emit("Conectando Chrome...", "white")

        def boot_task():
            self.logger.info("INICIANDO SISTEMA...", extra={'tags': 'DESTAK'})
            self.automation = AutomationLogic(self.logger, self.stop_event, self.config_manager)
            sucesso = self.automation.garantir_chrome_aberto()
            if not sucesso:
                self.logger.error("Falha crítica ao abrir navegador.")
                self.execution_error.emit("Falha crítica ao abrir navegador.")
                return

            # Keep ctypes for behavioral consistency with original code
            ctypes.windll.user32.MessageBoxW(0, "Chrome aberto.\n\nFAÇA O LOGIN NO GOV.BR.\n\nClique OK quando estiver logado.", "Aguardando Login", 0x40 | 0x1000)

            self.logger.info("Login confirmado. Conectando Selenium...", extra={'tags': 'INFO'})

            driver = self.automation.conectar_selenium()
            if driver:
                self.logger.info("Navegador Conectado.", extra={'tags': 'SUCCESS'})
                self.automation.garantir_acesso_manutencao()
                self.status_signal.emit("Navegador Conectado", "#10B981")
                self.browser_connected.emit()
            else:
                self.logger.error("Falha Selenium.")
                self.execution_error.emit("Falha Selenium.")

        self.current_worker = WorkerThread(boot_task)
        self.current_worker.start()

    def stop_automation(self):
        self.stop_event.set()
        self.logger.error(">>> PARANDO... <<<", extra={'tags': 'ERROR'})

    def open_tabs(self):
        if self.automation:
            def task():
                self.automation.restaurar_abas_trabalho()
            threading.Thread(target=task, daemon=True).start()

    def run_search(self, force_new=False):
        self.stop_event.clear()
        self.status_signal.emit("● Escaneando...", "#FACC15")

        def search_task():
            if not self.automation or not self.automation.driver:
                return

            self.logger.info("Iniciando varredura de pendências...", extra={'tags': 'INFO'})
            try:
                if force_new:
                    self.automation.garantir_acesso_manutencao()

                driver = self.automation.driver
                linhas = []
                max_retries = 10

                for i in range(max_retries):
                    if self.stop_event.is_set(): break
                    try:
                        table = driver.find_elements(By.TAG_NAME, "table")
                        if table:
                            linhas = driver.find_elements(By.XPATH, "//table/tbody/tr")
                            if linhas: break
                    except: pass

                    time.sleep(2)

                if self.stop_event.is_set(): return

                if not linhas:
                    self.logger.warning("Tabela não encontrada após 10 tentativas.")
                    self.status_signal.emit("● Erro", "#EF4444")
                    self.search_error.emit("Tabela não encontrada.")
                    return

                self.status_signal.emit("● Conectado", "#10B981")

                results = []
                for idx, row in enumerate(linhas):
                    txt = row.text
                    # Logic from original code
                    status_text = ""
                    try:
                        status_elem = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
                        status_text = status_elem.text
                    except: pass

                    is_enviado = "Enviado" in txt or "Enviado" in status_text
                    is_pendente = "Pendente" in txt or "Rascunho" in txt

                    if is_pendente or is_enviado:
                        try:
                            ano = "Desconhecido"
                            colunas = row.find_elements(By.TAG_NAME, "td")
                            for col in colunas:
                                if re.match(r'20\d{2}', col.text.strip()):
                                    ano = col.text.strip()
                                    break

                            results.append({
                                'index': idx,
                                'year': ano,
                                'sent': is_enviado
                            })
                        except: pass

                self.search_result.emit(results)
                if results:
                    self.logger.info("Lista Atualizada com Sucesso!", extra={'tags': 'SUCCESS'})
                else:
                    self.logger.info("Nenhuma pendência encontrada.")

            except Exception as e:
                self.logger.error(f"Erro na varredura: {e}")
                self.status_signal.emit("● Erro", "#EF4444")
                self.search_error.emit(str(e))

        self.current_worker = WorkerThread(search_task)
        self.current_worker.start()

    def run_year(self, index, ano):
        self.stop_event.clear()
        meses_selecionados = set(self.config_manager.data.get("meses_selecionados", TODOS_MESES_ORDENADOS))
        self.logger.info(f"Iniciando {ano} | Meses: {len(meses_selecionados)} selecionados", extra={'tags': 'DESTAK'})

        def run_task():
            if self.automation:
                self.automation.trazer_navegador_frente()

            try:
                driver = self.automation.driver
                linhas = driver.find_elements(By.XPATH, "//table/tbody/tr")
                if index >= len(linhas):
                    self.logger.error("Tabela mudou.")
                    return

                row = linhas[index]
                btn = row.find_element(By.XPATH, ".//button[contains(@class, 'br-button') and @aria-label='editar']")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                btn.click()

                self.automation.processar_etapa_1()
                if self.automation.avancar():
                    self.automation.processar_etapa_2()
                    if self.automation.avancar():
                        self.automation.processar_etapa_3(meses_selecionados)
                        if self.automation.avancar():
                            self.automation.processar_etapa_4()

                self.logger.info(f"Fim {ano}.", extra={'tags': 'SUCCESS'})
                self.year_finished.emit(ano)

            except InterruptedError:
                self.logger.warning("Parada Solicitada.")
                # Logic for popup is handled in UI based on signal or here?
                # The original code showed popup in the thread.
                # "show_stop_decision_popup"
                # I should probably emit a signal for the UI to show the popup.
                self.execution_error.emit("INTERRUPTED")

            except Exception as e:
                self.logger.error(f"Erro execução: {e}")
                self.execution_error.emit(str(e))

        self.current_worker = WorkerThread(run_task)
        self.current_worker.start()

    def force_return_home(self):
        if self.automation:
             threading.Thread(target=self.automation.forcar_retorno_inicio, daemon=True).start()
