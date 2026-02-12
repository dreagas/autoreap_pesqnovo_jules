import sys
import os
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QSplashScreen, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from core.constants import VERSION, IMG_DIR, resource_path, BASE_DIR
from services.license_manager import LicenseManager
from services.updater import AutoUpdater

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

def check_license_and_updates(splash=None):
    """
    Executa a validação da licença e verifica atualizações.
    Caso a licença falte ou seja inválida, solicita ao utilizador.
    Retorna uma tupla (Sucesso, DadosDaLicenca).
    """
    lic_mgr = LicenseManager()
    
    while True:
        if splash:
            splash.showMessage(f"Verificando licença...\n\nAutoREAP v{VERSION}", Qt.AlignCenter | Qt.AlignBottom, QColor("#38BDF8"))
            QApplication.processEvents()

        is_valid, msg, remote_data = lic_mgr.validate()

        if is_valid:
            if splash:
                splash.showMessage(f"Verificando atualizações...\n\nAutoREAP v{VERSION}", Qt.AlignCenter | Qt.AlignBottom, QColor("#38BDF8"))
                QApplication.processEvents()

            # Se a licença for validada online (remote_data presente), verifica updates
            if remote_data:
                updater = AutoUpdater(VERSION, remote_data)
                if updater.check_for_updates():
                    # Usando QMessageBox ao invés de ctypes
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("Atualização Disponível")
                    msg_box.setText(f"Uma nova versão ({remote_data.get('versao')}) está disponível!\n\nDeseja atualizar agora?")
                    msg_box.setIcon(QMessageBox.Icon.Information)
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint) # Garante que fique no topo

                    resp = msg_box.exec()

                    if resp == QMessageBox.StandardButton.Yes: # Botão 'Sim'
                        updater.download_and_install()

                        info_box = QMessageBox()
                        info_box.setWindowTitle("Download Concluído")
                        info_box.setText("O pacote de atualização foi baixado.\nPor favor, verifique a pasta do programa e atualize manualmente.")
                        info_box.setIcon(QMessageBox.Icon.Information)
                        info_box.exec()
            
            return True, remote_data
        
        # Se a validação falhar (chave inexistente ou expirada)
        # É necessária uma instância do QApplication para o QInputDialog funcionar
        temp_app = QApplication.instance() 
        if not temp_app: temp_app = QApplication(sys.argv)

        # Esconde splash para mostrar diálogo
        if splash: splash.hide()

        key, ok = QInputDialog.getText(
            None, 
            "Ativação Necessária", 
            f"{msg}\n\nPor favor, insira a sua Chave de Licença:", 
            QLineEdit.Normal, 
            ""
        )
        
        # Restaura splash se necessário (embora vá loopar e atualizar msg)
        if splash: splash.show()

        if ok and key.strip():
            # Guarda a chave localmente e repete o loop para validar
            lic_mgr.save_local_key(key)
        else:
            # Utilizador cancelou ou fechou a caixa de diálogo
            return False, None

def main():
    # 0. Data Truth Policy: Remove arquivos locais de configuração
    # Para garantir sincronização limpa.
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

    splash.showMessage(f"INICIANDO SISTEMA...\nCarregando módulos.\n\nAutoREAP v{VERSION}", Qt.AlignCenter | Qt.AlignBottom, QColor("#38BDF8"))
    splash.show()
    app.processEvents()
    # --------------------------------------------

    # 2. Verificação de Acesso e Atualizações
    # Bloqueia a abertura se não houver licença válida
    # Passamos o splash para que ele possa atualizar o status
    success, license_data = check_license_and_updates(splash)

    if not success:
        sys.exit()

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

    # Passamos os dados da licença para configurar municípios personalizados
    window = MainWindow(license_data)
    window.show()

    # Fecha o splash quando a janela principal abrir
    if splash:
        splash.finish(window)

    # Execução do loop principal
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
