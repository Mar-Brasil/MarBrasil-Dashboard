import os
import sys
import sqlite3
from datetime import datetime

# Adicionar o diretório raiz ao path para permitir importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar utilitários e funções comuns
try:
    from downloads.utils import get_db_connection
    from downloads.common import login_to_auvo, get_api_headers, safe_json_serialize, process_api_response, paginate_api_request
except ImportError:
    # Importação direta quando executado da pasta downloads
    from utils import get_db_connection
    from common import login_to_auvo, get_api_headers, safe_json_serialize, process_api_response, paginate_api_request

def create_teams_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'teams'...")
        cursor.execute('''
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY,
            description TEXT,
            active INTEGER,
            creationDate TEXT,
            dateLastUpdate TEXT,
            externalId TEXT,
            teamUsers TEXT,
            teamManagers TEXT
        )
        ''')
        conn.commit()
        print("Tabela 'teams' criada com sucesso!")
    else:
        # Verificar todas as colunas necessárias
        cursor.execute("PRAGMA table_info(teams)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print(f"Colunas existentes na tabela 'teams': {column_names}")
        
        # Adicionar colunas que não existem
        required_columns = ['description', 'active', 'creationDate', 'dateLastUpdate', 
                           'externalId', 'teamUsers', 'teamManagers']
        
        for column in required_columns:
            if column not in column_names:
                print(f"Adicionando coluna '{column}' à tabela 'teams'...")
                cursor.execute(f"ALTER TABLE teams ADD COLUMN {column} TEXT")
                conn.commit()
            
        print("Tabela 'teams' já existe e foi atualizada se necessário.")
    
    conn.close()
    return column_names

def get_teams(token, base_url):
    """Busca times da API Auvo com paginação."""
    url = f"{base_url}/teams"
    headers = get_api_headers(token)
    
    # Usar função comum de paginação
    return paginate_api_request(url, headers, "times")

# A função safe_json_serialize agora é importada do módulo common.py

def save_teams_to_db(teams, available_columns):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    try:
        for team in teams:
            # Verificar se team é um dicionário
            if not isinstance(team, dict):
                print(f"Aviso: Item não é um dicionário: {team}")
                continue
                
            team_id = team.get("id")
            if team_id is None:
                print(f"Aviso: Item sem ID válido: {team}")
                continue
            
            # Verificar se o time já existe
            cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
            existing_team = cursor.fetchone()
            
            # Preparar os dados e as colunas para inserção/atualização
            data_dict = {
                "id": team_id
            }
            
            # Adicionar dados apenas para colunas que existem na tabela
            if "description" in available_columns:
                data_dict["description"] = safe_json_serialize(team.get("description", ""))
                
            if "active" in available_columns:
                data_dict["active"] = 1 if team.get("active", False) else 0
                
            if "creationDate" in available_columns:
                data_dict["creationDate"] = safe_json_serialize(team.get("creationDate", ""))
                
            if "dateLastUpdate" in available_columns:
                data_dict["dateLastUpdate"] = safe_json_serialize(team.get("dateLastUpdate", ""))
                
            if "externalId" in available_columns:
                data_dict["externalId"] = safe_json_serialize(team.get("externalId", ""))
                
            if "teamUsers" in available_columns:
                data_dict["teamUsers"] = safe_json_serialize(team.get("teamUsers", []))
                
            if "teamManagers" in available_columns:
                data_dict["teamManagers"] = safe_json_serialize(team.get("teamManagers", []))
            
            if existing_team:
                # Construir query de atualização dinâmica
                update_cols = [f"{col} = ?" for col in data_dict.keys() if col != "id"]
                if not update_cols:  # Se não houver colunas para atualizar
                    continue
                    
                update_query = f"UPDATE teams SET {', '.join(update_cols)} WHERE id = ?"
                update_values = [data_dict[col] for col in data_dict.keys() if col != "id"]
                update_values.append(team_id)  # Adicionar o ID para a cláusula WHERE
                
                cursor.execute(update_query, update_values)
                updated += 1
            else:
                # Construir query de inserção dinâmica
                columns = list(data_dict.keys())
                placeholders = ["?" for _ in columns]
                
                insert_query = f"INSERT INTO teams ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                insert_values = [data_dict[col] for col in columns]
                
                cursor.execute(insert_query, insert_values)
                inserted += 1
        
        conn.commit()
        print(f"Times inseridos: {inserted}, atualizados: {updated}")
    
    except Exception as e:
        print(f"Erro ao salvar times no banco de dados: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE TIMES ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela teams se não existir e obter colunas disponíveis
    available_columns = create_teams_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar times
    teams = get_teams(token, base_url)
    
    # Salvar times no banco de dados
    save_teams_to_db(teams, available_columns)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de times processados: {len(teams)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
