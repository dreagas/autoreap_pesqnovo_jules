from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QHBoxLayout, QScrollArea, QWidget, QMessageBox
from PySide6.QtCore import Qt
from core.constants import TODOS_MESES_ORDENADOS
from ui.theme_manager import apply_dialog_theme

class MonthSelectorDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Meses")
        self.resize(300, 450) # Smaller default
        self.cfg = config_manager

        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        lbl = QLabel("Selecione os meses para preenchimento:")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.checks_layout = QVBoxLayout(content)
        self.checks_layout.setContentsMargins(5, 5, 5, 5)

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
        # Cyan #0891B2 works on dark, might be dark on light. I'll rely on theme manager or use a safe color.
        # But for "Save", a primary color is good.
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
        QMessageBox.information(self, "Sucesso", f"{len(new_selection)} meses selecionados para processamento.")
        self.accept()
