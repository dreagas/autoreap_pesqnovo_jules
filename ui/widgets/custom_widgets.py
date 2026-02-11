from PySide6.QtWidgets import (
    QComboBox, QSpinBox, QDoubleSpinBox, QDialog, QVBoxLayout, 
    QLabel, QPushButton, QHBoxLayout, QFrame, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        if self.hasFocus():
            pass
        event.ignore()

class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class ModernMessageBox(QDialog):
    """
    Um pop-up moderno, compacto, responsivo e com controles de janela.
    """
    def __init__(self, title, message, icon_type="INFO", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        # WindowStaysOnTopHint para ficar sobre qualquer programa
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Tamanho
        self.setFixedWidth(360) 
        
        # Cores baseadas no tipo
        if icon_type == "ERROR":
            self.accent_color = "#EF4444" # Red
            title_text = "ERRO"
        elif icon_type == "WARNING":
            self.accent_color = "#F59E0B" # Amber
            title_text = "ATENÇÃO"
        elif icon_type == "SUCCESS":
            self.accent_color = "#10B981" # Green
            title_text = "SUCESSO"
        else:
            self.accent_color = "#38BDF8" # Blue
            title_text = title

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container (Borda e Fundo)
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: #0F172A;
                border: 1px solid {self.accent_color};
                border-radius: 8px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # --- Barra de Título Customizada ---
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: transparent; border: none;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 5, 0) # Margem esq para texto, dir para botoes
        
        # Título
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"color: {self.accent_color}; font-size: 14px; font-weight: bold; border: none; font-family: 'Roboto';")
        title_layout.addWidget(lbl_title)
        
        title_layout.addStretch()
        
        # Botão Minimizar
        btn_min = QPushButton("−") # Unicode minus
        btn_min.setObjectName("WindowControl")
        btn_min.setFixedSize(30, 30)
        btn_min.setCursor(Qt.PointingHandCursor)
        btn_min.clicked.connect(self.showMinimized)
        title_layout.addWidget(btn_min)

        # Botão Fechar
        btn_close = QPushButton("✕") # Unicode multiplication X
        btn_close.setObjectName("WindowControl")
        btn_close.setObjectName("WindowClose") # Para cor vermelha no hover (QSS)
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        title_layout.addWidget(btn_close)
        
        container_layout.addWidget(title_bar)
        
        # --- Conteúdo ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(15)

        # Mensagem
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #E2E8F0; font-size: 13px; font-family: 'Roboto'; border: none;")
        content_layout.addWidget(lbl_msg)
        
        # Botões de Ação
        btn_layout = QHBoxLayout()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setMinimumHeight(35)
        # Expandir horizontalmente para preencher
        self.btn_ok.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: #0F172A;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                border: none;
                font-family: 'Roboto';
            }}
            QPushButton:hover {{
                background-color: white;
            }}
        """)
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        
        content_layout.addLayout(btn_layout)
        container_layout.addWidget(content_widget)
        
        main_layout.addWidget(container)

    def mousePressEvent(self, event):
        # Permitir arrastar a janela sem barra nativa
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'oldPos'):
            delta = event.globalPos() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'oldPos'):
            del self.oldPos