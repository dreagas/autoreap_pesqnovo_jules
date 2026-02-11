import os
import sys

# ==============================================================================
#  CONSTANTES GLOBAIS
# ==============================================================================

VERSION = "1.0.3.0"
EDGE_DEBUG_PORT = 9555
BASE_DIR = r"C:\chrome_reap"
CONFIG_FILE = os.path.join(BASE_DIR, "autoreapmpa.json")

def resource_path(relative_path):
    """ Obtém o caminho absoluto para recursos, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver rodando como EXE, usa o caminho do projeto
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            # Sobe um nível pois este arquivo está em /core
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

# Caminho da aplicação (Raiz dos recursos)
APP_PATH = resource_path("")

# CAMINHO DAS IMAGENS (Sempre resolvido via resource_path)
IMG_DIR = resource_path("img")

# Garante que a pasta C:\chrome_reap exista para salvar logs e configs
if not os.path.exists(BASE_DIR):
    try: os.makedirs(BASE_DIR)
    except: pass

# Define o arquivo de log fixo dentro de C:\chrome_reap
LOG_FILE = os.path.join(BASE_DIR, "reap_debug_log.txt")
EDGE_PROFILE_PATH = BASE_DIR

# URLs para abrir automaticamente
URLS_ABERTURA = [
    "https://pesqbrasil-pescadorprofissional.mpa.gov.br/manutencao",
    "https://cadunico.dataprev.gov.br/#/home",
    "https://login.esocial.gov.br/",
    "https://cav.receita.fazenda.gov.br/"
]
URL_ALVO = URLS_ABERTURA[0]

# Listas de Meses
MESES_DEFESO_PADRAO = ["Janeiro", "Fevereiro", "Março", "Dezembro"]
MESES_PRODUCAO_PADRAO = ["Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro"]
TODOS_MESES_ORDENADOS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]