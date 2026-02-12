import os
import json
from core.constants import BASE_DIR, CONFIG_FILE, MESES_DEFESO_PADRAO, MESES_PRODUCAO_PADRAO, TODOS_MESES_ORDENADOS

class ConfigManager:
    # Configuração Padrão
    DEFAULT_CONFIG = {
        # Dados Pessoais / Básicos
        "municipio_padrao": "Nova Olinda do Maranhão",
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
        
        # Referência de Lógica (Estes definem o comportamento do robô)
        # Podem ser sobrescritos pelo JSON da nuvem
        "meses_defeso": MESES_DEFESO_PADRAO,
        "meses_producao": MESES_PRODUCAO_PADRAO,

        # Resultado Anual
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

    def reset_to_defaults(self, license_data=None):
        self.data = self.DEFAULT_CONFIG.copy()
        if license_data:
            self.apply_cloud_overrides(license_data)
        self.save()

    def export_config(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar config: {e}")
            return False

    def get_municipio_efetivo(self):
        sel = self.data.get("municipio_padrao")
        if sel == "Outros":
            return self.data.get("municipio_manual", "")
        return sel

    def apply_cloud_overrides(self, license_data):
        """
        Aplica configurações vindas da nuvem (JSON da Licença).
        Isso permite personalizar UF, Espécies, Municípios e Regras de Negócio por cliente.
        """
        if not license_data:
            return

        # 1. Busca perfil de configuração no JSON
        perfil = license_data.get("perfil_config", {})
        if not perfil:
            return

        print("Aplicando perfil de configuração da nuvem...")
        changed = False

        # Lista MESTRA de chaves permitidas para sobrescrever (Cobre sua solicitação completa)
        keys_to_override = [
            # 1. Localização e Dados Básicos
            "uf_residencia", 
            "municipio_padrao", 
            "municipio_manual",
            "categoria", 
            "forma_atuacao",
            
            # 2. Detalhes da Atividade
            "relacao_trabalho", 
            "estado_comercializacao",
            "grupos_alvo", 
            "compradores",
            
            # 3. Regras de Tempo (Meses de realização e não realização)
            "meses_defeso",   # Meses de não realização
            "meses_producao", # Meses de realização
            "dias_min", 
            "dias_max",
            
            # 4. Local Específico da Pesca
            "local_pesca_tipo", 
            "uf_pesca", 
            "nome_local_pesca",
            "metodos_pesca", # Petrecho
            
            # 5. Resultado Anual (Espécies e Valores)
            "catalogo_especies", 
            "meta_financeira_min", 
            "meta_financeira_max", 
            "variacao_peso_pct"
        ]

        for key in keys_to_override:
            if key in perfil:
                # Verifica se o valor é diferente para evitar escritas desnecessárias,
                # mas garante que a nuvem tem autoridade sobre o local.
                # Para listas (como catalogo_especies), a comparação direta funciona bem em Python.
                if self.data.get(key) != perfil[key]:
                    self.data[key] = perfil[key]
                    changed = True
        
        # Salva se houve mudança para persistir nas próximas aberturas
        if changed:
            self.save()
            print("Configurações atualizadas via nuvem com sucesso.")