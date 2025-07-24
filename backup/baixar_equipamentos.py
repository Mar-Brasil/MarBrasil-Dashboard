import os
import sqlite3
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')
DB_PATH = os.path.abspath('equipamentos.sqlite3')

def autenticar():
    if API_TOKEN:
        return API_TOKEN
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
    resp = requests.post(f"{API_URL}/login", headers=headers)
    if resp.status_code == 200:
        return resp.json().get('token')
    print('Erro ao autenticar:', resp.text)
    return None

def criar_tabela_equipamentos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS equipments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            serialNumber TEXT,
            json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def baixar_equipamentos():
    token = autenticar()
    if not token:
        print('Falha na autenticação.')
        return
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    print('Baixando equipamentos...')
    all_equip = []
    page = 1
    while True:
        params = {'page': page, 'pageSize': 100, 'order': 'asc'}
        resp = requests.get(f"{API_URL}/equipments/", headers=headers, params=params)
        if resp.status_code != 200:
            print(f'Erro ao baixar equipamentos: HTTP {resp.status_code} - {resp.text}')
            break
        data = resp.json().get('result', resp.json())
        items = data.get('entityList', data if isinstance(data, list) else [])
        if not items:
            break
        all_equip.extend(items)
        if data.get('page', page) >= data.get('pageCount', page):
            break
        page += 1
    print(f"Total de equipamentos recebidos: {len(all_equip)}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for item in all_equip:
        cur.execute('''INSERT OR REPLACE INTO equipments (id, name, serialNumber, json) VALUES (?, ?, ?, ?)''', (
            item.get('id'),
            item.get('name'),
            item.get('serialNumber'),
            json.dumps(item, ensure_ascii=False)
        ))
    conn.commit()
    conn.close()
    print('Equipamentos salvos no banco local.')

if __name__ == '__main__':
    criar_tabela_equipamentos()
    baixar_equipamentos()
