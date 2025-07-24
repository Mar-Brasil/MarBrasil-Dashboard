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

def create_questionnaires_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questionnaires'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'questionnaires'...")
        cursor.execute('''
        CREATE TABLE questionnaires (
            id INTEGER PRIMARY KEY,
            description TEXT,
            header TEXT,
            footer TEXT,
            creationDate TEXT,
            questions TEXT
        )
        ''')
        conn.commit()
        print("Tabela 'questionnaires' criada com sucesso!")
    else:
        print("Tabela 'questionnaires' já existe.")
    
    conn.close()

def get_questionnaires(token, base_url):
    url = f"{base_url}/questionnaires"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_questionnaires = []
    page = 1
    page_size = 100
    total_questionnaires = 0
    
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
                print(f"Erro ao buscar questionários: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
            
            questionnaires = data["result"]
            print(f"[DEBUG] Lista bruta de questionários recebida: {questionnaires}")
            questionnaires_count = len(questionnaires)
            total_questionnaires += questionnaires_count
            
            # Filtrar apenas dicionários para evitar erro de 'str' object has no attribute 'get'
            questionnaires = [q for q in questionnaires if isinstance(q, dict)]
            print(f"[DEBUG] Lista de questionários após filtro dict: {questionnaires}")
            # Para cada questionário na lista, buscar detalhes completos
            for questionnaire in questionnaires:
                questionnaire_id = questionnaire.get("id")
                print(f"[DEBUG] Processando questionário id={questionnaire_id}")
                if questionnaire_id:
                    all_questionnaires.append(questionnaire)
                else:
                    print(f"[DEBUG] Questionário sem id válido: {questionnaire}")
            
            print(f"Encontrados {questionnaires_count} questionários na página {page}")
            
            if questionnaires_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar questionários: {e}")
    
    print(f"Total de questionários encontrados: {total_questionnaires}")
    return all_questionnaires

def get_questionnaire_detail(token, base_url, questionnaire_id):
    url = f"{base_url}/questionnaires/{questionnaire_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro ao buscar detalhes do questionário {questionnaire_id}: {response.status_code}")
            return None
        
        data = response.json()
        print(f"[DEBUG] Detalhe do questionário {questionnaire_id}: {data}")
        if "result" in data:
            return data["result"]
        elif isinstance(data, dict) and "id" in data:
            return data
        else:
            return None
    
    except Exception as e:
        print(f"Erro ao buscar detalhes do questionário {questionnaire_id}: {e}")
        return None

def save_questionnaires_to_db(questionnaires):
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for questionnaire in questionnaires:
            # Garante que é um dicionário
            if not isinstance(questionnaire, dict):
                continue
            questionnaire_id = questionnaire.get("id")
            if not questionnaire_id:
                continue

            # Detectar e criar colunas automaticamente
            cursor.execute("PRAGMA table_info(questionnaires)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            for key in questionnaire.keys():
                if key not in existing_columns:
                    print(f"Adicionando coluna '{key}' na tabela 'questionnaires'...")
                    cursor.execute(f"ALTER TABLE questionnaires ADD COLUMN {key} TEXT")
                    conn.commit()

            # Serializar valores não primitivos
            row = {}
            for key, value in questionnaire.items():
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value

            # Montar listas de campos e valores
            fields = ', '.join(row.keys())
            placeholders = ', '.join(['?'] * len(row))
            values = list(row.values())

            # Verificar se já existe
            cursor.execute("SELECT id FROM questionnaires WHERE id = ?", (questionnaire_id,))
            existing = cursor.fetchone()
            if existing:
                # UPDATE
                set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                cursor.execute(f"UPDATE questionnaires SET {set_clause} WHERE id = ?", values + [questionnaire_id])
                updated += 1
            else:
                # INSERT
                cursor.execute(f"INSERT INTO questionnaires ({fields}) VALUES ({placeholders})", values)
                inserted += 1
        conn.commit()
        print(f"Questionários inseridos: {inserted}, atualizados: {updated}")
    except Exception as e:
        print(f"Erro ao salvar questionários no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    print("=== DOWNLOAD DE QUESTIONÁRIOS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela questionnaires se não existir
    create_questionnaires_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar questionários
    questionnaires = get_questionnaires(token, base_url)
    
    # Salvar questionários no banco de dados
    save_questionnaires_to_db(questionnaires)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de questionários processados: {len(questionnaires)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
