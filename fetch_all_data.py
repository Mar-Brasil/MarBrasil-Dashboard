import sqlite3
import requests
import json
import os
import sys
import time
from dotenv import load_dotenv

class AuvoAPI:
    """Classe para interagir com a API Auvo"""
    
    def __init__(self, api_key, api_token):
        self.api_key = api_key
        self.api_token = api_token
        self.base_url = "https://api.auvo.com.br/v2"
        self.token = None
    
    def login(self):
        """Faz login na API Auvo e obtém o token de autenticação"""
        url = f"{self.base_url}/login/?apiKey={self.api_key}&apiToken={self.api_token}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if "result" in data and data["result"]["authenticated"]:
                self.token = data["result"]["accessToken"]
                print(f"Login realizado com sucesso! Token válido até: {data['result']['expiration']}")
                return True
            else:
                print("Falha na autenticação!")
                return False
        except Exception as e:
            print(f"Erro ao fazer login: {e}")
            return False
    
    def get_data(self, endpoint, params=None):
        """Busca dados de um endpoint específico"""
        if not self.token:
            print("Você precisa fazer login primeiro!")
            return None
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao acessar {endpoint}: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Erro na requisição para {endpoint}: {e}")
            return None

def extract_data_from_response(response):
    """Extrai os dados da resposta da API, lidando com diferentes formatos"""
    if not response:
        return []
    
    # Verificar se a resposta tem a chave 'result'
    if isinstance(response, dict) and 'result' in response:
        result = response['result']
        
        # Se result for uma lista, retornar diretamente
        if isinstance(result, list):
            return result
        
        # Se result for um dicionário com 'entityList'
        if isinstance(result, dict) and 'entityList' in result:
            return result['entityList']
    
    # Verificar se a resposta tem a chave 'entityList' diretamente
    if isinstance(response, dict) and 'entityList' in response:
        return response['entityList']
    
    # Se não conseguir extrair dados em um formato conhecido, retornar vazio
    print(f"Formato de resposta desconhecido: {type(response)}")
    print(f"Amostra da resposta: {str(response)[:200]}...")
    return []

def normalize_keys(data_item):
    """Normaliza as chaves de um item para o formato esperado pelo banco"""
    if not isinstance(data_item, dict):
        return data_item
    
    normalized = {}
    
    # Mapeamento de chaves comuns
    key_mapping = {
        'userid': 'userId',
        'userID': 'userId',
        'id': 'id',
        'taskid': 'taskID',
        'taskID': 'taskID',
        'customerid': 'customerId',
        'customerID': 'customerId'
    }
    
    for key, value in data_item.items():
        # Verificar se a chave precisa ser normalizada
        if key.lower() in key_mapping:
            normalized_key = key_mapping[key.lower()]
        else:
            normalized_key = key
        
        # Normalizar valores que são dicionários ou listas
        if isinstance(value, dict):
            normalized[normalized_key] = normalize_keys(value)
        elif isinstance(value, list):
            normalized[normalized_key] = [normalize_keys(item) if isinstance(item, dict) else item for item in value]
        else:
            normalized[normalized_key] = value
    
    return normalized

def create_table_if_not_exists(cursor, table_name, data_item):
    """Cria uma tabela no banco de dados com base nas chaves do item de dados"""
    if not data_item:
        print(f"Não é possível criar a tabela {table_name} sem um exemplo de dados.")
        return False
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if cursor.fetchone():
        return True  # Tabela já existe
    
    # Mapear tipos Python para tipos SQLite
    type_mapping = {
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bool: "INTEGER",  # SQLite não tem tipo booleano nativo
        type(None): "TEXT"  # Para valores None
    }
    
    # Determinar as colunas com base nas chaves do item
    columns = []
    primary_key = None
    
    # Identificar possíveis chaves primárias
    pk_candidates = ['id', 'userId', 'taskID', 'customerId']
    
    for key, value in data_item.items():
        # Determinar o tipo de coluna
        if isinstance(value, (dict, list)):
            column_type = "TEXT"  # Armazenar objetos complexos como JSON
        else:
            column_type = type_mapping.get(type(value), "TEXT")
        
        # Verificar se é uma chave primária
        if key.lower() in [c.lower() for c in pk_candidates]:
            primary_key = key
            columns.append(f"{key} {column_type} PRIMARY KEY")
        else:
            columns.append(f"{key} {column_type}")
    
    # Se não encontrou uma chave primária, adicionar uma coluna ID
    if not primary_key:
        columns.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")
    
    # Criar a tabela
    create_statement = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
    print(f"Criando tabela {table_name}...")
    print(create_statement)
    
    try:
        cursor.execute(create_statement)
        return True
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela {table_name}: {e}")
        return False

def save_data_to_db(db_path, table_name, data_items):
    """Salva os dados no banco de dados"""
    if not data_items:
        print(f"Nenhum dado para salvar na tabela {table_name}.")
        return 0, 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Normalizar os dados
        normalized_items = [normalize_keys(item) for item in data_items if isinstance(item, dict)]
        
        if not normalized_items:
            print(f"Nenhum item válido para salvar na tabela {table_name}.")
            return 0, 0
        
        # Criar a tabela se não existir
        if not create_table_if_not_exists(cursor, table_name, normalized_items[0]):
            conn.close()
            return 0, 0
        
        # Obter as colunas existentes na tabela
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns = [row[1] for row in cursor.fetchall()]
        
        # Contadores
        inserted_count = 0
        updated_count = 0
        
        # Identificar possíveis chaves primárias
        pk_candidates = ['id', 'userId', 'taskID', 'customerId']
        primary_key = None
        
        for candidate in pk_candidates:
            if candidate in normalized_items[0]:
                primary_key = candidate
                break
        
        # Se não encontrou uma chave primária, usar a primeira coluna
        if not primary_key and table_columns:
            primary_key = table_columns[0]
        
        # Para cada item nos dados
        for item in normalized_items:
            try:
                # Verificar se o item tem a chave primária
                if primary_key and primary_key in item:
                    # Verificar se o registro já existe
                    cursor.execute(f"SELECT {primary_key} FROM {table_name} WHERE {primary_key} = ?", (item[primary_key],))
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        # Atualizar registro existente
                        update_fields = []
                        update_values = []
                        
                        for key, value in item.items():
                            if key in table_columns and key != primary_key:
                                # Converter valores complexos para JSON
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value)
                                
                                update_fields.append(f"{key} = ?")
                                update_values.append(value)
                        
                        if update_fields:
                            # Adicionar o valor da chave primária para a cláusula WHERE
                            update_values.append(item[primary_key])
                            
                            # Executar a atualização
                            cursor.execute(
                                f"UPDATE {table_name} SET {', '.join(update_fields)} WHERE {primary_key} = ?",
                                update_values
                            )
                            updated_count += 1
                    else:
                        # Inserir novo registro
                        columns = []
                        placeholders = []
                        values = []
                        
                        for key, value in item.items():
                            if key in table_columns:
                                # Converter valores complexos para JSON
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value)
                                
                                columns.append(key)
                                placeholders.append("?")
                                values.append(value)
                        
                        if columns:
                            # Executar a inserção
                            cursor.execute(
                                f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                                values
                            )
                            inserted_count += 1
                else:
                    # Sem chave primária, sempre inserir
                    columns = []
                    placeholders = []
                    values = []
                    
                    for key, value in item.items():
                        if key in table_columns:
                            # Converter valores complexos para JSON
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value)
                            
                            columns.append(key)
                            placeholders.append("?")
                            values.append(value)
                    
                    if columns:
                        # Executar a inserção
                        cursor.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                            values
                        )
                        inserted_count += 1
            except Exception as e:
                print(f"Erro ao processar item para tabela {table_name}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count, updated_count
    except Exception as e:
        print(f"Erro ao salvar dados na tabela {table_name}: {e}")
        return 0, 0

def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurações
    db_path = "auvo.db"
    
    # Obter credenciais da API do arquivo .env
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        print("Verifique se o arquivo .env existe e contém as variáveis API_KEY e API_TOKEN.")
        sys.exit(1)
    
    print("=== BUSCA DE DADOS DA API AUVO ===")
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Inicializar API
    api = AuvoAPI(api_key, api_token)
    
    # Fazer login
    if not api.login():
        print("Não foi possível fazer login. Verifique suas credenciais.")
        sys.exit(1)
    
    # Lista de endpoints para buscar dados
    endpoints = [
        ("/users", "users"),
        ("/customers", "customers"),
        ("/teams", "teams"),
        ("/tasks", "tasks"),
        ("/services", "services"),
        ("/products", "products"),
        ("/equipment_categories", "equipment_categories"),
        ("/equipments", "equipments"),
        ("/product_categories", "product_categories"),
        ("/task_types", "task_types"),
        ("/expense_types", "expense_types"),
        ("/expenses", "expenses"),
        ("/segments", "segments"),
        ("/keywords", "keywords"),
        ("/questionnaires", "questionnaires"),
        ("/webhooks", "webhooks"),
        ("/gps", "gps"),
        ("/satisfaction_surveys", "satisfaction_surveys"),
        ("/quotations", "quotations"),
        ("/tickets", "tickets"),
        ("/service_orders", "service_orders")
    ]
    
    # Resultados
    results = {}
    
    # Para cada endpoint
    for endpoint, table_name in endpoints:
        print(f"\n=== Buscando dados de {endpoint} ===")
        
        # Buscar dados
        response = api.get_data(endpoint)
        
        # Extrair dados da resposta
        data_items = extract_data_from_response(response)
        
        if isinstance(data_items, list):
            print(f"Encontrados {len(data_items)} itens.")
            
            # Salvar no banco
            inserted, updated = save_data_to_db(db_path, table_name, data_items)
            print(f"Inseridos: {inserted}, Atualizados: {updated}")
            
            results[table_name] = {
                "total": len(data_items),
                "inserted": inserted,
                "updated": updated
            }
        else:
            print(f"Nenhum dado encontrado ou formato inválido.")
            results[table_name] = {
                "total": 0,
                "inserted": 0,
                "updated": 0
            }
    
    # Resumo final
    print("\n=== RESUMO DA IMPORTAÇÃO ===")
    for table_name, result in results.items():
        print(f"{table_name}: {result['total']} itens encontrados, {result['inserted']} inseridos, {result['updated']} atualizados")
    
    print("\nOperação concluída!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
