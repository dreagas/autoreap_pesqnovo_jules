import os
import sys
import time
import subprocess
import re
import unicodedata
import random
import socket
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException, NoSuchElementException

from core.constants import (
    CHROME_DEBUG_PORT,
    CHROME_PROFILE_PATH,
    URLS_ABERTURA,
    URL_ALVO,
    MESES_DEFESO_PADRAO,
    MESES_PRODUCAO_PADRAO
)

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
            # Teste de vida
            _ = self.driver.current_window_handle
            self.logger.info("Conexão Selenium ESTABELECIDA com sucesso!", extra={'tags': 'SUCCESS'})
            return self.driver
        except Exception as e:
            self.logger.error(f"Erro conexão Selenium: {e}")
            return None

    def obter_driver_robusto(self):
        if not self.is_port_in_use(CHROME_DEBUG_PORT):
            self.garantir_chrome_aberto()

        driver = self.conectar_selenium()
        
        # Check de saúde
        try:
            if driver:
                _ = driver.title # Tenta acessar algo simples
        except:
            driver = None

        if not driver:
            self.logger.warning("Conexão falhou ou driver 'zumbi'. Reiniciando Chrome...")
            self.fechar_chrome_brutalmente()
            time.sleep(1)
            self.garantir_chrome_aberto()
            driver = self.conectar_selenium()
        
        self.driver = driver
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
                    url_atual = driver.current_url.lower()
                    titulo_atual = driver.title.lower()
                    
                    # Detecção aprimorada
                    if "pesqbrasil" in url_atual or "manutencao" in url_atual or "pescador profissional" in titulo_atual:
                        aba_encontrada = j
                        break
                except: continue

            if aba_encontrada:
                driver.switch_to.window(aba_encontrada)
                self.logger.info("Aba PesqBrasil encontrada.", extra={'tags': 'INFO'})
                # Só recarrega se não estiver na página certa (evita reload desnecessário)
                if URL_ALVO not in driver.current_url:
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
        """Verifica quais abas já estão abertas e abre apenas as faltantes."""
        if not self.driver: return
        self.logger.info("Verificando abas de trabalho...", extra={'tags': 'INFO'})
        
        try:
            janelas = self.driver.window_handles
            urls_abertas = []
            
            # Coleta URLs abertas (pode ser lento se houver muitas abas)
            for j in janelas:
                try:
                    self.driver.switch_to.window(j)
                    urls_abertas.append(self.driver.current_url.lower())
                except: pass
            
            # Volta para a primeira (só para não ficar perdido)
            if janelas: self.driver.switch_to.window(janelas[0])

            count_abertas = 0
            for url_alvo in URLS_ABERTURA:
                # Simplificação: verifica se parte da URL alvo está em alguma aberta
                # Ex: "cadunico" em "https://cadunico..."
                keyword = ""
                if "cadunico" in url_alvo: keyword = "cadunico"
                elif "esocial" in url_alvo: keyword = "esocial"
                elif "receita" in url_alvo: keyword = "receita"
                elif "pesqbrasil" in url_alvo: keyword = "pesqbrasil"
                
                ja_existe = False
                for u in urls_abertas:
                    if keyword and keyword in u:
                        ja_existe = True
                        break
                
                if not ja_existe:
                    self.logger.info(f"Abrindo aba faltante: {keyword}")
                    self.driver.execute_script(f"window.open('{url_alvo}', '_blank');")
                    count_abertas += 1
                    time.sleep(0.5)
            
            if count_abertas == 0:
                self.logger.info("Todas as abas de trabalho já estão abertas.", extra={'tags': 'SUCCESS'})
            
            self.garantir_acesso_manutencao()
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar abas: {e}")

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
            
            # REMOVIDO: ctypes.windll.user32.MessageBoxW...
            # A mensagem de sucesso agora é gerenciada pelo AppController -> UI
            
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