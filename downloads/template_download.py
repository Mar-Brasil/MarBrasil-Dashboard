"""
Template para criação de novos scripts de download da API Auvo.
Substitua ENTITY_NAME pelo nome da entidade (ex: users, tasks, etc.)
"""
import os
import sys
import sqlite3
from datetime import datetime

# Importar utilitários e funções comuns
from downloads.utils import get_db_connection
from downloads.common import login_to_auvo, get_api_headers, safe_json_serialize, process_api_response, paginate_api_request

def create_table():
    """Cria ou atualiza a tabela no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Nome da tabela
    table_name = "ENTITY_NAME"
    
    # Verificar se a tabela já existe
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print(f"Criando tabela '{table_name}'...")
        cursor.execute(f'''
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY,
            description TEXT,
            active INTEGER,
            creationDate TEXT,
            dateLastUpdate TEXT
            -- Adicione outras colunas conforme necessário
        )
        ''')
        conn.commit()
        print(f"Tabela '{table_name}' criada com sucesso!")
    else:
        # Verificar todas as colunas necessárias
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print(f"Colunas existentes na tabela '{table_name}': {column_names}")
        
        # Adicionar colunas que não existem
        required_columns = ['description', 'active', 'creationDate', 'dateLastUpdate']
        
        for column in required_columns:
            if column not in column_names:
                print(f"Adicionando coluna '{column}' à tabela '{table_name}'...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} TEXT")
                conn.commit()
            
        print(f"Tabela '{table_name}' já existe e foi atualizada se necessário.")
    
    conn.close()
    return column_names

def get_data(token, base_url):
    """Busca dados da API Auvo com paginação."""
    url = f"{base_url}/ENTITY_NAME"  # Substitua pelo endpoint correto
    headers = get_api_headers(token)
    
    # Usar função comum de paginação
    return paginate_api_request(url, headers, "ENTITY_NAME")

def save_to_db(data_list, available_columns):
    """Salva os dados no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for item in data_list:
        # Verificar se o registro já existe
        cursor.execute("SELECT id FROM ENTITY_NAME WHERE id = ?", (item.get('id'),))
        exists = cursor.fetchone()
        
        # Preparar os valores para inserção/atualização
        values = {}
        for key, value in item.items():
            if key in available_columns:
                values[key] = safe_json_serialize(value)
        
        if not exists:
            # Inserir novo registro
            columns = ', '.join(values.keys())
            placeholders = ', '.join(['?' for _ in values])
            query = f"INSERT INTO ENTITY_NAME ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(values.values()))
            inserted += 1
        else:
            # Atualizar registro existente
            set_clause = ', '.join([f"{key} = ?" for key in values.keys()])
            query = f"UPDATE ENTITY_NAME SET {set_clause} WHERE id = ?"
            cursor.execute(query, list(values.values()) + [item.get('id')])
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"ENTITY_NAME inseridos: {inserted}, atualizados: {updated}")
    return inserted, updated

def main():
    print(f"=== DOWNLOAD DE ENTITY_NAME ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar ou verificar tabela
    available_columns = create_table()
    
    # Fazer login na API
    token, base_url = login_to_auvo()
    
    # Buscar dados
    data_list = get_data(token, base_url)
    
    # Salvar no banco de dados
    inserted, updated = save_to_db(data_list, available_columns)
    
    # Resumo da operação
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de ENTITY_NAME processados: {len(data_list)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
