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

def create_task_types_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_types'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'task_types'...")
        cursor.execute('''
        CREATE TABLE task_types (
            id INTEGER PRIMARY KEY,
            description TEXT,
            creationDate TEXT,
            dateLastUpdate TEXT,
            active INTEGER,
            externalId TEXT,
            color TEXT,
            requirements TEXT,
            sendSatisfactionSurvey INTEGER,
            standartQuestionnaireId INTEGER,
            standartTime TEXT,
            toleranceTime TEXT,
            creatorId INTEGER
        )
        ''')
        conn.commit()
        print("Tabela 'task_types' criada com sucesso!")
    else:
        # Adiciona colunas que possam faltar
        cursor.execute("PRAGMA table_info(task_types)")
        columns = [col[1] for col in cursor.fetchall()]
        required_columns = [
            ("dateLastUpdate", "TEXT"),
            ("externalId", "TEXT"),
            ("color", "TEXT"),
            ("requirements", "TEXT"),
            ("sendSatisfactionSurvey", "INTEGER"),
            ("standartQuestionnaireId", "INTEGER"),
            ("standartTime", "TEXT"),
            ("toleranceTime", "TEXT"),
            ("creatorId", "INTEGER")
        ]
        for col_name, col_type in required_columns:
            if col_name not in columns:
                print(f"Adicionando coluna '{col_name}' na tabela 'task_types'...")
                cursor.execute(f"ALTER TABLE task_types ADD COLUMN {col_name} {col_type}")
                conn.commit()
    
    conn.close()

def get_task_types(token, base_url):
    url = f"{base_url}/taskTypes"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_task_types = []
    page = 1
    page_size = 100
    total_task_types = 0
    
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
                print(f"Erro ao buscar tipos de tarefas: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
            
            print("[DEBUG] Estrutura de data['result']:", data["result"])
            result = data["result"]
            # Se result for dict e tiver 'entityList', use ela
            if isinstance(result, dict) and "entityList" in result:
                task_types = result["entityList"]
            else:
                task_types = result if isinstance(result, list) else []
            task_types_count = len(task_types)
            total_task_types += task_types_count
            all_task_types.extend(task_types)
            
            print(f"Encontrados {task_types_count} tipos de tarefas na página {page}")
            
            if task_types_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar tipos de tarefas: {e}")
    
    print(f"Total de tipos de tarefas encontrados: {total_task_types}")
    return all_task_types

def get_task_type_detail(token, base_url, task_type_id):
    url = f"{base_url}/taskTypes/{task_type_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                return data["result"]
        else:
            print(f"Erro ao buscar detalhe do tipo de tarefa {task_type_id}: {response.status_code}")
    except Exception as e:
        print(f"Erro ao buscar detalhe do tipo de tarefa {task_type_id}: {e}")
    return None


def save_task_types_to_db(task_types):
    # Filtrar apenas dicionários para evitar erro de 'str' object has no attribute 'get'
    task_types = [t for t in task_types if isinstance(t, dict)]
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    try:
        for task_type in task_types:
            task_type_id = task_type.get("id")
            
            # Verificar se o tipo de tarefa já existe
            cursor.execute("SELECT id FROM task_types WHERE id = ?", (task_type_id,))
            existing_task_type = cursor.fetchone()
            
            # Preparar os dados para inserção/atualização
            task_type_data = (
                task_type_id,
                task_type.get("description", ""),
                task_type.get("creationDate", ""),
                task_type.get("dateLastUpdate", ""),
                1 if task_type.get("active", False) else 0,
                task_type.get("externalId", ""),
                task_type.get("color", ""),
                json.dumps(task_type.get("requirements", {})),
                1 if task_type.get("sendSatisfactionSurvey", False) else 0,
                task_type.get("standartQuestionnaireId", None),
                task_type.get("standartTime", ""),
                task_type.get("toleranceTime", ""),
                task_type.get("creatorId", None)
            )
            
            if existing_task_type:
                # Atualizar tipo de tarefa existente
                cursor.execute('''
                UPDATE task_types
                SET description = ?, creationDate = ?, dateLastUpdate = ?, active = ?, externalId = ?, color = ?, requirements = ?, sendSatisfactionSurvey = ?, standartQuestionnaireId = ?, standartTime = ?, toleranceTime = ?, creatorId = ?
                WHERE id = ?
                ''', (task_type_data[1], task_type_data[2], task_type_data[3], task_type_data[4], task_type_data[5], task_type_data[6], task_type_data[7], task_type_data[8], task_type_data[9], task_type_data[10], task_type_data[11], task_type_id))
                updated += 1
            else:
                # Inserir novo tipo de tarefa
                cursor.execute('''
                INSERT INTO task_types (id, description, creationDate, dateLastUpdate, active, externalId, color, requirements, sendSatisfactionSurvey, standartQuestionnaireId, standartTime, toleranceTime, creatorId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', task_type_data)
                inserted += 1
        
        conn.commit()
        print(f"Tipos de tarefas inseridos: {inserted}, atualizados: {updated}")
    
    except Exception as e:
        print(f"Erro ao salvar tipos de tarefas no banco de dados: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE TIPOS DE TAREFAS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela task_types se não existir
    create_task_types_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar tipos de tarefas (lista resumida)
    task_types_basic = get_task_types(token, base_url)
    
    # Buscar detalhes completos de cada tipo de tarefa
    task_types = []
    for t in task_types_basic:
        if not isinstance(t, dict):
            print(f"[WARN] Tipo inesperado na lista de task_types: {t}")
            continue
        task_type_id = t.get("id")
        if task_type_id:
            detail = get_task_type_detail(token, base_url, task_type_id)
            if detail:
                task_types.append(detail)
            else:
                print(f"[WARN] Não foi possível obter detalhes do tipo de tarefa id={task_type_id}")
        else:
            print(f"[WARN] Tipo de tarefa sem id: {t}")
    
    # Salvar tipos de tarefas detalhados no banco de dados
    save_task_types_to_db(task_types)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de tipos de tarefas processados: {len(task_types)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
