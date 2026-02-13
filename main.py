import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QSplashScreen
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
from core.constants import VERSION, resource_path, CONFIG_FILE
from services.license_manager import LicenseManager
from services.updater import AutoUpdater

# Ajuste para o ícone aparecer corretamente na barra de tarefas do Windows
try:
    myappid = f'autoreap.version.{VERSION}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

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
                    # MB_YESNO | MB_ICONINFORMATION | MB_TOPMOST
                    resp = ctypes.windll.user32.MessageBoxW(
                        0, 
                        f"Uma nova versão ({remote_data.get('versao')}) está disponível!\n\nDeseja atualizar agora?", 
                        "Atualização Disponível", 
                        0x04 | 0x40 | 0x1000 
                    )
                    if resp == 6: # Botão 'Sim'
                        updater.download_and_install()
                        # Se o update for iniciado, o programa fecha-se dentro da função
            
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
    # 0. Limpeza de Configurações (Sync Truth) - Garante que use dados da nuvem
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
            print("Arquivo de configuração local removido para sincronização obrigatória.")
        except Exception as e:
            print(f"Erro ao remover config local: {e}")

    # 1. Criação da aplicação (necessário antes de diálogos e temas)
    app = QApplication(sys.argv)
    app.setApplicationName("AutoREAPv2")

    # --- TELA DE CARREGAMENTO (SPLASH SCREEN) ---
    # Dimensões da Splash
    w, h = 450, 300

    # Tenta carregar imagem, senão usa cor sólida
    splash_img_path = resource_path(os.path.join("img", "splashscreen.png"))

    if os.path.exists(splash_img_path):
        source_pix = QPixmap(splash_img_path)
        # Escala mantendo aspecto e preenchendo (crop se necessário)
        source_pix = source_pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    else:
        source_pix = QPixmap(w, h)
        source_pix.fill(QColor("#0F172A")) # Fundo Azul Escuro do Tema

    # Aplicar Cantos Arredondados (Rounded Corners)
    final_pix = QPixmap(w, h)
    final_pix.fill(Qt.transparent)

    painter = QPainter(final_pix)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, w, h, 20, 20) # Raio de 20px

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, source_pix)
    painter.end()

    splash = QSplashScreen(final_pix, Qt.WindowStaysOnTopHint)

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