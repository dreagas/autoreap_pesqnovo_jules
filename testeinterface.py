import os
import sys
import time
import subprocess
import logging
import re
import unicodedata
import random
import socket
import threading
import ctypes
import queue
import json
import traceback
from datetime import datetime

# Bibliotecas de Interface
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException, NoSuchElementException

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

# ==============================================================================
#  GESTOR DE CONFIGURAÇÕES (JSON)
# ==============================================================================

class ConfigManager:
    # Configuração Padrão
    DEFAULT_CONFIG = {
        "municipio_padrao": "Nova Olinda do Maranhão", 
        "municipio_manual": "", 
        "uf_residencia": "MARANHAO",
        "categoria": "Artesanal",
        "forma_atuacao": "Desembarcado",
        "relacao_trabalho": "Economia Familiar",
        "estado_comercializacao": "MARANHAO",
        
        # Local e Pesca
        "local_pesca_tipo": "Rio",
        "uf_pesca": "MARANHAO",
        "nome_local_pesca": "RIO TURI",
        "metodos_pesca": ["Tarrafa"], # Padrão definido apenas como Tarrafa
        
        # Checkboxes
        "grupos_alvo": ["Peixes"],
        "compradores": ["Venda direta ao consumidor", "Outros"],
        
        # Financeiro
        "dias_min": 18,
        "dias_max": 22,
        "meta_financeira_min": 990.00,
        "meta_financeira_max": 1100.00,
        "variacao_peso_pct": 0.15,
        
        # Meses Configurados
        "meses_selecionados": TODOS_MESES_ORDENADOS.copy(),
        # Referência de meses (não editável via GUI, mas salvo)
        "meses_defeso": MESES_DEFESO_PADRAO,
        "meses_producao": MESES_PRODUCAO_PADRAO,
        
        "catalogo_especies": [
            {"nome": "Branquinha",                  "preco": 12.00, "kg_base": 21},
            {"nome": "Mandi",                       "preco": 15.00, "kg_base": 20},
            {"nome": "Piau",                        "preco": 15.00, "kg_base": 20},
            {"nome": "Piaba",                       "preco": 12.00, "kg_base": 12}, 
            {"nome": "Surubim ou Cachara",          "preco": 18.00, "kg_base": 17}, 
            {"nome": "Piau-cabeça-gorda",           "preco": 15.00, "kg_base": 12},
            {"nome": "Piau-de-vara",                "preco": 17.00, "kg_base": 16},
            {"nome": "Mandi, Cabeçudo, Mandiguaru", "preco": 16.00, "kg_base": 16}
        ]
    }

    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(BASE_DIR):
            try: os.makedirs(BASE_DIR)
            except: pass
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    
                    if "catalogo_especies" in config:
                        for esp in config["catalogo_especies"]:
                            if esp["nome"] == "Surubim":
                                esp["nome"] = "Surubim ou Cachara"
                    
                    return config
            except:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")

    def reset_to_defaults(self):
        self.data = self.DEFAULT_CONFIG.copy()
        self.save()

    def get_municipio_efetivo(self):
        sel = self.data.get("municipio_padrao")
        if sel == "Outros":
            return self.data.get("municipio_manual", "")
        return sel

# ==============================================================================
#  CLASSE DE LOG
# ==============================================================================

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

# ==============================================================================
#  LÓGICA DO NAVEGADOR (BACKEND)
# ==============================================================================

class AutomationLogic:
    def __init__(self, logger, stop_event, config_manager):
        self.logger = logger
        self.stop_event = stop_event
        self.driver = None
        self.cfg = config_manager 
        try:
            import psutil
            self.psutil_ref = psutil
        except ImportError:
            self.psutil_ref = None

    def check_stop(self):
        if self.stop_event.is_set():
            self.logger.warning(">>> INTERRUPÇÃO IMEDIATA SOLICITADA PELO USUÁRIO <<<")
            raise InterruptedError("Parada solicitada")

    def tiny_sleep(self, seconds=0.0): 
        self.check_stop()
        if seconds > 0:
            time.sleep(seconds)

    def normalize_text(self, text):
        if not text: return ""
        text = unicodedata.normalize("NFKD", str(text))
        text = text.replace("R$", "").replace("\u00a0", "").strip()
        return text.lower()

    # --- CHROME ENGINE ---
    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def encontrar_executavel_chrome(self):
        caminhos = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        for c in caminhos:
            if os.path.exists(c): 
                return c
        return None

    def fechar_chrome_brutalmente(self):
        try:
            subprocess.run("taskkill /f /im chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    def garantir_chrome_aberto(self):
        if self.is_port_in_use(CHROME_DEBUG_PORT):
            self.logger.info("Chrome já está rodando na porta de debug. Conectando...", extra={'tags': 'SUCCESS'})
            return True

        self.logger.info("Iniciando nova instância do Chrome...", extra={'tags': 'INFO'})
        chrome_exe = self.encontrar_executavel_chrome()
        
        if chrome_exe:
            if not os.path.exists(CHROME_PROFILE_PATH): 
                try: os.makedirs(CHROME_PROFILE_PATH, exist_ok=True)
                except: pass
            
            cmd = [
                chrome_exe, 
                f"--remote-debugging-port={CHROME_DEBUG_PORT}", 
                rf"--user-data-dir={CHROME_PROFILE_PATH}", 
                "--no-first-run", "--no-default-browser-check", "--start-maximized",
                "--disable-popup-blocking" 
            ] + URLS_ABERTURA
            
            subprocess.Popen(
                cmd, shell=True, creationflags=0x00000008, 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL, close_fds=True
            )
            for i in range(20):
                time.sleep(0.5)
                if self.is_port_in_use(CHROME_DEBUG_PORT): 
                    return True
        return False

    def conectar_selenium(self):
        self.logger.info("Tentando conectar Selenium ao navegador...")
        opts = Options()
        opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")
        try:
            self.driver = webdriver.Chrome(options=opts)
            self.logger.info("Conexão Selenium ESTABELECIDA com sucesso!", extra={'tags': 'SUCCESS'})
            return self.driver
        except Exception as e:
            self.logger.error(f"Erro conexão Selenium: {e}")
            return None

    def obter_driver_robusto(self):
        if not self.is_port_in_use(CHROME_DEBUG_PORT):
            self.garantir_chrome_aberto()
        
        driver = self.conectar_selenium()
        if not driver:
            self.logger.warning("Primeira tentativa de conexão falhou. Reiniciando Chrome...")
            self.fechar_chrome_brutalmente()
            time.sleep(1)
            self.garantir_chrome_aberto()
            driver = self.conectar_selenium()
        return driver

    def trazer_navegador_frente(self):
        if not self.driver: return
        try:
            self.driver.minimize_window()
            time.sleep(0.1)
            self.driver.maximize_window()
            self.driver.switch_to.window(self.driver.current_window_handle)
        except: pass

    def garantir_acesso_manutencao(self):
        self.check_stop()
        driver = self.driver
        if not driver: return False

        try:
            self.logger.info("Verificando abas para garantir acesso à Manutenção...")
            aba_encontrada = None
            try:
                janelas = driver.window_handles
            except:
                return False

            for j in janelas:
                try:
                    driver.switch_to.window(j)
                    if "pesqbrasil" in driver.current_url:
                        aba_encontrada = j
                        break
                except: continue
            
            if aba_encontrada:
                driver.switch_to.window(aba_encontrada)
                self.logger.info("Aba PesqBrasil encontrada. Forçando atualização...", extra={'tags': 'INFO'})
                driver.get(URL_ALVO)
                try: WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except: time.sleep(1.0)
                return True
            else:
                self.logger.info("Aba PesqBrasil não encontrada. Abrindo nova guia...", extra={'tags': 'WARNING'})
                driver.execute_script(f"window.open('{URL_ALVO}', '_blank');")
                time.sleep(1.5)
                driver.switch_to.window(driver.window_handles[-1])
                return True
                
        except Exception as e:
            self.logger.error(f"Erro crítico na navegação: {e}")
            return False

    def forcar_retorno_inicio(self):
        self.logger.info("Forçando retorno à página inicial...")
        self.garantir_acesso_manutencao()

    def restaurar_abas_trabalho(self):
        if not self.driver: return
        self.logger.info("Restaurando abas de trabalho...", extra={'tags': 'INFO'})
        for url in URLS_ABERTURA:
            try:
                self.driver.execute_script(f"window.open('{url}', '_blank');")
                time.sleep(0.1)
            except: pass
        self.garantir_acesso_manutencao()

    # --- INTERAÇÃO COM ELEMENTOS ---
    
    def click_robusto(self, elemento, timeout=2):
        try:
            # Tenta clique direto via JS (mais rápido e ignora overlays)
            self.driver.execute_script("arguments[0].click();", elemento)
            return True
        except:
            try:
                # Se falhar, tenta o clique padrão com espera
                WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(elemento))
                elemento.click()
                return True
            except Exception as e:
                return False

    def limpar_e_digitar(self, elemento, texto):
        self.check_stop()
        texto = str(texto)
        self.logger.info(f"Digitando '{texto}'...")
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", elemento)
            try: elemento.clear()
            except: pass
            
            try:
                self.driver.execute_script("arguments[0].click();", elemento)
            except: pass
            
            elemento.send_keys(Keys.CONTROL + "a")
            elemento.send_keys(Keys.DELETE)
            elemento.send_keys(texto)
            elemento.send_keys(Keys.TAB)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao digitar '{texto}': {e}")
            return False

    def selecionar_combo(self, container_pai, valor, eh_busca=False):
        self.check_stop()
        self.logger.debug(f"Selecionando no combo: '{valor}'")
        driver = self.driver
        MAX_TENTATIVAS = 3
        
        for tentativa in range(MAX_TENTATIVAS):
            try:
                valor_norm = self.normalize_text(valor)
                
                try: 
                    br_select = container_pai.find_element(By.XPATH, ".//div[contains(@class, 'br-select')]")
                except: 
                    br_select = container_pai.find_element(By.XPATH, "./ancestor-or-self::div[contains(@class, 'br-select')]")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", br_select)
                
                input_elem = br_select.find_element(By.TAG_NAME, "input")
                lista = br_select.find_element(By.CLASS_NAME, "br-list")
                
                if not lista.is_displayed():
                    try: 
                        btn = br_select.find_element(By.XPATH, ".//button[contains(@class, 'br-button')]")
                        self.driver.execute_script("arguments[0].click();", btn)
                    except: 
                        self.driver.execute_script("arguments[0].click();", input_elem)
                    
                    try: WebDriverWait(driver, 2).until(lambda d: lista.is_displayed())
                    except: pass

                if eh_busca:
                    input_elem.clear()
                    input_elem.send_keys(valor)
                    time.sleep(0.5) 

                opcoes = lista.find_elements(By.TAG_NAME, "label")
                match_candidato = None
                
                for i in range(len(opcoes)):
                    try:
                        opc = opcoes[i]
                        txt_opc = self.normalize_text(opc.get_attribute("textContent"))
                        
                        if txt_opc == valor_norm:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", opc)
                            self.click_robusto(opc)
                            self.logger.info(f"Selecionado: {valor}", extra={'tags': 'SUCCESS'})
                            return True
                        
                        if eh_busca and not match_candidato:
                            if valor_norm in txt_opc:
                                match_candidato = opc
                                
                    except StaleElementReferenceException:
                        continue

                if match_candidato:
                    self.logger.info(f"Selecionado (Parcial): {match_candidato.text}", extra={'tags': 'WARNING'})
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", match_candidato)
                    self.click_robusto(match_candidato)
                    return True
                
                try: self.driver.execute_script("document.body.click()")
                except: pass
                
            except Exception as e:
                time.sleep(0.5)
                continue

        self.logger.error(f"FALHA ao selecionar combo: {valor}")
        return False

    def garantir_selecao_unica_combo(self, nome_campo, valor_unico):
        self.check_stop()
        self.logger.debug(f"Seleção única: {valor_unico}")
        try:
            inp = self.driver.find_element(By.XPATH, f"//input[@name='{nome_campo}']")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", inp)
            
            try: inp.find_element(By.XPATH, "./following-sibling::button").click()
            except: self.driver.execute_script("arguments[0].click();", inp)
            
            try: WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "./ancestor::div[contains(@class, 'br-select')]//div[contains(@class, 'br-list')]")))
            except: pass
            
            lista = inp.find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]//div[contains(@class, 'br-list')]")
            itens = lista.find_elements(By.CLASS_NAME, "br-item")
            valor_alvo = self.normalize_text(valor_unico)
            
            for item in itens:
                lbl = item.find_element(By.TAG_NAME, "label")
                txt = self.normalize_text(lbl.get_attribute("textContent"))
                if not txt or "selecionar todos" in txt: continue
                chk = item.find_element(By.TAG_NAME, "input")
                marcado = self.driver.execute_script("return arguments[0].checked;", chk)
                if txt == valor_alvo and not marcado: self.click_robusto(lbl)
                elif txt != valor_alvo and marcado: self.click_robusto(lbl)
            
            try: self.driver.execute_script("document.body.click()")
            except: pass
        except Exception as e:
            self.logger.warning(f"Erro em seleção única: {e}")

    def garantir_checkbox_group(self, nome_grupo, lista_alvos):
        self.check_stop()
        self.logger.debug(f"Processando checkboxes: {lista_alvos}")
        try:
            alvos_norm = [self.normalize_text(x) for x in lista_alvos]
            itens = self.driver.find_elements(By.XPATH, f"//input[@name='{nome_grupo}']/ancestor::div[contains(@class, 'br-checkbox')]")
            for item in itens:
                txt = self.normalize_text(item.text or item.get_attribute("textContent"))
                chk = item.find_element(By.TAG_NAME, "input")
                marcado = self.driver.execute_script("return arguments[0].checked;", chk)
                eh_alvo = any(alvo in txt for alvo in alvos_norm)
                
                if (eh_alvo and not marcado):
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chk)
                    self.driver.execute_script("arguments[0].click();", chk)
                elif (not eh_alvo and marcado):
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chk)
                    self.driver.execute_script("arguments[0].click();", chk)
        except Exception as e:
            self.logger.warning(f"Erro check group: {e}")

    # --- LÓGICA DE NEGÓCIO ---
    def gerar_dados_mes(self, mes_nome):
        d_min = float(self.cfg.data['meta_financeira_min'])
        d_max = float(self.cfg.data['meta_financeira_max'])
        variacao_pct = float(self.cfg.data.get('variacao_peso_pct', 0.15))
        catalogo = self.cfg.data['catalogo_especies']
        
        is_november = (mes_nome.lower() == "novembro")
        
        start_time = time.time()
        while True:
            if time.time() - start_time > 10:
                self.logger.warning(f"Timeout ao gerar valores para {mes_nome}.")
                break

            self.check_stop()
            qtd_especies = random.choice([3, 4])
            if len(catalogo) < qtd_especies:
                especies_selecionadas = catalogo
            else:
                especies_selecionadas = random.sample(catalogo, qtd_especies)
            producao = []
            if is_november:
                soma_parcial = 0
                temp_prod = []
                for i in range(len(especies_selecionadas) - 1):
                    esp = especies_selecionadas[i]
                    base = esp["kg_base"]
                    variacao = int(base * variacao_pct)
                    peso = random.randint(max(1, base - variacao), base + variacao)
                    preco = esp["preco"]
                    temp_prod.append({"nome": esp["nome"], "preco": preco, "peso": peso})
                    soma_parcial += (peso * preco)
                ultimo_esp = especies_selecionadas[-1]
                preco_ultimo = ultimo_esp["preco"]
                falta = 1000.00 - soma_parcial
                if falta > 0 and (falta % preco_ultimo == 0):
                    peso_necessario = int(falta / preco_ultimo)
                    if 1 <= peso_necessario <= 100: 
                        temp_prod.append({"nome": ultimo_esp["nome"], "preco": preco_ultimo, "peso": peso_necessario})
                        producao = temp_prod
                        return [(item['nome'], "Quilo (Kg)", str(item['peso']), f"{item['preco']:.2f}".replace('.', ',')) for item in producao]
            else:
                producao = []
                for esp in especies_selecionadas:
                    base = esp["kg_base"]
                    variacao = int(base * variacao_pct)
                    peso = random.randint(max(1, base - variacao), base + variacao)
                    producao.append({"nome": esp["nome"], "preco": esp["preco"], "peso": peso})
                total_mes = sum(item["peso"] * item["preco"] for item in producao)
                if d_min <= total_mes <= d_max:
                    return [(item['nome'], "Quilo (Kg)", str(item['peso']), f"{item['preco']:.2f}".replace('.', ',')) for item in producao]
        return [(item['nome'], "Quilo (Kg)", str(item['peso']), f"{item['preco']:.2f}".replace('.', ',')) for item in producao]

    def processar_etapa_1(self):
        self.logger.info(">>> Etapa 1: Dados Básicos <<<", extra={'tags': 'DESTAK'})
        self.check_stop()
        municipio = self.cfg.get_municipio_efetivo()
        try:
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.NAME, "uf")))
            inp_uf = self.driver.find_element(By.NAME, "uf").find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]")
            self.selecionar_combo(inp_uf, self.cfg.data['uf_residencia'])
            inp_mun = self.driver.find_element(By.NAME, "municipio").find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]")
            self.selecionar_combo(inp_mun, municipio, eh_busca=True)
            inp_cat = self.driver.find_element(By.NAME, "categoria").find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]")
            self.selecionar_combo(inp_cat, self.cfg.data['categoria'])
            inp_emb = self.driver.find_element(By.NAME, "embarcado").find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]")
            self.selecionar_combo(inp_emb, self.cfg.data['forma_atuacao'])
            self.logger.info("Etapa 1 preenchida.")
        except Exception as e:
            self.logger.warning(f"Aviso Etapa 1: {e}")

    def processar_etapa_2(self):
        self.logger.info(">>> Etapa 2: Atividade <<<", extra={'tags': 'DESTAK'})
        self.check_stop()
        try:
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Atividade pesqueira')]")))
            try:
                inp = self.driver.find_element(By.NAME, "prestacaoServico")
                container = inp.find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-select')]")
                self.selecionar_combo(container, self.cfg.data['relacao_trabalho'])
            except: pass
            self.garantir_selecao_unica_combo("estadosComercializacao", self.cfg.data['estado_comercializacao'])
            self.garantir_checkbox_group("gruposAlvo", self.cfg.data['grupos_alvo'])
            self.garantir_checkbox_group("compradoresPescado", self.cfg.data['compradores'])
            self.logger.info("Etapa 2 preenchida.")
        except Exception as e:
            self.logger.error(f"Erro Etapa 2: {e}")

    def preencher_tabela_especies(self, dados_especies):
        self.check_stop()
        self.logger.info(f"Preenchendo {len(dados_especies)} espécies na tabela...")
        try:
            tabela = self.driver.find_element(By.XPATH, "//div[contains(@class, 'br-table') and .//div[contains(text(), 'Resultado anual')]]")
            btn_add = tabela.find_element(By.XPATH, ".//button[contains(., 'Adicionar nova') or .//i[contains(@class, 'fa-plus')]]")
            for i, (esp, und, qtd, val) in enumerate(dados_especies):
                self.check_stop()
                linhas = tabela.find_elements(By.XPATH, ".//tbody/tr")
                if i >= len(linhas):
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_add)
                        self.click_robusto(btn_add)
                        WebDriverWait(self.driver, 2).until(lambda d: len(tabela.find_elements(By.XPATH, ".//tbody/tr")) > i)
                    except:
                        self.driver.execute_script("arguments[0].click();", btn_add)
                        time.sleep(0.3)
                    linhas = tabela.find_elements(By.XPATH, ".//tbody/tr")
                if i < len(linhas):
                    self.logger.info(f"Preenchendo linha {i+1}: {esp} | {qtd}kg | R${val}")
                    col = linhas[i].find_elements(By.TAG_NAME, "td")
                    self.selecionar_combo(col[0], esp, eh_busca=True)
                    self.selecionar_combo(col[1], und, eh_busca=False)
                    self.limpar_e_digitar(col[2].find_element(By.TAG_NAME, "input"), qtd)
                    self.limpar_e_digitar(col[3].find_element(By.TAG_NAME, "input"), val)
        except Exception as e:
            self.logger.error(f"Erro ao preencher espécies: {e}")

    def processar_mes_defeso(self, mes):
        self.check_stop()
        try:
            self.logger.info(f"Processando Defeso: {mes}")
            xpath_header = f"//button[contains(@class, 'br-accordion-header') and .//*[contains(text(), '{mes}')]]"
            header = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath_header)))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", header)
            if "accordion-icon-approved" in header.get_attribute('innerHTML') or "Não houve pesca" in header.text:
                self.logger.info(f"Mês {mes} já parece estar preenchido ou fechado.")
                return
            self.click_robusto(header)
            try:
                radio_nao = WebDriverWait(self.driver, 1.5).until(EC.visibility_of_element_located((By.XPATH, "//label[normalize-space()='Não']")))
                self.click_robusto(radio_nao)
                self.logger.info("Marcado 'Não' houve atividade.")
            except: pass
            try:
                chk_defeso = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Período regulamentado de defeso')]")
                self.click_robusto(chk_defeso)
                self.logger.info("Marcado motivo 'Defeso'.")
            except: pass
        except: pass

    def processar_mes_producao(self, mes):
        self.check_stop()
        self.logger.info(f"Iniciando Produção: {mes}", extra={'tags': 'INFO'})
        dados = self.gerar_dados_mes(mes) 
        municipio_pesca = self.cfg.get_municipio_efetivo() 
        try:
            xpath_header = f"//button[contains(@class, 'br-accordion-header') and .//*[contains(text(), '{mes}')]]"
            header = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath_header)))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", header)
            self.click_robusto(header)
            label_sim = WebDriverWait(self.driver, 1.5).until(EC.visibility_of_element_located((By.XPATH, "//label[normalize-space()='Sim']")))
            self.click_robusto(label_sim)
            dias = str(random.randint(int(self.cfg.data['dias_min']), int(self.cfg.data['dias_max'])))
            self.logger.info(f"Dias trabalhados: {dias}")
            inp_dias = WebDriverWait(self.driver, 1.5).until(EC.visibility_of_element_located((By.XPATH, "//label[contains(text(), 'dias trabalhados')]/ancestor::div[contains(@class, 'br-input')]//input")))
            self.limpar_e_digitar(inp_dias, dias)
            tbl = self.driver.find_element(By.XPATH, "//table[caption[contains(text(), 'Área de realização')]]")
            cols = tbl.find_element(By.XPATH, ".//tbody/tr[1]").find_elements(By.TAG_NAME, "td")
            self.selecionar_combo(cols[0], self.cfg.data['local_pesca_tipo'])
            self.selecionar_combo(cols[1], self.cfg.data['uf_pesca'])
            self.selecionar_combo(cols[2], municipio_pesca, eh_busca=True)
            self.limpar_e_digitar(cols[3].find_element(By.TAG_NAME, "input"), self.cfg.data['nome_local_pesca'])
            cell_metodo = cols[4]
            inp_met = cell_metodo.find_element(By.TAG_NAME, "input")
            self.click_robusto(inp_met)
            br_select = cell_metodo.find_element(By.XPATH, ".//div[contains(@class, 'br-select')]")
            lista = br_select.find_element(By.CLASS_NAME, "br-list")
            lista_metodos_cfg = self.cfg.data.get('metodos_pesca', [])
            opcoes = lista.find_elements(By.TAG_NAME, "label")
            for opc in opcoes:
                txt_opc = self.normalize_text(opc.get_attribute("textContent"))
                for metodo_usuario in lista_metodos_cfg:
                    if self.normalize_text(metodo_usuario) == txt_opc:
                        chk = opc.find_element(By.XPATH, "./preceding-sibling::input")
                        if not self.driver.execute_script("return arguments[0].checked;", chk):
                            self.click_robusto(opc)
                        break
            try: self.driver.find_element(By.TAG_NAME, "caption").click()
            except: pass
            self.preencher_tabela_especies(dados)
            self.logger.info(f"Mês {mes} finalizado com sucesso.", extra={'tags': 'SUCCESS'})
        except Exception as e:
            self.logger.error(f"Erro crítico no mês {mes}: {e}")
            self.logger.error(traceback.format_exc())

    def processar_etapa_3(self, meses_selecionados_set):
        self.logger.info(">>> Iniciando Etapa 3: Meses <<<", extra={'tags': 'DESTAK'})
        self.check_stop()
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "br-accordion")))
            try:
                all_defeso = self.cfg.data.get('meses_defeso', MESES_DEFESO_PADRAO)
                all_producao = self.cfg.data.get('meses_producao', MESES_PRODUCAO_PADRAO)
            except Exception as e:
                self.logger.warning(f"Erro ao ler configuração de meses: {e}. Usando padrão.")
                all_defeso = MESES_DEFESO_PADRAO
                all_producao = MESES_PRODUCAO_PADRAO
            self.logger.info(f"Meses selecionados pelo usuário: {len(meses_selecionados_set)}", extra={'tags': 'INFO'})
            defesos_to_run = [m for m in all_defeso if m in meses_selecionados_set]
            producao_to_run = [m for m in all_producao if m in meses_selecionados_set]
            self.logger.info(f"Defesos a preencher: {defesos_to_run}")
            for mes in defesos_to_run: 
                self.processar_mes_defeso(mes)
            self.logger.info(f"Produção a preencher: {producao_to_run}")
            for mes in producao_to_run: 
                self.processar_mes_producao(mes)
        except Exception as e:
            self.logger.error(f"ERRO CRÍTICO NA ETAPA 3: {e}")
            self.logger.error(traceback.format_exc())
            raise 

    def processar_etapa_4(self):
        self.logger.info(">>> Etapa 4: Aceite <<<", extra={'tags': 'DESTAK'})
        self.check_stop()
        try:
            self.logger.info("Procurando checkbox de responsabilidade...")
            chk = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "concordaComDeclaracaoResponsabilidade")))
            container = chk.find_element(By.XPATH, "./ancestor::div[contains(@class, 'br-checkbox')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", container)
            if not self.driver.execute_script("return arguments[0].checked;", chk):
                self.click_robusto(chk)
                self.logger.info("Termo aceito!", extra={'tags': 'SUCCESS'})
            ctypes.windll.user32.MessageBoxW(0, "O preenchimento automático foi CONCLUÍDO!\nRevise e clique em Enviar.", "Automação REAP", 0x40 | 0x1000)
        except Exception as e:
            self.logger.error(f"Erro Etapa 4: {e}")

    def avancar(self):
        self.check_stop()
        self.logger.info("Tentando clicar em Avançar...", extra={'tags': 'INFO'})
        try:
            btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Avançar') or @data-action='avancar']")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", btn)
            time.sleep(0.1)
            self.click_robusto(btn)
            time.sleep(1.0) 
            self.logger.info("Botão avançar clicado. Aguardando transição.")
            return True
        except:
            self.logger.error("Falha ao clicar em avançar.")
            return False

# ==============================================================================
#  CLASSE PRINCIPAL DA GUI (App)
# ==============================================================================

class ReapApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg_manager = ConfigManager()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        self.COLOR_BG = "#0F172A"        
        self.COLOR_SIDEBAR = "#1E293B"   
        self.COLOR_ACCENT = "#2563EB"    
        self.COLOR_ACCENT_HOVER = "#1D4ED8" 
        self.COLOR_SUCCESS = "#0891B2"   
        self.COLOR_SUCCESS_HOVER = "#0E7490" 
        self.COLOR_STOP = "#4338CA"      
        self.COLOR_STOP_HOVER = "#3730A3" 
        self.COLOR_TEXT = "#F8FAFC"      
        self.COLOR_FRAME = "#334155"     

        self.title(f"Automação REAP v{VERSION}")
        self.geometry("1100x750")
        self.configure(fg_color=self.COLOR_BG)
        
        icon_path = os.path.join(APP_PATH, 'imagens', 'REAP2.ico')
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.automation = None 
        self.config_widgets = {}
        self.species_widgets = []
        self.checkbox_groups = {} 
        self.month_vars = {}
        self.log_window = None 
        self.log_content = []

        self.setup_logging()
        self.setup_ui()
        
        self.after(500, self.boot_app)
        self.after(100, self.process_log_queue)

    def setup_logging(self):
        self.logger = logging.getLogger("REAP_GUI")
        self.logger.setLevel(logging.INFO)
        queue_handler = QueueHandler(self.log_queue)
        queue_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M')
        queue_handler.setFormatter(queue_formatter)
        self.logger.addHandler(queue_handler)
        try:
            file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
            file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            self.logger.info("="*50)
            self.logger.info(f"NOVA SESSÃO INICIADA: {VERSION}")
            self.logger.info(f"Log gravando em: {LOG_FILE}")
            self.logger.info("="*50)
        except Exception as e:
            print(f"ERRO CRÍTICO AO CRIAR ARQUIVO DE LOG: {e}")

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1) 
        ctk.CTkLabel(self.sidebar, text="REAP AUTO", font=("Segoe UI", 24, "bold"), text_color="#60A5FA").grid(row=0, column=0, padx=20, pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text=f"{VERSION}", font=("Segoe UI", 12), text_color="#94A3B8").grid(row=1, column=0, padx=20, pady=(0, 20))
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Status: Iniciando...", font=("Segoe UI", 12, "bold"), text_color="#38BDF8")
        self.lbl_status.grid(row=2, column=0, padx=10, pady=10)
        self.btn_reconnect = ctk.CTkButton(self.sidebar, text="RECONECTAR CHROME", command=self.boot_app, 
                                   font=("Segoe UI", 12, "bold"), fg_color="#475569", hover_color="#334155", 
                                   height=40, corner_radius=8)
        self.btn_reconnect.grid(row=3, column=0, padx=15, pady=(15, 5), sticky="ew")
        self.btn_open_tabs = ctk.CTkButton(self.sidebar, text="ABRIR ABAS DE TRABALHO", command=self.action_open_tabs, 
                                   font=("Segoe UI", 12, "bold"), fg_color="#0D9488", hover_color="#0F766E", 
                                   height=40, corner_radius=8)
        self.btn_open_tabs.grid(row=4, column=0, padx=15, pady=(5, 15), sticky="ew")
        self.btn_search = ctk.CTkButton(self.sidebar, text="ATUALIZAR LISTA", command=lambda: self.action_search(force_new=True), 
                                   font=("Segoe UI", 13, "bold"), fg_color=self.COLOR_SUCCESS, hover_color=self.COLOR_SUCCESS_HOVER, 
                                   height=45, corner_radius=8, state="disabled")
        self.btn_search.grid(row=5, column=0, padx=15, pady=15, sticky="ew")
        self.btn_logs = ctk.CTkButton(self.sidebar, text="VER LOGS", command=self.open_logs_window, 
                                   font=("Segoe UI", 12, "bold"), fg_color="#64748B", hover_color="#475569", 
                                   height=40, corner_radius=8)
        self.btn_logs.grid(row=6, column=0, padx=15, pady=(5, 15), sticky="ew")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="PARAR TUDO", command=self.action_stop, 
                                 font=("Segoe UI", 13, "bold"), fg_color=self.COLOR_STOP, hover_color=self.COLOR_STOP_HOVER, 
                                 height=45, corner_radius=8, state="disabled")
        self.btn_stop.grid(row=7, column=0, padx=15, pady=15, sticky="ew")
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        self.tabview.add("Painel Principal")
        self.tabview.add("Configurações")
        self.setup_main_tab()
        self.setup_config_tab()

    def setup_main_tab(self):
        self.tab_main = self.tabview.tab("Painel Principal")
        self.tab_main.grid_columnconfigure(0, weight=1)
        self.tab_main.grid_rowconfigure(2, weight=1) 
        self.frame_mun = ctk.CTkFrame(self.tab_main, fg_color=self.COLOR_FRAME, corner_radius=10)
        self.frame_mun.grid(row=0, column=0, sticky="ew", pady=(10, 10), padx=5)
        ctk.CTkLabel(self.frame_mun, text="MUNICÍPIO DE OPERAÇÃO", font=("Segoe UI", 13, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(10, 5))
        self.var_municipio = ctk.StringVar(value=self.cfg_manager.data.get("municipio_padrao"))
        self.combo_mun = ctk.CTkOptionMenu(self.frame_mun, values=["Nova Olinda do Maranhão", "Presidente Sarney", "Outros"],
                                         variable=self.var_municipio, command=self.on_municipio_change,
                                         fg_color=self.COLOR_SIDEBAR, button_color=self.COLOR_ACCENT, button_hover_color=self.COLOR_ACCENT_HOVER)
        self.combo_mun.pack(pady=5)
        self.entry_mun_manual = ctk.CTkEntry(self.frame_mun, placeholder_text="Digite o nome do município...", width=300)
        if self.var_municipio.get() == "Outros":
            self.entry_mun_manual.pack(pady=10)
            self.entry_mun_manual.insert(0, self.cfg_manager.data.get("municipio_manual", ""))
        self.btn_save_mun = ctk.CTkButton(self.frame_mun, text="Salvar Preferência", command=self.save_municipio_pref, width=150, fg_color=self.COLOR_ACCENT)
        self.btn_save_mun.pack(pady=(5, 10))
        self.frame_actions = ctk.CTkFrame(self.tab_main, fg_color=self.COLOR_FRAME, corner_radius=10)
        self.frame_actions.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=5)
        ctk.CTkLabel(self.frame_actions, text="CONTROLE DE PREENCHIMENTO", font=("Segoe UI", 13, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(10, 5))
        frame_btns = ctk.CTkFrame(self.frame_actions, fg_color="transparent")
        frame_btns.pack(pady=(0, 15))
        ctk.CTkButton(frame_btns, text="SELECIONAR MESES", command=self.open_month_selector,
                      font=("Segoe UI", 11, "bold"), fg_color="#475569", width=140).pack(side="left", padx=10)
        ctk.CTkButton(frame_btns, text="SIMULAR VALORES", command=self.simulate_values_interactive,
                      font=("Segoe UI", 11, "bold"), fg_color="#0D9488", width=140).pack(side="left", padx=10)
        ctk.CTkLabel(self.frame_actions, text="Valor alvo: R$ 990 a R$ 1100 (Novembro fixo em R$ 1000)", font=("Segoe UI", 10), text_color="gray").pack(pady=(0, 10))
        
        # --- CABEÇALHO DO STATUS (CONECTADO) ---
        self.frame_list_header = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.frame_list_header.grid(row=2, column=0, sticky="ew", padx=5, pady=(0,2))
        
        ctk.CTkLabel(self.frame_list_header, text="PAINEL DE VARREDURA", font=("Segoe UI", 12, "bold"), text_color="gray").pack(side="left")
        
        # Label "Conectado" inicialmente cinza (inativo) e com texto "● Aguardando"
        self.lbl_small_connected = ctk.CTkLabel(self.frame_list_header, text="● Aguardando", font=("Segoe UI", 10, "bold"), text_color="gray") 
        self.lbl_small_connected.pack(side="right", padx=10)

        self.dynamic_frame = ctk.CTkScrollableFrame(self.tab_main, label_text="Lista de Anos Pendentes", label_font=("Segoe UI", 16, "bold"), 
                                                    fg_color=self.COLOR_SIDEBAR, corner_radius=10)
        self.dynamic_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        self._update_dynamic_frame_msg("Aguardando Login...")

        self.mini_log_box = ctk.CTkTextbox(self.tab_main, height=60, font=("Consolas", 10), fg_color="#000000", text_color="#A1A1AA", corner_radius=6)
        self.mini_log_box.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        self.mini_log_box.configure(state="disabled")
        self.mini_log_box.tag_config("INFO", foreground="#E2E8F0")
        self.mini_log_box.tag_config("WARNING", foreground="#FACC15")
        self.mini_log_box.tag_config("ERROR", foreground="#F87171")
        self.mini_log_box.tag_config("SUCCESS", foreground="#38BDF8")
        self.mini_log_box.tag_config("DESTAK", foreground="#818CF8")

    def _update_dynamic_frame_msg(self, msg, color="gray", font_size=14):
        for widget in self.dynamic_frame.winfo_children(): widget.destroy()
        weight = "bold" if color == "#EF4444" else "normal"
        lbl = ctk.CTkLabel(self.dynamic_frame, text=msg, font=("Segoe UI", font_size, weight), text_color=color, wraplength=400)
        lbl.pack(pady=40)

    def open_logs_window(self):
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = ctk.CTkToplevel(self)
            self.log_window.title(f"Logs Completos - {LOG_FILE}")
            self.log_window.geometry("900x600")
            self.log_window.transient(self)
            self.log_window.attributes("-topmost", True)
            toolbar = ctk.CTkFrame(self.log_window, height=40)
            toolbar.pack(fill="x", padx=5, pady=5)
            ctk.CTkButton(toolbar, text="Atualizar do Arquivo", command=self.load_log_file_content, width=150, fg_color="#475569").pack(side="left", padx=5)
            ctk.CTkButton(toolbar, text="Abrir Arquivo no Bloco de Notas", command=self.open_log_file_system, width=200, fg_color="#2563EB").pack(side="left", padx=5)
            self.log_box_widget = ctk.CTkTextbox(self.log_window, font=("Consolas", 11), fg_color="#000000", text_color="#A1A1AA")
            self.log_box_widget.pack(fill="both", expand=True, padx=5, pady=5)
            self.log_box_widget.tag_config("INFO", foreground="#E2E8F0")
            self.log_box_widget.tag_config("WARNING", foreground="#FACC15")
            self.log_box_widget.tag_config("ERROR", foreground="#F87171")
            self.log_box_widget.tag_config("SUCCESS", foreground="#38BDF8")
            self.log_box_widget.tag_config("DESTAK", foreground="#818CF8", font=("Consolas", 11, "bold"))
            self.load_log_file_content()
            self.log_window.focus_force()
        else:
            self.log_window.focus_force()
            self.log_window.lift()

    def load_log_file_content(self):
        if hasattr(self, 'log_box_widget') and self.log_box_widget.winfo_exists():
            self.log_box_widget.configure(state="normal")
            self.log_box_widget.delete("0.0", "end")
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        self.log_box_widget.insert("0.0", content)
                except Exception as e:
                    self.log_box_widget.insert("0.0", f"Erro ao ler arquivo de log: {e}")
            else:
                self.log_box_widget.insert("0.0", "Arquivo de log ainda não existe.")
            self.log_box_widget.see("end")
            self.log_box_widget.configure(state="disabled")

    def open_log_file_system(self):
        try: os.startfile(LOG_FILE)
        except Exception as e: messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = self.logger.handlers[0].format(record)
                tag = "INFO"
                if hasattr(record, 'tags'): tag = record.tags
                elif record.levelno == logging.WARNING: tag = "WARNING"
                elif record.levelno == logging.ERROR: tag = "ERROR"
                self.log_content.append({'msg': msg, 'tag': tag})
                self.mini_log_box.configure(state="normal")
                self.mini_log_box.insert("end", msg + "\n", tag)
                self.mini_log_box.see("end")
                self.mini_log_box.configure(state="disabled")
                if self.log_window is not None and self.log_window.winfo_exists():
                    self.log_box_widget.configure(state="normal")
                    self.log_box_widget.insert("end", msg + "\n")
                    self.log_box_widget.see("end")
                    self.log_box_widget.configure(state="disabled")
        except queue.Empty: pass
        self.after(100, self.process_log_queue)

    def setup_config_tab(self):
        self.tab_cfg = self.tabview.tab("Configurações")
        self.tab_cfg.grid_columnconfigure(0, weight=1)
        self.tab_cfg.grid_rowconfigure(0, weight=1)
        self.scroll_cfg = ctk.CTkScrollableFrame(self.tab_cfg, fg_color="transparent")
        self.scroll_cfg.grid(row=0, column=0, sticky="nsew")
        def add_field(parent, label, key, kind="entry", options=None, height=30):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            ctk.CTkLabel(frame, text=label, width=200, anchor="w", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
            val_init = self.cfg_manager.data.get(key, "")
            if kind == "entry":
                var = ctk.StringVar(value=str(val_init))
                widget = ctk.CTkEntry(frame, textvariable=var, width=250)
                widget.pack(side="left", fill="x", expand=True)
                self.config_widgets[key] = widget
            elif kind == "option":
                var = ctk.StringVar(value=str(val_init))
                widget = ctk.CTkOptionMenu(frame, variable=var, values=options or [], width=250, fg_color=self.COLOR_FRAME)
                widget.pack(side="left", fill="x", expand=True)
                self.config_widgets[key] = widget
            elif kind == "multi-text": 
                var = ctk.StringVar(value=", ".join(val_init) if isinstance(val_init, list) else str(val_init))
                widget = ctk.CTkEntry(frame, textvariable=var, width=250)
                widget.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(parent, text="(Separe os itens por vírgula. Ex: Item1, Item2)", font=("Segoe UI", 10), text_color="gray").pack(anchor="w", padx=220)
                self.config_widgets[key] = widget

        def add_checkbox_group(parent, label, key, options):
            group_frame = ctk.CTkFrame(parent, fg_color=self.COLOR_FRAME, corner_radius=8)
            group_frame.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(group_frame, text=label, font=("Segoe UI", 13, "bold"), text_color=self.COLOR_ACCENT).pack(pady=5, anchor="w", padx=10)
            checks_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
            checks_frame.pack(fill="both", padx=10, pady=5)
            current_values = self.cfg_manager.data.get(key, [])
            vars_list = []
            col1 = ctk.CTkFrame(checks_frame, fg_color="transparent")
            col1.pack(side="left", fill="y", expand=True)
            col2 = ctk.CTkFrame(checks_frame, fg_color="transparent")
            col2.pack(side="left", fill="y", expand=True)
            for idx, opt in enumerate(options):
                parent_col = col1 if idx % 2 == 0 else col2
                is_checked = opt in current_values
                var = ctk.BooleanVar(value=is_checked)
                chk = ctk.CTkCheckBox(parent_col, text=opt, variable=var, font=("Segoe UI", 11))
                chk.pack(anchor="w", pady=2)
                vars_list.append((opt, var))
            self.checkbox_groups[key] = vars_list

        ctk.CTkLabel(self.scroll_cfg, text="DADOS PESSOAIS / BÁSICOS", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(10, 5), anchor="w")
        add_field(self.scroll_cfg, "UF Residência:", "uf_residencia", "option", ["MARANHAO", "PARA", "PIAUI"])
        add_field(self.scroll_cfg, "Categoria:", "categoria", "option", ["Artesanal", "Industrial"])
        add_field(self.scroll_cfg, "Forma Atuação:", "forma_atuacao", "option", ["Desembarcado", "Embarcado"])
        ctk.CTkLabel(self.scroll_cfg, text="ATIVIDADE - DETALHES", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(15, 5), anchor="w")
        opts_relacao = ["Individual/Autônomo", "Economia Familiar", "Regime de Parceria", "Carteira de Trabalho", "Contrato de Trabalho"]
        add_field(self.scroll_cfg, "Relação Trabalho:", "relacao_trabalho", "option", opts_relacao)
        add_field(self.scroll_cfg, "Est. Comercialização:", "estado_comercializacao", "option", ["MARANHAO", "PARA"])
        opts_grupos = ["Algas", "Moluscos", "Mariscos", "Peixes", "Quelônios (Tartarugas de água doce)", "Répteis (jacarés e outros)", "Crustáceos (camarão, lagosta, caranguejo, entre outros)"]
        add_checkbox_group(self.scroll_cfg, "Grupos Alvo:", "grupos_alvo", opts_grupos)
        opts_compradores = ["Associação", "Colônia", "Comércio de pescados (feira, mercado)", "Cooperativa", "Intermediário/atrevessador", "Venda direta ao consumidor", "Supermercado", "Outros"]
        add_checkbox_group(self.scroll_cfg, "Compradores:", "compradores", opts_compradores)
        ctk.CTkLabel(self.scroll_cfg, text="LOCAL E MÉTODOS DE PESCA", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(15, 5), anchor="w")
        opts_local = ["Açude", "Estuário", "Mar", "Lago", "Lagoa", "Rio", "Represa", "Reservatório", "Laguna"]
        add_field(self.scroll_cfg, "Tipo Local:", "local_pesca_tipo", "option", opts_local)
        add_field(self.scroll_cfg, "Nome do Local:", "nome_local_pesca", "entry")
        add_field(self.scroll_cfg, "UF Pesca:", "uf_pesca", "option", ["MARANHAO", "PARA"])
        opts_metodos = ["Arrasto", "Cerco", "Covos", "Emalhe", "Espinhel", "Linha de Mão", "Linha e Anzol", "Mariscagem", "Matapi", "Pesca Subaquática", "Tarrafa", "Vara", "Outro"]
        add_checkbox_group(self.scroll_cfg, "Métodos / Apetrechos:", "metodos_pesca", opts_metodos)
        ctk.CTkLabel(self.scroll_cfg, text="PRODUÇÃO E VALORES", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(15, 5), anchor="w")
        add_field(self.scroll_cfg, "Meta Fin. Mín (R$):", "meta_financeira_min", "entry")
        add_field(self.scroll_cfg, "Meta Fin. Máx (R$):", "meta_financeira_max", "entry")
        add_field(self.scroll_cfg, "Variação Peso (%):", "variacao_peso_pct", "entry")
        add_field(self.scroll_cfg, "Dias Trab. Mín:", "dias_min", "entry")
        add_field(self.scroll_cfg, "Dias Trab. Máx:", "dias_max", "entry")
        ctk.CTkLabel(self.scroll_cfg, text="CATÁLOGO DE ESPÉCIES", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_ACCENT).pack(pady=(25, 5), anchor="w")
        self.frame_species_container = ctk.CTkFrame(self.scroll_cfg, fg_color=self.COLOR_FRAME, border_width=1, border_color="#475569")
        self.frame_species_container.pack(fill="x", pady=5, padx=5)
        hdr = ctk.CTkFrame(self.frame_species_container, fg_color="#1E293B", height=35)
        hdr.pack(fill="x", pady=(1, 0))
        ctk.CTkLabel(hdr, text="Nome da Espécie", width=220, anchor="w", font=("Segoe UI", 11, "bold"), text_color="white").pack(side="left", padx=(10, 5))
        ctk.CTkLabel(hdr, text="Preço (R$)", width=80, font=("Segoe UI", 11, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Kg Base", width=60, font=("Segoe UI", 11, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Ação", width=40, font=("Segoe UI", 11, "bold"), text_color="white").pack(side="left", padx=5)
        self.species_scroll = ctk.CTkScrollableFrame(self.frame_species_container, height=220, fg_color="transparent")
        self.species_scroll.pack(fill="x", expand=True, padx=2, pady=2)
        self.reload_species_widgets()
        btn_add = ctk.CTkButton(self.scroll_cfg, text="+ ADICIONAR NOVA ESPÉCIE", command=self.add_species_row_interactive, 
                      fg_color="#0D9488", hover_color="#0F766E", height=35, font=("Segoe UI", 12, "bold"))
        btn_add.pack(pady=10, fill="x", padx=100)
        ctk.CTkButton(self.scroll_cfg, text="SALVAR TODAS AS CONFIGURAÇÕES", command=self.save_full_config, 
                      fg_color=self.COLOR_SUCCESS, hover_color=self.COLOR_SUCCESS_HOVER, 
                      height=45, font=("Segoe UI", 13, "bold")).pack(pady=(40, 10), fill="x", padx=40)
        ctk.CTkButton(self.scroll_cfg, text="RESTAURAR PADRÕES ORIGINAIS", command=self.reset_config, 
                      fg_color="#1E40AF", hover_color="#1E3A8A", 
                      height=45, font=("Segoe UI", 13, "bold")).pack(pady=(10, 40), fill="x", padx=40)

    def open_month_selector(self):
        top = ctk.CTkToplevel(self)
        top.title("Selecionar Meses")
        top.geometry("350x600") 
        top.transient(self) 
        top.attributes("-topmost", True) 
        lbl = ctk.CTkLabel(top, text="Selecione os meses para preenchimento:", font=("Segoe UI", 13, "bold"))
        lbl.pack(pady=10)
        scroll = ctk.CTkScrollableFrame(top, width=300, height=400)
        scroll.pack(pady=10, padx=10)
        current_selection = self.cfg_manager.data.get("meses_selecionados", TODOS_MESES_ORDENADOS)
        self.month_vars = {}
        for mes in TODOS_MESES_ORDENADOS:
            var = ctk.BooleanVar(value=(mes in current_selection))
            chk = ctk.CTkCheckBox(scroll, text=mes, variable=var)
            chk.pack(anchor="w", pady=5, padx=10)
            self.month_vars[mes] = var
        frame_btns = ctk.CTkFrame(top, fg_color="transparent")
        frame_btns.pack(pady=10, fill="x")
        def save_selection():
            new_selection = [m for m in TODOS_MESES_ORDENADOS if self.month_vars[m].get()]
            self.cfg_manager.data["meses_selecionados"] = new_selection
            self.cfg_manager.save()
            top.destroy()
            messagebox.showinfo("Sucesso", f"{len(new_selection)} meses selecionados para processamento.")
        def toggle_all(state):
            for var in self.month_vars.values():
                var.set(state)
        ctk.CTkButton(frame_btns, text="Marcar Todos", width=100, command=lambda: toggle_all(True)).pack(side="left", padx=10)
        ctk.CTkButton(frame_btns, text="Desmarcar Todos", width=100, command=lambda: toggle_all(False)).pack(side="left", padx=10)
        ctk.CTkButton(top, text="SALVAR SELEÇÃO", fg_color=self.COLOR_SUCCESS, command=save_selection).pack(pady=5, fill="x", padx=20)
        top.focus_force()

    def simulate_values_interactive(self):
        top = ctk.CTkToplevel(self)
        top.title("Simulação Interativa de Valores")
        top.geometry("500x700") 
        top.transient(self)
        top.attributes("-topmost", True)
        frame_header = ctk.CTkFrame(top, fg_color=self.COLOR_SIDEBAR)
        frame_header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_header, text="Simulação de Produção", font=("Segoe UI", 16, "bold"), text_color="#38BDF8").pack(pady=5)
        sps = [e['nome'] for e in self.cfg_manager.data['catalogo_especies']]
        ctk.CTkLabel(frame_header, text=f"Espécies Disponíveis: {', '.join(sps[:3])}...", font=("Segoe UI", 10), text_color="gray").pack(pady=(0,5))
        btn_reroll = ctk.CTkButton(frame_header, text="RESORTEAR SIMULAÇÃO", command=lambda: self.run_simulation_logic(scroll_results, total_lbl),
                                   font=("Segoe UI", 12, "bold"), fg_color="#F59E0B", hover_color="#D97706")
        btn_reroll.pack(pady=10)
        total_lbl = ctk.CTkLabel(top, text="Total Anual: R$ 0,00", font=("Segoe UI", 14, "bold"), text_color=self.COLOR_SUCCESS)
        total_lbl.pack(pady=5)
        scroll_results = ctk.CTkScrollableFrame(top, width=450, height=450)
        scroll_results.pack(fill="both", expand=True, padx=10, pady=5)
        self.run_simulation_logic(scroll_results, total_lbl)
        top.focus_force()

    def run_simulation_logic(self, parent_frame, total_label):
        for widget in parent_frame.winfo_children(): widget.destroy()
        meses_prod = self.cfg_manager.data.get("meses_producao", [])
        logic = AutomationLogic(self.logger, self.stop_event, self.cfg_manager)
        total_ano = 0
        for mes in meses_prod:
            dados = logic.gerar_dados_mes(mes)
            total_mes = 0.0
            detalhes_str = ""
            for item in dados:
                nome = item[0]
                peso = float(item[2])
                preco = float(item[3].replace(',', '.'))
                subtotal = peso * preco
                total_mes += subtotal
                detalhes_str += f"• {nome}: {peso}kg x R${preco:.2f} = R${subtotal:.2f}\n"
            total_ano += total_mes
            card = ctk.CTkFrame(parent_frame, fg_color=self.COLOR_FRAME)
            card.pack(fill="x", pady=5, padx=5)
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=10)
            lbl_mes = ctk.CTkLabel(header_frame, text=f"{mes.upper()}", font=("Segoe UI", 12, "bold"), width=100, anchor="w")
            lbl_mes.pack(side="left")
            lbl_val = ctk.CTkLabel(header_frame, text=f"R$ {total_mes:.2f}", font=("Segoe UI", 12, "bold"), text_color=self.COLOR_ACCENT)
            lbl_val.pack(side="left", padx=20)
            lbl_expand = ctk.CTkLabel(header_frame, text="▼", font=("Segoe UI", 10), text_color="gray")
            lbl_expand.pack(side="right")
            detail_frame = ctk.CTkFrame(card, fg_color="#0F172A") 
            lbl_detalhes = ctk.CTkLabel(detail_frame, text=detalhes_str, justify="left", font=("Consolas", 11), text_color="#94A3B8")
            lbl_detalhes.pack(padx=10, pady=5, anchor="w")
            def toggle(f=detail_frame, b=lbl_expand):
                if f.winfo_viewable():
                    f.pack_forget()
                    b.configure(text="▼")
                else:
                    f.pack(fill="x", padx=10, pady=(0, 10))
                    b.configure(text="▲")
            header_frame.bind("<Button-1>", lambda e, f=detail_frame, b=lbl_expand: toggle(f, b))
            lbl_mes.bind("<Button-1>", lambda e, f=detail_frame, b=lbl_expand: toggle(f, b))
            lbl_val.bind("<Button-1>", lambda e, f=detail_frame, b=lbl_expand: toggle(f, b))
        total_label.configure(text=f"Total Anual Simulado: R$ {total_ano:.2f}")

    def reload_species_widgets(self):
        for widget in self.species_scroll.winfo_children():
            widget.destroy()
        self.species_widgets = []
        catalogo = self.cfg_manager.data.get("catalogo_especies", [])
        for esp in catalogo:
            self.add_species_row(esp)

    def add_species_row(self, data=None, focus=False):
        if data is None: data = {"nome": "", "preco": 0.0, "kg_base": 10}
        row = ctk.CTkFrame(self.species_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ent_nome = ctk.CTkEntry(row, width=220, placeholder_text="Nome da espécie...")
        ent_nome.insert(0, data["nome"])
        ent_nome.pack(side="left", padx=(5, 5))
        ent_preco = ctk.CTkEntry(row, width=80)
        ent_preco.insert(0, str(data["preco"]))
        ent_preco.pack(side="left", padx=5)
        ent_kg = ctk.CTkEntry(row, width=60)
        ent_kg.insert(0, str(data["kg_base"]))
        ent_kg.pack(side="left", padx=5)
        btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="#EF4444", hover_color="#B91C1C", command=lambda: self.remove_species_row(row))
        btn_del.pack(side="left", padx=10)
        self.species_widgets.append({"frame": row, "nome": ent_nome, "preco": ent_preco, "kg": ent_kg})
        if focus:
            ent_nome.focus_set()
            self.species_scroll._parent_canvas.yview_moveto(1.0)

    def add_species_row_interactive(self):
        self.add_species_row(focus=True)

    def remove_species_row(self, row_widget):
        row_widget.destroy()
        self.species_widgets = [w for w in self.species_widgets if w["frame"] != row_widget]

    def on_municipio_change(self, value):
        if value == "Outros":
            self.entry_mun_manual.pack(pady=10, after=self.combo_mun)
        else:
            self.entry_mun_manual.pack_forget()

    def save_municipio_pref(self):
        val = self.var_municipio.get()
        manual = self.entry_mun_manual.get()
        self.cfg_manager.data["municipio_padrao"] = val
        self.cfg_manager.data["municipio_manual"] = manual
        self.cfg_manager.save()
        self.logger.info(f"Município salvo: {val}", extra={'tags': 'SUCCESS'})

    def save_full_config(self):
        for key, widget in self.config_widgets.items():
            val = widget.get()
            if key in ["dias_min", "dias_max", "meta_financeira_min", "meta_financeira_max", "variacao_peso_pct"]:
                try: val = float(val) if '.' in val else int(val)
                except: pass
            self.cfg_manager.data[key] = val
        for key, var_list in self.checkbox_groups.items():
            selected_values = []
            for txt, var in var_list:
                if var.get():
                    selected_values.append(txt)
            self.cfg_manager.data[key] = selected_values
        nova_lista = []
        for item in self.species_widgets:
            try:
                nome = item["nome"].get()
                preco = float(item["preco"].get())
                kg = int(item["kg"].get())
                if nome:
                    nova_lista.append({"nome": nome, "preco": preco, "kg_base": kg})
            except: pass 
        self.cfg_manager.data["catalogo_especies"] = nova_lista
        self.cfg_manager.save()
        self.logger.info("Configurações completas salvas.", extra={'tags': 'SUCCESS'})
        ctypes.windll.user32.MessageBoxW(0, "Configurações Salvas!", "REAP AUTO", 0x40 | 0x1000)

    def reset_config(self):
        resp = ctypes.windll.user32.MessageBoxW(0, "Tem certeza? Isso apagará todas as personalizações.", "Restaurar Padrão", 0x04 | 0x20 | 0x1000)
        if resp != 6: return 
        self.cfg_manager.reset_to_defaults()
        self.reload_config_tab_ui()
        self.logger.info("Configurações restauradas.", extra={'tags': 'WARNING'})

    def reload_config_tab_ui(self):
        for key, widget in self.config_widgets.items():
            val = self.cfg_manager.data.get(key, "")
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, str(val))
            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.set(str(val))
        for key, var_list in self.checkbox_groups.items():
            saved_vals = self.cfg_manager.data.get(key, [])
            for txt, var in var_list:
                var.set(txt in saved_vals)
        self.reload_species_widgets()
        mun_padrao = self.cfg_manager.data.get("municipio_padrao")
        mun_manual = self.cfg_manager.data.get("municipio_manual")
        self.var_municipio.set(mun_padrao)
        self.entry_mun_manual.delete(0, "end")
        self.entry_mun_manual.insert(0, mun_manual)
        self.on_municipio_change(mun_padrao)

    def boot_app(self):
        self.lbl_status.configure(text="Conectando Chrome...", text_color="white")
        threading.Thread(target=self._thread_boot_sequence, daemon=True).start()

    def _thread_boot_sequence(self):
        self.logger.info("INICIANDO SISTEMA...", extra={'tags': 'DESTAK'})
        self.automation = AutomationLogic(self.logger, self.stop_event, self.cfg_manager)
        sucesso = self.automation.garantir_chrome_aberto()
        if not sucesso:
            self.logger.error("Falha crítica ao abrir navegador.")
            return

        # POP-UP LOGIN (Bloqueia thread)
        ctypes.windll.user32.MessageBoxW(0, "Chrome aberto.\n\nFAÇA O LOGIN NO GOV.BR.\n\nClique OK quando estiver logado.", "Aguardando Login", 0x40 | 0x1000)
        self.logger.info("Login confirmado. Conectando Selenium...", extra={'tags': 'INFO'})

        # SÓ AGORA CONECTA
        driver = self.automation.conectar_selenium()
        
        if driver:
            self.after(0, self.unlock_interface)
            self.logger.info("Navegador Conectado.", extra={'tags': 'SUCCESS'})
            self.logger.info("Iniciando varredura...", extra={'tags': 'INFO'})
            
            # Força aba correta
            self.automation.garantir_acesso_manutencao()
            
            # Inicia busca automaticamente
            self.action_search()
        else:
            self.logger.error("Falha Selenium.")

    def unlock_interface(self):
        self.lbl_status.configure(text="Navegador Conectado", text_color="#A7F3D0")
        self.btn_stop.configure(state="normal")
        self.btn_search.configure(state="normal") 
        self.lbl_instr.configure(text="Conectado.")

    def action_open_tabs(self):
        if self.automation:
            threading.Thread(target=self.automation.restaurar_abas_trabalho, daemon=True).start()

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = self.logger.handlers[0].format(record)
                tag = "INFO"
                if hasattr(record, 'tags'): tag = record.tags
                elif record.levelno == logging.WARNING: tag = "WARNING"
                elif record.levelno == logging.ERROR: tag = "ERROR"
                self.log_content.append({'msg': msg, 'tag': tag})
                self.mini_log_box.configure(state="normal")
                self.mini_log_box.insert("end", msg + "\n", tag)
                self.mini_log_box.see("end")
                self.mini_log_box.configure(state="disabled")
                if self.log_window is not None and self.log_window.winfo_exists():
                    self.log_box_widget.configure(state="normal")
                    self.log_box_widget.insert("end", msg + "\n")
                    self.log_box_widget.see("end")
                    self.log_box_widget.configure(state="disabled")
        except queue.Empty: pass
        self.after(100, self.process_log_queue)

    def action_search(self, force_new=False):
        self.stop_event.clear()
        # Inicia com status de escaneamento em laranja
        self.lbl_small_connected.configure(text="● Escaneando...", text_color="#FACC15")
        self._update_dynamic_frame_msg("⏳ Carregando dados da tabela...", color="#FACC15", font_size=16)
        threading.Thread(target=self._thread_search, args=(force_new,), daemon=True).start()

    def _thread_search(self, force_new):
        if not self.automation or not self.automation.driver: return
        self.logger.info("Iniciando varredura de pendências...", extra={'tags': 'INFO'})
        
        try:
            if force_new:
                self.automation.garantir_acesso_manutencao()
            
            driver = self.automation.driver
            
            linhas = []
            max_retries = 10 
            
            for i in range(max_retries):
                if self.stop_event.is_set(): break
                try:
                    table = driver.find_elements(By.TAG_NAME, "table")
                    if table:
                        linhas = driver.find_elements(By.XPATH, "//table/tbody/tr")
                        if linhas: break
                except: pass
                
                # Atualiza feedback de tentativa
                msg_status = f"⏳ Procurando tabela... (Tentativa {i+1}/10)"
                self.after(0, lambda m=msg_status: self._update_dynamic_frame_msg(m, color="#FACC15", font_size=16))
                
                time.sleep(2) 
            
            if self.stop_event.is_set(): return

            # Se não encontrou linhas após as tentativas
            if not linhas:
                self.logger.warning("Tabela não encontrada após 10 tentativas.")
                # Atualiza UI para erro
                self.after(0, lambda: self.lbl_small_connected.configure(text="● Erro", text_color="#EF4444"))
                self.after(0, lambda: self._update_dynamic_frame_msg("❌ Tabela não encontrada.", color="#EF4444", font_size=18))
                self.after(0, self.show_retry_popup)
                return

            # Se encontrou, atualiza UI para sucesso
            self.after(0, lambda: self.lbl_small_connected.configure(text="● Conectado", text_color="#10B981"))

            def update_list_gui():
                for widget in self.dynamic_frame.winfo_children(): widget.destroy()
                
                encontrou = False
                for idx, row in enumerate(linhas):
                    txt = row.text
                    status_text = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]").text if "status" in row.get_attribute("innerHTML") else ""
                    
                    is_enviado = "Enviado" in txt or "Enviado" in status_text
                    is_pendente = "Pendente" in txt or "Rascunho" in txt

                    if is_pendente or is_enviado:
                        encontrou = True
                        try:
                            ano = "Desconhecido"
                            colunas = row.find_elements(By.TAG_NAME, "td")
                            for col in colunas:
                                if re.match(r'20\d{2}', col.text.strip()):
                                    ano = col.text.strip()
                                    break
                            
                            if is_enviado:
                                ctk.CTkButton(self.dynamic_frame, text=f"{ano} (JÁ ENVIADO)", 
                                              font=("Segoe UI", 12, "bold"), fg_color="#475569", 
                                              state="disabled", height=35, corner_radius=6).pack(pady=5, padx=10, fill="x")
                            else:
                                ctk.CTkButton(self.dynamic_frame, text=f"PROCESSAR {ano}", 
                                              command=lambda i=idx, a=ano: self.action_run_year(i, a),
                                              font=("Segoe UI", 12, "bold"), fg_color=self.COLOR_ACCENT, hover_color=self.COLOR_ACCENT_HOVER, 
                                              height=35, corner_radius=6).pack(pady=5, padx=10, fill="x")
                        except: pass

                if not encontrou:
                    ctk.CTkLabel(self.dynamic_frame, text="Nenhuma pendência encontrada.", text_color="gray").pack(pady=20)
                else:
                    self.logger.info("Lista Atualizada com Sucesso!", extra={'tags': 'SUCCESS'})

            self.after(0, update_list_gui)

        except Exception as e:
            self.logger.error(f"Erro na varredura: {e}")
            self.after(0, lambda: self.lbl_small_connected.configure(text="● Erro", text_color="#EF4444"))
            self.after(0, lambda: self._update_dynamic_frame_msg(f"❌ Erro na varredura: {e}", color="#EF4444", font_size=16))

    def show_retry_popup(self):
        """Pop-up para tentar novamente se a busca falhar."""
        if messagebox.askyesno("Tabela não encontrada", "Não foi possível ler a tabela de pendências após várias tentativas.\n\nDeseja atualizar a página e tentar novamente?"):
            self.action_search(force_new=True)

    def action_run_year(self, index, ano):
        self.stop_event.clear()
        meses_selecionados = set(self.cfg_manager.data.get("meses_selecionados", TODOS_MESES_ORDENADOS))
        self.logger.info(f"Iniciando {ano} | Meses: {len(meses_selecionados)} selecionados", extra={'tags': 'DESTAK'})
        if self.automation:
            threading.Thread(target=self.automation.trazer_navegador_frente).start()
            
        threading.Thread(target=self._thread_run_year, args=(index, ano, meses_selecionados), daemon=True).start()

    def _thread_run_year(self, index, ano, meses_selecionados_set):
        try:
            driver = self.automation.driver
            linhas = driver.find_elements(By.XPATH, "//table/tbody/tr")
            if index >= len(linhas):
                self.logger.error("Tabela mudou.")
                return

            row = linhas[index]
            btn = row.find_element(By.XPATH, ".//button[contains(@class, 'br-button') and @aria-label='editar']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            btn.click()
            
            self.automation.processar_etapa_1()
            if self.automation.avancar():
                self.automation.processar_etapa_2()
                if self.automation.avancar():
                    self.automation.processar_etapa_3(meses_selecionados_set)
                    if self.automation.avancar():
                        self.automation.processar_etapa_4()

            self.logger.info(f"Fim {ano}.", extra={'tags': 'SUCCESS'})
        except InterruptedError:
            self.logger.warning("Parada Solicitada.")
            self.after(0, self.show_stop_decision_popup)
            
        except Exception as e:
            self.logger.error(f"Erro execução: {e}")
            self.after(0, lambda: self.show_error_recovery_popup(str(e)))

    def show_stop_decision_popup(self):
        resp = ctypes.windll.user32.MessageBoxW(0, "Automação Parada!\nDeseja voltar para a página inicial de manutenções?", "Decisão", 0x04 | 0x20 | 0x1000)
        if resp == 6: 
            if self.automation:
                threading.Thread(target=self.automation.forcar_retorno_inicio, daemon=True).start()

    def show_error_recovery_popup(self, error_msg):
        msg = f"Ocorreu um erro durante o processamento:\n\n{error_msg}\n\nDeseja retornar à página inicial de manutenções para tentar novamente?"
        resp = ctypes.windll.user32.MessageBoxW(0, msg, "Erro de Execução", 0x04 | 0x10 | 0x1000) 
        if resp == 6: 
             if self.automation:
                threading.Thread(target=self.automation.forcar_retorno_inicio, daemon=True).start()

    def action_stop(self):
        self.stop_event.set()
        self.logger.error(">>> PARANDO... <<<", extra={'tags': 'ERROR'})

if __name__ == "__main__":
    try:
        app = ReapApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit()