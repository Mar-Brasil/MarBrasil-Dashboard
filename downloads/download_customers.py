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
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL") # Modo Write-Ahead Log para melhor performance
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    errors = 0
    skipped = 0
    
    try:
        # Verificamos primeiro o schema para evitar alterações durante o loop
        cursor.execute("PRAGMA table_info(customers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Coletamos todos os novos campos antes de iniciar as atualizações
        all_keys = set()
        for customer in customers:
            all_keys.update(customer.keys())
        
        # Adicionamos colunas que faltam antes de começar as atualizações
        for key in all_keys:
            if key not in existing_columns:
                print(f"Adicionando coluna '{key}' à tabela 'customers'...")
                try:
                    cursor.execute(f"ALTER TABLE customers ADD COLUMN {key} TEXT")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"Coluna '{key}' já existe. Ignorando.")
                    else:
                        raise e
        
        # Agora processamos cada cliente individualmente
        for customer in customers:
            try:
                # Obter ID e externalId
                id_value = customer.get("id")
                external_id = customer.get("externalId")
                
                if not id_value:
                    print(f"Cliente sem ID único: {customer.get('description', 'Sem descrição')}")
                    errors += 1
                    continue
                
                # Prepara linha para salvar
                row = {}
                for key, value in customer.items():
                    if key not in existing_columns:
                        continue  # Ignorar campos que não estão na tabela
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                
                # Verificar existência por ID ou externalId
                exists_by_id = False
                exists_by_external_id = False
                existing_id = None
                
                # Verificar pelo ID principal
                cursor.execute("SELECT id FROM customers WHERE id = ?", (id_value,))
                result = cursor.fetchone()
                if result:
                    exists_by_id = True
                    existing_id = result[0]
                
                # Se tiver externalId, verificar se já existe outro registro com esse externalId
                if external_id:
                    cursor.execute("SELECT id FROM customers WHERE externalId = ? AND id != ?", 
                                  (external_id, id_value))
                    result = cursor.fetchone()
                    if result:
                        exists_by_external_id = True
                        # Encontrou outro registro com mesmo externalId mas ID diferente
                        print(f"Aviso: externalId {external_id} já existe com outro ID ({result[0]}). Cliente atual ID={id_value} será ignorado.")
                        skipped += 1
                        continue
                
                if exists_by_id:
                    # Atualizar registro existente
                    set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                    cursor.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", list(row.values()) + [id_value])
                    updated += 1
                else:
                    # Antes de inserir, verificar se já existe por externalId
                    if external_id:
                        cursor.execute("SELECT id FROM customers WHERE externalId = ?", (external_id,))
                        result = cursor.fetchone()
                        if result:
                            print(f"Pulando registro com externalId duplicado: {external_id} (já existe com ID={result[0]})")
                            skipped += 1
                            continue
                    
                    # Inserir novo registro
                    fields = ', '.join(row.keys())
                    placeholders = ', '.join(['?'] * len(row))
                    try:
                        cursor.execute(f"INSERT INTO customers ({fields}) VALUES ({placeholders})", list(row.values()))
                        inserted += 1
                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed: customers.externalId" in str(e):
                            print(f"Erro de duplicidade no externalId: {external_id}")
                            # Tentar uma última verificação
                            cursor.execute("SELECT id FROM customers WHERE externalId = ?", (external_id,))
                            result = cursor.fetchone()
                            if result:
                                print(f"   > Registro com mesmo externalId já existe (ID={result[0]}), atualizando em vez de inserir")
                                set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                                cursor.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", list(row.values()) + [result[0]])
                                updated += 1
                            else:
                                errors += 1
                        else:
                            raise e
                
                conn.commit()  # Commit após cada operação para evitar bloqueios longos
                
            except Exception as e:
                print(f"Erro ao processar cliente {customer.get('id')}: {e}")
                errors += 1
                conn.rollback()
                
        print(f"\nResumo: {inserted} inseridos, {updated} atualizados, {skipped} pulados, {errors} erros")
        
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
