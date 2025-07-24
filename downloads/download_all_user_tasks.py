import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

def create_tasks_table(conn):
    """Cria a tabela de tarefas se não existir"""
    cursor = conn.cursor()
    
    # Primeiro, verificamos se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Se a tabela existe, verificamos se as colunas necessárias existem
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Verificar e adicionar colunas que podem estar faltando
        missing_columns = [
            ('openedOnLocation', 'INTEGER'),
            ('lastUpdate', 'TEXT'),
            ('taskStatus', 'INTEGER'),
            ('signatureUrl', 'TEXT'),
            ('signatureName', 'TEXT'),
            ('signatureDocument', 'TEXT')
        ]
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                print(f"Adicionando coluna '{col_name}' à tabela tasks...")
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                    print(f"Coluna '{col_name}' adicionada com sucesso!")
                except sqlite3.OperationalError as e:
                    print(f"Erro ao adicionar coluna {col_name}: {e}")
    else:
        # Se a tabela não existe, criamos ela com todas as colunas necessárias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            taskID INTEGER PRIMARY KEY,
            idUserFrom INTEGER,
            userFromName TEXT,
            idUserTo INTEGER,
            userToName TEXT,
            customerId INTEGER,
            customerDescription TEXT,
            taskType INTEGER,
            creationDate TEXT,
            taskDate TEXT,
            latitude REAL,
            longitude REAL,
            address TEXT,
            orientation TEXT,
            priority INTEGER,
            deliveredOnSmarthPhone INTEGER,
            deliveredDate TEXT,
            finished INTEGER,
            report TEXT,
            visualized INTEGER,
            visualizedDate TEXT,
            checkIn INTEGER,
            checkInDate TEXT,
            checkOut INTEGER,
            checkOutDate TEXT,
            checkinType INTEGER,
            keyWords TEXT,
            keyWordsDescriptions TEXT,
            inputedKm REAL,
            adoptedKm REAL,
            attachments TEXT,
            questionnaires TEXT,
            signatureUrl TEXT,
            checkInDistance REAL,
            checkOutDistance REAL,
            sendSatisfactionSurvey INTEGER,
            survey TEXT,
            taskUrl TEXT,
            pendency TEXT,
            equipmentsId TEXT,
            dateLastUpdate TEXT,
            ticketId INTEGER,
            expense TEXT,
            duration TEXT,
            durationDecimal TEXT,
            displacementStart TEXT,
            products TEXT,
            services TEXT,
            additionalCosts TEXT,
            summary TEXT,
            openedOnLocation INTEGER,
            taskStatus INTEGER,
            lastUpdate TEXT
        )
        """)
        print("Tabela 'tasks' criada com sucesso!")
    
    conn.commit()

def login_to_auvo():
    """Faz login na API Auvo e retorna o token de acesso"""
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

def get_all_users_from_db(db_path):
    """Obtém todos os IDs de usuários do banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Buscar todos os usuários, independentemente do status de ativo
        cursor.execute("SELECT userId, name FROM users")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("Nenhum usuário encontrado no banco de dados!")
            sys.exit(1)
            
        print(f"Encontrados {len(users)} usuários no banco de dados.")
        return users
    except Exception as e:
        print(f"Erro ao obter usuários do banco de dados: {e}")
        sys.exit(1)

def get_current_month_dates():
    """Retorna as datas de início e fim do mês atual"""
    today = datetime.now()
    first_day = today.replace(day=1).strftime("%Y-%m-%d")
    
    # Calcular o último dia do mês atual
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    last_day = last_day.strftime("%Y-%m-%d")
    
    print(f"Período do mês atual: {first_day} até {last_day}")
    
    return first_day, last_day

# Removendo a função try_alternative_date_formats pois agora usamos a abordagem que sabemos que funciona

def get_tasks_for_user(token, base_url, user_id, user_name, start_date, end_date):
    """Busca tarefas da API Auvo para um usuário específico com lógica de busca robusta."""
    url = f"{base_url}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": os.getenv("API_KEY"),
        "Content-Type": "application/json"
    }
    
    all_tasks = []
    page = 1
    
    print(f"\nBuscando tarefas para o usuário {user_name} (ID: {user_id})...")
    
    while True:
        params = {
            "paramFilter": json.dumps({
                "idUserTo": user_id,
                "startDate": f"{start_date}T00:00:00",
                "endDate": f"{end_date}T23:59:59"
            }),
            "page": page,
            "pageSize": 50
        }
        
        try:
            print(f"Buscando página {page}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                break
            
            response.raise_for_status()
            data = response.json()
            
            tasks = []
            if "result" in data:
                if isinstance(data["result"], list):
                    tasks = data["result"]
                elif isinstance(data["result"], dict) and "entityList" in data["result"]:
                    tasks = data["result"]["entityList"]
            elif "entityList" in data:
                tasks = data["entityList"]
            
            if not tasks:
                break
            
            valid_tasks = [task for task in tasks if isinstance(task, dict)]
            all_tasks.extend(valid_tasks)
            
            print(f"Encontradas {len(valid_tasks)} tarefas na página {page}")
            
            if len(tasks) < 50:
                break
            
            page += 1
            time.sleep(0.2)
        
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code != 404:
                print(f"    -> Erro HTTP ao buscar tarefas para {user_name}: {http_err}")
            break
        except Exception as e:
            print(f"    -> Erro inesperado ao buscar tarefas para {user_name}: {e}")
            break
    
    if not all_tasks:
        print(f"Nenhuma tarefa encontrada para o usuário {user_name}")

    return all_tasks

    """Salva as tarefas no banco de dados SQLite"""
    if not tasks:
        print("Nenhuma tarefa para salvar no banco de dados.")
        return 0, 0
    
    try:
        conn = sqlite3.connect(db_path)
        create_tasks_table(conn)
        cursor = conn.cursor()
        
        inserted_count = 0
        updated_count = 0
        
        for task in tasks:
            try:
                # Normalizar as chaves da tarefa
                task_id = task.get("taskID") or task.get("id")
                
                if not task_id:
                    print(f"Pulando tarefa sem ID: {task}")
                    continue
                
                # ... (restante do código)
                
                # Preparar os dados para inserção/atualização
                task_data = (
                    task_id,  # 1
                    task.get("idUserFrom", 0),  # 2
                    task.get("userFromName", ""),  # 3
                    task.get("idUserTo", 0),  # 4
                    task.get("userToName", ""),  # 5
                    task.get("customerId", 0),  # 6
                    task.get("customerDescription", ""),  # 7
                    task.get("taskType", 0),  # 8
                    task.get("creationDate", ""),  # 9
                    task.get("taskDate", ""),  # 10
                    task.get("latitude", 0.0),  # 11
                    task.get("longitude", 0.0),  # 12
                    task.get("address", ""),  # 13
                    task.get("orientation", ""),  # 14
                    task.get("priority", 0),  # 15
                    task.get("deliveredOnSmarthPhone", 0),  # 16
                    task.get("deliveredDate", ""),  # 17
                    task.get("finished", 0),  # 18
                    task.get("report", ""),  # 19
                    task.get("visualized", 0),  # 20
                    task.get("visualizedDate", ""),  # 21
                    task.get("checkIn", 0),  # 22
                    task.get("checkInDate", ""),  # 23
                    task.get("checkOut", 0),  # 24
                    task.get("checkOutDate", ""),  # 25
                    task.get("checkinType", 0),  # 26
                    key_words,  # 27
                    key_words_descriptions,  # 28
                    task.get("inputedKm", 0.0),  # 29
                    task.get("adoptedKm", 0.0),  # 30
                    attachments,  # 31
                    questionnaires,  # 32
                    signature_url,  # 33
                    task.get("checkInDistance", 0.0),  # 34
                    task.get("checkOutDistance", 0.0),  # 35
                    task.get("sendSatisfactionSurvey", 0),  # 36
                    survey,  # 37
                    task.get("taskUrl", ""),  # 38
                    pendency,  # 39
                    equipments_id,  # 40
                    task.get("dateLastUpdate", ""),  # 41
                    task.get("ticketId", 0),  # 42
                    expense,  # 43
                    task.get("duration", ""),  # 44
                    task.get("durationDecimal", ""),  # 45
                    task.get("displacementStart", ""),  # 46
                    products,  # 47
                    services,  # 48
                    additional_costs,  # 49
                    summary,  # 50
                    task.get("openedOnLocation", 0),  # 51
                    task.get("taskStatus", 0),  # 52
                    task.get("lastUpdate", ""),  # 53
                    signature_name,  # 54
                    signature_document  # 55
                )

                if existing_task:
                    # A ordem das colunas no UPDATE deve corresponder à ordem no SELECT
                    # Atualizar todos os campos, incluindo assinatura
                    update_query = """
                        UPDATE tasks SET
                            idUserFrom = ?, userFromName = ?, idUserTo = ?, userToName = ?,
                            customerId = ?, customerDescription = ?, taskType = ?, creationDate = ?,
                            taskDate = ?, latitude = ?, longitude = ?, address = ?, orientation = ?,
                            priority = ?, deliveredOnSmarthPhone = ?, deliveredDate = ?, finished = ?,
                            report = ?, visualized = ?, visualizedDate = ?, checkIn = ?, checkInDate = ?,
                            checkOut = ?, checkOutDate = ?, checkinType = ?, keyWords = ?,
                            keyWordsDescriptions = ?, inputedKm = ?, adoptedKm = ?, attachments = ?,
                            questionnaires = ?, signatureUrl = ?, checkInDistance = ?, checkOutDistance = ?,
                            sendSatisfactionSurvey = ?, survey = ?, taskUrl = ?, pendency = ?,
                            equipmentsId = ?, dateLastUpdate = ?, ticketId = ?, expense = ?,
                            duration = ?, durationDecimal = ?, displacementStart = ?, products = ?,
                            services = ?, additionalCosts = ?, summary = ?, openedOnLocation = ?,
                            taskStatus = ?, lastUpdate = ?, signatureName = ?, signatureDocument = ?
                        WHERE taskID = ?
                    """
                    cursor.execute(update_query, task_data[1:] + (task_id,))
                    updated_count += 1
                else:
                    # Inserir nova tarefa
                    insert_query = """
                        INSERT INTO tasks (
                            taskID, idUserFrom, userFromName, idUserTo, userToName,
                            customerId, customerDescription, taskType, creationDate, taskDate,
                            latitude, longitude, address, orientation, priority,
                            deliveredOnSmarthPhone, deliveredDate, finished, report, visualized,
                            visualizedDate, checkIn, checkInDate, checkOut, checkOutDate,
                            checkinType, keyWords, keyWordsDescriptions, inputedKm, adoptedKm,
                            attachments, questionnaires, signatureUrl, checkInDistance, checkOutDistance,
                            sendSatisfactionSurvey, survey, taskUrl, pendency, equipmentsId,
                            dateLastUpdate, ticketId, expense, duration, durationDecimal,
                            displacementStart, products, services, additionalCosts,
                            summary, openedOnLocation, taskStatus, lastUpdate,
                            signatureName, signatureDocument
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, task_data)
                    inserted_count += 1
            
            except Exception as e:
                print(f"Erro ao processar tarefa {task.get('taskID', 'desconhecida')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count, updated_count
    
    except Exception as e:
        print(f"Erro ao salvar tarefas no banco de dados: {e}")
        return 0, 0

def main():
    """Função principal"""
    start_time = datetime.now()
    print("=== DOWNLOAD DE TAREFAS DE TODOS OS USUÁRIOS PARA O MÊS ATUAL ===")
    print(f"Iniciando em: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configurações
    # Aponta para o banco de dados na pasta raiz do projeto
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auvo.db'))
    
    # Login na API Auvo
    token, base_url = login_to_auvo()
    
    # Obter todos os usuários do banco de dados
    users = get_all_users_from_db(db_path)
    
    # Obter datas do mês atual
    start_date, end_date = get_current_month_dates()
    
    # Contadores
    total_tasks = 0
    total_inserted = 0
    total_updated = 0
    
    # Para cada usuário, buscar suas tarefas
    for user_id, user_name in users:
        # Buscar tarefas usando o formato de data correto
        tasks = get_tasks_for_user(token, base_url, user_id, user_name, start_date, end_date)
        
        if tasks:
            print(f"Encontradas {len(tasks)} tarefas para o usuário {user_name}")
            total_tasks += len(tasks)
            
            # Salvar tarefas no banco de dados
            inserted, updated = save_tasks_to_db(tasks, db_path)
            total_inserted += inserted
            total_updated += updated
            
            print(f"Tarefas inseridas: {inserted}, atualizadas: {updated}")
        else:
            print(f"Nenhuma tarefa encontrada para o usuário {user_name}")
        
        # Pequena pausa entre usuários para não sobrecarregar a API
        time.sleep(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {duration}")
    print(f"Total de usuários processados: {len(users)}")
    print(f"Total de tarefas encontradas: {total_tasks}")
    print(f"Total de tarefas inseridas: {total_inserted}")
    print(f"Total de tarefas atualizadas: {total_updated}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
