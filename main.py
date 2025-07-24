#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal para demonstrar o uso da classe AuvoDatabase
"""

import os
import json
import traceback
from auvo_database import AuvoDatabase

def main():
    """Função principal para demonstrar o uso da classe AuvoDatabase"""
    
    # Verifica se o banco de dados já existe e o remove para demonstração
    db_file = "auvo.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Banco de dados existente removido: {db_file}")
    
    # Inicializa o banco de dados
    print("Inicializando banco de dados...")
    db = AuvoDatabase(db_file=db_file, auto_connect=True)
    
    # Criar tabelas manualmente na ordem correta
    try:
        # Desativar temporariamente a verificação de chaves estrangeiras
        db.cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Primeiro as tabelas independentes (sem foreign keys)
        print("\nCriando tabelas independentes...")
        db.create_users_table()
        db.create_segments_table()
        db.create_teams_table()
        db.create_keywords_table()
        db.create_questionnaires_table()
        db.create_equipment_categories_table()
        db.create_product_categories_table()
        db.create_services_table()
        
        # Depois as tabelas com dependências
        print("\nCriando tabelas com dependências...")
        db.create_customers_table()
        db.create_task_types_table()
        db.create_tasks_table()
        db.create_webhooks_table()
        db.create_expense_types_table()
        db.create_expenses_table()
        db.create_gps_table()
        db.create_satisfaction_surveys_table()
        db.create_equipments_table()
        db.create_products_table()
        db.create_quotations_table()
        db.create_tickets_table()
        db.create_service_orders_table()
        
        # Reativar a verificação de chaves estrangeiras
        db.cursor.execute("PRAGMA foreign_keys = ON")
        db.conn.commit()
        print("\nTodas as tabelas foram criadas com sucesso!")
    except Exception as e:
        print(f"\nERRO ao criar tabelas: {e}")
        traceback.print_exc()
        db.close()
        return
    
    # Exemplo de como inserir dados de usuário
    try:
        print("\nInserindo dados de exemplo...")
        
        # Exemplo de inserção de um usuário
        user_data = {
            "userId": 1,
            "name": "João Silva",
            "email": "joao.silva@exemplo.com",
            "login": "joao.silva",
            "active": True,
            "smartphoneNumber": "+5511999999999",
            "culture": "pt-BR",
            "jobPosition": "Técnico de Campo"
        }
        
        # Convertendo booleanos para inteiros (0/1) para SQLite
        user_data["active"] = 1 if user_data["active"] else 0
        
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
        db.cursor.execute("SELECT * FROM users")
        users = db.cursor.fetchall()
        print(f"Usuários no banco de dados: {len(users)}")
        
        # Exemplo de consulta
        print("\nConsultando usuário inserido:")
        db.cursor.execute("SELECT userId, name, email, jobPosition FROM users WHERE userId = ?", (1,))
        user = db.cursor.fetchone()
        if user:
            print(f"ID: {user[0]}")
            print(f"Nome: {user[1]}")
            print(f"Email: {user[2]}")
            print(f"Cargo: {user[3]}")
    except Exception as e:
        print(f"\nERRO ao inserir dados: {e}")
        traceback.print_exc()
    
    # Fechando a conexão com o banco de dados
    db.close()
    print("\nBanco de dados fechado.")
    print("Demonstração concluída com sucesso!")

if __name__ == "__main__":
    main()
