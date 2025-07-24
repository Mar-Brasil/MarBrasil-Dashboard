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

def create_keywords_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("Criando tabela 'keywords'...")
        cursor.execute('''CREATE TABLE keywords (id INTEGER PRIMARY KEY)''')
        conn.commit()
        print("Tabela 'keywords' criada com sucesso!")
    conn.close()

def get_keywords(token, base_url):
    url = f"{base_url}/keywords"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_keywords = []
    page = 1
    page_size = 100
    total_keywords = 0
    
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
                print(f"Erro ao buscar palavras-chave: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
            
            keywords = data["result"]
            keywords_count = len(keywords)
            total_keywords += keywords_count
            all_keywords.extend(keywords)
            
            print(f"Encontradas {keywords_count} palavras-chave na página {page}")
            
            if keywords_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar palavras-chave: {e}")
    
    print(f"Total de palavras-chave encontradas: {total_keywords}")
    return all_keywords

def save_keywords_to_db(keywords):
    keywords = [k for k in keywords if isinstance(k, dict)]
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for keyword in keywords:
            keyword_id = keyword.get("id")
            if keyword_id is None:
                continue
            # Atualiza schema dinamicamente
            cursor.execute("PRAGMA table_info(keywords)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            for key in keyword.keys():
                if key not in existing_columns:
                    print(f"Adicionando coluna '{key}' à tabela 'keywords'...")
                    cursor.execute(f"ALTER TABLE keywords ADD COLUMN {key} TEXT")
                    conn.commit()
            # Prepara linha para salvar
            row = {}
            for key, value in keyword.items():
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            fields = ', '.join(row.keys())
            placeholders = ', '.join(['?'] * len(row))
            values = list(row.values())
            cursor.execute("SELECT id FROM keywords WHERE id = ?", (keyword_id,))
            existing = cursor.fetchone()
            if existing:
                set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                cursor.execute(f"UPDATE keywords SET {set_clause} WHERE id = ?", values + [keyword_id])
                updated += 1
            else:
                cursor.execute(f"INSERT INTO keywords ({fields}) VALUES ({placeholders})", values)
                inserted += 1
        conn.commit()
        print(f"Palavras-chave inseridas: {inserted}, atualizadas: {updated}")
    except Exception as e:
        print(f"Erro ao salvar palavras-chave no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE PALAVRAS-CHAVE ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela keywords se não existir
    create_keywords_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar palavras-chave
    keywords = get_keywords(token, base_url)
    
    # Salvar palavras-chave no banco de dados
    save_keywords_to_db(keywords)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de palavras-chave processadas: {len(keywords)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
