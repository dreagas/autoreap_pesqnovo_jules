from PySide6.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        if self.hasFocus():
             # If focused, maybe allow? Instructions say "desabilitar wheel event ... e só permitir mudança por clique explícito e seleção"
             # "Bloquear QWheelEvent e exigir clique para abrir opções"
             # So ignoring it completely is safer.
             pass
        event.ignore()

class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()
