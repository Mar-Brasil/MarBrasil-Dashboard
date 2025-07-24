#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para inserir dados de exemplo no banco de dados Auvo
"""

import os
import json
import datetime
import random
from auvo_database import AuvoDatabase

def insert_sample_users(db):
    """Insere usuários de exemplo no banco de dados"""
    print("Inserindo usuários de exemplo...")
    
    users = [
        (1, "João Silva", "+5511999999999", "joao.silva", "joao.silva@exemplo.com", "pt-BR", "Técnico de Campo"),
        (2, "Maria Oliveira", "+5511888888888", "maria.oliveira", "maria.oliveira@exemplo.com", "pt-BR", "Técnico de Suporte"),
        (3, "Carlos Santos", "+5511777777777", "carlos.santos", "carlos.santos@exemplo.com", "pt-BR", "Gerente de Campo"),
        (4, "Ana Pereira", "+5511666666666", "ana.pereira", "ana.pereira@exemplo.com", "pt-BR", "Atendente"),
        (5, "Roberto Almeida", "+5511555555555", "roberto.almeida", "roberto.almeida@exemplo.com", "pt-BR", "Técnico Especialista")
    ]
    
    for user in users:
        try:
            db.cursor.execute('''
            INSERT OR REPLACE INTO users (userId, name, smartphoneNumber, login, email, culture, jobPosition)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', user)
        except Exception as e:
            print(f"Erro ao inserir usuário {user[1]}: {e}")
    
    db.conn.commit()
    print(f"Inseridos {len(users)} usuários com sucesso!")

def insert_sample_segments(db):
    """Insere segmentos de exemplo no banco de dados"""
    print("Inserindo segmentos de exemplo...")
    
    segments = [
        (1, "Residencial"),
        (2, "Comercial"),
        (3, "Industrial"),
        (4, "Governamental"),
        (5, "Educacional")
    ]
    
    for segment in segments:
        try:
            db.cursor.execute('''
            INSERT OR REPLACE INTO segments (id, description)
            VALUES (?, ?)
            ''', segment)
        except Exception as e:
            print(f"Erro ao inserir segmento {segment[1]}: {e}")
    
    db.conn.commit()
    print(f"Inseridos {len(segments)} segmentos com sucesso!")

def insert_sample_teams(db):
    """Insere equipes de exemplo no banco de dados"""
    print("Inserindo equipes de exemplo...")
    
    teams = [
        (1, "Equipe Suporte Técnico", json.dumps([1, 2]), json.dumps([3])),
        (2, "Equipe Manutenção", json.dumps([4, 5]), json.dumps([3])),
        (3, "Equipe Instalação", json.dumps([1, 5]), json.dumps([3]))
    ]
    
    for team in teams:
        try:
            db.cursor.execute('''
            INSERT OR REPLACE INTO teams (id, description, teamUsers, teamManagers)
            VALUES (?, ?, ?, ?)
            ''', team)
        except Exception as e:
            print(f"Erro ao inserir equipe {team[1]}: {e}")
    
    db.conn.commit()
    print(f"Inseridas {len(teams)} equipes com sucesso!")

def insert_sample_customers(db):
    """Insere clientes de exemplo no banco de dados"""
    print("Inserindo clientes de exemplo...")
    
    customers = [
        (1, "CUST001", "Empresa ABC Ltda", "12345678000199", "+551133334444", "contato@empresaabc.com.br", 
         "José Gerente", "Diretor", "Cliente VIP", "Av. Paulista, 1000, São Paulo, SP", 
         -23.5505, -46.6333, 120, 60, None, None, None, 2, 1, "Sala 1010", 
         datetime.datetime.now().isoformat(), None, datetime.datetime.now().isoformat(), None),
        
        (2, "CUST002", "Comércio XYZ S/A", "98765432000188", "+551144445555", "contato@comercioxyz.com.br", 
         "Maria Gestora", "Gerente Geral", "Cliente Novo", "Av. Brasil, 500, Rio de Janeiro, RJ", 
         -22.9068, -43.1729, 90, 45, None, None, None, 1, 1, "Térreo", 
         datetime.datetime.now().isoformat(), None, datetime.datetime.now().isoformat(), None),
        
        (3, "CUST003", "Indústria 123 S/A", "45678912000177", "+551155556666", "contato@industria123.com.br", 
         "Pedro Diretor", "Diretor Industrial", "Cliente Antigo", "Rod. Anhanguera, Km 100, Campinas, SP", 
         -22.9099, -47.0626, 180, 90, None, None, None, 3, 1, "Galpão 5", 
         datetime.datetime.now().isoformat(), None, datetime.datetime.now().isoformat(), None)
    ]
    
    for customer in customers:
        try:
            db.cursor.execute('''
            INSERT OR REPLACE INTO customers (id, externalId, description, cpfCnpj, phoneNumber, email,
            manager, managerJobPosition, note, address, latitude, longitude, maximumVisitTime,
            unitMaximumTime, groupsId, managerTeamsId, managersId, segmentId, active, adressComplement,
            creationDate, contacts, dateLastUpdate, uriAnexos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', customer)
        except Exception as e:
            print(f"Erro ao inserir cliente {customer[2]}: {e}")
    
    db.conn.commit()
    print(f"Inseridos {len(customers)} clientes com sucesso!")

def insert_sample_task_types(db):
    """Insere tipos de tarefas de exemplo no banco de dados"""
    print("Inserindo tipos de tarefas de exemplo...")
    
    task_types = [
        (1, "Instalação", 1),
        (2, "Manutenção Preventiva", 1),
        (3, "Manutenção Corretiva", 1),
        (4, "Vistoria", 1),
        (5, "Suporte Técnico", 1)
    ]
    
    for task_type in task_types:
        try:
            db.cursor.execute('''
            INSERT OR REPLACE INTO task_types (id, description, active)
            VALUES (?, ?, ?)
            ''', task_type)
        except Exception as e:
            print(f"Erro ao inserir tipo de tarefa {task_type[1]}: {e}")
    
    db.conn.commit()
    print(f"Inseridos {len(task_types)} tipos de tarefas com sucesso!")

def insert_sample_tasks(db):
    """Insere tarefas de exemplo no banco de dados"""
    print("Inserindo tarefas de exemplo...")
    
    # Data atual para referência
    now = datetime.datetime.now()
    
    # Algumas datas para usar nas tarefas
    tomorrow = now + datetime.timedelta(days=1)
    yesterday = now - datetime.timedelta(days=1)
    next_week = now + datetime.timedelta(days=7)
    
    # Consultar nomes dos usuários e clientes para preencher os campos de nome
    db.cursor.execute("SELECT userId, name FROM users WHERE userId = 1")
    user1 = db.cursor.fetchone()
    user1_name = user1[1] if user1 else "Usuário 1"
    
    db.cursor.execute("SELECT userId, name FROM users WHERE userId = 2")
    user2 = db.cursor.fetchone()
    user2_name = user2[1] if user2 else "Usuário 2"
    
    db.cursor.execute("SELECT userId, name FROM users WHERE userId = 3")
    user3 = db.cursor.fetchone()
    user3_name = user3[1] if user3 else "Usuário 3"
    
    db.cursor.execute("SELECT id, description FROM customers WHERE id = 1")
    customer1 = db.cursor.fetchone()
    customer1_name = customer1[1] if customer1 else "Cliente 1"
    
    db.cursor.execute("SELECT id, description FROM customers WHERE id = 2")
    customer2 = db.cursor.fetchone()
    customer2_name = customer2[1] if customer2 else "Cliente 2"
    
    db.cursor.execute("SELECT id, description FROM customers WHERE id = 3")
    customer3 = db.cursor.fetchone()
    customer3_name = customer3[1] if customer3 else "Cliente 3"
    
    # Definir exatamente 59 valores para cada tarefa (correspondendo às 59 colunas da tabela tasks)
    tasks = [
        # Tarefa 1
        (1, "TASK001", 1, 3, user3_name, user1_name, 1, "CUST001", customer1_name, 
         1, "Instalação", now.isoformat(), tomorrow.isoformat(), -23.5505, -46.6333, 
         "Av. Paulista, 1000, São Paulo, SP", "Procurar o Sr. José na recepção", 2, 
         0, None, 0, None, 0, None, 0, None, 0, None, 0, None, None, None, 0.0, 0.0, 
         None, None, None, 0.0, 0.0, 0, None, None, None, now.isoformat(), None, None, 
         None, None, None, None, None, None, None, None, None, None, None, None, 1),
        
        # Tarefa 2
        (2, "TASK002", 1, 1, user1_name, user3_name, 2, "CUST002", customer2_name, 
         2, "Manutenção Preventiva", now.isoformat(), next_week.isoformat(), -22.9068, -43.1729, 
         "Av. Brasil, 500, Rio de Janeiro, RJ", "Agendar com a recepção", 1, 
         0, None, 0, None, 0, None, 0, None, 0, None, 0, None, None, None, 0.0, 0.0, 
         None, None, None, 0.0, 0.0, 0, None, None, None, now.isoformat(), None, None, 
         None, None, None, None, None, None, None, None, None, None, None, None, 1),
        
        # Tarefa 3 - Concluída
        (3, "TASK003", 2, 2, user2_name, user1_name, 3, "CUST003", customer3_name, 
         5, "Suporte Técnico", now.isoformat(), yesterday.isoformat(), -22.9099, -47.0626, 
         "Rod. Anhanguera, Km 100, Campinas, SP", "Procurar o Sr. Pedro", 3, 
         1, now.isoformat(), 1, "Sistema reiniciado e funcionando normalmente", 1, now.isoformat(), 
         1, now.isoformat(), 1, now.isoformat(), 1, "Checkin manual", None, None, 15.5, 15.5, 
         None, None, None, 0.1, 0.1, 0, None, None, None, now.isoformat(), None, None, 
         None, None, None, "2:30", "2.5", None, None, None, None, None, None, None, 2)
    ]
    
    for task in tasks:
        try:
            # Verificar o número de valores e colunas para depuração
            num_values = len(task)
            print(f"Número de valores na tarefa: {num_values}")
            
            # Consulta SQL com exatamente 59 placeholders (um para cada coluna)
            db.cursor.execute('''
            INSERT OR REPLACE INTO tasks (
                taskID, externalId, idUserFrom, idUserTo, userToName, userFromName, 
                customerId, customerExternalId, customerDescription, taskType, taskTypeDescription, 
                creationDate, taskDate, latitude, longitude, address, orientation, priority, 
                deliveredOnSmarthPhone, deliveredDate, finished, report, visualized, visualizedDate, 
                checkIn, checkInDate, checkOut, checkOutDate, checkinType, equipmentsId, keyWords, 
                keyWordsDescriptions, inputedKm, adoptedKm, attachments, questionnaires, signatureUrl, 
                checkInDistance, checkOutDistance, sendSatisfactionSurvey, survey, taskUrl, pendency, 
                dateLastUpdate, ticketId, ticketTitle, signatureName, signatureDocument, expense, 
                duration, durationDecimal, displacementStart, products, services, additionalCosts, 
                summary, estimatedDuration, financialCategory, taskStatus
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?)
            ''', task)
        except Exception as e:
            print(f"Erro ao inserir tarefa {task[1]}: {e}")
            import traceback
            traceback.print_exc()
    
    db.conn.commit()
    print(f"Inseridas {len(tasks)} tarefas com sucesso!")

def main():
    """Função principal para inserir dados de exemplo no banco de dados"""
    
    # Verificar se o banco de dados existe
    db_file = "auvo.db"
    if not os.path.exists(db_file):
        print(f"Banco de dados não encontrado: {db_file}")
        print("Criando novo banco de dados...")
        db = AuvoDatabase(db_file=db_file, auto_connect=True, create_tables=True)
    else:
        print(f"Conectando ao banco de dados existente: {db_file}")
        db = AuvoDatabase(db_file=db_file, auto_connect=True)
    
    # Inserir dados de exemplo
    try:
        print("\n=== INSERINDO DADOS DE EXEMPLO ===\n")
        
        # Inserir dados nas tabelas independentes primeiro
        insert_sample_users(db)
        insert_sample_segments(db)
        insert_sample_teams(db)
        
        # Depois inserir dados nas tabelas com dependências
        insert_sample_customers(db)
        insert_sample_task_types(db)
        insert_sample_tasks(db)
        
        print("\nTodos os dados de exemplo foram inseridos com sucesso!")
    except Exception as e:
        print(f"\nERRO ao inserir dados de exemplo: {e}")
        import traceback
        traceback.print_exc()
    
    # Fechar a conexão
    db.close()
    print("\nBanco de dados fechado.")
    print("Processo concluído!")

if __name__ == "__main__":
    main()
