#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar as tabelas criadas no banco de dados
"""

import os
import sqlite3

def main():
    """Função para verificar as tabelas criadas no banco de dados"""
    
    # Verificar se o banco de dados existe
    db_file = "auvo.db"
    if not os.path.exists(db_file):
        print(f"Banco de dados não encontrado: {db_file}")
        return
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Verificar as tabelas criadas
    print("\n=== TABELAS NO BANCO DE DADOS ===\n")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"Total de tabelas: {len(tables)}")
    
    print("\nLista de tabelas:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table[0]}")
    
    # Verificar estrutura de algumas tabelas importantes
    print("\n=== ESTRUTURA DA TABELA USERS ===\n")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Coluna: {col[1]}, Tipo: {col[2]}")
    
    print("\n=== ESTRUTURA DA TABELA TASKS ===\n")
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Coluna: {col[1]}, Tipo: {col[2]}")
    
    # Verificar se há dados na tabela users
    print("\n=== DADOS NA TABELA USERS ===\n")
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"Total de registros: {count}")
    
    if count > 0:
        cursor.execute("SELECT userId, name, email, jobPosition FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"ID: {user[0]}, Nome: {user[1]}, Email: {user[2]}, Cargo: {user[3]}")
    
    # Fechar a conexão
    conn.close()
    print("\nVerificação concluída!")

if __name__ == "__main__":
    main()
