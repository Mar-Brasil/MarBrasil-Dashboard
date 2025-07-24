import sqlite3
import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

def create_equipments_table(conn):
    """Verifica e atualiza a estrutura da tabela de equipamentos"""
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipments'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        # Criar tabela com estrutura completa
        cursor.execute("""
        CREATE TABLE equipments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            tipo TEXT,
            setor_id INTEGER,
            associated_customer_id INTEGER,
            ativo INTEGER,
            identificador TEXT,
            externalId TEXT,
            parentEquipmentId INTEGER,
            associatedCustomerId INTEGER,
            associatedUserId INTEGER,
            categoryId INTEGER,
            identifier TEXT,
            urlImage TEXT,
            uriAnexos TEXT,
            active INTEGER,
            creationDate TEXT,
            expirationDate TEXT,
            equipmentSpecifications TEXT,
            description TEXT,
            warrantyStartDate TEXT,
            warrantyEndDate TEXT
        )
        """)
        conn.commit()
        print("Tabela equipments criada com estrutura completa.")
    else:
        # Verificar se todas as colunas necessárias existem
        cursor.execute("PRAGMA table_info(equipments)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'externalId', 'parentEquipmentId', 'associatedCustomerId', 'associatedUserId',
            'categoryId', 'identifier', 'urlImage', 'uriAnexos', 'active', 'creationDate',
            'expirationDate', 'equipmentSpecifications', 'description', 'warrantyStartDate',
            'warrantyEndDate'
        ]
        
        # Adicionar colunas que não existem
        for column in required_columns:
            if column not in existing_columns:
                try:
                    if column in ['parentEquipmentId', 'associatedCustomerId', 'associatedUserId', 'categoryId', 'active']:
                        cursor.execute(f"ALTER TABLE equipments ADD COLUMN {column} INTEGER")
                    else:
                        cursor.execute(f"ALTER TABLE equipments ADD COLUMN {column} TEXT")
                    print(f"Coluna {column} adicionada à tabela equipments.")
                except Exception as e:
                    print(f"Erro ao adicionar coluna {column}: {e}")
        
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

def get_equipments(token, base_url):
    """Busca todos os equipamentos da API Auvo"""
    url = f"{base_url}/equipments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_equipments = []
    page = 1
    page_size = 100
    
    print("\nBuscando equipamentos da API Auvo...")
    
    try:
        while True:
            print(f"Buscando página {page}...")
            response = requests.get(f"{url}?Page={page}&PageSize={page_size}", headers=headers)
            
            if response.status_code != 200:
                print(f"Erro ao buscar equipamentos: {response.status_code}")
                print(response.text)
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
                print(f"Nenhum equipamento encontrado na página {page} ou formato de resposta desconhecido.")
                print(f"Resposta: {json.dumps(data)[:200]}...")
                break
            
            # Filtrar apenas os equipamentos válidos (dicionários)
            valid_equipments = [equip for equip in equipments if isinstance(equip, dict)]
            all_equipments.extend(valid_equipments)
            
            print(f"Encontrados {len(valid_equipments)} equipamentos na página {page}")
            
            # Verificar se há mais páginas
            if len(equipments) < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar equipamentos: {e}")
    
    return all_equipments

def save_equipments_to_db(equipments, db_path):
    """Salva os equipamentos no banco de dados SQLite"""
    if not equipments:
        print("Nenhum equipamento para salvar no banco de dados.")
        return 0, 0

    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)

        # Criar/atualizar tabela se necessário
        create_equipments_table(conn)

        cursor = conn.cursor()
        inserted_count = 0
        updated_count = 0

        for equipment in equipments:
            try:
                equipment_id = equipment.get("id")
                if not equipment_id:
                    continue
                
                # Verificar se o equipamento já existe
                cursor.execute("SELECT id FROM equipments WHERE id = ?", (equipment_id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Atualizar equipamento existente (apenas campos da API)
                    cursor.execute("""
                        UPDATE equipments SET
                            name=?, externalId=?, parentEquipmentId=?, associatedCustomerId=?, 
                            associatedUserId=?, categoryId=?, identifier=?, urlImage=?, 
                            uriAnexos=?, active=?, creationDate=?, expirationDate=?,
                            equipmentSpecifications=?, description=?, warrantyStartDate=?, warrantyEndDate=?
                        WHERE id = ?
                    """, (
                        equipment.get("name"),
                        equipment.get("externalId"),
                        equipment.get("parentEquipmentId"),
                        equipment.get("associatedCustomerId"),
                        equipment.get("associatedUserId"),
                        equipment.get("categoryId"),
                        equipment.get("identifier"),
                        equipment.get("urlImage"),
                        json.dumps(equipment.get("uriAnexos", []), ensure_ascii=False),
                        1 if equipment.get("active") else 0,
                        equipment.get("creationDate"),
                        equipment.get("expirationDate"),
                        json.dumps(equipment.get("equipmentSpecifications", []), ensure_ascii=False),
                        equipment.get("description"),
                        equipment.get("warrantyStartDate"),
                        equipment.get("warrantyEndDate"),
                        equipment_id
                    ))
                    updated_count += 1
                else:
                    # Inserir novo equipamento
                    cursor.execute("""
                        INSERT INTO equipments (
                            id, name, tipo, setor_id, associated_customer_id, ativo, identificador,
                            externalId, parentEquipmentId, associatedCustomerId, associatedUserId, 
                            categoryId, identifier, urlImage, uriAnexos, active, creationDate, 
                            expirationDate, equipmentSpecifications, description, warrantyStartDate, 
                            warrantyEndDate
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        equipment_id,
                        equipment.get("name"),
                        None,  # tipo - campo legado
                        None,  # setor_id - campo legado
                        equipment.get("associatedCustomerId"),  # associated_customer_id
                        1 if equipment.get("active") else 0,  # ativo
                        equipment.get("identifier"),  # identificador
                        equipment.get("externalId"),
                        equipment.get("parentEquipmentId"),
                        equipment.get("associatedCustomerId"),
                        equipment.get("associatedUserId"),
                        equipment.get("categoryId"),
                        equipment.get("identifier"),
                        equipment.get("urlImage"),
                        json.dumps(equipment.get("uriAnexos", []), ensure_ascii=False),
                        1 if equipment.get("active") else 0,
                        equipment.get("creationDate"),
                        equipment.get("expirationDate"),
                        json.dumps(equipment.get("equipmentSpecifications", []), ensure_ascii=False),
                        equipment.get("description"),
                        equipment.get("warrantyStartDate"),
                        equipment.get("warrantyEndDate")
                    ))
                    inserted_count += 1
                    
            except Exception as e:
                print(f"Erro ao processar equipamento {equipment.get('id', 'desconhecido')}: {e}")
                continue

        conn.commit()
        conn.close()
        print(f"\nResumo da operação:")
        print(f"Equipamentos inseridos: {inserted_count}")
        print(f"Equipamentos atualizados: {updated_count}")
        return inserted_count, updated_count

    except Exception as e:
        print(f"Erro ao salvar equipamentos no banco de dados: {e}")
        return 0, 0

def main():
    """Função principal"""
    print("=== DOWNLOAD DE EQUIPAMENTOS DA API AUVO ===")
    
    # Configurações
    db_path = "auvo.db"
    
    # Login na API Auvo
    token, base_url = login_to_auvo()
    
    # Buscar equipamentos
    equipments = get_equipments(token, base_url)
    
    if not equipments:
        print("Nenhum equipamento encontrado.")
        sys.exit(1)
    
    print(f"\nForam encontrados {len(equipments)} equipamentos na API Auvo.")
    
    # Salvar equipamentos no banco de dados
    inserted, updated = save_equipments_to_db(equipments, db_path)
    
    print(f"\nOperação concluída!")
    print(f"Equipamentos inseridos: {inserted}")
    print(f"Equipamentos atualizados: {updated}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
