import os
import sqlite3
import requests
import json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'auvo_sync.sqlite3')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def autenticar():
    headers = {'Content-Type': 'application/json'}
    body = {'apiKey': API_KEY, 'apiToken': API_TOKEN}
    resp = requests.post(f"{API_URL}/login", headers=headers, json=body)
    if resp.status_code == 200:
        return resp.json().get('result', {}).get('accessToken')
    print('Erro ao autenticar:', resp.text)
    return None

def fetch_all(endpoint: str, token: str, params=None) -> List[Dict]:
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
            next_url = None
            for link in data.get('links', []):
                if link.get('rel') == 'nextPage':
                    next_url = link.get('href')
                    break
            if next_url:
                url = next_url
                page += 1
                continue
            if data.get('page', page) >= data.get('pageCount', page):
                break
        page += 1
    return all_items

def get_all_keys(items: List[Dict]) -> List[str]:
    keys = set()
    for item in items:
        keys.update(item.keys())
    return sorted(list(keys))

def ensure_table(table: str, keys: List[str]):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        existing_cols = set(row[1] for row in cur.fetchall())
        # Cria tabela caso não exista
        if not existing_cols:
            cols_sql = ', '.join([f'"{k}" TEXT' for k in keys] + ['json TEXT'])
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols_sql})")
            return
        # Adiciona coluna json se não existir
        if 'json' not in existing_cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN json TEXT")
            existing_cols.add('json')
        # Adiciona colunas novas
        for k in keys:
            if k not in existing_cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN '{k}' TEXT")
        conn.commit()

def upsert_dynamic(table: str, items: List[Dict], keys: List[str]):
    if not items:
        return
    with sqlite3.connect(DB_PATH) as conn:
        for item in items:
            row = {k: str(item.get(k, '')) for k in keys}
            row['json'] = json.dumps(item, ensure_ascii=False)
            placeholders = ','.join(['?'] * len(row))
            columns = ','.join([f'"{k}"' for k in row.keys()])
            # Usa o campo 'id' ou 'userId' como PRIMARY KEY se existir
            pk = 'id' if 'id' in row else ('userId' if 'userId' in row else keys[0])
            sql = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
            conn.execute(sql, list(row.values()))
        conn.commit()

def sync_dynamic(entity: str, endpoint: str):
    print(f"Sincronizando {entity}...")
    token = autenticar()
    if not token:
        print("Falha na autenticação. Abortando.")
        return
    items = fetch_all(endpoint, token)
    if not items:
        print(f"Nenhum dado recebido para {entity}.")
        return
    keys = get_all_keys(items)
    ensure_table(entity, keys)
    upsert_dynamic(entity, items, keys)
    print(f"{len(items)} registros inseridos/atualizados em {entity}.")

if __name__ == "__main__":
    # Exemplo de uso: sincronizar users
    sync_dynamic('users', '/users/')
    # Para sincronizar outras entidades, basta chamar:
    # sync_dynamic('customers', '/customers/')
    # sync_dynamic('equipments', '/equipments/')
    # sync_dynamic('task_types', '/taskTypes/')
