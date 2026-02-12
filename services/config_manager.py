import os
import json
from core.constants import BASE_DIR, CONFIG_FILE, MESES_DEFESO_PADRAO, MESES_PRODUCAO_PADRAO, TODOS_MESES_ORDENADOS

class ConfigManager:
    # Configuração Padrão (APAPS - OFFLINE/STANDALONE)
    DEFAULT_CONFIG = {
        # Dados Pessoais / Básicos
        "municipio_padrao": "Presidente Sarney",
        "municipio_manual": "",
        "uf_residencia": "MARANHAO",
        "categoria": "Artesanal",
        "forma_atuacao": "Desembarcado",
        
        # Atividade - Detalhes
        "relacao_trabalho": "Economia Familiar",
        "estado_comercializacao": "MARANHAO",
        "grupos_alvo": ["Peixes"],
        "compradores": ["Venda direta ao consumidor", "Outros"],

        # Local e Pesca
        "local_pesca_tipo": "Rio",
        "uf_pesca": "MARANHAO",
        "nome_local_pesca": "RIO TURI",
        "metodos_pesca": ["Tarrafa"], 

        # Financeiro e Produção
        "dias_min": 18,
        "dias_max": 22,
        "meta_financeira_min": 990.00,
        "meta_financeira_max": 1100.00,
        "variacao_peso_pct": 0.15,

        # Meses Configurados (Controle de Checkboxes da UI)
        "meses_selecionados": TODOS_MESES_ORDENADOS.copy(),
        
        # Regras de Negócio
        "meses_defeso": ["Janeiro", "Fevereiro", "Março", "Dezembro"],
        "meses_producao": ["Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro"],

        # Resultado Anual (Catálogo APAPS)
        "catalogo_especies": [
            {"nome": "Branquinha", "preco": 12.0, "kg_base": 21},
            {"nome": "Mandi", "preco": 15.0, "kg_base": 20},
            {"nome": "Piau", "preco": 15.0, "kg_base": 20},
            {"nome": "Piaba", "preco": 12.0, "kg_base": 12},
            {"nome": "Surubim ou Cachara", "preco": 18.0, "kg_base": 17},
            {"nome": "Piau-cabeça-gorda", "preco": 15.0, "kg_base": 12},
            {"nome": "Piau-de-vara", "preco": 17.0, "kg_base": 16},
            {"nome": "Mandi, Cabeçudo, Mandiguaru", "preco": 16.0, "kg_base": 16}
        ]
    }

    # Lista de Municípios Customizada para a UI
    MUNICIPIOS_CUSTOM = ["Presidente Sarney", "Nova Olinda do Maranhão", "Santa Helena", "Outros"]

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

                    # Correção legada específica
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

    def export_config(self):
        """Exporta a configuração atual para a pasta Home ou Documentos do usuário."""
        home = os.path.expanduser("~")
        docs = os.path.join(home, "Documents")
        if not os.path.exists(docs):
            docs = home

        target_path = os.path.join(docs, "autoreap_config.json")

        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            return True, target_path
        except Exception as e:
            return False, str(e)
