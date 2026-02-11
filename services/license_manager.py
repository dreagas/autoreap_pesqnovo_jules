import os
import json
import requests
import ctypes
from datetime import datetime
from core.constants import BASE_DIR

# URL Onde ficam as licenças e versões
LICENSE_URL = "https://gist.githubusercontent.com/dreagas/1f1410aac58eb9ec5338fd2d9e8c1d7c/raw/licencas.json"

# Data Limite Local (Fallback caso não tenha internet ou arquivo de licença)
# Formato: YYYY-MM-DD HH:MM:SS
HARD_LIMIT_DATE = "2026-02-11 12:00:00"

class LicenseManager:
    def __init__(self):
        # Arquivo local que o usuário pode criar para colocar sua chave
        # Conteúdo esperado: {"chave": "teste_reap2025"}
        if not os.path.exists(BASE_DIR):
            try: os.makedirs(BASE_DIR)
            except: pass
            
        self.local_license_file = os.path.join(BASE_DIR, "user_license.json")
        self.user_key = None
        self.license_data = None # Guarda dados retornados (versão, url, etc)

    def get_local_key(self):
        """Tenta ler a chave do usuário de um arquivo local JSON."""
        if os.path.exists(self.local_license_file):
            try:
                with open(self.local_license_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("chave", "").strip()
            except:
                return None
        return None

    def save_local_key(self, key):
        """Salva a chave digitada pelo usuário no arquivo JSON."""
        try:
            with open(self.local_license_file, 'w', encoding='utf-8') as f:
                json.dump({"chave": key.strip()}, f)
            return True
        except Exception as e:
            print(f"Erro ao salvar licença: {e}")
            return False

    def validate(self):
        """
        Retorna uma tupla: (is_valid, message, remote_data_dict)
        remote_data_dict contém 'versao', 'url_download', etc. se validado online.
        """
        current_time = datetime.now()
        self.user_key = self.get_local_key()

        # 1. TENTATIVA ONLINE (Se tiver chave local)
        if self.user_key:
            print(f"[License] Chave encontrada: {self.user_key}. Verificando online...")
            try:
                response = requests.get(LICENSE_URL, timeout=5)
                if response.status_code == 200:
                    all_licenses = response.json()
                    
                    if self.user_key in all_licenses:
                        user_data = all_licenses[self.user_key]
                        self.license_data = user_data
                        
                        # Checa status
                        if user_data.get("status") != "ativo":
                            return False, f"LICENÇA SUSPENSA: {user_data.get('msg')}", None
                        
                        # Checa validade online
                        validade_online = datetime.strptime(user_data.get("validade"), "%Y-%m-%d %H:%M:%S")
                        if current_time > validade_online:
                            return False, "Sua licença online expirou.", None
                        
                        return True, f"Licença Ativa (Online). Válida até {user_data.get('validade')}", user_data
                    else:
                        return False, "Chave de licença não encontrada ou inválida.", None
            except Exception as e:
                print(f"[License] Falha na verificação online: {e}. Indo para fallback.")

        # 2. FALLBACK (Data Fixa Local - Apenas se não conseguiu validar online com sucesso)
        # Se a chave foi rejeitada online (return False acima), ele nem chega aqui.
        # Ele só chega aqui se não tinha chave ou se deu erro de conexão.
        
        print("[License] Usando validação local (Hardcoded Date).")
        try:
            limit_date = datetime.strptime(HARD_LIMIT_DATE, "%Y-%m-%d %H:%M:%S")
            # Se já passou da data limite E não temos uma chave válida online -> Bloqueia
            if current_time > limit_date:
                return False, f"PERÍODO DE TESTES ENCERRADO.\nO sistema expirou em {HARD_LIMIT_DATE}.\nInsira uma chave válida.", None
            
            return True, f"Modo Offline/Teste. Válido até {HARD_LIMIT_DATE}", None
        except Exception as e:
            return False, f"Erro crítico de validação: {e}", None