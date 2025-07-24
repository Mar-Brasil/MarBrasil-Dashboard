import os
import sqlite3
import requests
import json
import calendar
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')

# Aponta para o banco de dados principal na pasta raiz, uma pasta acima do diretório atual
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'auvo.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'db_schema_auvo.sql')

# --- Funções auxiliares ---
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

# --- Autenticação na API Auvo ---
def autenticar():
    url = f"{API_URL}/login/?apiKey={API_KEY}&apiToken={API_TOKEN}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()['result']['accessToken']
    else:
        print(f"Erro ao autenticar: {resp.status_code}")
        return None

# --- Função genérica para buscar dados paginados ---
def fetch_all(endpoint, token, params=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    all_items = []
    url = f"{API_URL}{endpoint}"
    page = 1
    while True:
        p = params.copy() if params else {}
        p.update({'page': page, 'pageSize': 100, 'order': 'asc'})
        resp = requests.get(url, headers=headers, params=p)
        if resp.status_code != 200:
            print(f"[ERRO ao buscar {endpoint}: {resp.status_code}]")
            print("Resposta da API:", resp.text)
            break
        data = resp.json().get('result', resp.json())
        # Se for lista direta
        if isinstance(data, list):
            if not data:
                break
            all_items.extend(data)
            if len(data) < 100:
                break
        else:
            items = data.get('entityList', [])
            if not items:
                break
            all_items.extend(items)
            # Paginado por links nextPage
            next_url = None
            for link in data.get('links', []):
                if link.get('rel') == 'nextPage':
                    next_url = link.get('href')
                    break
            if next_url:
                url = next_url
                page += 1
                continue
            # Ou por page/pageCount
            if data.get('page', page) >= data.get('pageCount', page):
                break
        page += 1
    return all_items

# --- Função para inserir/atualizar dados no banco ---
def upsert(table, items, pk='id'):
    if not items:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # Descobrir colunas existentes na tabela UMA VEZ
        cur.execute(f'PRAGMA table_info({table})')
        columns_db = set([row[1] for row in cur.fetchall()])
        
        for item in items:
            try:
                # --- Correção do campo 'id' para pk dinâmico ---
                if pk in item and item[pk] is not None:
                    item['id'] = item[pk]

                # Filtrar o item para conter apenas as chaves que são colunas no DB
                item_filtered = {k: v for k, v in item.items() if k in columns_db}

                # Adicionar o JSON bruto se a coluna 'json' existir
                if 'json' in columns_db:
                    item_filtered['json'] = json.dumps(item, ensure_ascii=False)

                # Conversão de tipos complexos para string
                for key, value in item_filtered.items():
                    if isinstance(value, (dict, list)):
                        item_filtered[key] = json.dumps(value, ensure_ascii=False)

                if not item_filtered or 'id' not in item_filtered or item_filtered['id'] is None:
                    continue

                cols = ', '.join(item_filtered.keys())
                placeholders = ', '.join(['?'] * len(item_filtered))
                
                sql = f"REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
                cur.execute(sql, list(item_filtered.values()))

            except Exception as e:
                print(f"Erro ao inserir em {table}: {e}")
        conn.commit()

# --- Sincronização principal ---
def sync_auvo():
    print('Iniciando sincronização com a Auvo...')
    init_db()
    token = autenticar()
    if not token:
        print('Falha na autenticação. Abortando.')
        return

    # Sincronizar entidades principais
    entidades = [
        ('users', '/users/'),
        ('tasks', '/tasks/'),
        ('customers', '/customers/'),
        ('customer_groups', '/customer-groups/'),
        ('customer_group_customers', '/customer-group-customers/'),
        ('equipments', '/equipments/'), # Adicionado para sincronizar os equipamentos
        ('teams', '/teams/'),
        ('task_types', '/taskTypes/'),
        ('segments', '/segments/'),
        ('questionnaires', '/questionnaires/'),
        ('keywords', '/keywords/'),
        ('equipments', '/equipments/')
    ]
    # Campos de atualização incremental por entidade
    campos_incrementais = {
        'users': 'updated',
        'customers': 'dateLastUpdate',
        'task_types': 'updated',
        'teams': 'updated',
        'segments': 'updated',
        'questionnaires': 'updated',
        'keywords': 'updated',
        'customer_groups': 'updated',
        'equipments': 'updated',
    }
    for table, endpoint in entidades:
        print(f'Baixando {table}...')
        # Busca o último valor do campo incremental
        campo_inc = campos_incrementais.get(table)
        last_updated = None
        if campo_inc:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute(f"SELECT MAX({campo_inc}) FROM {table}")
                    result = cur.fetchone()
                    last_updated = result[0] if result and result[0] else None
                except Exception:
                    last_updated = None
        param_filter = {}
        if last_updated:
            # Filtro incremental: registros atualizados após o último valor salvo
            param_filter[campo_inc] = {"$gt": last_updated}
        params = {}
        if param_filter:
            params["paramFilter"] = json.dumps(param_filter)
        items = fetch_all(endpoint, token, params)
        upsert(table, items)
        print(f'{len(items)} registros inseridos/atualizados em {table}.')

    # Busca de tarefas por usuário/mês
    print("Baixando tasks do ano de 2025...")
    tasks_total = 0
    user_ids = []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            # Busca IDs de usuários ativos para otimizar a busca de tarefas
            cur.execute('SELECT userId FROM users WHERE active = 1')
            user_ids = [row[0] for row in cur.fetchall() if row[0] is not None]
        except sqlite3.OperationalError:
            # Fallback se a coluna 'active' não existir
            cur.execute('SELECT userId FROM users')
            user_ids = [row[0] for row in cur.fetchall() if row[0] is not None]
    
    print(f"Encontrados {len(user_ids)} usuários para buscar tarefas.")

    for user_id in user_ids:
        for month in range(1, 13):
            start_date = f"2025-{month:02d}-01"
            last_day = calendar.monthrange(2025, month)[1]
            end_date = f"2025-{month:02d}-{last_day:02d}"
            param_filter = json.dumps({
                "userId": user_id,
                "startDate": start_date,
                "endDate": end_date
            })
            params = {"paramFilter": param_filter}
            
            # print(f"Buscando tarefas de user {user_id} de {start_date} a {end_date}...")
            user_tasks = fetch_all("/tasks/", token, params)
            if user_tasks:
                upsert("tasks", user_tasks, pk="taskId")
                tasks_total += len(user_tasks)
    
    print(f"{tasks_total} registros de tarefas inseridos/atualizados.")

    print('Sincronização concluída!')

if __name__ == '__main__':
    sync_auvo()
