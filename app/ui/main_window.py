from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from app.ui.widgets import StyledButton, LogWidget, StatusIndicator, NoScrollComboBox, NoScrollSpinBox, Card
from app.core.controller import MainController
import logging

class MainWindow(QMainWindow):
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        self.logger = logging.getLogger("MainWindow")

        self.setWindowTitle("Automação Desktop - PySide6")
        self.resize(1100, 750)

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Header
        self.setup_header()

        # 2. Body (Tabs)
        self.setup_tabs()

        # 3. Footer (Logs)
        self.setup_footer()

    def setup_header(self):
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header")
        header_layout = QHBoxLayout(self.header_frame)

        # Title
        title = QLabel("AUTOMAÇÃO DESKTOP")
        title.setObjectName("title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Status
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)

        # Main Actions
        self.btn_start = StyledButton("INICIAR", variant="primary")
        self.btn_stop = StyledButton("PARAR", variant="danger")
        self.btn_stop.setEnabled(False)

        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)

        self.main_layout.addWidget(self.header_frame)

    def setup_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setObjectName("main_tabs")

        # Tab 1: Dashboard
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "Painel Principal")

        # Tab 2: Configurações
        self.tab_config = QWidget()
        self.setup_config_tab()
        self.tabs.addTab(self.tab_config, "Configurações")

        self.main_layout.addWidget(self.tabs)

    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(20, 20, 20, 20)

        # Example Card
        card = Card()
        card_layout = QVBoxLayout(card)

        lbl = QLabel("Bem-vindo ao novo sistema modular.")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #EAF2FF;")
        card_layout.addWidget(lbl)

        lbl_sub = QLabel("Utilize as abas para navegar e configurar o processo.")
        lbl_sub.setStyleSheet("color: #B0BEC5;")
        card_layout.addWidget(lbl_sub)

        layout.addWidget(card)
        layout.addStretch()

    def setup_config_tab(self):
        layout = QVBoxLayout(self.tab_config)
        layout.setContentsMargins(20, 20, 20, 20)

        # Config Form Example
        form_card = Card()
        form_layout = QVBoxLayout(form_card)

        # Combo Example
        lbl_combo = QLabel("Selecione o Modo:")
        self.combo_mode = NoScrollComboBox()
        self.combo_mode.addItems(["Produção", "Homologação", "Dev"])
        form_layout.addWidget(lbl_combo)

        # Spin Example
        lbl_spin = QLabel("Delay (segundos):")
        self.spin_delay = NoScrollSpinBox()
        self.spin_delay.setRange(0, 60)
        self.spin_delay.setValue(5)
        form_layout.addWidget(lbl_spin)

        form_layout.addStretch()

        layout.addWidget(form_card)
        layout.addStretch()

    def setup_footer(self):
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("footer")
        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        lbl_log = QLabel("Logs do Sistema:")
        lbl_log.setStyleSheet("font-weight: bold; color: #B0BEC5; font-size: 12px;")
        footer_layout.addWidget(lbl_log)

        self.log_widget = LogWidget()
        footer_layout.addWidget(self.log_widget)

        self.main_layout.addWidget(self.footer_frame)

    def setup_connections(self):
        # UI Actions
        self.btn_start.clicked.connect(self.controller.start_process)
        self.btn_stop.clicked.connect(self.controller.stop_process)

        # Controller Signals
        self.controller.log_message.connect(self.log_widget.append_log)
        self.controller.update_status.connect(self.update_status_ui)

    @Slot(str, str)
    def update_status_ui(self, status_code, message):
        self.status_indicator.set_status(status_code, message)

        if status_code == "running":
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.tabs.setEnabled(False) # Lock config while running
        else:
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.tabs.setEnabled(True)
