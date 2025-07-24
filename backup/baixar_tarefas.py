import os
import sqlite3
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')
DB_PATH = os.path.abspath('tarefas.sqlite3')

def autenticar():
    if API_TOKEN:
        return API_TOKEN
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
    resp = requests.post(f"{API_URL}/login", headers=headers)
    if resp.status_code == 200:
        return resp.json().get('token')
    print('Erro ao autenticar:', resp.text)
    return None

def criar_tabela_tarefas():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            description TEXT,
            status TEXT,
            userId TEXT,
            json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def baixar_tarefas():
    token = autenticar()
    if not token:
        print('Falha na autenticação.')
        return
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    print('Baixando tarefas...')
    all_tasks = []
    page = 1
    while True:
        params = {'page': page, 'pageSize': 100, 'order': 'asc'}
        resp = requests.get(f"{API_URL}/tasks/", headers=headers, params=params)
        if resp.status_code != 200:
            print(f'Erro ao baixar tarefas: HTTP {resp.status_code} - {resp.text}')
            break
        data = resp.json().get('result', resp.json())
        items = data.get('entityList', data if isinstance(data, list) else [])
        if not items:
            break
        all_tasks.extend(items)
        if data.get('page', page) >= data.get('pageCount', page):
            break
        page += 1
    print(f"Total de tarefas recebidas: {len(all_tasks)}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for item in all_tasks:
        cur.execute('''INSERT OR REPLACE INTO tasks (id, description, status, userId, json) VALUES (?, ?, ?, ?, ?)''', (
            item.get('id'),
            item.get('description'),
            item.get('status'),
            item.get('userId'),
            json.dumps(item, ensure_ascii=False)
        ))
    conn.commit()
    conn.close()
    print('Tarefas salvas no banco local.')

if __name__ == '__main__':
    criar_tabela_tarefas()
    baixar_tarefas()
