#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para exportar informações do banco de dados para um arquivo de texto
"""

import os
import sqlite3
import datetime

def main():
    """Função para exportar informações do banco de dados para um arquivo de texto"""
    
    # Verificar se o banco de dados existe
    db_file = "auvo.db"
    if not os.path.exists(db_file):
        print(f"Banco de dados não encontrado: {db_file}")
        return
    
    # Nome do arquivo de saída
    output_file = "db_info.txt"
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Abrir arquivo para escrita
    with open(output_file, 'w', encoding='utf-8') as f:
        # Escrever cabeçalho
        f.write("=== RELATÓRIO DO BANCO DE DADOS AUVO ===\n")
        f.write(f"Data/Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Arquivo do banco: {os.path.abspath(db_file)}\n\n")
        
        # Listar todas as tabelas
        f.write("=== TABELAS NO BANCO DE DADOS ===\n\n")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        f.write(f"Total de tabelas: {len(tables)}\n\n")
        
        f.write("Lista de tabelas:\n")
        for i, table in enumerate(tables, 1):
            f.write(f"{i}. {table[0]}\n")
        
        # Para cada tabela, listar sua estrutura
        f.write("\n=== ESTRUTURA DAS TABELAS ===\n")
        for table in tables:
            table_name = table[0]
            f.write(f"\nTabela: {table_name}\n")
            f.write("-" * (len(table_name) + 8) + "\n")
            
            # Obter informações sobre as colunas
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Escrever cabeçalho das colunas
            f.write(f"{'Nome':<20} {'Tipo':<15} {'NotNull':<8} {'PK':<4} {'Default':<15}\n")
            f.write("-" * 65 + "\n")
            
            # Escrever informações de cada coluna
            for col in columns:
                col_id, name, type_, not_null, default_val, pk = col
                f.write(f"{name:<20} {type_:<15} {not_null:<8} {pk:<4} {str(default_val):<15}\n")
            
            # Verificar chaves estrangeiras
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            
            if fks:
                f.write("\nChaves Estrangeiras:\n")
                f.write(f"{'Coluna':<20} {'Tabela Ref.':<20} {'Coluna Ref.':<20}\n")
                f.write("-" * 65 + "\n")
                
                for fk in fks:
                    _, _, ref_table, from_col, to_col, _, _, _ = fk
                    f.write(f"{from_col:<20} {ref_table:<20} {to_col:<20}\n")
        
        # Verificar se há dados na tabela users
        f.write("\n=== DADOS NA TABELA USERS ===\n\n")
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        f.write(f"Total de registros: {count}\n\n")
        
        if count > 0:
            cursor.execute("SELECT userId, name, email, jobPosition FROM users")
            users = cursor.fetchall()
            
            f.write(f"{'ID':<5} {'Nome':<30} {'Email':<30} {'Cargo':<20}\n")
            f.write("-" * 85 + "\n")
            
            for user in users:
                f.write(f"{user[0]:<5} {user[1]:<30} {user[2]:<30} {user[3]:<20}\n")
    
    # Fechar a conexão
    conn.close()
    
    print(f"Informações do banco de dados exportadas para {output_file}")
    print("Exportação concluída!")

if __name__ == "__main__":
    main()
