import os
import sys
import json
import time
import sqlite3
import requests
from datetime import datetime
from calendar import monthrange
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def login_to_auvo():
    """Faz login na API Auvo e retorna o token de acesso e a URL base."""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL", "https://api.auvo.com.br/v2")
    
    if not api_key or not api_token:
        print("Erro: Credenciais da API (API_KEY, API_TOKEN) não encontradas no arquivo .env!")
        sys.exit(1)

    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    try:
        response = requests.get(login_url)
        response.raise_for_status()
        data = response.json()
        if data.get("result", {}).get("authenticated"):
            token = data["result"]["accessToken"] # Corrigido de "token" para "accessToken"
            print("Login na API Auvo bem-sucedido.")
            return token, base_url
        else:
            print(f"Falha no login: {data.get('error')}")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"Erro de conexão ao tentar fazer login: {e}")
        sys.exit(1)

def get_all_users_from_db(db_path):
    """Obtém todos os IDs e nomes de usuários do banco de dados.
"""
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados '{db_path}' não encontrado.")
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT userId, name FROM users") # Corrigido de 'id, nome' para 'userId, name'
    users = cursor.fetchall()
    conn.close()
    print(f"Encontrados {len(users)} usuários no banco de dados local.")
    return users

def get_current_month_dates():
    """Retorna as datas de início e fim do mês atual no formato YYYY-MM-DD."""
    today = datetime.today()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    _, last_day = monthrange(today.year, today.month)
    end_date = today.replace(day=last_day).strftime('%Y-%m-%d')
    return start_date, end_date

def get_all_task_ids_from_auvo(token, base_url, users, start_date, end_date):
    """Busca todos os IDs de tarefas na API da Auvo para um determinado período, usando o endpoint correto com paginação."""
    # Cabeçalho correto, incluindo x-api-key, como no script de download que funciona
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": os.getenv("API_KEY"),
        "Content-Type": "application/json"
    }
    api_task_ids = set()
    url = f"{base_url}/tasks"

    for user_id, user_name in users:
        print(f"Buscando tarefas na API para {user_name} (ID: {user_id})...")
        page = 1
        user_tasks_found_count = 0 # Contador para tarefas por usuário

        while True:
            params = {
                "paramFilter": json.dumps({
                    "idUserTo": user_id,
                    "startDate": start_date + "T00:00:00",
                    "endDate": end_date + "T23:59:59"
                }),
                "page": page,
                "pageSize": 50
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 404:
                    # Nenhuma tarefa encontrada para este usuário, ir para o próximo
                    break 

                response.raise_for_status()
                data = response.json()

                # Lógica de extração de tarefas robusta, como no script de download
                tasks = []
                if "result" in data:
                    if isinstance(data["result"], list):
                        tasks = data["result"]
                    elif isinstance(data["result"], dict) and "entityList" in data["result"]:
                        tasks = data["result"]["entityList"]
                elif "entityList" in data:
                    tasks = data["entityList"]

                if not tasks:
                    break  # Sai do loop se não houver mais tarefas nesta página

                # Filtra tarefas válidas e adiciona seus IDs
                valid_tasks = [task for task in tasks if isinstance(task, dict) and 'taskID' in task]
                for task in valid_tasks:
                    api_task_ids.add(task['taskID'])
                
                user_tasks_found_count += len(valid_tasks)

                if len(tasks) < 50:
                    break  # Última página para este usuário
                
                page += 1
                time.sleep(0.2) 

            except requests.exceptions.HTTPError as http_err:
                print(f"    -> Erro HTTP: {http_err}")
                break  # Interrompe o processamento para este usuário em caso de erro
            except Exception as e:
                print(f"    -> Erro inesperado: {e}")
                break # Interrompe o processamento para este usuário em caso de erro
        
        if user_tasks_found_count > 0:
            print(f"    -> Encontradas {user_tasks_found_count} tarefas para {user_name}.")

    return api_task_ids

def get_local_db_task_ids_for_month(db_path, start_date, end_date):
    """Busca no DB local todos os taskIDs do mês atual."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT taskID FROM tasks WHERE taskDate BETWEEN ? AND ?"
    cursor.execute(query, (start_date, end_date))
    local_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return local_ids

def main():
    """Função principal para sincronizar e limpar tarefas."""
    print("--- INICIANDO SCRIPT DE LIMPEZA DE TAREFAS ---")
    # Aponta para o banco de dados na pasta raiz do projeto
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auvo.db'))
    
    # 1. Login e obtenção de dados básicos
    token, base_url = login_to_auvo()
    users = get_all_users_from_db(db_path)
    start_date, end_date = get_current_month_dates()
    print(f"Período de análise: {start_date} a {end_date}")

    # 2. Buscar IDs da API e do Banco Local
    print("\n--- Etapa 1: Coletando todos os IDs de tarefas da API Auvo ---")
    api_task_ids = get_all_task_ids_from_auvo(token, base_url, users, start_date, end_date)
    print(f"\nTotal de tarefas existentes na API para o mês: {len(api_task_ids)}")

    print("\n--- Etapa 2: Coletando todos os IDs de tarefas do banco de dados local ---")
    local_task_ids = get_local_db_task_ids_for_month(db_path, start_date, end_date)
    print(f"Total de tarefas no banco local para o mês: {len(local_task_ids)}")
    
    # 3. Comparar e encontrar tarefas a serem removidas
    tasks_to_delete = local_task_ids - api_task_ids
    
    if not tasks_to_delete:
        print("\n--- RESULTADO ---")
        print("✅ O banco de dados já está sincronizado. Nenhuma tarefa a ser removida.")
        return

    print(f"\n--- Etapa 3: Removendo {len(tasks_to_delete)} tarefas inexistentes ---")
    
    # 4. Executar a limpeza
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Usar uma lista de tuplas para o executemany
    tasks_to_delete_tuples = [(task_id,) for task_id in tasks_to_delete]
    
    cursor.executemany("DELETE FROM tasks WHERE taskID = ?", tasks_to_delete_tuples)
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print("\n--- RESULTADO ---")
    print(f"✅ Limpeza concluída. {deleted_count} tarefas foram removidas do banco de dados.")

if __name__ == "__main__":
    main()
