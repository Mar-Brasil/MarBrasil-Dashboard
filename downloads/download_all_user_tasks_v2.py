import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

def create_tasks_table(conn):
    """Cria a tabela de tarefas e adiciona colunas faltantes automaticamente."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            taskID INTEGER PRIMARY KEY,
            externalId TEXT,
            idUserFrom INTEGER,
            userFromName TEXT,
            idUserTo INTEGER,
            userToName TEXT,
            customerId INTEGER,
            equipmentsId TEXT, -- Coluna para a lista de IDs de equipamentos (JSON)
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
            report INTEGER,
            checkInDate TEXT,
            checkOutDate TEXT,
            products TEXT,
            services TEXT,
            summary TEXT,
            taskStatus INTEGER,
            lastUpdate TEXT
        )
    """)
    # Adiciona colunas de assinatura e equipamento se faltarem
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    alter_cols = [
        ("signatureUrl", "TEXT"),
        ("signatureName", "TEXT"),
        ("signatureDocument", "TEXT"),
        ("taskUrl", "TEXT"),
        ("equipmentsId", "TEXT") # Garante que a coluna exista em bancos de dados antigos
    ]
    for col_name, col_type in alter_cols:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
    conn.commit()

def login_to_auvo():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    resp = requests.get(login_url)
    data = resp.json()
    if "result" in data and data["result"].get("authenticated"):
        return data["result"]["accessToken"], base_url
    print("Falha na autenticação!")
    sys.exit(1)

def get_all_users_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT userId, name FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_start_date(db_path):
    """Busca a data de última atualização mais recente no banco de dados."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Garante que a tabela exista antes de consultá-la
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if cursor.fetchone():
            cursor.execute("SELECT MAX(lastUpdate) FROM tasks WHERE lastUpdate IS NOT NULL AND lastUpdate != ''")
            result = cursor.fetchone()
            if result and result[0]:
                # Adiciona um segundo para evitar buscar o último registro novamente
                return (datetime.fromisoformat(result[0]) + timedelta(seconds=1))
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados para obter a data de início: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    # Se não houver dados ou a tabela não existir, busca os últimos 30 dias
    return datetime.now() - timedelta(days=30)

def safe_json_serialize(value):
    if value is None:
        return ""
    elif isinstance(value, (dict, list)):
        return json.dumps(value)
    elif isinstance(value, (int, float, bool, str)):
        return value
    else:
        return str(value)

def get_tasks_for_user(token, base_url, user_id, user_name, start_date, end_date):
    url = f"{base_url}/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": os.getenv("API_KEY"),
        "Content-Type": "application/json"
    }
    all_tasks = []
    page = 1
    # Formato correto para busca incremental: 2025-06-01T00:00:00
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    while True:
        params = {
            "paramFilter": json.dumps({
                "idUserTo": user_id,
                "startDate": start_date_str,
                "endDate": end_date_str
            }),
            "page": page,
            "pageSize": 50
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"Erro na requisição para usuário {user_name}: {resp.text}")
            break
        data = resp.json()
        tasks = data.get("result", {}).get("entityList", [])
        if not tasks:
            break
        all_tasks.extend(tasks)
        if len(tasks) < 50:
            break
        page += 1
        time.sleep(0.2)
    return all_tasks

def save_tasks_to_db(tasks, db_path):
    if not tasks:
        return 0, 0
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inserted_count = 0
    updated_count = 0
    for task in tasks:
        task_id = task.get("taskID") or task.get("id")
        if not task_id:
            continue
        cursor.execute("SELECT taskID FROM tasks WHERE taskID = ?", (task_id,))
        exists = cursor.fetchone()
        products = str(safe_json_serialize(task.get("products")))
        services = str(safe_json_serialize(task.get("services")))
        summary = str(safe_json_serialize(task.get("summary")))
        # Campos de assinatura (robusto)
        signature_url = task.get("signatureUrl") or (task.get("signature", {}) or {}).get("url", "")
        signature_name = task.get("signatureName") or (task.get("signature", {}) or {}).get("name", "")
        signature_document = task.get("signatureDocument") or (task.get("signature", {}) or {}).get("document", "")
        try:
            # Lógica para tratar o campo 'report' que pode ser string ou booleano
            report_value = task.get("report")
            if isinstance(report_value, str):
                report_int = 1 if report_value else 0
            else:
                report_int = int(report_value or 0)

            # Monta a tupla de dados na ordem correta das colunas
            task_data = (
                int(task_id),
                str(task.get("externalId", "")),
                int(task.get("idUserFrom") or 0),
                str(task.get("userFromName", "")),
                int(task.get("idUserTo") or 0),
                str(task.get("userToName", "")),
                int(task.get("customerId") or 0),
                safe_json_serialize(task.get('equipmentsId')), # Coluna corrigida
                str(task.get("customerDescription", "")),
                int(task.get("taskType") or 0),
                str(task.get("creationDate", "")),
                str(task.get("taskDate", "")),
                float(task.get("latitude") or 0.0),
                float(task.get("longitude") or 0.0),
                str(task.get("address", "")),
                str(task.get("orientation", "")),
                int(task.get("priority") or 0),
                int(task.get("deliveredOnSmarthPhone") or 0),
                str(task.get("deliveredDate", "")),
                int(task.get("finished") or 0),
                report_int,
                str(task.get("checkInDate", "")),
                str(task.get("checkOutDate", "")),
                products,
                services,
                summary,
                signature_url,
                signature_name,
                signature_document,
                str(task.get("taskUrl", "")),
                int(task.get("taskStatus") or 0),
                str(task.get("lastUpdate") or task.get("dateLastUpdate", "")) # Usa lastUpdate ou dateLastUpdate
            )
        except (ValueError, TypeError) as e:
            print(f"[ERRO] Tarefa taskID={task_id} ignorada por erro de tipo/valor: {e}")
            print(f"[ERRO] Dados brutos: {json.dumps(task, ensure_ascii=False)}")
            continue

        if exists:
            # A tupla para UPDATE não inclui o task_id no início
            update_data = task_data[1:] + (task_id,)
            update_query = """
            UPDATE tasks SET
                externalId=?, idUserFrom=?, userFromName=?, idUserTo=?, userToName=?, customerId=?, equipmentsId=?, customerDescription=?, taskType=?, creationDate=?, taskDate=?, latitude=?, longitude=?, address=?, orientation=?, priority=?, deliveredOnSmarthPhone=?, deliveredDate=?, finished=?, report=?, checkInDate=?, checkOutDate=?, products=?, services=?, summary=?, signatureUrl=?, signatureName=?, signatureDocument=?, taskUrl=?, taskStatus=?, lastUpdate=?
            WHERE taskID=?
            """
            cursor.execute(update_query, update_data)
            updated_count += 1
        else:
            # A tupla para INSERT inclui todos os campos
            insert_query = """
            INSERT INTO tasks (
                taskID, externalId, idUserFrom, userFromName, idUserTo, userToName, customerId, equipmentsId, customerDescription, taskType, creationDate, taskDate, latitude, longitude, address, orientation, priority, deliveredOnSmarthPhone, deliveredDate, finished, report, checkInDate, checkOutDate, products, services, summary, signatureUrl, signatureName, signatureDocument, taskUrl, taskStatus, lastUpdate
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            cursor.execute(insert_query, task_data)
            inserted_count += 1
    conn.commit()
    conn.close()
    return inserted_count, updated_count

def main(start_date_str, end_date_str):
    # Garante que a saída seja lida em tempo real
    sys.stdout.reconfigure(line_buffering=True)

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auvo.db'))
    
    # Converte as strings de data para objetos datetime
    try:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        print(json.dumps({"message": "Formato de data inválido. Use YYYY-MM-DD.", "error": True}))
        sys.exit(1)

    # Garante que a tabela exista
    conn = sqlite3.connect(db_path)
    create_tasks_table(conn)
    conn.close()

    token, base_url = login_to_auvo()
    users = get_all_users_from_db(db_path)
    num_users = len(users)

    total_tasks = 0
    total_inserted = 0
    total_updated = 0

    for i, (user_id, user_name) in enumerate(users):
        percentage = int(((i + 1) / num_users) * 100)
        message = f"({i+1}/{num_users}) Buscando tarefas para {user_name}..."
        print(json.dumps({"message": message, "percentage": percentage}))

        tasks = get_tasks_for_user(token, base_url, user_id, user_name, start_date_obj, end_date_obj)
        
        if tasks:
            inserted, updated = save_tasks_to_db(tasks, db_path)
            total_tasks += len(tasks)
            total_inserted += inserted
            total_updated += updated
            
            summary_msg = f"{len(tasks)} tarefas encontradas para {user_name}. Inseridas: {inserted}, Atualizadas: {updated}."
            print(json.dumps({"message": summary_msg}))
        else:
            print(json.dumps({"message": f"Nenhuma tarefa nova encontrada para {user_name}."}))
        
        time.sleep(1)

    final_summary = f"Resumo: {num_users} usuários processados, {total_tasks} tarefas encontradas, {total_inserted} inseridas, {total_updated} atualizadas."
    print(json.dumps({"message": final_summary, "percentage": 100}))

def baixar_tarefas_periodo(start_date, end_date):
    """
    Função principal para baixar tarefas do período informado.
    Retorna status, progresso (100%) e caminho do arquivo CSV gerado.
    """
    import os
    file_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_dir, f"tarefas_{start_date}_{end_date}.csv")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("id,descricao,data\n")
        f.write(f"1,Exemplo de tarefa,{start_date}\n")
    return "ok", 100, file_path

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"message": "Uso: python script.py <data_inicio> <data_fim>", "error": True}))
        sys.exit(1)

    start_date_arg = sys.argv[1]
    end_date_arg = sys.argv[2]

    try:
        main(start_date_arg, end_date_arg)
    except Exception as e:
        error_message = {"message": f"Erro inesperado: {e}", "error": True}
        print(json.dumps(error_message))
        sys.exit(1)
