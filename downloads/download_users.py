import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

def create_users_table(conn):
    """Cria a tabela de usuários se não existir"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        userId INTEGER PRIMARY KEY,
        externalId TEXT,
        name TEXT,
        smartphoneNumber TEXT,
        login TEXT,
        email TEXT,
        culture TEXT,
        jobPosition TEXT,
        userTypeId INTEGER,
        userTypeDescription TEXT,
        workDaysOfWeek TEXT,
        startWorkHour TEXT,
        endWorkHour TEXT,
        startLunchHour TEXT,
        endLunchHour TEXT,
        hourValue REAL,
        pictureUrl TEXT,
        basePointAddress TEXT,
        basePointLatitude REAL,
        basePointLongitude REAL,
        active INTEGER,
        isAdmin INTEGER,
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

def get_users(token, base_url):
    """Busca todos os usuários da API Auvo"""
    url = f"{base_url}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_users = []
    page = 1
    page_size = 100
    
    print("\nBuscando usuários da API Auvo...")
    
    try:
        while True:
            print(f"Buscando página {page}...")
            response = requests.get(f"{url}?Page={page}&PageSize={page_size}", headers=headers)
            
            if response.status_code != 200:
                print(f"Erro ao buscar usuários: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            # Verificar o formato da resposta
            users = []
            if "result" in data:
                if isinstance(data["result"], list):
                    users = data["result"]
                elif isinstance(data["result"], dict) and "entityList" in data["result"]:
                    users = data["result"]["entityList"]
            elif "entityList" in data:
                users = data["entityList"]
            
            if not users:
                print(f"Nenhum usuário encontrado na página {page} ou formato de resposta desconhecido.")
                print(f"Resposta: {json.dumps(data)[:200]}...")
                break
            
            # Filtrar apenas os usuários válidos (dicionários)
            valid_users = [user for user in users if isinstance(user, dict)]
            all_users.extend(valid_users)
            
            print(f"Encontrados {len(valid_users)} usuários na página {page}")
            
            # Verificar se há mais páginas
            if len(users) < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar usuários: {e}")
    
    return all_users

def save_users_to_db(users, db_path):
    """Salva os usuários no banco de dados SQLite"""
    if not users:
        print("Nenhum usuário para salvar no banco de dados.")
        return 0, 0
    
    try:
        conn = sqlite3.connect(db_path)
        create_users_table(conn)
        cursor = conn.cursor()
        
        inserted_count = 0
        updated_count = 0
        
        for user in users:
            try:
                # Normalizar as chaves do usuário
                user_id = user.get("userId") or user.get("userID") or user.get("userid")
                
                if not user_id:
                    print(f"Pulando usuário sem ID: {user}")
                    continue
                
                # Extrair dados do usuário
                user_type = user.get("userType", {})
                base_point = user.get("BasePoint", {})
                
                # Verificar se o usuário já existe
                cursor.execute("SELECT userId FROM users WHERE userId = ?", (user_id,))
                existing_user = cursor.fetchone()
                
                # Preparar os dados para inserção/atualização
                user_data = (
                    user_id,
                    user.get("externalId", ""),
                    user.get("name", ""),
                    user.get("smartphoneNumber", ""),
                    user.get("login", ""),
                    user.get("email", ""),
                    user.get("culture", ""),
                    user.get("jobPosition", ""),
                    user_type.get("userTypeId", 0) if isinstance(user_type, dict) else 0,
                    user_type.get("description", "") if isinstance(user_type, dict) else "",
                    json.dumps(user.get("workDaysOfWeek", [])),
                    user.get("startWorkHour", ""),
                    user.get("endWorkHour", ""),
                    user.get("startLunchHour", ""),
                    user.get("endLunchHour", ""),
                    user.get("hourValue", 0.0),
                    user.get("pictureUrl", ""),
                    base_point.get("address", "") if isinstance(base_point, dict) else "",
                    base_point.get("latitude", 0.0) if isinstance(base_point, dict) else 0.0,
                    base_point.get("longitude", 0.0) if isinstance(base_point, dict) else 0.0,
                    1 if user.get("active", False) else 0,
                    1 if user.get("isAdmin", False) else 0,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                if existing_user:
                    # Atualizar usuário existente
                    cursor.execute("""
                    UPDATE users SET
                        externalId = ?,
                        name = ?,
                        smartphoneNumber = ?,
                        login = ?,
                        email = ?,
                        culture = ?,
                        jobPosition = ?,
                        userTypeId = ?,
                        userTypeDescription = ?,
                        workDaysOfWeek = ?,
                        startWorkHour = ?,
                        endWorkHour = ?,
                        startLunchHour = ?,
                        endLunchHour = ?,
                        hourValue = ?,
                        pictureUrl = ?,
                        basePointAddress = ?,
                        basePointLatitude = ?,
                        basePointLongitude = ?,
                        active = ?,
                        isAdmin = ?,
                        lastUpdate = ?
                    WHERE userId = ?
                    """, user_data[1:] + (user_id,))
                    updated_count += 1
                else:
                    # Inserir novo usuário
                    cursor.execute("""
                    INSERT INTO users (
                        userId, externalId, name, smartphoneNumber, login, email,
                        culture, jobPosition, userTypeId, userTypeDescription,
                        workDaysOfWeek, startWorkHour, endWorkHour, startLunchHour,
                        endLunchHour, hourValue, pictureUrl, basePointAddress,
                        basePointLatitude, basePointLongitude, active, isAdmin, lastUpdate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, user_data)
                    inserted_count += 1
            
            except Exception as e:
                print(f"Erro ao processar usuário {user.get('userId', 'desconhecido')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count, updated_count
    
    except Exception as e:
        print(f"Erro ao salvar usuários no banco de dados: {e}")
        return 0, 0

def main():
    """Função principal"""
    print("=== DOWNLOAD DE USUÁRIOS DA API AUVO ===")
    
    # Configurações
    db_path = "auvo.db"
    
    # Login na API Auvo
    token, base_url = login_to_auvo()
    
    # Buscar usuários
    users = get_users(token, base_url)
    
    if not users:
        print("Nenhum usuário encontrado.")
        sys.exit(1)
    
    print(f"\nForam encontrados {len(users)} usuários na API Auvo.")
    
    # Salvar usuários no banco de dados
    inserted, updated = save_users_to_db(users, db_path)
    
    print(f"\nOperação concluída!")
    print(f"Usuários inseridos: {inserted}")
    print(f"Usuários atualizados: {updated}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
