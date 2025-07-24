import sqlite3
import json

def inspect_table(table_name):
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    print(f"\n=== Estrutura da tabela {table_name} ===")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Coluna: {col[1]}, Tipo: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
    
    print(f"\n=== Definição SQL da tabela {table_name} ===")
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()
    if result:
        print(result[0])
    else:
        print(f"Tabela {table_name} não encontrada")
    
    print("\n=== Índices da tabela ===")
    cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
    indexes = cursor.fetchall()
    if indexes:
        for idx in indexes:
            print(f"Nome: {idx[0]}")
            print(f"SQL: {idx[1]}")
    else:
        print(f"Nenhum índice encontrado para a tabela {table_name}")
    
    conn.close()

if __name__ == "__main__":
    inspect_table("customers")
