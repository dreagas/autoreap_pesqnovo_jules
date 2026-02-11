import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
from core.constants import VERSION, IMG_DIR
from services.license_manager import LicenseManager
from services.updater import AutoUpdater

# Ajuste para ícone na barra de tarefas (Windows)
try:
    myappid = f'autoreap.version.{VERSION}'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

def load_stylesheet(app):
    try:
        # Lógica robusta para encontrar o arquivo QSS tanto em DEV quanto em EXE
        if getattr(sys, 'frozen', False):
            # Se for EXE, a pasta 'ui' estará ao lado do executável
            base_path = os.path.dirname(sys.executable)
        else:
            # Se for Script, está na pasta relativa a este arquivo
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        qss_path = os.path.join(base_path, "ui", "theme.qss")
        
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"ERRO: Arquivo de tema não encontrado em: {qss_path}")
            
    except Exception as e:
        print(f"Error loading stylesheet: {e}")

def check_license_and_updates():
    # ... (Mantém sua lógica de licença inalterada aqui) ...
    from PySide6.QtWidgets import QInputDialog, QLineEdit # Import local para evitar erro circular
    lic_mgr = LicenseManager()
    
    while True:
        is_valid, msg, remote_data = lic_mgr.validate()

        if is_valid:
            if remote_data:
                updater = AutoUpdater(VERSION, remote_data)
                if updater.check_for_updates():
                    resp = ctypes.windll.user32.MessageBoxW(
                        0, 
                        f"Uma nova versão ({remote_data.get('versao')}) está disponível!\n\nDeseja atualizar agora?", 
                        "Atualização Disponível", 
                        0x04 | 0x40 | 0x1000 
                    )
                    if resp == 6: 
                        updater.download_and_install()
            return True
        
        # Pede licença se falhar
        # Precisamos de uma instância temporária de QApplication para o Dialog funcionar se o main ainda não criou
        temp_app = QApplication.instance() 
        if not temp_app: temp_app = QApplication(sys.argv)

        key, ok = QInputDialog.getText(
            None, 
            "Ativação Necessária", 
            f"{msg}\n\nPor favor, insira sua Chave de Licença:", 
            QLineEdit.Normal, 
            ""
        )
        
        if ok and key.strip():
            lic_mgr.save_local_key(key)
        else:
            return False

def main():
    # Checagem antes de criar a App principal
    if not check_license_and_updates():
        sys.exit()

    app = QApplication(sys.argv)
    app.setApplicationName("AutoREAPv2")

    # Define o ícone
    icon_path = os.path.join(IMG_DIR, "REAP2.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()