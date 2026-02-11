import os
import sys
import requests
import subprocess
import ctypes
from packaging import version

class AutoUpdater:
    def __init__(self, current_version, repo_data, app_logger=None):
        self.current_version = current_version
        self.repo_data = repo_data
        self.logger = app_logger
        
        # Define onde salvar o instalador temporário
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.temp_installer_path = os.path.join(base_dir, "setup_update_temp.exe")

    def log(self, msg):
        if self.logger: self.logger.info(f"[UPDATER] {msg}")
        else: print(f"[UPDATER] {msg}")

    def check_for_updates(self):
        """Verifica se a versão online é maior que a atual."""
        if not self.repo_data: return False

        online_ver = self.repo_data.get("versao")
        if not online_ver: return False

        try:
            v_curr = version.parse(self.current_version)
            v_new = version.parse(online_ver)
            
            if v_new > v_curr:
                self.log(f"Update disponível: {v_curr} -> {v_new}")
                return True
            return False
        except Exception as e:
            self.log(f"Erro ao comparar versões: {e}")
            return False

    def download_and_install(self):
        """Baixa o instalador e o executa."""
        url = self.repo_data.get("url_download")
        if not url: return

        self.log(f"Baixando instalador: {url}")
        
        try:
            # 1. Download do Instalador
            response = requests.get(url, stream=True, timeout=90)
            response.raise_for_status()
            
            with open(self.temp_installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.log("Download concluído. Iniciando instalador...")

            # 2. Executar o Instalador
            # Passamos argumentos para tentar fazer uma instalação mais silenciosa ou normal
            # Se for Inno Setup padrão, ele vai abrir a janela de instalação por cima
            subprocess.Popen([self.temp_installer_path], shell=True)

            # 3. Fechar o programa atual imediatamente para não bloquear a substituição de arquivos
            self.log("Encerrando aplicação para permitir atualização...")
            sys.exit(0)

        except Exception as e:
            self.log(f"Erro na atualização: {e}")
            ctypes.windll.user32.MessageBoxW(0, f"Erro ao baixar atualização:\n{e}", "Erro", 0x10)