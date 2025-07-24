import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

def login_to_auvo():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    try:
        response = requests.get(login_url)
        data = response.json()
        if "result" in data and data["result"].get("authenticated"):
            token = data["result"]["accessToken"]
            return token, base_url
        else:
            print("Falha na autenticação!")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        sys.exit(1)

def create_customer_groups_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_groups'")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("Criando tabela 'customer_groups'...")
        cursor.execute('''CREATE TABLE customer_groups (
            id INTEGER PRIMARY KEY,
            description TEXT
        )''')
        conn.commit()
        print("Tabela 'customer_groups' criada com sucesso!")
    conn.close()

def get_customer_groups(token, base_url):
    url = f"{base_url}/customerGroups/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    all_groups = []
    page = 1
    page_size = 100
    try:
        while True:
            params = {
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }
            print(f"Buscando grupos página {page}...")
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Erro ao buscar grupos: {response.status_code}")
                print(response.text)
                break
            data = response.json()
            # Tratar diferentes formatos de resposta
            entity_list = []
            if isinstance(data, dict):
                entity_list = data.get("result", [])
            elif isinstance(data, list):
                entity_list = data
            else:
                print("Resposta inesperada da API:", data)
            count = len(entity_list)
            all_groups.extend(entity_list)
            print(f"Encontrados {count} grupos na página {page}")
            if count < page_size:
                break
            page += 1
    except Exception as e:
        print(f"Erro ao buscar grupos: {e}")
        try:
            print("Resposta bruta da API:", response.text)
        except:
            pass
    print(f"Total de grupos encontrados: {len(all_groups)}")
    return all_groups

def save_customer_groups_to_db(groups):
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for group in groups:
            group_id = group.get("id")
            if not group_id:
                continue
            cursor.execute("SELECT id FROM customer_groups WHERE id = ?", (group_id,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("UPDATE customer_groups SET description = ? WHERE id = ?", (group.get("description"), group_id))
                updated += 1
                print(f"Atualizado grupo {group_id} ({group.get('description', '')})")
            else:
                cursor.execute("INSERT INTO customer_groups (id, description) VALUES (?, ?)", (group_id, group.get("description")))
                inserted += 1
                print(f"Inserido grupo {group_id} ({group.get('description', '')})")
        conn.commit()
        print(f"Grupos inseridos: {inserted}, atualizados: {updated}")
    except Exception as e:
        print(f"Erro ao salvar grupos no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE GRUPOS DE CLIENTES ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    create_customer_groups_table()
    token, base_url = login_to_auvo()
    groups = get_customer_groups(token, base_url)
    save_customer_groups_to_db(groups)
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de grupos processados: {len(groups)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
