#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para depurar a criação do banco de dados
"""

import os
import traceback
import json
from auvo_database import AuvoDatabase

def main():
    """Função para depurar a criação do banco de dados"""
    
    # Verifica se o banco de dados já existe e o remove para demonstração
    db_file = "auvo.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Banco de dados existente removido: {db_file}")
    
    # Inicializa o banco de dados
    print("Inicializando banco de dados...")
    db = AuvoDatabase(db_file=db_file, auto_connect=True)
    
    # Desativar temporariamente a verificação de chaves estrangeiras
    db.cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Lista de métodos para criar tabelas na ordem correta
    table_methods = [
        'create_users_table',
        'create_segments_table',
        'create_teams_table',
        'create_keywords_table',
        'create_questionnaires_table',
        'create_equipment_categories_table',
        'create_product_categories_table',
        'create_services_table',
        'create_customers_table',
        'create_task_types_table',
        'create_tasks_table',
        'create_webhooks_table',
        'create_expense_types_table',
        'create_expenses_table',
        'create_gps_table',
        'create_satisfaction_surveys_table',
        'create_equipments_table',
        'create_products_table',
        'create_quotations_table',
        'create_tickets_table',
        'create_service_orders_table'
    ]
    
    # Tenta criar cada tabela individualmente com tratamento de exceções
    for method_name in table_methods:
        try:
            method = getattr(db, method_name)
            method()
        except Exception as e:
            print(f"ERRO ao criar tabela {method_name}: {e}")
            traceback.print_exc()
            break
    
    # Reativar a verificação de chaves estrangeiras
    db.cursor.execute("PRAGMA foreign_keys = ON")
    db.conn.commit()
    
    # Tenta inserir um usuário de teste
    try:
        print("\nInserindo usuário de teste...")
        user_data = {
            "userId": 1,
            "name": "João Silva",
            "email": "joao.silva@exemplo.com",
            "login": "joao.silva",
            "active": 1,  # Boolean como INTEGER (0/1)
            "smartphoneNumber": "+5511999999999",
            "culture": "pt-BR",
            "jobPosition": "Técnico de Campo"
        }
        
        # Inserindo o usuário no banco de dados
        db.cursor.execute('''
        INSERT INTO users (userId, name, email, login, smartphoneNumber, culture, jobPosition)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_data["userId"], user_data["name"], user_data["email"], 
            user_data["login"], user_data["smartphoneNumber"], user_data["culture"],
            user_data["jobPosition"]
        ))
        db.conn.commit()
        print("Usuário inserido com sucesso!")
        
        # Verificando se o usuário foi inserido corretamente
        db.cursor.execute("SELECT userId, name, email FROM users WHERE userId = ?", (1,))
        user = db.cursor.fetchone()
        if user:
            print(f"Usuário encontrado: ID={user[0]}, Nome={user[1]}, Email={user[2]}")
        else:
            print("Usuário não encontrado!")
    except Exception as e:
        print(f"ERRO ao inserir usuário: {e}")
        traceback.print_exc()
    
    # Fechando a conexão com o banco de dados
    db.close()
    print("\nBanco de dados fechado.")
    print("Depuração concluída!")

if __name__ == "__main__":
    main()
