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

    def download_and_install(self, target_path):
        """Baixa o instalador no caminho especificado e o executa."""
        url = self.repo_data.get("url_download")
        if not url: return

        self.log(f"Baixando instalador: {url} -> {target_path}")
        
        try:
            # 1. Download do Instalador
            response = requests.get(url, stream=True, timeout=90)
            response.raise_for_status()
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.log("Download concluído. Iniciando instalador...")

            # 2. Executar o Instalador
            subprocess.Popen([target_path], shell=True)

            # 3. Fechar o programa atual imediatamente
            self.log("Encerrando aplicação para permitir atualização...")
            sys.exit(0)

        except Exception as e:
            self.log(f"Erro na atualização: {e}")
            ctypes.windll.user32.MessageBoxW(0, f"Erro ao baixar atualização:\n{e}", "Erro", 0x10)