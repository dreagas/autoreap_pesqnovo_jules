import os
import json
from core.constants import BASE_DIR, CONFIG_FILE, MESES_DEFESO_PADRAO, MESES_PRODUCAO_PADRAO, TODOS_MESES_ORDENADOS

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
