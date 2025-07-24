import os
import sqlite3
import requests
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
API_TOKEN = os.getenv('API_TOKEN')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'auvo_sync.sqlite3')
os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)

def autenticar():
    headers = {'Content-Type': 'application/json'}
    body = {'apiKey': API_KEY, 'apiToken': API_TOKEN}
    resp = requests.post(f"{API_URL}/login", headers=headers, json=body)
    if resp.status_code == 200:
        return resp.json().get('result', {}).get('accessToken')
    print('Erro ao autenticar:', resp.text)
    return None

def garantir_colunas_users():
    # Garante que todas as colunas do schema existem na tabela users
    colunas_necessarias = [
        ('userType', 'TEXT'),
        ('externalId', 'TEXT'),
        ('smartPhoneNumber', 'TEXT'),
        ('created', 'TEXT'),
        ('updated', 'TEXT'),
    ]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    existentes = set([row[1] for row in cur.fetchall()])
    for nome, tipo in colunas_necessarias:
        if nome not in existentes:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {nome} {tipo}")
            except Exception as e:
                print(f"Erro ao adicionar coluna {nome}: {e}")
    conn.commit()
    conn.close()

def criar_tabela_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            active BOOLEAN,
            userType TEXT,
            externalId TEXT,
            smartPhoneNumber TEXT,
            created TEXT,
            updated TEXT,
            json TEXT
        )
    ''')
    conn.commit()
    conn.close()


def baixar_usuarios():
    token = autenticar()
    if not token:
        print('Falha na autenticação.')
        return
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    print('Baixando usuários...')
    url = f"{API_URL}/users/"
    total = 0
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f'Erro ao baixar usuários: HTTP {resp.status_code} - {resp.text}')
            break
        data = resp.json().get('result', resp.json())
        items = data.get('entityList', data if isinstance(data, list) else [])
        for item in items:
            cur.execute('''INSERT OR REPLACE INTO users (
                id, name, email, active, userType, externalId, smartPhoneNumber, created, updated, json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                item.get('id') or item.get('userID'),
                item.get('name'),
                item.get('email'),
                int(item.get('active', 0) or 0),
                item.get('userType', {}).get('description', '') if isinstance(item.get('userType'), dict) else (item.get('userType') or ''),
                item.get('externalId', ''),
                item.get('smartPhoneNumber', ''),
                item.get('registrationDate', ''),
                item.get('updated', ''),
                json.dumps(item, ensure_ascii=False)
            ))
        total += len(items)
        # Busca link da próxima página, se houver
        next_url = None
        for link in data.get('links', []):
            if link.get('rel') == 'nextPage':
                next_url = link.get('href')
                break
        url = next_url
    conn.commit()
    conn.close()
    print(f'Total de usuários recebidos: {total}')
    print('Usuários salvos no banco local.')

if __name__ == '__main__':
    criar_tabela_usuarios()
    garantir_colunas_users()
    baixar_usuarios()
