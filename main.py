import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from services.updater import LicenseUpdater

def load_stylesheet(app):
    try:
        # Resolve path relative to this file
        base_path = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(base_path, "ui", "theme.qss")
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Error loading stylesheet: {e}")

def main():
    app = QApplication(sys.argv)

    # Set app info if needed
    app.setApplicationName("Automação REAP")

    # --- VERIFICAÇÃO DE LICENÇA E ATUALIZAÇÃO ---
    print("[INIT] Iniciando verificação de licença e atualizações...")
    updater = LicenseUpdater()

    # 1. Validar Licença
    valido, msg, dados_licenca = updater.validar_licenca()

    if not valido:
        print(f"[ERRO] Licença inválida: {msg}")
        QMessageBox.critical(None, "Erro de Licença", f"Falha na validação da licença:\n{msg}")
        sys.exit(1)

    print(f"[SUCESSO] Licença validada: {msg}")

    # 2. Verificar Atualização (se estiver online e válido)
    if dados_licenca:
        tem_update, url_download = updater.verificar_atualizacao(dados_licenca)

        if tem_update and url_download:
            print("[INFO] Atualização disponível encontrada.")
            resposta = QMessageBox.question(
                None,
                "Atualização Disponível",
                "Uma nova versão do programa está disponível.\nDeseja baixar e atualizar agora?",
                QMessageBox.Yes | QMessageBox.No
            )

            if resposta == QMessageBox.Yes:
                updater.realizar_atualizacao(url_download)
                # O método realizar_atualizacao fecha o app se funcionar o update em .exe
                # Se continuar aqui, algo falhou ou é script .py
    # ---------------------------------------------

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()