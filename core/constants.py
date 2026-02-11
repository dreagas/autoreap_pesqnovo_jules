import os
import sys

# ==============================================================================
#  CONSTANTES GLOBAIS
# ==============================================================================

VERSION = "1.0.1.1"
CHROME_DEBUG_PORT = 9222
BASE_DIR = r"C:\chrome_reap"
CONFIG_FILE = os.path.join(BASE_DIR, "autoreapmpa.json")

# Define o caminho do log para funcionar em .exe e .py
if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

# Adjust APP_PATH to point to root if we are inside core/
# However, os.path.abspath(__file__) will be .../core/constants.py
# So os.path.dirname will be .../core
# The original code was in root.
# If I move this file to core/constants.py, APP_PATH will be .../core
# The original logic: APP_PATH = os.path.dirname(os.path.abspath(__file__)) (when in root)
# If I want to preserve the location of log file and icon in the root folder (or relative to executable),
# I should adjust this.
# If frozen, sys.executable is the exe path, so dirname is the folder containing exe. This remains correct.
# If not frozen, it depends where this file is.
# If I want APP_PATH to be the project root:
if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
else:
    # Assuming this file is in core/constants.py, go up one level
    APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_FILE = os.path.join(APP_PATH, "reap_debug_log.txt")
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
