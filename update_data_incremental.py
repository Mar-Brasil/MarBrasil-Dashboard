import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_incremental.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_database(db_path):
    """Configura o banco de dados e cria tabelas se não existirem"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de usuários
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
    
    # Tabela de equipamentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipments (
        id INTEGER PRIMARY KEY,
        name TEXT,
        tipo TEXT,
        setor_id INTEGER,
        associated_customer_id INTEGER,
        ativo INTEGER,
        identificador TEXT,
        lastUpdate TEXT
    )
    """)
    
    # Tabela de controle de atualizações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS update_control (
        entity_type TEXT PRIMARY KEY,
        last_update TIMESTAMP,
        records_updated INTEGER,
        status TEXT
    )
    """)
    
    conn.commit()
    return conn

def login_to_auvo():
    """Faz login na API Auvo e retorna o token de acesso"""
    # Carregar credenciais do arquivo .env
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    
    if not api_key or not api_token:
        logger.error("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    
    logger.info(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Fazer login
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    
    try:
        response = requests.get(login_url)
        data = response.json()
        
        if "result" in data and data["result"]["authenticated"]:
            token = data["result"]["accessToken"]
            expiration = data["result"]["expiration"]
            logger.info(f"Login realizado com sucesso! Token válido até: {expiration}")
            return token, base_url
        else:
            logger.error("Falha na autenticação!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Erro ao fazer login: {e}")
        sys.exit(1)

def get_last_update_date(conn, entity_type):
    """Obtém a data da última atualização para o tipo de entidade especificado"""
    cursor = conn.cursor()
    cursor.execute("SELECT last_update FROM update_control WHERE entity_type = ?", (entity_type,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        # Se não houver registro, insere um novo com data atual menos 30 dias
        default_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO update_control (entity_type, last_update, records_updated, status) VALUES (?, ?, 0, 'initial')", 
                      (entity_type, default_date))
        conn.commit()
        return default_date

def update_last_update_date(conn, entity_type, records_updated, status="success"):
    """Atualiza a data da última atualização para o tipo de entidade especificado"""
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE update_control 
    SET last_update = ?, records_updated = ?, status = ?
    WHERE entity_type = ?
    """, (current_time, records_updated, status, entity_type))
    conn.commit()

def get_users_incremental(token, base_url, conn):
    """Busca usuários da API Auvo de forma incremental"""
    url = f"{base_url}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    last_update = get_last_update_date(conn, "users")
    logger.info(f"Buscando usuários atualizados desde: {last_update}")
    
    all_users = []
    page = 1
    page_size = 100
    total_pages = 0
    
    try:
        while True:
            logger.info(f"Buscando página {page} de usuários...")
            response = requests.get(f"{url}?Page={page}&PageSize={page_size}", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar usuários: {response.status_code}")
                logger.error(response.text)
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
                logger.info(f"Nenhum usuário encontrado na página {page} ou formato de resposta desconhecido.")
                break
            
            # Filtrar apenas os usuários válidos (dicionários)
            valid_users = [user for user in users if isinstance(user, dict)]
            all_users.extend(valid_users)
            
            logger.info(f"Encontrados {len(valid_users)} usuários na página {page}")
            total_pages = page
            
            # Verificar se há mais páginas
            if len(users) < page_size:
                break
            
            page += 1
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
    
    except Exception as e:
        logger.error(f"Erro ao buscar usuários: {e}")
    
    logger.info(f"Total de {len(all_users)} usuários encontrados em {total_pages} páginas")
    return all_users

def get_equipments_incremental(token, base_url, conn):
    """Busca equipamentos da API Auvo de forma incremental"""
    url = f"{base_url}/equipments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    last_update = get_last_update_date(conn, "equipments")
    logger.info(f"Buscando equipamentos atualizados desde: {last_update}")
    
    all_equipments = []
    page = 1
    page_size = 100
    total_pages = 0
    
    try:
        while True:
            logger.info(f"Buscando página {page} de equipamentos...")
            response = requests.get(f"{url}?Page={page}&PageSize={page_size}", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar equipamentos: {response.status_code}")
                logger.error(response.text)
                break
            
            data = response.json()
            
            # Verificar o formato da resposta
            equipments = []
            if "result" in data:
                if isinstance(data["result"], list):
                    equipments = data["result"]
                elif isinstance(data["result"], dict) and "entityList" in data["result"]:
                    equipments = data["result"]["entityList"]
            elif "entityList" in data:
                equipments = data["entityList"]
            
            if not equipments:
                logger.info(f"Nenhum equipamento encontrado na página {page} ou formato de resposta desconhecido.")
                break
            
            # Filtrar apenas os equipamentos válidos (dicionários)
            valid_equipments = [equip for equip in equipments if isinstance(equip, dict)]
            all_equipments.extend(valid_equipments)
            
            logger.info(f"Encontrados {len(valid_equipments)} equipamentos na página {page}")
            total_pages = page
            
            # Verificar se há mais páginas
            if len(equipments) < page_size:
                break
            
            page += 1
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
    
    except Exception as e:
        logger.error(f"Erro ao buscar equipamentos: {e}")
    
    logger.info(f"Total de {len(all_equipments)} equipamentos encontrados em {total_pages} páginas")
    return all_equipments

def update_users(users, conn):
    """Atualiza os usuários no banco de dados de forma incremental"""
    if not users:
        logger.info("Nenhum usuário para atualizar no banco de dados.")
        return 0, 0
    
    try:
        cursor = conn.cursor()
        inserted_count = 0
        updated_count = 0
        
        for user in users:
            try:
                # Normalizar as chaves do usuário
                user_id = user.get("userId") or user.get("id")
                
                if not user_id:
                    logger.warning(f"Pulando usuário sem ID: {user}")
                    continue
                
                # Extrair dados do usuário
                base_point = user.get("basePoint", {})
                user_type = user.get("userType", {})
                
                # Verificar se o usuário já existe
                cursor.execute("SELECT userId FROM users WHERE userId = ?", (user_id,))
                existing_user = cursor.fetchone()
                
                # Preparar os dados para inserção/atualização
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                    user.get("workDaysOfWeek", ""),
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
                    current_time
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
                logger.error(f"Erro ao processar usuário {user.get('userId', 'desconhecido')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Usuários inseridos: {inserted_count}")
        logger.info(f"Usuários atualizados: {updated_count}")
        return inserted_count, updated_count
    
    except Exception as e:
        logger.error(f"Erro ao atualizar usuários no banco de dados: {e}")
        return 0, 0

def update_equipments(equipments, conn):
    """Atualiza os equipamentos no banco de dados de forma incremental"""
    if not equipments:
        logger.info("Nenhum equipamento para atualizar no banco de dados.")
        return 0, 0
    
    try:
        cursor = conn.cursor()
        inserted_count = 0
        updated_count = 0
        
        for equipment in equipments:
            try:
                # Normalizar as chaves do equipamento
                equipment_id = equipment.get("equipmentId") or equipment.get("id")
                
                if not equipment_id:
                    logger.warning(f"Pulando equipamento sem ID: {equipment}")
                    continue
                
                # Extrair dados do equipamento
                category = equipment.get("category", {})
                customer = equipment.get("customer", {})
                
                # Verificar se o equipamento já existe
                cursor.execute("SELECT id FROM equipments WHERE id = ?", (equipment_id,))
                existing_equipment = cursor.fetchone()
                
                # Preparar os dados para inserção/atualização
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                equipment_data = (
                    equipment_id,
                    equipment.get("name", ""),
                    category.get("description", "") if isinstance(category, dict) else "",  # tipo
                    category.get("categoryId", 0) if isinstance(category, dict) else 0,  # setor_id
                    customer.get("customerId", 0) if isinstance(customer, dict) else 0,  # associated_customer_id
                    1 if equipment.get("active", False) else 0,  # ativo
                    equipment.get("identifier", "") or equipment.get("serialNumber", ""),  # identificador
                    current_time  # lastUpdate
                )
                
                if existing_equipment:
                    # Atualizar equipamento existente
                    cursor.execute("""
                    UPDATE equipments SET
                        name = ?,
                        tipo = ?,
                        setor_id = ?,
                        associated_customer_id = ?,
                        ativo = ?,
                        identificador = ?,
                        lastUpdate = ?
                    WHERE id = ?
                    """, equipment_data[1:] + (equipment_id,))
                    updated_count += 1
                else:
                    # Inserir novo equipamento
                    cursor.execute("""
                    INSERT INTO equipments (
                        id, name, tipo, setor_id, associated_customer_id, ativo, identificador, lastUpdate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, equipment_data)
                    inserted_count += 1
            
            except Exception as e:
                logger.error(f"Erro ao processar equipamento {equipment.get('equipmentId', 'desconhecido')}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Equipamentos inseridos: {inserted_count}")
        logger.info(f"Equipamentos atualizados: {updated_count}")
        return inserted_count, updated_count
    
    except Exception as e:
        logger.error(f"Erro ao atualizar equipamentos no banco de dados: {e}")
        return 0, 0

def main():
    """Função principal para atualização incremental de dados"""
    start_time = datetime.now()
    logger.info("=== ATUALIZAÇÃO INCREMENTAL DE DADOS DA API AUVO ===")
    logger.info(f"Iniciando atualização em: {start_time}")
    
    # Configurações
    db_path = "auvo.db"
    
    # Configurar banco de dados
    conn = setup_database(db_path)
    
    # Login na API Auvo
    token, base_url = login_to_auvo()
    
    try:
        # Atualizar usuários
        logger.info("Iniciando atualização de usuários...")
        users = get_users_incremental(token, base_url, conn)
        users_inserted, users_updated = update_users(users, conn)
        update_last_update_date(conn, "users", users_inserted + users_updated)
        
        # Atualizar equipamentos
        logger.info("Iniciando atualização de equipamentos...")
        equipments = get_equipments_incremental(token, base_url, conn)
        equipments_inserted, equipments_updated = update_equipments(equipments, conn)
        update_last_update_date(conn, "equipments", equipments_inserted + equipments_updated)
        
        # Fechar conexão com o banco de dados
        conn.close()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n=== RESUMO DA ATUALIZAÇÃO ===")
        logger.info(f"Tempo total de execução: {duration}")
        logger.info(f"Usuários: {users_inserted} inseridos, {users_updated} atualizados")
        logger.info(f"Equipamentos: {equipments_inserted} inseridos, {equipments_updated} atualizados")
        logger.info("Atualização concluída com sucesso!")
        
    except KeyboardInterrupt:
        logger.warning("\nOperação cancelada pelo usuário.")
        conn.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nErro inesperado durante a atualização: {e}")
        update_last_update_date(conn, "users", 0, "error")
        update_last_update_date(conn, "equipments", 0, "error")
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
