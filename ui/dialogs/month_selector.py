from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QHBoxLayout, QScrollArea, QWidget
from PySide6.QtCore import Qt
from core.constants import TODOS_MESES_ORDENADOS
from ui.widgets.custom_widgets import ModernMessageBox

class MonthSelectorDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Meses")
        self.resize(350, 600)
        self.cfg = config_manager

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecione os meses para preenchimento:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.checks_layout = QVBoxLayout(content)

        self.month_vars = {}
        current_selection = self.cfg.data.get("meses_selecionados", TODOS_MESES_ORDENADOS)

        for mes in TODOS_MESES_ORDENADOS:
            chk = QCheckBox(mes)
            if mes in current_selection:
                chk.setChecked(True)
            self.checks_layout.addWidget(chk)
            self.month_vars[mes] = chk

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_all = QPushButton("Marcar Todos")
        btn_all.clicked.connect(lambda: self.toggle_all(True))
        btn_none = QPushButton("Desmarcar Todos")
        btn_none.clicked.connect(lambda: self.toggle_all(False))
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        layout.addLayout(btn_layout)

        btn_save = QPushButton("SALVAR SELEÇÃO")
        btn_save.setStyleSheet("background-color: #0891B2; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_selection)
        layout.addWidget(btn_save)

    def toggle_all(self, state):
        for chk in self.month_vars.values():
            chk.setChecked(state)

    def save_selection(self):
        new_selection = [m for m in TODOS_MESES_ORDENADOS if self.month_vars[m].isChecked()]
        self.cfg.data["meses_selecionados"] = new_selection
        self.cfg.save()
        ModernMessageBox("SUCESSO", f"{len(new_selection)} meses selecionados para processamento.", "SUCCESS", self).exec()
        self.accept()