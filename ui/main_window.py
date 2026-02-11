from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QScrollArea, QFrame, QLineEdit, QTextEdit, QMessageBox,
    QGridLayout, QGroupBox, QCheckBox, QApplication
)
from PySide6.QtCore import Qt, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QAction

from ui.controllers.app_controller import AppController
from ui.widgets.custom_widgets import NoWheelComboBox, NoWheelSpinBox, NoWheelDoubleSpinBox
from ui.dialogs.month_selector import MonthSelectorDialog
from ui.dialogs.simulation_dialog import SimulationDialog
from core.constants import VERSION, LOG_FILE

import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Automação REAP v{VERSION}")
        self.resize(1100, 750)

        # Controller
        self.controller = AppController()
        self.connect_signals()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Tabs
        self.tabs = QTabWidget()
        self.setup_main_tab()
        self.setup_config_tab()

        main_layout.addWidget(self.tabs)

        # Start connection logic automatically after show?
        QTimer.singleShot(500, self.controller.start_browser)

    def connect_signals(self):
        self.controller.log_signal.connect(self.append_log)
        self.controller.status_signal.connect(self.update_status)
        self.controller.browser_connected.connect(self.on_browser_connected)
        self.controller.search_result.connect(self.update_task_list)
        self.controller.search_error.connect(self.on_search_error)
        self.controller.year_finished.connect(self.on_year_finished)
        self.controller.execution_error.connect(self.on_execution_error)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #1E293B; border-right: 1px solid #335c81;")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("REAP AUTO")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #60A5FA; border: none;")
        layout.addWidget(title)

        ver = QLabel(f"{VERSION}")
        ver.setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
        layout.addWidget(ver)

        # Status
        self.lbl_status = QLabel("Status: Iniciando...")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #38BDF8; border: none;")
        layout.addWidget(self.lbl_status)

        # Buttons
        self.btn_reconnect = QPushButton("RECONECTAR CHROME")
        self.btn_reconnect.clicked.connect(self.controller.start_browser)
        layout.addWidget(self.btn_reconnect)

        self.btn_open_tabs = QPushButton("ABRIR ABAS DE TRABALHO")
        self.btn_open_tabs.clicked.connect(self.controller.open_tabs)
        layout.addWidget(self.btn_open_tabs)

        self.btn_search = QPushButton("ATUALIZAR LISTA")
        self.btn_search.clicked.connect(lambda: self.controller.run_search(force_new=True))
        self.btn_search.setEnabled(False)
        self.btn_search.setStyleSheet("QPushButton { background-color: #0891B2; } QPushButton:disabled { background-color: #334155; }")
        layout.addWidget(self.btn_search)

        self.btn_logs = QPushButton("VER LOGS")
        self.btn_logs.clicked.connect(self.open_logs)
        layout.addWidget(self.btn_logs)

        layout.addStretch()

        self.btn_stop = QPushButton("PARAR TUDO")
        self.btn_stop.clicked.connect(self.controller.stop_automation)
        self.btn_stop.setStyleSheet("background-color: #EF4444;")
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        return sidebar

    def setup_main_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Painel Principal")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Municipality Frame
        frame_mun = QFrame()
        frame_mun.setObjectName("Card")
        mun_layout = QVBoxLayout(frame_mun)

        mun_layout.addWidget(QLabel("MUNICÍPIO DE OPERAÇÃO", styleSheet="color: #2563EB; font-weight: bold;"))

        self.combo_mun = NoWheelComboBox()
        self.combo_mun.addItems(["Nova Olinda do Maranhão", "Presidente Sarney", "Outros"])
        self.combo_mun.currentTextChanged.connect(self.on_municipio_change)

        # Load initial value
        current_mun = self.controller.config_manager.data.get("municipio_padrao")
        self.combo_mun.setCurrentText(current_mun)

        mun_layout.addWidget(self.combo_mun)

        self.entry_mun_manual = QLineEdit()
        self.entry_mun_manual.setPlaceholderText("Digite o nome do município...")
        self.entry_mun_manual.setVisible(current_mun == "Outros")
        self.entry_mun_manual.setText(self.controller.config_manager.data.get("municipio_manual", ""))
        mun_layout.addWidget(self.entry_mun_manual)

        btn_save_mun = QPushButton("Salvar Preferência")
        btn_save_mun.clicked.connect(self.save_municipio_pref)
        mun_layout.addWidget(btn_save_mun)

        layout.addWidget(frame_mun)

        # Actions Frame
        frame_actions = QFrame()
        frame_actions.setObjectName("Card")
        act_layout = QVBoxLayout(frame_actions)
        act_layout.addWidget(QLabel("CONTROLE DE PREENCHIMENTO", styleSheet="color: #2563EB; font-weight: bold;"))

        btn_layout = QHBoxLayout()
        btn_months = QPushButton("SELECIONAR MESES")
        btn_months.clicked.connect(self.open_month_selector)
        btn_sim = QPushButton("SIMULAR VALORES")
        btn_sim.clicked.connect(self.open_simulation)

        btn_layout.addWidget(btn_months)
        btn_layout.addWidget(btn_sim)
        act_layout.addLayout(btn_layout)

        act_layout.addWidget(QLabel("Valor alvo: R$ 990 a R$ 1100 (Novembro fixo em R$ 1000)", styleSheet="color: gray; font-size: 10px;"))

        layout.addWidget(frame_actions)

        # Status Header
        status_header = QHBoxLayout()
        status_header.addWidget(QLabel("PAINEL DE VARREDURA", styleSheet="color: gray; font-weight: bold;"))
        self.lbl_small_connected = QLabel("● Aguardando")
        self.lbl_small_connected.setStyleSheet("color: gray; font-weight: bold;")
        status_header.addStretch()
        status_header.addWidget(self.lbl_small_connected)
        layout.addLayout(status_header)

        # Dynamic List (Scroll Area)
        list_scroll = QScrollArea()
        list_scroll.setWidgetResizable(True)
        list_scroll.setStyleSheet("QScrollArea { border: 1px solid #335c81; border-radius: 6px; background-color: #1E293B; }")

        self.dynamic_list_container = QWidget()
        self.dynamic_list_container.setStyleSheet("background-color: #1E293B;")
        self.dynamic_list_layout = QVBoxLayout(self.dynamic_list_container)
        list_scroll.setWidget(self.dynamic_list_container)

        self.update_list_msg("Aguardando Login...")

        layout.addWidget(list_scroll)

        # Mini Log Box
        self.mini_log = QTextEdit()
        self.mini_log.setReadOnly(True)
        self.mini_log.setFixedHeight(80)
        self.mini_log.setStyleSheet("font-family: Consolas; font-size: 10px; background-color: black; color: #A1A1AA;")
        layout.addWidget(self.mini_log)

    def setup_config_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Configurações")
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.cfg_layout = QVBoxLayout(content)

        self.config_widgets = {}
        self.checkbox_groups = {}
        self.species_rows = []

        # Helper functions
        def add_header(text):
            self.cfg_layout.addWidget(QLabel(text, styleSheet="color: #2563EB; font-weight: bold; margin-top: 10px; font-size: 16px;"))

        def add_field(label, key, kind="entry", options=None):
            row = QWidget()
            h_layout = QHBoxLayout(row)
            h_layout.setContentsMargins(0,0,0,0)
            h_layout.addWidget(QLabel(label, styleSheet="font-weight: bold; width: 150px;"))

            val_init = self.controller.config_manager.data.get(key, "")
            widget = None

            if kind == "entry":
                widget = QLineEdit(str(val_init))
            elif kind == "option":
                widget = NoWheelComboBox()
                widget.addItems(options or [])
                widget.setCurrentText(str(val_init))

            h_layout.addWidget(widget)
            self.config_widgets[key] = widget
            self.cfg_layout.addWidget(row)

        def add_checkbox_group(label, key, options):
            group = QGroupBox(label)
            g_layout = QGridLayout(group)

            current_values = self.controller.config_manager.data.get(key, [])
            vars_list = []

            for i, opt in enumerate(options):
                chk = QCheckBox(opt)
                if opt in current_values:
                    chk.setChecked(True)
                g_layout.addWidget(chk, i // 2, i % 2)
                vars_list.append((opt, chk))

            self.checkbox_groups[key] = vars_list
            self.cfg_layout.addWidget(group)

        # Build Config UI
        add_header("DADOS PESSOAIS / BÁSICOS")
        add_field("UF Residência:", "uf_residencia", "option", ["MARANHAO", "PARA", "PIAUI"])
        add_field("Categoria:", "categoria", "option", ["Artesanal", "Industrial"])
        add_field("Forma Atuação:", "forma_atuacao", "option", ["Desembarcado", "Embarcado"])

        add_header("ATIVIDADE - DETALHES")
        add_field("Relação Trabalho:", "relacao_trabalho", "option", ["Individual/Autônomo", "Economia Familiar", "Regime de Parceria", "Carteira de Trabalho", "Contrato de Trabalho"])
        add_field("Est. Comercialização:", "estado_comercializacao", "option", ["MARANHAO", "PARA"])
        add_checkbox_group("Grupos Alvo:", "grupos_alvo", ["Algas", "Moluscos", "Mariscos", "Peixes", "Quelônios (Tartarugas de água doce)", "Répteis (jacarés e outros)", "Crustáceos (camarão, lagosta, caranguejo, entre outros)"])
        add_checkbox_group("Compradores:", "compradores", ["Associação", "Colônia", "Comércio de pescados (feira, mercado)", "Cooperativa", "Intermediário/atrevessador", "Venda direta ao consumidor", "Supermercado", "Outros"])

        add_header("LOCAL E MÉTODOS DE PESCA")
        add_field("Tipo Local:", "local_pesca_tipo", "option", ["Açude", "Estuário", "Mar", "Lago", "Lagoa", "Rio", "Represa", "Reservatório", "Laguna"])
        add_field("Nome do Local:", "nome_local_pesca", "entry")
        add_field("UF Pesca:", "uf_pesca", "option", ["MARANHAO", "PARA"])
        add_checkbox_group("Métodos / Apetrechos:", "metodos_pesca", ["Arrasto", "Cerco", "Covos", "Emalhe", "Espinhel", "Linha de Mão", "Linha e Anzol", "Mariscagem", "Matapi", "Pesca Subaquática", "Tarrafa", "Vara", "Outro"])

        add_header("PRODUÇÃO E VALORES")
        add_field("Meta Fin. Mín (R$):", "meta_financeira_min", "entry")
        add_field("Meta Fin. Máx (R$):", "meta_financeira_max", "entry")
        add_field("Variação Peso (%):", "variacao_peso_pct", "entry")
        add_field("Dias Trab. Mín:", "dias_min", "entry")
        add_field("Dias Trab. Máx:", "dias_max", "entry")

        add_header("CATÁLOGO DE ESPÉCIES")

        self.species_container = QWidget()
        self.species_layout = QVBoxLayout(self.species_container)
        self.cfg_layout.addWidget(self.species_container)

        self.reload_species_widgets()

        btn_add_sp = QPushButton("+ ADICIONAR NOVA ESPÉCIE")
        btn_add_sp.setStyleSheet("background-color: #0D9488;")
        btn_add_sp.clicked.connect(self.add_species_row_interactive)
        self.cfg_layout.addWidget(btn_add_sp)

        self.cfg_layout.addSpacing(20)

        btn_save_all = QPushButton("SALVAR TODAS AS CONFIGURAÇÕES")
        btn_save_all.setStyleSheet("background-color: #0891B2; font-size: 14px; padding: 10px;")
        btn_save_all.clicked.connect(self.save_full_config)
        self.cfg_layout.addWidget(btn_save_all)

        btn_reset = QPushButton("RESTAURAR PADRÕES ORIGINAIS")
        btn_reset.setStyleSheet("background-color: #1E40AF;")
        btn_reset.clicked.connect(self.reset_config)
        self.cfg_layout.addWidget(btn_reset)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def reload_species_widgets(self):
        # Clear
        while self.species_layout.count():
            child = self.species_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.species_rows = []

        catalogo = self.controller.config_manager.data.get("catalogo_especies", [])
        for esp in catalogo:
            self.add_species_row(esp)

    def add_species_row(self, data=None):
        if data is None: data = {"nome": "", "preco": 0.0, "kg_base": 10}

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)

        name = QLineEdit(data["nome"])
        name.setPlaceholderText("Nome da espécie...")
        row_layout.addWidget(name, stretch=3)

        price = QLineEdit(str(data["preco"]))
        price.setPlaceholderText("Preço")
        row_layout.addWidget(price, stretch=1)

        kg = QLineEdit(str(data["kg_base"]))
        kg.setPlaceholderText("Kg Base")
        row_layout.addWidget(kg, stretch=1)

        btn_del = QPushButton("X")
        btn_del.setStyleSheet("background-color: #EF4444; width: 30px;")
        btn_del.setFixedWidth(30)
        btn_del.clicked.connect(lambda: self.remove_species_row(row_widget))
        row_layout.addWidget(btn_del)

        self.species_rows.append({"widget": row_widget, "name": name, "price": price, "kg": kg})
        self.species_layout.addWidget(row_widget)

    def add_species_row_interactive(self):
        self.add_species_row()

    def remove_species_row(self, row_widget):
        row_widget.deleteLater()
        self.species_rows = [r for r in self.species_rows if r["widget"] != row_widget]

    def on_municipio_change(self, text):
        self.entry_mun_manual.setVisible(text == "Outros")

    def save_municipio_pref(self):
        val = self.combo_mun.currentText()
        manual = self.entry_mun_manual.text()
        self.controller.config_manager.data["municipio_padrao"] = val
        self.controller.config_manager.data["municipio_manual"] = manual
        self.controller.config_manager.save()
        QMessageBox.information(self, "Sucesso", "Município salvo.")

    def save_full_config(self):
        # Fields
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QLineEdit):
                val = widget.text()
                # conversion logic
                if key in ["dias_min", "dias_max", "meta_financeira_min", "meta_financeira_max", "variacao_peso_pct"]:
                    try: val = float(val) if '.' in val else int(val)
                    except: pass
                self.controller.config_manager.data[key] = val
            elif isinstance(widget, NoWheelComboBox):
                self.controller.config_manager.data[key] = widget.currentText()

        # Checkboxes
        for key, var_list in self.checkbox_groups.items():
            selected = [opt for opt, chk in var_list if chk.isChecked()]
            self.controller.config_manager.data[key] = selected

        # Species
        new_species = []
        for r in self.species_rows:
            try:
                n = r["name"].text()
                p = float(r["price"].text())
                k = int(r["kg"].text())
                if n:
                    new_species.append({"nome": n, "preco": p, "kg_base": k})
            except: pass
        self.controller.config_manager.data["catalogo_especies"] = new_species

        self.controller.config_manager.save()
        QMessageBox.information(self, "Sucesso", "Configurações salvas!")

    def reset_config(self):
        ret = QMessageBox.question(self, "Restaurar Padrão", "Tem certeza? Isso apagará todas as personalizações.")
        if ret == QMessageBox.StandardButton.Yes:
            self.controller.config_manager.reset_to_defaults()
            self.refresh_config_tab()

    def refresh_config_tab(self):
        # Update widgets with new data
        for key, widget in self.config_widgets.items():
            val = self.controller.config_manager.data.get(key, "")
            if isinstance(widget, QLineEdit):
                widget.setText(str(val))
            elif isinstance(widget, NoWheelComboBox):
                widget.setCurrentText(str(val))

        for key, var_list in self.checkbox_groups.items():
            saved_vals = self.controller.config_manager.data.get(key, [])
            for opt, chk in var_list:
                chk.setChecked(opt in saved_vals)

        self.reload_species_widgets()

        # Also Mun
        mun = self.controller.config_manager.data.get("municipio_padrao")
        self.combo_mun.setCurrentText(mun)
        self.entry_mun_manual.setText(self.controller.config_manager.data.get("municipio_manual", ""))

    def open_month_selector(self):
        dlg = MonthSelectorDialog(self.controller.config_manager, self)
        dlg.exec()

    def open_simulation(self):
        dlg = SimulationDialog(self.controller.config_manager, self)
        dlg.exec()

    def open_logs(self):
        # Open in system editor
        try:
            os.startfile(LOG_FILE)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o log:\n{e}")

    @Slot(str, str)
    def append_log(self, msg, tag):
        # Colorize logic
        color = "#e0e0e0"
        if tag == "WARNING": color = "#FACC15"
        elif tag == "ERROR": color = "#F87171"
        elif tag == "SUCCESS": color = "#38BDF8"
        elif tag == "DESTAK": color = "#818CF8"

        html = f"<span style='color:{color}'>{msg}</span>"
        self.mini_log.append(html)

    @Slot(str, str)
    def update_status(self, msg, color_code):
        # e.g. "Conectado", "#10B981"
        if msg.startswith("●"):
            self.lbl_small_connected.setText(msg)
            self.lbl_small_connected.setStyleSheet(f"color: {color_code}; font-weight: bold;")
            # Also update dynamic list message
            self.update_list_msg(msg, color_code)
        else:
            self.lbl_status.setText(f"Status: {msg}")
            # Map color names to hex if needed, but hex is passed
            if color_code == "white": self.lbl_status.setStyleSheet("color: white; font-weight: bold;")
            else: self.lbl_status.setStyleSheet(f"color: {color_code}; font-weight: bold;")

    @Slot()
    def on_browser_connected(self):
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.controller.run_search()

    @Slot(str)
    def on_search_error(self, msg):
        self.lbl_small_connected.setText("● Erro")
        self.lbl_small_connected.setStyleSheet("color: #EF4444; font-weight: bold;")
        self.update_list_msg("Erro na varredura.", "#EF4444")
        QMessageBox.warning(self, "Erro", msg)

    @Slot(str)
    def on_execution_error(self, msg):
        if msg == "INTERRUPTED":
             ret = QMessageBox.question(self, "Parado", "Automação Parada!\nDeseja voltar para a página inicial?")
             if ret == QMessageBox.StandardButton.Yes:
                 self.controller.force_return_home()
        else:
             ret = QMessageBox.critical(self, "Erro", f"{msg}\n\nTentar voltar ao início?")
             if ret == QMessageBox.StandardButton.Yes:
                 self.controller.force_return_home()

    @Slot(str)
    def on_year_finished(self, year):
        pass

    @Slot(list)
    def update_task_list(self, results):
        # Clear
        while self.dynamic_list_layout.count():
            child = self.dynamic_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not results:
            self.update_list_msg("Nenhuma pendência encontrada.")
            return

        for item in results:
            idx = item['index']
            year = item['year']
            sent = item['sent']

            btn = QPushButton()
            btn.setFixedHeight(40)

            if sent:
                btn.setText(f"{year} (JÁ ENVIADO)")
                btn.setEnabled(False)
                btn.setStyleSheet("background-color: #475569; color: gray; font-weight: bold;")
            else:
                btn.setText(f"PROCESSAR {year}")
                btn.setStyleSheet("background-color: #2563EB; font-weight: bold;")
                btn.clicked.connect(lambda checked=False, i=idx, y=year: self.controller.run_year(i, y))

            self.dynamic_list_layout.addWidget(btn)

    def update_list_msg(self, msg, color="gray"):
        # Clear
        while self.dynamic_list_layout.count():
            child = self.dynamic_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; margin-top: 40px;")
        self.dynamic_list_layout.addWidget(lbl)
