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

def create_services_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'services'...")
        cursor.execute('''
        CREATE TABLE services (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            price REAL,
            active INTEGER,
            creationDate TEXT,
            dateLastUpdate TEXT,
            fiscalServiceId TEXT,
            externalId TEXT
        )
        ''')
        conn.commit()
        print("Tabela 'services' criada com sucesso!")
    else:
        print("Tabela 'services' já existe.")
    
    conn.close()

def get_services(token, base_url):
    url = f"{base_url}/services"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_services = []
    page = 1
    page_size = 100
    total_services = 0
    
    try:
        while True:
            params = {
                "paramFilter": json.dumps({}),  # Filtro vazio para trazer todos
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }
            
            print(f"Buscando página {page}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Erro ao buscar serviços: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
            
            services = data["result"]
            services_count = len(services)
            total_services += services_count
            all_services.extend(services)
            
            print(f"Encontrados {services_count} serviços na página {page}")
            
            if services_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar serviços: {e}")
    
    print(f"Total de serviços encontrados: {total_services}")
    return all_services

def save_services_to_db(services):
    # Filtrar apenas dicionários para evitar erro de 'str' object has no attribute 'get'
    services = [s for s in services if isinstance(s, dict)]
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    try:
        for service in services:
            service_id = service.get("id")
            
            # Verificar se o serviço já existe
            cursor.execute("SELECT id FROM services WHERE id = ?", (service_id,))
            existing_service = cursor.fetchone()
            
            # Preparar os dados para inserção/atualização
            service_data = (
                service_id,
                service.get("title", ""),
                service.get("description", ""),
                service.get("price", 0.0),
                1 if service.get("active", False) else 0,
                service.get("creationDate", ""),
                service.get("dateLastUpdate", ""),
                service.get("fiscalServiceId", ""),
                service.get("externalId", "")
            )
            
            if existing_service:
                # Atualizar serviço existente
                cursor.execute('''
                UPDATE services
                SET title = ?, description = ?, price = ?, active = ?, 
                    creationDate = ?, dateLastUpdate = ?, fiscalServiceId = ?, externalId = ?
                WHERE id = ?
                ''', (service_data[1], service_data[2], service_data[3], service_data[4], 
                      service_data[5], service_data[6], service_data[7], service_data[8], service_id))
                updated += 1
            else:
                # Inserir novo serviço
                cursor.execute('''
                INSERT INTO services (id, title, description, price, active, 
                                     creationDate, dateLastUpdate, fiscalServiceId, externalId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', service_data)
                inserted += 1
        
        conn.commit()
        print(f"Serviços inseridos: {inserted}, atualizados: {updated}")
    
    except Exception as e:
        print(f"Erro ao salvar serviços no banco de dados: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE SERVIÇOS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela services se não existir
    create_services_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar serviços
    services = get_services(token, base_url)
    
    # Salvar serviços no banco de dados
    save_services_to_db(services)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de serviços processados: {len(services)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
