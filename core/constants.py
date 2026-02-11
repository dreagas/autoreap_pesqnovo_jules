import os
import sys

# ==============================================================================
#  CONSTANTES GLOBAIS
# ==============================================================================

VERSION = "1.0.2.0"
CHROME_DEBUG_PORT = 9222
BASE_DIR = r"C:\chrome_reap"
CONFIG_FILE = os.path.join(BASE_DIR, "autoreapmpa.json")

# Caminho da aplicação (para achar a pasta img/, etc)
if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como script, sobe um nível pois este arquivo está em /core
    APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CAMINHO DAS IMAGENS
IMG_DIR = os.path.join(APP_PATH, "img")

# LOG AGORA FICA NA PASTA CHROME_REAP (BASE_DIR)
if not os.path.exists(BASE_DIR):
    try: os.makedirs(BASE_DIR)
    except: pass

LOG_FILE = os.path.join(BASE_DIR, "reap_debug_log.txt")
CHROME_PROFILE_PATH = BASE_DIR

# URLs para abrir automaticamente
URLS_ABERTURA = [
    "https://pesqbrasil-pescadorprofissional.mpa.gov.br/manutencao",
    "https://cadunico.dataprev.gov.br/#/home",
    "https://login.esocial.gov.br/",
    "https://cav.receita.fazenda.gov.br/"
]
URL_ALVO = URLS_ABERTURA[0] # Link da Manutenção

# Listas de Meses
MESES_DEFESO_PADRAO = ["Janeiro", "Fevereiro", "Março", "Dezembro"]
MESES_PRODUCAO_PADRAO = ["Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro"]
TODOS_MESES_ORDENADOS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]