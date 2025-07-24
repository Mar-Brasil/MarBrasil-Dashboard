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

def create_segments_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cria a tabela com apenas o campo id se não existir
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='segments'")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("Criando tabela 'segments'...")
        cursor.execute('''CREATE TABLE segments (id INTEGER PRIMARY KEY)''')
        conn.commit()
        print("Tabela 'segments' criada com sucesso!")
    # Retorna as colunas atuais
    cursor.execute("PRAGMA table_info(segments)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    conn.close()
    return column_names


def get_segments(token, base_url):
    """Busca segmentos da API Auvo com paginação."""
    url = f"{base_url}/segments"
    headers = get_api_headers(token)
    
    # Usar função comum de paginação
    return paginate_api_request(url, headers, "segmentos")

def save_segments_to_db(segments, _):
    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for segment in segments:
            if not isinstance(segment, dict):
                print(f"Aviso: Item não é um dicionário: {segment}")
                continue
            segment_id = segment.get("id")
            if segment_id is None:
                print(f"Aviso: Item sem ID válido: {segment}")
                continue
            # Atualiza schema dinamicamente
            cursor.execute("PRAGMA table_info(segments)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            for key in segment.keys():
                if key not in existing_columns:
                    print(f"Adicionando coluna '{key}' à tabela 'segments'...")
                    cursor.execute(f"ALTER TABLE segments ADD COLUMN {key} TEXT")
                    conn.commit()
            # Prepara linha para salvar
            row = {}
            for key, value in segment.items():
                if isinstance(value, (dict, list)):
                    row[key] = safe_json_serialize(value)
                else:
                    row[key] = value
            fields = ', '.join(row.keys())
            placeholders = ', '.join(['?'] * len(row))
            values = list(row.values())
            cursor.execute("SELECT id FROM segments WHERE id = ?", (segment_id,))
            existing = cursor.fetchone()
            if existing:
                set_clause = ', '.join([f"{k} = ?" for k in row.keys()])
                cursor.execute(f"UPDATE segments SET {set_clause} WHERE id = ?", values + [segment_id])
                updated += 1
            else:
                cursor.execute(f"INSERT INTO segments ({fields}) VALUES ({placeholders})", values)
                inserted += 1
        conn.commit()
        print(f"Segmentos inseridos: {inserted}, atualizados: {updated}")
    except Exception as e:
        print(f"Erro ao salvar segmentos no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    print("=== DOWNLOAD DE SEGMENTOS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela segments se não existir e obter colunas disponíveis
    available_columns = create_segments_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar segmentos
    segments = get_segments(token, base_url)
    
    # Salvar segmentos no banco de dados
    save_segments_to_db(segments, available_columns)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de segmentos processados: {len(segments)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
