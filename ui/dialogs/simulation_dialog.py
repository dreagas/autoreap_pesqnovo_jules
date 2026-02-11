import logging
import threading
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from core.automation import AutomationLogic

class SimulationDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulação Interativa de Valores")
        self.resize(500, 700)
        self.cfg = config_manager

        layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0,0,0,0)

        title = QLabel("Simulação de Produção")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        h_layout.addWidget(title)

        catalogo = self.cfg.data.get('catalogo_especies', [])
        sps = [e['nome'] for e in catalogo]
        if sps:
            lbl_sps = QLabel(f"Espécies Disponíveis: {', '.join(sps[:3])}...")
            lbl_sps.setStyleSheet("color: gray; font-size: 10px;")
            h_layout.addWidget(lbl_sps)

        btn_reroll = QPushButton("RESORTEAR SIMULAÇÃO")
        btn_reroll.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
        btn_reroll.clicked.connect(self.run_simulation)
        h_layout.addWidget(btn_reroll)
        layout.addWidget(header)

        self.total_lbl = QLabel("Total Anual: R$ 0,00")
        self.total_lbl.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.total_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(10)
        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

        self.run_simulation()

    def run_simulation(self):
        # Clear previous
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Instantiate Logic with dummy logger
        logger = logging.getLogger("REAP_SIMULATION")
        # Ensure it doesn't print to console if not wanted, but defaults are fine
        stop_event = threading.Event()

        logic = AutomationLogic(logger, stop_event, self.cfg)

        meses_prod = self.cfg.data.get("meses_producao", [])
        total_ano = 0.0

        for mes in meses_prod:
            dados = logic.gerar_dados_mes(mes)
            total_mes = 0.0
            detalhes_str = ""
            for item in dados:
                nome = item[0]
                peso = float(item[2])
                preco_str = item[3].replace(',', '.')
                preco = float(preco_str)
                subtotal = peso * preco
                total_mes += subtotal
                detalhes_str += f"• {nome}: {peso}kg x R${preco:.2f} = R${subtotal:.2f}\n"

            total_ano += total_mes

            # Create Card
            card = QFrame()
            card.setObjectName("Card")
            # Using global theme for style
            card_layout = QVBoxLayout(card)

            # Header line
            top_line = QWidget()
            # Make it clickable
            top_line.setCursor(Qt.PointingHandCursor)
            tl_layout = QHBoxLayout(top_line)
            tl_layout.setContentsMargins(5, 5, 5, 5)

            lbl_mes = QLabel(mes.upper())
            lbl_mes.setStyleSheet("font-weight: bold; color: #E2E8F0;")

            lbl_val = QLabel(f"R$ {total_mes:.2f}")
            lbl_val.setStyleSheet("color: #38BDF8; font-weight: bold;")

            expand_lbl = QLabel("▼")
            expand_lbl.setStyleSheet("color: gray;")

            tl_layout.addWidget(lbl_mes)
            tl_layout.addStretch()
            tl_layout.addWidget(lbl_val)
            tl_layout.addWidget(expand_lbl)

            card_layout.addWidget(top_line)

            # Details
            details = QLabel(detalhes_str)
            details.setStyleSheet("color: #94A3B8; font-family: Consolas; padding: 5px;")
            details.setVisible(False)
            card_layout.addWidget(details)

            # Toggle Logic
            def make_toggle(w_details, w_icon):
                def toggle(event):
                    visible = w_details.isVisible()
                    w_details.setVisible(not visible)
                    w_icon.setText("▲" if not visible else "▼")
                return toggle

            top_line.mousePressEvent = make_toggle(details, expand_lbl)

            self.results_layout.addWidget(card)

        self.total_lbl.setText(f"Total Anual Simulado: R$ {total_ano:.2f}")
