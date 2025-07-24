import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

def login_to_auvo():
    # Carregar credenciais do arquivo .env
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Fazer login
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    
    try:
        response = requests.get(login_url)
        data = response.json()
        
        if "result" in data and data["result"]["authenticated"]:
            token = data["result"]["accessToken"]
            expiration = data["result"]["expiration"]
            print(f"Login realizado com sucesso! Token válido até: {expiration}")
            return token, base_url
        else:
            print("Falha na autenticação!")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        sys.exit(1)

def create_customers_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'customers'...")
        cursor.execute('''CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            externalId TEXT,
            description TEXT,
            cpfCnpj TEXT,
            phoneNumber TEXT,
            email TEXT,
            manager TEXT,
            managerJobPosition TEXT,
            note TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            maximumVisitTime INTEGER,
            unitMaximumTime INTEGER,
            groupsId TEXT,
            managerTeamsId TEXT,
            managersId TEXT,
            segmentId INTEGER,
            active INTEGER,
            adressComplement TEXT,
            creationDate TIMESTAMP,
            contacts TEXT,
            dateLastUpdate TIMESTAMP,
            uriAnexos TEXT,
            uriAttachments TEXT
        )''')
        conn.commit()
        print("Tabela 'customers' criada com sucesso!")
    else:
        # Verificar e adicionar colunas que podem estar faltando
        cursor.execute("PRAGMA table_info(customers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = {
            'externalId': 'TEXT',
            'description': 'TEXT',
            'cpfCnpj': 'TEXT',
            'phoneNumber': 'TEXT',
            'email': 'TEXT',
            'manager': 'TEXT',
            'managerJobPosition': 'TEXT',
            'note': 'TEXT',
            'address': 'TEXT',
            'latitude': 'REAL',
            'longitude': 'REAL',
            'maximumVisitTime': 'INTEGER',
            'unitMaximumTime': 'INTEGER',
            'groupsId': 'TEXT',
            'managerTeamsId': 'TEXT',
            'managersId': 'TEXT',
            'segmentId': 'INTEGER',
            'active': 'INTEGER',
            'adressComplement': 'TEXT',
            'creationDate': 'TIMESTAMP',
            'contacts': 'TEXT',
            'dateLastUpdate': 'TIMESTAMP',
            'uriAnexos': 'TEXT',
            'uriAttachments': 'TEXT'
        }
        
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                print(f"Adicionando coluna '{column_name}' à tabela 'customers'...")
                cursor.execute(f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}")
                conn.commit()
        
        print("Estrutura da tabela 'customers' verificada e atualizada!")
    conn.close()

def get_customers(token, base_url):
    url = f"{base_url}/customers/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }

    all_customers = []
    page = 1
    page_size = 100
    total_customers = 0

    try:
        while True:
            params = {
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }

            print(f"Buscando página {page}...")
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"Erro ao buscar clientes: {response.status_code}")
                print(response.text)
                break

            data = response.json()

            # Corrigir para acessar a lista correta
            entity_list = data.get("result", {}).get("entityList", [])
            customers_count = len(entity_list)
            total_customers += customers_count
            all_customers.extend(entity_list)

            print(f"Encontrados {customers_count} clientes na página {page}")

            # Se menos que page_size, acabou
            if customers_count < page_size:
                break
            page += 1

    except Exception as e:
        print(f"Erro ao buscar clientes: {e}")

    print(f"Total de clientes encontrados: {total_customers}")
    return all_customers

def safe_json_serialize(value):
    if value is None:
        return ""
    elif isinstance(value, (dict, list)):
        return json.dumps(value)
    elif isinstance(value, (int, float, bool, str)):
        return value
    else:
        # Para qualquer outro tipo, converter para string
        return str(value)

def save_customers_to_db(customers):
    customers = [c for c in customers if isinstance(c, dict)]
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for customer in customers:
            # Preferencialmente usar externalId como chave única, se existir
            unique_key = customer.get("externalId") or customer.get("id")
            unique_field = "externalId" if customer.get("externalId") else "id"
            if not unique_key:
                print(f"Cliente sem identificador único: {customer}")
                continue
            # Atualiza schema dinamicamente
            cursor.execute("PRAGMA table_info(customers)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            for key in customer.keys():
                if key not in existing_columns:
                    print(f"Adicionando coluna '{key}' à tabela 'customers'...")
                    cursor.execute(f"ALTER TABLE customers ADD COLUMN {key} TEXT")
                    conn.commit()
            # Prepara linha para salvar
            row = {}
            for key, value in customer.items():
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            fields = ', '.join(row.keys())
            placeholders = ', '.join(['?'] * len(row))
            values = list(row.values())
            # Verifica existência pelo campo correto
            cursor.execute(f"SELECT {unique_field} FROM customers WHERE {unique_field} = ?", (unique_key,))
            existing = cursor.fetchone()
            if existing:
                set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                cursor.execute(f"UPDATE customers SET {set_clause} WHERE {unique_field} = ?", values + [unique_key])
                updated += 1
                print(f"Atualizado cliente {unique_key} ({customer.get('description', '')})")
            else:
                cursor.execute(f"INSERT INTO customers ({fields}) VALUES ({placeholders})", values)
                inserted += 1
                print(f"Inserido cliente {unique_key} ({customer.get('description', '')})")
        conn.commit()
        print(f"Clientes inseridos: {inserted}, atualizados: {updated}")
    except Exception as e:
        print(f"Erro ao salvar clientes no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE CLIENTES ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela customers se não existir
    create_customers_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar clientes
    customers = get_customers(token, base_url)
    
    # Salvar clientes no banco de dados
    save_customers_to_db(customers)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de clientes processados: {len(customers)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
