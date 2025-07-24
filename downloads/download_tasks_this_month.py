import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

def create_tasks_table(conn):
    """Cria a tabela de tarefas se não existir"""
    cursor = conn.cursor()
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

def get_tasks(token, base_url, start_date, end_date, user_id=None):
    """Busca tarefas da API Auvo com filtros opcionais"""
    url = f"{base_url}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Construir filtro - usando formato de data simples YYYY-MM-DD
    param_filter = {
        "taskDateFrom": start_date,
        "taskDateTo": end_date
    }
    
    # Adicionar filtro de usuário se especificado
    if user_id:
        param_filter["idUserTo"] = user_id
    
    # Converter filtro para JSON
    filter_json = json.dumps(param_filter)
    
    all_tasks = []
    page = 1
    page_size = 50  # Tamanho menor para evitar timeout
    
    print(f"\nBuscando tarefas da API Auvo...")
    print(f"Período: {start_date} a {end_date}")
    print(f"Filtro JSON: {filter_json}")
    if user_id:
        print(f"Usuário: {user_id}")
    
    try:
        while True:
            print(f"Buscando página {page}...")
            
            # Tentar abordagem alternativa para o filtro
            params = {
                "Page": page,
                "PageSize": page_size,
                "filter": filter_json
            }
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"Erro ao buscar tarefas: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            # Verificar o formato da resposta
            tasks = []
            if "result" in data:
                if isinstance(data["result"], list):
                    tasks = data["result"]
                elif isinstance(data["result"], dict) and "entityList" in data["result"]:
                    tasks = data["result"]["entityList"]
            elif "entityList" in data:
                tasks = data["entityList"]
            
            if not tasks:
                print(f"Nenhuma tarefa encontrada na página {page} ou formato de resposta desconhecido.")
                print(f"Resposta: {json.dumps(data)[:200]}...")
                break
            
            # Filtrar apenas as tarefas válidas (dicionários)
            valid_tasks = [task for task in tasks if isinstance(task, dict)]
            all_tasks.extend(valid_tasks)
            
            print(f"Encontradas {len(valid_tasks)} tarefas na página {page}")
            
            # Verificar se há mais páginas
            if len(tasks) < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar tarefas: {e}")
    
    return all_tasks

def save_tasks_to_db(tasks, db_path):
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
                
                # Verificar se a tarefa já existe
                cursor.execute("SELECT taskID FROM tasks WHERE taskID = ?", (task_id,))
                existing_task = cursor.fetchone()
                
                # Extrair dados complexos
                attachments = json.dumps(task.get("attachments", [])) if isinstance(task.get("attachments"), list) else ""
                questionnaires = json.dumps(task.get("questionnaires", [])) if isinstance(task.get("questionnaires"), list) else ""
                survey = json.dumps(task.get("survey", {})) if isinstance(task.get("survey"), dict) else ""
                pendency = json.dumps(task.get("pendency", {})) if isinstance(task.get("pendency"), dict) else ""
                equipments_id = json.dumps(task.get("equipmentsId", [])) if isinstance(task.get("equipmentsId"), list) else ""
                expense = json.dumps(task.get("expense", {})) if isinstance(task.get("expense"), dict) else ""
                products = json.dumps(task.get("products", [])) if isinstance(task.get("products"), list) else ""
                services = json.dumps(task.get("services", [])) if isinstance(task.get("services"), list) else ""
                additional_costs = json.dumps(task.get("additionalCosts", [])) if isinstance(task.get("additionalCosts"), list) else ""
                summary = json.dumps(task.get("summary", {})) if isinstance(task.get("summary"), dict) else ""
                
                # Preparar os dados para inserção/atualização
                task_data = (
                    task_id,
                    task.get("idUserFrom", 0),
                    task.get("userFromName", ""),
                    task.get("idUserTo", 0),
                    task.get("userToName", ""),
                    task.get("customerId", 0),
                    task.get("customerDescription", ""),
                    task.get("taskType", 0),
                    task.get("creationDate", ""),
                    task.get("taskDate", ""),
                    task.get("latitude", 0.0),
                    task.get("longitude", 0.0),
                    task.get("address", ""),
                    task.get("orientation", ""),
                    task.get("priority", 0),
                    1 if task.get("deliveredOnSmarthPhone", False) else 0,
                    task.get("deliveredDate", ""),
                    1 if task.get("finished", False) else 0,
                    task.get("report", ""),
                    1 if task.get("visualized", False) else 0,
                    task.get("visualizedDate", ""),
                    1 if task.get("checkIn", False) else 0,
                    task.get("checkInDate", ""),
                    1 if task.get("checkOut", False) else 0,
                    task.get("checkOutDate", ""),
                    task.get("checkinType", 0),
                    task.get("keyWords", ""),
                    task.get("keyWordsDescriptions", ""),
                    task.get("inputedKm", 0.0),
                    task.get("adoptedKm", 0.0),
                    attachments,
                    questionnaires,
                    task.get("signatureUrl", ""),
                    task.get("checkInDistance", 0.0),
                    task.get("checkOutDistance", 0.0),
                    1 if task.get("sendSatisfactionSurvey", False) else 0,
                    survey,
                    task.get("taskUrl", ""),
                    pendency,
                    equipments_id,
                    task.get("dateLastUpdate", ""),
                    task.get("ticketId", 0),
                    expense,
                    task.get("duration", ""),
                    task.get("durationDecimal", ""),
                    task.get("displacementStart", ""),
                    products,
                    services,
                    additional_costs,
                    summary,
                    1 if task.get("openedOnLocation", False) else 0,
                    task.get("taskStatus", 0),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                if existing_task:
                    # Atualizar tarefa existente
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
                        taskStatus = ?, lastUpdate = ?
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
                        summary, openedOnLocation, taskStatus, lastUpdate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def get_current_month_dates():
    """Retorna as datas de início e fim do mês atual no formato esperado pela API"""
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

def main():
    """Função principal"""
    print("=== DOWNLOAD DE TAREFAS DO MÊS ATUAL DA API AUVO ===")
    
    # Configurações
    db_path = "auvo.db"
    
    # Login na API Auvo
    token, base_url = login_to_auvo()
    
    # Obter datas do mês atual
    start_date, end_date = get_current_month_dates()
    
    # Buscar tarefas para todos os usuários no mês atual
    tasks = get_tasks(token, base_url, start_date, end_date)
    
    if not tasks:
        print("Nenhuma tarefa encontrada para o mês atual.")
        sys.exit(1)
    
    print(f"\nForam encontradas {len(tasks)} tarefas na API Auvo para o mês atual.")
    
    # Salvar tarefas no banco de dados
    inserted, updated = save_tasks_to_db(tasks, db_path)
    
    print(f"\nOperação concluída!")
    print(f"Tarefas inseridas: {inserted}")
    print(f"Tarefas atualizadas: {updated}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
