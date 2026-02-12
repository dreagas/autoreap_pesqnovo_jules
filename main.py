import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from core.constants import VERSION, IMG_DIR, resource_path, BASE_DIR
# REMOVIDO: from services.license_manager import LicenseManager
# REMOVIDO: from services.updater import AutoUpdater

def load_stylesheet(app):
    """
    Carrega o ficheiro CSS do tema. Usa o resource_path para garantir 
    que o caminho funciona tanto em desenvolvimento como no executável.
    """
    try:
        # No EXE, a pasta 'ui' fica dentro de '_internal' (onedir) ou na raiz temporária (onefile)
        qss_path = resource_path(os.path.join("ui", "theme.qss"))
        
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"ERRO: Ficheiro de tema não encontrado em: {qss_path}")
            
    except Exception as e:
        print(f"Erro ao carregar folha de estilos: {e}")

def main():
    # 0. Data Truth Policy: Remove arquivos locais de configuração
    # Para garantir sincronização limpa (e forçar defaults APAPS neste caso)
    config_path = os.path.join(BASE_DIR, "autoreapmpa.json")
    if os.path.exists(config_path):
        try:
            os.remove(config_path)
            print("Configuração local removida para garantir sincronização.")
        except Exception as e:
            print(f"Erro ao limpar config local: {e}")

    # 1. Criação da aplicação (necessário antes de diálogos e temas)
    app = QApplication(sys.argv)
    app.setApplicationName("AutoREAPv2")

    # --- TELA DE CARREGAMENTO (SPLASH SCREEN) ---
    splash_path = resource_path(os.path.join("img", "splashscreen.png"))
    if os.path.exists(splash_path):
        splash_pix = QPixmap(splash_path)
    else:
        # Fallback
        splash_pix = QPixmap(450, 300)
        splash_pix.fill(QColor("#0F172A"))

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_TranslucentBackground) # Importante para transparência no Linux
    if not splash_pix.isNull():
        splash.setMask(splash_pix.mask())

    # Configura fonte da splash
    font = splash.font()
    font.setPixelSize(14)
    font.setBold(True)
    splash.setFont(font)

    splash.showMessage(f"INICIANDO SISTEMA [APAPS OFFLINE]...\nCarregando módulos.\n\nAutoREAP v{VERSION}", Qt.AlignCenter | Qt.AlignBottom, QColor("#38BDF8"))
    splash.show()
    app.processEvents()
    # --------------------------------------------

    # 2. Verificação de Acesso e Atualizações (BYPASSED)
    # Nesta versão específica APAPS, ignoramos a verificação online e injetamos
    # dados de licença simulados caso alguma parte do sistema precise.

    # Dados Hardcoded APAPS (Apenas para compatibilidade de assinatura, se houver)
    license_data = {
        "status": "ativo",
        "msg": "Modo Offline APAPS",
        "perfil_config": {
            # Os dados reais estão no ConfigManager, aqui é apenas metadado
            "cliente": "APAPS"
        }
    }

    # 3. Configurações Visuais
    # Define o ícone da aplicação na janela
    icon_path = resource_path(os.path.join("img", "REAP2.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Carrega o CSS (Tema Azul)
    load_stylesheet(app)

    # 4. Inicialização da Interface Principal
    if splash:
        splash.showMessage(f"ABRINDO INTERFACE...\n\nAutoREAP v{VERSION}", Qt.AlignCenter | Qt.AlignBottom, QColor("#38BDF8"))
        app.processEvents()

    # Passamos os dados da licença (fake/bypass) para configurar janela
    window = MainWindow(license_data)
    window.show()

    # Fecha o splash quando a janela principal abrir
    if splash:
        splash.finish(window)

    # Execução do loop principal
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
