from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QScrollArea, QFrame, QLineEdit, QTextEdit, QMessageBox,
    QGridLayout, QGroupBox, QCheckBox, QApplication, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QAction

from ui.controllers.app_controller import AppController
from ui.widgets.custom_widgets import NoWheelComboBox, NoWheelSpinBox, NoWheelDoubleSpinBox, ModernMessageBox
from ui.dialogs.month_selector import MonthSelectorDialog
from ui.dialogs.simulation_dialog import SimulationDialog
from core.constants import VERSION, LOG_FILE, IMG_DIR

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

        # Start connection logic automatically
        QTimer.singleShot(500, self.controller.start_browser)

    def connect_signals(self):
        self.controller.log_signal.connect(self.append_log)
        self.controller.status_signal.connect(self.update_status)
        self.controller.browser_connected.connect(self.on_browser_connected)
        self.controller.search_result.connect(self.update_task_list)
        self.controller.search_error.connect(self.on_search_error)
        self.controller.year_finished.connect(self.on_year_finished)
        self.controller.execution_error.connect(self.on_execution_error)
        self.controller.request_login.connect(self.show_login_popup)
        self.controller.show_success_popup.connect(self.show_success_message)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("REAP AUTO")
        title.setStyleSheet("font-family: 'Roboto'; font-size: 32px; font-weight: 900; color: #38BDF8; border: none; background: transparent;")
        layout.addWidget(title)

        ver = QLabel(f"Versão {VERSION}")
        ver.setStyleSheet("color: #64748B; font-size: 13px; border: none; background: transparent; font-weight: bold;")
        layout.addWidget(ver)

        # Status
        self.lbl_status = QLabel("Status: Iniciando...")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #E2E8F0; border: none; margin-bottom: 10px; background: transparent; font-size: 14px;")
        layout.addWidget(self.lbl_status)

        # Buttons Helper
        def create_btn(text, icon_name=None, color_style=None):
            btn = QPushButton(text)
            if icon_name:
                icon_path = os.path.join(IMG_DIR, icon_name)
                if os.path.exists(icon_path):
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(28, 28))
            
            if color_style:
                btn.setStyleSheet(color_style)
                
            return btn

        # Sidebar Buttons
        self.btn_reconnect = create_btn(" CONECTAR CHROME", "img_chrome.png")
        self.btn_reconnect.setObjectName("BoldButton") 
        self.btn_reconnect.clicked.connect(self.controller.start_browser)
        layout.addWidget(self.btn_reconnect)

        self.btn_open_tabs = create_btn(" ABRIR ABAS", "img_abas.png")
        self.btn_open_tabs.clicked.connect(self.controller.open_tabs)
        layout.addWidget(self.btn_open_tabs)

        self.btn_search = create_btn(" ATUALIZAR LISTA", "img_atualizar.png")
        self.btn_search.clicked.connect(lambda: self.controller.run_search(force_new=True))
        self.btn_search.setEnabled(False)
        layout.addWidget(self.btn_search)

        self.btn_logs = create_btn(" VER LOGS COMPLETO", "img_log.png")
        self.btn_logs.clicked.connect(self.open_logs)
        layout.addWidget(self.btn_logs)

        layout.addStretch()

        # PARAR TUDO (Borda Vermelha Forçada)
        self.btn_stop = create_btn(" PARAR TUDO", "img_parar.png")
        self.btn_stop.setObjectName("BoldButton")
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        # Estilo específico com borda vermelha explícita
        self.btn_stop.setStyleSheet("""
            QPushButton#BoldButton { 
                background-color: #EF4444; 
                border: 2px solid #B91C1C; /* Borda Vermelho Escuro */
            } 
            QPushButton#BoldButton:hover { 
                background-color: #DC2626; 
                border-color: #991B1B;
            }
            QPushButton:disabled { 
                background-color: #1E293B; 
                border-color: #334155; 
                color: #475569; 
            }
        """)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        return sidebar

    def setup_main_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "PAINEL DE OPERAÇÃO")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. LISTA DE ANOS
        list_container_frame = QWidget()
        list_layout = QVBoxLayout(list_container_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(5)

        status_header = QHBoxLayout()
        status_header.addWidget(QLabel("LISTA DE ANOS", styleSheet="color: #E2E8F0; font-weight: 900; font-size: 15px; background: transparent;"))
        self.lbl_small_connected = QLabel("● Aguardando")
        self.lbl_small_connected.setStyleSheet("color: #64748B; font-weight: bold; background: transparent;")
        status_header.addStretch()
        status_header.addWidget(self.lbl_small_connected)
        list_layout.addLayout(status_header)

        list_scroll = QScrollArea()
        list_scroll.setWidgetResizable(True)
        list_scroll.setFrameShape(QFrame.NoFrame)
        list_scroll.setFixedHeight(220)
        
        self.dynamic_list_container = QWidget()
        self.dynamic_list_layout = QVBoxLayout(self.dynamic_list_container)
        self.dynamic_list_layout.setContentsMargins(0, 0, 5, 0)
        self.dynamic_list_layout.setSpacing(10)
        self.dynamic_list_layout.setAlignment(Qt.AlignTop)
        
        list_scroll.setWidget(self.dynamic_list_container)
        list_layout.addWidget(list_scroll)
        
        self.update_list_msg("Aguardando Login...")
        layout.addWidget(list_container_frame)

        # 2. MUNICÍPIO
        frame_mun = QFrame()
        frame_mun.setObjectName("Card")
        mun_layout = QVBoxLayout(frame_mun)
        mun_layout.setContentsMargins(8, 8, 8, 8)

        mun_header = QLabel("MUNICÍPIO DE OPERAÇÃO")
        mun_header.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 14px; background: transparent;")
        mun_layout.addWidget(mun_header)
        
        # Fundo transparente garantido
        lbl_hint = QLabel("(Clique na seta abaixo para alterar)")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px; margin-bottom: 2px; background: transparent;")
        mun_layout.addWidget(lbl_hint)

        self.combo_mun = NoWheelComboBox()
        self.combo_mun.addItems(["Nova Olinda do Maranhão", "Presidente Sarney", "Outros"])
        self.combo_mun.currentTextChanged.connect(self.on_municipio_change)

        current_mun = self.controller.config_manager.data.get("municipio_padrao")
        self.combo_mun.setCurrentText(current_mun)

        mun_layout.addWidget(self.combo_mun)

        self.entry_mun_manual = QLineEdit()
        self.entry_mun_manual.setPlaceholderText("Digite o nome do município...")
        self.entry_mun_manual.setVisible(current_mun == "Outros")
        self.entry_mun_manual.setText(self.controller.config_manager.data.get("municipio_manual", ""))
        mun_layout.addWidget(self.entry_mun_manual)

        btn_save_mun = QPushButton(" SALVAR PREFERÊNCIA")
        btn_save_mun.setObjectName("BoldButton")
        icon_path = os.path.join(IMG_DIR, "img_salvar.png")
        if os.path.exists(icon_path):
            btn_save_mun.setIcon(QIcon(icon_path))
            btn_save_mun.setIconSize(QSize(20, 20))
        
        btn_save_mun.clicked.connect(self.save_municipio_pref)
        btn_save_mun.setStyleSheet("min-height: 35px; font-size: 12px;") 
        mun_layout.addWidget(btn_save_mun)

        layout.addWidget(frame_mun)

        # 3. AÇÕES
        frame_actions = QFrame()
        frame_actions.setObjectName("Card")
        act_layout = QVBoxLayout(frame_actions)
        act_layout.setContentsMargins(8, 8, 8, 8)
        
        act_header = QLabel("CONTROLE DE PREENCHIMENTO")
        act_header.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 14px; background: transparent;")
        act_layout.addWidget(act_header)

        btn_layout = QHBoxLayout()
        
        btn_months = QPushButton("SELECIONAR MESES")
        btn_months.setObjectName("BoldButton")
        btn_months.clicked.connect(self.open_month_selector)
        btn_months.setStyleSheet("min-height: 35px; font-size: 12px;")
        
        btn_sim = QPushButton("SIMULAR VALORES")
        btn_sim.setObjectName("BoldButton")
        btn_sim.clicked.connect(self.open_simulation)
        btn_sim.setStyleSheet("min-height: 35px; font-size: 12px;")

        btn_layout.addWidget(btn_months)
        btn_layout.addWidget(btn_sim)
        act_layout.addLayout(btn_layout)

        act_layout.addWidget(QLabel("Meta: R$ 990-1100 (Nov: R$ 1000)", styleSheet="color: #94A3B8; font-size: 11px; margin-top: 2px; background: transparent;"))

        layout.addWidget(frame_actions)

        # 4. LOG
        self.mini_log = QTextEdit()
        self.mini_log.setObjectName("LogBox")
        self.mini_log.setReadOnly(True)
        self.mini_log.setFixedHeight(70) 
        layout.addWidget(self.mini_log)

    def setup_config_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "CONFIGURAÇÕES")
        main_tab_layout = QVBoxLayout(tab)
        main_tab_layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.cfg_layout = QVBoxLayout(content)
        self.cfg_layout.setContentsMargins(0, 0, 0, 0)
        self.cfg_layout.setSpacing(25)

        self.config_widgets = {}
        self.checkbox_groups = {}
        self.species_rows = []

        def create_section_container(title):
            frame = QFrame()
            frame.setObjectName("ConfigSection")
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(25, 25, 25, 25)
            f_layout.setSpacing(15)
            header_lbl = QLabel(title)
            header_lbl.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 16px; background: transparent;")
            f_layout.addWidget(header_lbl)
            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            divider.setStyleSheet("background-color: #334155; max-height: 1px;")
            f_layout.addWidget(divider)
            grid = QGridLayout()
            grid.setSpacing(15)
            grid.setColumnStretch(1, 1)
            f_layout.addLayout(grid)
            return frame, f_layout, grid

        def add_field(grid_layout, row_idx, label, key, kind="entry", options=None):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #E2E8F0; background: transparent;")
            grid_layout.addWidget(lbl, row_idx, 0)
            val_init = self.controller.config_manager.data.get(key, "")
            widget = None
            if kind == "entry":
                widget = QLineEdit(str(val_init))
            elif kind == "option":
                widget = NoWheelComboBox()
                widget.addItems(options or [])
                widget.setCurrentText(str(val_init))
            grid_layout.addWidget(widget, row_idx, 1)
            self.config_widgets[key] = widget
            return row_idx + 1

        def add_checkbox_group(parent_layout, label, key, options):
            group = QGroupBox(label)
            g_layout = QGridLayout(group)
            g_layout.setSpacing(15)
            current_values = self.controller.config_manager.data.get(key, [])
            vars_list = []
            for i, opt in enumerate(options):
                chk = QCheckBox(opt)
                if opt in current_values:
                    chk.setChecked(True)
                g_layout.addWidget(chk, i // 2, i % 2)
                vars_list.append((opt, chk))
            self.checkbox_groups[key] = vars_list
            parent_layout.addWidget(group)

        # Config Sections
        s1_frame, s1_layout, s1_grid = create_section_container("DADOS PESSOAIS / BÁSICOS")
        r = 0
        estados_br = ["ACRE", "ALAGOAS", "AMAPA", "AMAZONAS", "BAHIA", "CEARA", "DISTRITO FEDERAL", "ESPIRITO SANTO", "GOIAS", "MARANHAO", "MATO GROSSO", "MATO GROSSO DO SUL", "MINAS GERAIS", "PARA", "PARAIBA", "PARANA", "PERNAMBUCO", "PIAUI", "RIO DE JANEIRO", "RIO GRANDE DO NORTE", "RIO GRANDE DO SUL", "RONDONIA", "RORAIMA", "SANTA CATARINA", "SAO PAULO", "SERGIPE", "TOCANTINS"]
        r = add_field(s1_grid, r, "UF Residência:", "uf_residencia", "option", estados_br)
        r = add_field(s1_grid, r, "Categoria:", "categoria", "option", ["Artesanal", "Industrial"])
        r = add_field(s1_grid, r, "Forma Atuação:", "forma_atuacao", "option", ["Desembarcado", "Embarcado"])
        self.cfg_layout.addWidget(s1_frame)

        s2_frame, s2_layout, s2_grid = create_section_container("ATIVIDADE - DETALHES")
        r = 0
        r = add_field(s2_grid, r, "Relação Trabalho:", "relacao_trabalho", "option", ["Individual/Autônomo", "Economia Familiar", "Regime de Parceria", "Carteira de Trabalho", "Contrato de Trabalho"])
        r = add_field(s2_grid, r, "Est. Comercialização:", "estado_comercializacao", "option", estados_br)
        add_checkbox_group(s2_layout, "Grupos Alvo:", "grupos_alvo", ["Algas", "Moluscos", "Mariscos", "Peixes", "Quelônios (Tartarugas de água doce)", "Répteis (jacarés e outros)", "Crustáceos (camarão, lagosta, caranguejo, entre outros)"])
        add_checkbox_group(s2_layout, "Compradores:", "compradores", ["Associação", "Colônia", "Comércio de pescados (feira, mercado)", "Cooperativa", "Intermediário/atrevessador", "Venda direta ao consumidor", "Supermercado", "Outros"])
        self.cfg_layout.addWidget(s2_frame)

        s3_frame, s3_layout, s3_grid = create_section_container("LOCAL E MÉTODOS DE PESCA")
        r = 0
        r = add_field(s3_grid, r, "Tipo Local:", "local_pesca_tipo", "option", ["Açude", "Estuário", "Mar", "Lago", "Lagoa", "Rio", "Represa", "Reservatório", "Laguna"])
        r = add_field(s3_grid, r, "Nome do Local:", "nome_local_pesca", "entry")
        r = add_field(s3_grid, r, "UF Pesca:", "uf_pesca", "option", estados_br)
        add_checkbox_group(s3_layout, "Métodos / Apetrechos:", "metodos_pesca", ["Arrasto", "Cerco", "Covos", "Emalhe", "Espinhel", "Linha de Mão", "Linha e Anzol", "Mariscagem", "Matapi", "Pesca Subaquática", "Tarrafa", "Vara", "Outro"])
        self.cfg_layout.addWidget(s3_frame)

        s4_frame, s4_layout, s4_grid = create_section_container("PRODUÇÃO E VALORES")
        r = 0
        r = add_field(s4_grid, r, "Meta Fin. Mín (R$):", "meta_financeira_min", "entry")
        r = add_field(s4_grid, r, "Meta Fin. Máx (R$):", "meta_financeira_max", "entry")
        r = add_field(s4_grid, r, "Variação Peso (%):", "variacao_peso_pct", "entry")
        r = add_field(s4_grid, r, "Dias Trab. Mín:", "dias_min", "entry")
        r = add_field(s4_grid, r, "Dias Trab. Máx:", "dias_max", "entry")
        self.cfg_layout.addWidget(s4_frame)

        s5_frame, s5_layout, _ = create_section_container("CATÁLOGO DE ESPÉCIES")
        
        # --- CABEÇALHO PARA O CATÁLOGO (CORREÇÃO SOLICITADA) ---
        header_row = QWidget()
        h_layout = QHBoxLayout(header_row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        # Background transparente para labels
        lbl_style = "color: #94A3B8; font-size: 12px; font-weight: bold; background: transparent;"
        h_layout.addWidget(QLabel("Nome da Espécie", styleSheet=lbl_style), stretch=3)
        h_layout.addWidget(QLabel("Preço (R$)", styleSheet=lbl_style), stretch=1)
        h_layout.addWidget(QLabel("Kg Base", styleSheet=lbl_style), stretch=1)
        h_layout.addSpacing(40) 
        s5_layout.addWidget(header_row)
        
        self.species_container = QWidget()
        self.species_layout = QVBoxLayout(self.species_container)
        self.species_layout.setContentsMargins(0,0,0,0)
        s5_layout.addWidget(self.species_container)
        self.reload_species_widgets()

        btn_add_sp = QPushButton(" ADICIONAR NOVA ESPÉCIE")
        btn_add_sp.setObjectName("BoldButton") 
        icon_path = os.path.join(IMG_DIR, "img_adicionar.png")
        if os.path.exists(icon_path):
            btn_add_sp.setIcon(QIcon(icon_path))
            btn_add_sp.setIconSize(QSize(20, 20))
        btn_add_sp.clicked.connect(self.add_species_row_interactive)
        s5_layout.addWidget(btn_add_sp)
        self.cfg_layout.addWidget(s5_frame)

        self.cfg_layout.addSpacing(20)

        btn_save_all = QPushButton(" SALVAR TODAS AS CONFIGURAÇÕES")
        btn_save_all.setObjectName("BoldButton") 
        icon_path = os.path.join(IMG_DIR, "img_salvar.png")
        if os.path.exists(icon_path):
            btn_save_all.setIcon(QIcon(icon_path))
            btn_save_all.setIconSize(QSize(24, 24))
        btn_save_all.clicked.connect(self.save_full_config)
        self.cfg_layout.addWidget(btn_save_all)

        btn_reset = QPushButton(" RESTAURAR PADRÕES ORIGINAIS")
        btn_reset.setObjectName("BoldButton") 
        icon_path = os.path.join(IMG_DIR, "img_restaurar.png")
        if os.path.exists(icon_path):
            btn_reset.setIcon(QIcon(icon_path))
            btn_reset.setIconSize(QSize(24, 24))
        btn_reset.clicked.connect(self.reset_config)
        self.cfg_layout.addWidget(btn_reset)

        scroll.setWidget(content)
        main_tab_layout.addWidget(scroll)

    def reload_species_widgets(self):
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
        btn_del = QPushButton()
        icon_path = os.path.join(IMG_DIR, "img_remover.png")
        if os.path.exists(icon_path):
            btn_del.setIcon(QIcon(icon_path))
            btn_del.setIconSize(QSize(20, 20))
        else:
            btn_del.setText("X")
        btn_del.setStyleSheet("""
            QPushButton { background-color: #EF4444; width: 40px; padding: 0px; min-height: 40px; border-radius: 6px; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        btn_del.setFixedWidth(40)
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

    # SLOT PARA AVISO DE PARADA
    def on_stop_clicked(self):
        self.controller.stop_automation()
        ModernMessageBox(
            "PARADO", 
            "Automação interrompida com sucesso.\n\nPara continuar, utilize a opção 'CONECTAR CHROME'.", 
            "WARNING", 
            self
        ).exec()

    def save_municipio_pref(self):
        val = self.combo_mun.currentText()
        manual = self.entry_mun_manual.text()
        self.controller.config_manager.data["municipio_padrao"] = val
        self.controller.config_manager.data["municipio_manual"] = manual
        self.controller.config_manager.save()
        ModernMessageBox("SUCESSO", "Preferência de município salva!", "SUCCESS", self).exec()

    def save_full_config(self):
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QLineEdit):
                val = widget.text()
                if key in ["dias_min", "dias_max", "meta_financeira_min", "meta_financeira_max", "variacao_peso_pct"]:
                    try: val = float(val) if '.' in val else int(val)
                    except: pass
                self.controller.config_manager.data[key] = val
            elif isinstance(widget, NoWheelComboBox):
                self.controller.config_manager.data[key] = widget.currentText()
        for key, var_list in self.checkbox_groups.items():
            selected = [opt for opt, chk in var_list if chk.isChecked()]
            self.controller.config_manager.data[key] = selected
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
        ModernMessageBox("SUCESSO", "Todas as configurações foram salvas!", "SUCCESS", self).exec()

    def reset_config(self):
        dlg = ModernMessageBox("CONFIRMAÇÃO", "Tem certeza? Isso apagará todas as personalizações e restaurará os valores padrão.", "WARNING", self)
        dlg.btn_ok.setText("SIM, RESTAURAR")
        if dlg.exec():
            self.controller.config_manager.reset_to_defaults()
            self.refresh_config_tab()

    def refresh_config_tab(self):
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
        try:
            os.startfile(LOG_FILE)
        except Exception as e:
            ModernMessageBox("ERRO", f"Não foi possível abrir o log:\n{e}", "ERROR", self).exec()

    @Slot(str, str)
    def append_log(self, msg, tag):
        color = "#94A3B8"
        if tag == "WARNING": color = "#FACC15"
        elif tag == "ERROR": color = "#EF4444"
        elif tag == "SUCCESS": color = "#10B981"
        elif tag == "DESTAK": color = "#38BDF8"
        html = f"<span style='color:{color}'>{msg}</span>"
        self.mini_log.append(html)

    @Slot(str, str)
    def update_status(self, msg, color_code):
        if msg.startswith("●"):
            self.lbl_small_connected.setText(msg)
            self.lbl_small_connected.setStyleSheet(f"color: {color_code}; font-weight: bold; background: transparent;")
            self.update_list_msg(msg, color_code)
        else:
            self.lbl_status.setText(f"Status: {msg}")
            if color_code == "white": self.lbl_status.setStyleSheet("color: white; font-weight: bold; background: transparent;")
            else: self.lbl_status.setStyleSheet(f"color: {color_code}; font-weight: bold; background: transparent;")

    @Slot()
    def on_browser_connected(self):
        self.btn_search.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.controller.run_search()

    @Slot(str)
    def on_search_error(self, msg):
        self.lbl_small_connected.setText("● Erro")
        self.lbl_small_connected.setStyleSheet("color: #EF4444; font-weight: bold; background: transparent;")
        self.update_list_msg("Erro na varredura.", "#EF4444")
        ModernMessageBox("ERRO DE VARREDURA", msg, "ERROR", self).exec()

    @Slot(str)
    def on_execution_error(self, msg):
        if msg == "INTERRUPTED":
             dlg = ModernMessageBox("PARADO", "Automação Parada com Sucesso!\nDeseja voltar a página inicial?", "WARNING", self)
             dlg.btn_ok.setText("VOLTAR INÍCIO")
             if dlg.exec():
                 self.controller.force_return_home()
        else:
             dlg = ModernMessageBox("ERRO CRÍTICO", f"{msg}\n\nDeseja tentar voltar ao início?", "ERROR", self)
             dlg.btn_ok.setText("SIM, VOLTAR")
             if dlg.exec():
                 self.controller.force_return_home()
                 
    @Slot()
    def show_login_popup(self):
        dlg = ModernMessageBox("LOGIN NECESSÁRIO", "O Chrome foi aberto.\n\nPor favor, faça o LOGIN no Gov.br.\n\nQuando estiver logado, clique abaixo.", "INFO", self)
        dlg.btn_ok.setText("JÁ ESTOU LOGADO")
        dlg.exec()
        self.controller.confirm_login()

    @Slot(str, str)
    def show_success_message(self, title, msg):
        ModernMessageBox(title, msg, "SUCCESS", self).exec()

    @Slot(str)
    def on_year_finished(self, year):
        pass

    @Slot(list)
    def update_task_list(self, results):
        while self.dynamic_list_layout.count():
            child = self.dynamic_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                pass 
        if not results:
            self.update_list_msg("Nenhuma pendência encontrada.")
            return
        self.dynamic_list_layout.setAlignment(Qt.AlignTop)
        for item in results:
            idx = item['index']
            year = item['year']
            sent = item['sent']
            btn = QPushButton()
            btn.setFixedHeight(55) 
            btn.setCursor(Qt.PointingHandCursor)
            if not sent:
                icon_path = os.path.join(IMG_DIR, "img_forms.png")
                if os.path.exists(icon_path):
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(28, 28))
            if sent:
                btn.setText(f"{year} (JÁ ENVIADO)")
                btn.setEnabled(False)
                btn.setStyleSheet("background-color: #1E293B; color: #64748B; border: 1px solid #334155;")
            else:
                btn.setText(f"  PROCESSAR {year}")
                btn.setStyleSheet("""
                    QPushButton { background-color: #0284C7; font-size: 15px; text-align: left; padding-left: 20px; font-weight: 900; }
                    QPushButton:hover { background-color: #0369A1; }
                """)
                btn.clicked.connect(lambda checked=False, i=idx, y=year: self.controller.run_year(i, y))
            self.dynamic_list_layout.addWidget(btn)
        self.dynamic_list_layout.addStretch()

    def update_list_msg(self, msg, color="#94A3B8"):
        while self.dynamic_list_layout.count():
            child = self.dynamic_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                pass
        self.dynamic_list_layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; background: transparent;")
        self.dynamic_list_layout.addWidget(lbl)