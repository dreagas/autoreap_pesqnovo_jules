import os
import sys
import json
import time
import datetime
import subprocess
import requests

# --- CONFIGURAÇÕES GERAIS ---
# Versão atual do software. Deve ser incrementada a cada nova compilação.
VERSAO_ATUAL = "1.0.2.0"

# URL onde o arquivo JSON com as licenças está hospedado
URL_JSON = "https://gist.githubusercontent.com/dreagas/1f1410aac58eb9ec5338fd2d9e8c1d7c/raw/licencas.json"

# Nome do arquivo local que guarda a chave do usuário (ex: {"chave": "teste_reap2025"})
ARQUIVO_LICENCA_LOCAL = "licenca.json"

# Data limite para uso caso não exista arquivo de licença ou validação online falhe (modo fallback)
# Ajuste conforme a necessidade (Ano, Mês, Dia)
DATA_LIMITE_FALLBACK = datetime.datetime(2026, 12, 31)


class LicenseUpdater:
    """
    Classe responsável por verificar a licença do usuário e buscar atualizações.
    """

    def __init__(self):
        self.versao_atual = VERSAO_ATUAL
        self.url_json = URL_JSON

        # Determina o diretório base da aplicação
        if getattr(sys, 'frozen', False):
            # Se for executável congelado (PyInstaller)
            base_dir = os.path.dirname(sys.executable)
        else:
            # Se for script Python (desenvolvimento)
            # Como este arquivo está em services/, subimos um nível para a raiz
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.arquivo_local = os.path.join(base_dir, ARQUIVO_LICENCA_LOCAL)
        self.base_dir = base_dir

    def carregar_licenca_local(self):
        """
        Tenta ler o arquivo 'licenca.json' localmente para obter a chave do usuário.
        Retorna a chave (string) ou None se não encontrar.
        """
        if os.path.exists(self.arquivo_local):
            try:
                with open(self.arquivo_local, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    return dados.get("chave")
            except Exception as e:
                print(f"[ERRO] Falha ao ler {self.arquivo_local}: {e}")
        return None

    def validar_licenca(self):
        """
        Fluxo principal de validação:
        1. Busca licença local.
        2. Se existir, consulta online e valida status/validade.
        3. Se não existir ou erro online, usa validação por data (fallback).

        Retorna: (bool, msg, dados_licenca_online)
        - bool: True se acesso permitido, False caso contrário.
        - msg: Mensagem explicativa.
        - dados_licenca_online: Dicionário com dados da licença (versão, url, etc) ou None.
        """
        chave_usuario = self.carregar_licenca_local()

        # Se não tem chave local, vai para o fallback de data
        if not chave_usuario:
            print("[AVISO] Licença local não encontrada. Verificando data limite (fallback)...")
            return self.validacao_fallback()

        # Se tem chave, tenta validar online
        try:
            print(f"[INFO] Verificando licença online para: {chave_usuario}...")
            response = requests.get(self.url_json, timeout=10)
            response.raise_for_status() # Garante que baixou ok

            todas_licencas = response.json()

            # Verifica se a chave existe no JSON
            if chave_usuario in todas_licencas:
                dados = todas_licencas[chave_usuario]

                # Verifica status
                if dados.get("status") != "ativo":
                    return False, f"Licença inativa: {dados.get('msg')}", None

                # Verifica validade (formato esperado: YYYY-MM-DD HH:MM:SS)
                str_validade = dados.get("validade")
                if str_validade:
                    data_validade = datetime.datetime.strptime(str_validade, "%Y-%m-%d %H:%M:%S")
                    if datetime.datetime.now() > data_validade:
                        return False, "Licença expirada.", None

                # Se passou por tudo, retorna Sucesso e os dados para verificar update depois
                return True, "Licença Válida.", dados
            else:
                return False, "Chave de licença não encontrada no servidor.", None

        except requests.RequestException as e:
            print(f"[ERRO] Falha na conexão para verificar licença: {e}")
            # Se falhar a internet, decide se bloqueia ou libera via fallback.
            # Aqui, optamos por tentar o fallback de data se a internet falhar.
            return self.validacao_fallback()
        except Exception as e:
            print(f"[ERRO] Erro inesperado na validação: {e}")
            return self.validacao_fallback()

    def validacao_fallback(self):
        """
        Validação offline baseada em data fixa (substituindo teste_licenca.py).
        """
        agora = datetime.datetime.now()
        if agora > DATA_LIMITE_FALLBACK:
            return False, f"Período de testes expirou em {DATA_LIMITE_FALLBACK.strftime('%d/%m/%Y')}.", None
        return True, "Acesso liberado (Modo Offline/Teste).", None

    def verificar_atualizacao(self, dados_licenca):
        """
        Verifica se a versão remota é maior que a local.
        Recebe 'dados_licenca' que vem do JSON online.
        """
        if not dados_licenca:
            return False, None

        versao_remota = dados_licenca.get("versao")
        url_download = dados_licenca.get("url_download")

        if not versao_remota or not url_download:
            return False, None

        print(f"[INFO] Versão Atual: {self.versao_atual} | Versão Remota: {versao_remota}")

        try:
            # Comparação semântica de versões (ex: 1.0.2.10 > 1.0.2.9)
            # Removemos caracteres não numéricos se houver e dividimos por '.'
            v_local_parts = [int(x) for x in self.versao_atual.strip().split('.')]
            v_remota_parts = [int(x) for x in versao_remota.strip().split('.')]

            if v_remota_parts > v_local_parts:
                return True, url_download
        except Exception as e:
            print(f"[AVISO] Erro ao comparar versões ({self.versao_atual} vs {versao_remota}): {e}")
            # Fallback para comparação de string se falhar a conversão
            if versao_remota > self.versao_atual:
                return True, url_download

        return False, None

    def realizar_atualizacao(self, url_download):
        """
        Baixa o novo executável e cria um script .bat para substituir o atual.
        """
        print("[UPDATE] Iniciando atualização...")

        # Caminho completo do executável atual
        caminho_exe_atual = sys.executable
        nome_exe_atual = os.path.basename(caminho_exe_atual)
        dir_atual = self.base_dir # Usamos o diretório base calculado no init

        # Se estiver rodando como script .py (não congelado), não faz sentido substituir o .py por .exe desta forma.
        # Mas vamos simular o comportamento.
        if not getattr(sys, 'frozen', False):
            print("[AVISO] Rodando em modo script (.py). A atualização real só funciona em .exe compilado.")
            print(f"[SIMULAÇÃO] Baixaria de {url_download} para {os.path.join(dir_atual, nome_exe_atual + '.new')}")
            return

        caminho_novo_exe = os.path.join(dir_atual, nome_exe_atual + ".new")
        caminho_bat = os.path.join(dir_atual, "update_installer.bat")

        try:
            # 1. Download do arquivo
            print(f"[DOWNLOAD] Baixando atualização de: {url_download}")
            with requests.get(url_download, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                baixado = 0

                with open(caminho_novo_exe, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            baixado += len(chunk)
                            # Mostra progresso simples
                            if total_size > 0:
                                percent = int((baixado / total_size) * 100)
                                print(f"Baixando: {percent}%", end='\r')

            print("\n[DOWNLOAD] Concluído com sucesso.")

            # 2. Criar script .bat para fazer a troca e reiniciar
            # O script espera o processo atual fechar, deleta o antigo, renomeia o novo e reabre.
            # Usamos aspas para proteger caminhos com espaços.
            bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
:loop
tasklist | find "{nome_exe_atual}" > NUL
if not errorlevel 1 (
    timeout /t 1 > NUL
    goto loop
)
move /y "{caminho_novo_exe}" "{caminho_exe_atual}"
start "" "{caminho_exe_atual}"
del "%~f0"
"""
            with open(caminho_bat, "w") as bat:
                bat.write(bat_script)

            print("[UPDATE] O programa será reiniciado para aplicar a atualização.")

            # 3. Executar o bat e fechar o programa atual
            subprocess.Popen(caminho_bat, shell=True)
            sys.exit(0) # Fecha o programa atual imediatamente

        except Exception as e:
            print(f"[ERRO] Falha na atualização: {e}")
            # Limpa arquivo temporário se der erro
            if os.path.exists(caminho_novo_exe):
                try:
                    os.remove(caminho_novo_exe)
                except:
                    pass
