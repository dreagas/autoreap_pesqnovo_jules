from PySide6.QtWidgets import (
    QComboBox, QSpinBox, QDoubleSpinBox, QDialog, QVBoxLayout, 
    QLabel, QPushButton, QHBoxLayout, QFrame, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QPoint
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
    Pop-up moderno com barra de título customizada e minimização global.
    """
    def __init__(self, title, message, icon_type="INFO", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        # Flags: Sem borda nativa, mas mantém comportamento de janela no topo
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedWidth(400) 
        
        # Definição de Cores
        if icon_type == "ERROR":
            self.accent_color = "#EF4444" 
            title_text = "ERRO"
        elif icon_type == "WARNING":
            self.accent_color = "#F59E0B" 
            title_text = "ATENÇÃO"
        elif icon_type == "SUCCESS":
            self.accent_color = "#10B981" 
            title_text = "SUCESSO"
        else:
            self.accent_color = "#38BDF8" 
            title_text = title

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container de Fundo
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
        
        # --- BARRA DE TÍTULO ---
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("background-color: transparent; border: none;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 5, 0)
        
        # Título
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"color: {self.accent_color}; font-size: 13px; font-weight: bold; border: none; font-family: 'Roboto';")
        title_layout.addWidget(lbl_title)
        
        title_layout.addStretch()
        
        # Botão Minimizar (-)
        btn_min = QPushButton("─") 
        btn_min.setObjectName("WindowControl")
        btn_min.setFixedSize(30, 30)
        btn_min.setCursor(Qt.PointingHandCursor)
        # Conecta à função que minimiza o app todo
        btn_min.clicked.connect(self.minimize_app)
        title_layout.addWidget(btn_min)

        # Botão Fechar (X)
        btn_close = QPushButton("✕") 
        btn_close.setObjectName("WindowControl")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        # Hover vermelho inline para garantir prioridade
        btn_close.setStyleSheet("QPushButton#WindowControl:hover { background-color: #EF4444; color: white; }")
        btn_close.clicked.connect(self.reject)
        title_layout.addWidget(btn_close)
        
        container_layout.addWidget(title_bar)
        
        # --- ÁREA DE CONTEÚDO ---
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(20)

        # Mensagem
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #E2E8F0; font-size: 14px; font-family: 'Roboto'; border: none;")
        content_layout.addWidget(lbl_msg)
        
        # Botão Principal (OK / JÁ ESTOU LOGADO)
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setMinimumHeight(35)
        self.btn_ok.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Estilo específico para este botão, garantindo visibilidade e fonte
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: #0F172A;
                font-weight: 900;
                font-size: 13px;
                border-radius: 6px;
                border: none;
                font-family: 'Roboto';
                text-transform: uppercase;
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

    def minimize_app(self):
        """Minimiza a janela pai (programa principal) se existir."""
        if self.parent():
            try:
                # Tenta acessar a janela principal e minimizá-la
                # window() retorna a janela de nível superior que contém este widget
                self.parent().window().showMinimized()
            except:
                self.showMinimized()
        else:
            self.showMinimized()

    # Permitir arrastar a janela clicando no corpo (já que não tem barra nativa)
    def mousePressEvent(self, event):
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