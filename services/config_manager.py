import os
import json
from core.constants import BASE_DIR, CONFIG_FILE, PROFILES_FILE, MESES_DEFESO_PADRAO, MESES_PRODUCAO_PADRAO, TODOS_MESES_ORDENADOS

class ConfigManager:
    # Configuração Padrão
    DEFAULT_CONFIG = {
        # Configuração de Navegador
        "navegador_padrao": "chrome",

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

    # Perfil vazio para novos slots (apenas UF Maranhão setado conforme pedido)
    EMPTY_PROFILE = {
        "navegador_padrao": "chrome",
        "municipio_padrao": "",
        "municipio_manual": "",
        "uf_residencia": "MARANHAO",
        "categoria": "",
        "forma_atuacao": "",
        "relacao_trabalho": "",
        "estado_comercializacao": "MARANHAO",
        "grupos_alvo": [],
        "compradores": [],
        "local_pesca_tipo": "",
        "uf_pesca": "MARANHAO",
        "nome_local_pesca": "",
        "metodos_pesca": [],
        "dias_min": 0,
        "dias_max": 0,
        "meta_financeira_min": 0.0,
        "meta_financeira_max": 0.0,
        "variacao_peso_pct": 0.0,
        "meses_selecionados": [],
        "meses_defeso": MESES_DEFESO_PADRAO, # Mantem lógica padrão de meses
        "meses_producao": MESES_PRODUCAO_PADRAO,
        "catalogo_especies": []
    }

    def __init__(self):
        self.current_profile_index = 0 # 0=Nuvem, 1,2,3=Locais
        self.data = self.load()
        self.local_profiles = self.load_local_profiles()

    def load(self):
        if not os.path.exists(BASE_DIR):
            try: os.makedirs(BASE_DIR)
            except: pass

        # O perfil 0 sempre tenta carregar do arquivo principal (legacy behavior)
        # Se não existir, usa DEFAULT
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def load_local_profiles(self):
        # Estrutura: {"1": {...}, "2": {...}, "3": {...}} (Índices 1, 2, 3 no código)
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save(self):
        try:
            if self.current_profile_index == 0:
                # Salva no arquivo principal (Nuvem/Padrão)
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
            else:
                # Salva no profiles.json
                self.local_profiles[str(self.current_profile_index)] = self.data
                with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.local_profiles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")

    def switch_profile(self, index):
        self.save() # Salva o atual antes de trocar
        self.current_profile_index = index

        if index == 0:
            # Recarrega do arquivo principal (que representa o perfil Nuvem + Edições)
            self.data = self.load()
        else:
            # Carrega do dicionário local
            if str(index) in self.local_profiles:
                self.data = self.local_profiles[str(index)]
            else:
                # Se não existe, cria novo zerado
                self.data = self.EMPTY_PROFILE.copy()
                self.local_profiles[str(index)] = self.data
                self.save() # Persiste a criação

    def reset_to_defaults(self, license_data=None):
        if self.current_profile_index == 0:
            self.data = self.DEFAULT_CONFIG.copy()
            if license_data:
                self.apply_cloud_overrides(license_data)
        else:
            self.data = self.EMPTY_PROFILE.copy()

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
        # Só aplica overrides no perfil 0 (Nuvem)
        if self.current_profile_index != 0 or not license_data:
            return

        perfil = license_data.get("perfil_config", {})
        if not perfil:
            return

        print("Aplicando perfil de configuração da nuvem...")
        changed = False

        keys_to_override = [
            "navegador_padrao",
            "uf_residencia", "municipio_padrao", "municipio_manual", "categoria", "forma_atuacao",
            "relacao_trabalho", "estado_comercializacao", "grupos_alvo", "compradores",
            "meses_defeso", "meses_producao", "dias_min", "dias_max",
            "local_pesca_tipo", "uf_pesca", "nome_local_pesca", "metodos_pesca",
            "catalogo_especies", "meta_financeira_min", "meta_financeira_max", "variacao_peso_pct"
        ]

        for key in keys_to_override:
            if key in perfil:
                if self.data.get(key) != perfil[key]:
                    self.data[key] = perfil[key]
                    changed = True
        
        if changed:
            self.save()
            print("Configurações atualizadas via nuvem com sucesso.")