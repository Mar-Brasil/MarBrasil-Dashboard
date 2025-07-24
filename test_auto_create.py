#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar a criação automática das tabelas
"""

import os
import sys
import json
import traceback
import time
from auvo_database import AuvoDatabase

def print_flush(message):
    """Imprime uma mensagem e força o flush do buffer de saída"""
    print(message)
    sys.stdout.flush()
    time.sleep(0.1)  # Pequena pausa para garantir que a saída seja exibida corretamente

def main():
    """Função para testar a criação automática das tabelas"""
    
    # Verifica se o banco de dados já existe e o remove para demonstração
    db_file = "auvo_auto.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print_flush(f"Banco de dados existente removido: {db_file}")
    
    # Inicializa o banco de dados com criação automática das tabelas
    print_flush("\n=== INICIALIZANDO BANCO DE DADOS ===\n")
    print_flush("Criando banco de dados com criação automática das tabelas...")
    
    # Criação do banco de dados
    db = AuvoDatabase(db_file=db_file, auto_connect=True, create_tables=True)
    
    # Verificar se as tabelas foram criadas
    print_flush("\n=== VERIFICANDO TABELAS CRIADAS ===\n")
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = db.cursor.fetchall()
    print_flush(f"Total de tabelas criadas: {len(tables)}")
    
    print_flush("\nLista de tabelas:")
    table_list = []
    for i, table in enumerate(tables, 1):
        table_list.append(f"{i}. {table[0]}")
    
    # Exibir todas as tabelas de uma vez
    print_flush("\n".join(table_list))
    
    # Inserir um usuário de teste
    try:
        print_flush("\n=== INSERINDO DADOS DE TESTE ===\n")
        db.cursor.execute('''
        INSERT INTO users (userId, name, email, login, smartphoneNumber, culture, jobPosition)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            1, "João Silva", "joao.silva@exemplo.com", "joao.silva", 
            "+5511999999999", "pt-BR", "Técnico de Campo"
        ))
        db.conn.commit()
        print_flush("Usuário inserido com sucesso!")
        
        # Verificar se o usuário foi inserido
        db.cursor.execute("SELECT userId, name, email FROM users")
        user = db.cursor.fetchone()
        if user:
            print_flush(f"Usuário encontrado: ID={user[0]}, Nome={user[1]}, Email={user[2]}")
    except Exception as e:
        print_flush(f"ERRO ao inserir usuário: {e}")
        traceback.print_exc()
    
    # Fechar a conexão
    db.close()
    print_flush("\n=== FINALIZAÇÃO ===\n")
    print_flush("Banco de dados fechado.")
    print_flush("Teste concluído com sucesso!")

if __name__ == "__main__":
    main()
