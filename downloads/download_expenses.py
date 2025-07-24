import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

def login_to_auvo():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    if not api_key or not api_token:
        print("Credenciais da API não encontradas!")
        sys.exit(1)
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    try:
        response = requests.get(login_url)
        data = response.json()
        if "result" in data and data["result"].get("authenticated"):
            token = data["result"]["accessToken"]
            print("Login realizado com sucesso!")
            return token, base_url
        else:
            print("Falha na autenticação!")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        sys.exit(1)

def create_expenses_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("Criando tabela 'expenses'...")
        cursor.execute('''CREATE TABLE expenses (
            id INTEGER PRIMARY KEY,
            description TEXT,
            userToId INTEGER,
            userToName TEXT,
            typeId INTEGER,
            typeName TEXT,
            date TEXT,
            attachmentUrl TEXT,
            creationDate TEXT,
            amount REAL
        )''')
        conn.commit()
        print("Tabela 'expenses' criada com sucesso!")
    conn.close()

from datetime import date, datetime
import json

def get_all_expenses(token, base_url):
    url = f"{base_url}/expenses/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    all_expenses = []
    page = 1
    page_size = 100
    # Definir período: do início do ano até hoje, formato yyyy-mm-ddTHH:MM:SS
    today = date.today()
    start_date = datetime(today.year, 1, 1, 0, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")
    end_date = datetime(today.year, today.month, today.day, 23, 59, 59).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        while True:
            param_filter = {
                "startDate": start_date,
                "endDate": end_date
            }
            params = {
                "paramFilter": json.dumps(param_filter),
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }
            print(f"Buscando página {page} de despesas ({start_date} a {end_date})...")
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Erro ao buscar despesas: {response.status_code}")
                print(response.text)
                break
            data = response.json()
            if "result" not in data or not data["result"]:
                break
            expenses = data["result"]
            expenses_count = len(expenses)
            all_expenses.extend(expenses)
            print(f"Encontradas {expenses_count} despesas na página {page}")
            if expenses_count < page_size:
                break
            page += 1
    except Exception as e:
        print(f"Erro ao buscar despesas: {e}")
    print(f"Total de despesas encontradas: {len(all_expenses)}")
    return all_expenses

def save_expense_to_db(expense):
    if not expense or not isinstance(expense, dict):
        print("Despesa inválida!")
        return
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(expenses)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        for key in expense.keys():
            if key not in existing_columns:
                print(f"Adicionando coluna '{key}' à tabela 'expenses'...")
                cursor.execute(f"ALTER TABLE expenses ADD COLUMN {key} TEXT")
                conn.commit()
        row = {}
        for key, value in expense.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value, ensure_ascii=False)
            else:
                row[key] = value
        fields = ', '.join(row.keys())
        placeholders = ', '.join(['?'] * len(row))
        values = list(row.values())
        cursor.execute("SELECT id FROM expenses WHERE id = ?", (expense.get("id"),))
        existing = cursor.fetchone()
        if existing:
            set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
            cursor.execute(f"UPDATE expenses SET {set_clause} WHERE id = ?", values + [expense.get("id")])
            print(f"Atualizada despesa {expense.get('id')}")
        else:
            cursor.execute(f"INSERT INTO expenses ({fields}) VALUES ({placeholders})", values)
            print(f"Inserida despesa {expense.get('id')}")
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar despesa no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE DESPESAS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    create_expenses_table()
    token, base_url = login_to_auvo()
    expenses = get_all_expenses(token, base_url)
    for expense in expenses:
        save_expense_to_db(expense)
    print("=== FIM DO DOWNLOAD DE DESPESAS ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
