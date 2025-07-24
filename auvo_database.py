import sqlite3
import os
import json
import requests
from datetime import datetime

class AuvoDatabase:
    """Classe para gerenciar o banco de dados SQLite da API Auvo"""
    
    def __init__(self, db_file="auvo.db", auto_connect=True, create_tables=False):
        """Inicializa a conexão com o banco de dados
        
        Args:
            db_file (str): Nome do arquivo do banco de dados SQLite
            auto_connect (bool): Se True, conecta automaticamente ao banco de dados
            create_tables (bool): Se True, cria todas as tabelas automaticamente
        """
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        
        if auto_connect:
            self.connect()
            
        if create_tables and self.conn is not None:
            self.create_all_tables()
        
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        print(f"Conectado ao banco de dados: {self.db_file}")
        
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
            print("Conexão com o banco de dados fechada")
            
    def create_tables(self):
        """Cria todas as tabelas necessárias no banco de dados (método obsoleto, use create_all_tables)"""
        # Método mantido para compatibilidade, mas agora apenas chama create_all_tables
        self.create_all_tables()
        
    def create_users_table(self):
        """Cria a tabela de usuários baseada no endpoint /users"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userId INTEGER PRIMARY KEY,
            externalId TEXT,
            name TEXT,
            smartphoneNumber TEXT,
            login TEXT,
            email TEXT,
            culture TEXT,
            jobPosition TEXT,
            userTypeId INTEGER,
            userTypeDescription TEXT,
            workDaysOfWeek TEXT,  -- Armazenado como JSON string
            startWorkHour TEXT,
            endWorkHour TEXT,
            startLunchHour TEXT,
            endLunchHour TEXT,
            hourValue REAL,
            pictureUrl TEXT,
            basePointAddress TEXT,
            basePointLatitude REAL,
            basePointLongitude REAL,
            openTaskInPlace INTEGER,  -- Boolean como INTEGER (0/1)
            grabGalleryPhotos INTEGER,  -- Boolean como INTEGER (0/1)
            gpsFrequency INTEGER,
            checkInManual INTEGER,  -- Boolean como INTEGER (0/1)
            unavailableForTasks INTEGER,  -- Boolean como INTEGER (0/1)
            editTaskAfterCheckout INTEGER,  -- Boolean como INTEGER (0/1)
            informStartTravel INTEGER,  -- Boolean como INTEGER (0/1)
            changeBasePoint INTEGER,  -- Boolean como INTEGER (0/1)
            monitoringNotification TEXT,  -- Armazenado como JSON string
            employeeNotification TEXT,  -- Armazenado como JSON string
            clientNotification TEXT,  -- Armazenado como JSON string
            taskNotification TEXT,  -- Armazenado como JSON string
            lastUpdate TIMESTAMP
        )
        ''')
        self.conn.commit()
        print("Tabela 'users' criada com sucesso")
        
    def create_tasks_table(self):
        """Cria a tabela de tarefas baseada no endpoint /tasks"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            taskID INTEGER PRIMARY KEY,
            externalId TEXT,
            idUserFrom INTEGER,
            idUserTo INTEGER,
            userToName TEXT,
            userFromName TEXT,
            customerId INTEGER,
            customerExternalId TEXT,
            customerDescription TEXT,
            taskType INTEGER,
            taskTypeDescription TEXT,
            creationDate TIMESTAMP,
            taskDate TIMESTAMP,
            latitude REAL,
            longitude REAL,
            address TEXT,
            orientation TEXT,
            priority INTEGER,
            deliveredOnSmarthPhone INTEGER,  -- Boolean como INTEGER (0/1)
            deliveredDate TIMESTAMP,
            finished INTEGER,  -- Boolean como INTEGER (0/1)
            report TEXT,
            visualized INTEGER,  -- Boolean como INTEGER (0/1)
            visualizedDate TIMESTAMP,
            checkIn INTEGER,  -- Boolean como INTEGER (0/1)
            checkInDate TIMESTAMP,
            checkOut INTEGER,  -- Boolean como INTEGER (0/1)
            checkOutDate TIMESTAMP,
            checkinType INTEGER,
            equipmentsId TEXT,  -- Armazenado como JSON string
            keyWords TEXT,  -- Armazenado como JSON string
            keyWordsDescriptions TEXT,  -- Armazenado como JSON string
            inputedKm REAL,
            adoptedKm REAL,
            attachments TEXT,  -- Armazenado como JSON string
            questionnaires TEXT,  -- Armazenado como JSON string
            signatureUrl TEXT,
            checkInDistance REAL,
            checkOutDistance REAL,
            sendSatisfactionSurvey INTEGER,  -- Boolean como INTEGER (0/1)
            survey TEXT,
            taskUrl TEXT,
            pendency TEXT,
            dateLastUpdate TIMESTAMP,
            ticketId INTEGER,
            ticketTitle TEXT,
            signatureName TEXT,
            signatureDocument TEXT,
            expense TEXT,
            duration TEXT,
            durationDecimal TEXT,
            displacementStart TEXT,
            products TEXT,  -- Armazenado como JSON string
            services TEXT,  -- Armazenado como JSON string
            additionalCosts TEXT,  -- Armazenado como JSON string
            summary TEXT,  -- Armazenado como JSON string
            estimatedDuration TEXT,
            financialCategory TEXT,
            taskStatus INTEGER,
            FOREIGN KEY (idUserFrom) REFERENCES users(userId),
            FOREIGN KEY (idUserTo) REFERENCES users(userId),
            FOREIGN KEY (customerId) REFERENCES customers(id)
        )
        ''')
        self.conn.commit()
        print("Tabela 'tasks' criada com sucesso")
        
    def create_customers_table(self):
        """Cria a tabela de clientes baseada no endpoint /customers"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            externalId TEXT,
            description TEXT,
            cpfCnpj TEXT,
            phoneNumber TEXT,  -- Armazenado como JSON string
            email TEXT,  -- Armazenado como JSON string
            manager TEXT,
            managerJobPosition TEXT,
            note TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            maximumVisitTime INTEGER,
            unitMaximumTime INTEGER,
            groupsId TEXT,  -- Armazenado como JSON string
            managerTeamsId TEXT,  -- Armazenado como JSON string
            managersId TEXT,  -- Armazenado como JSON string
            segmentId INTEGER,
            active INTEGER,  -- Boolean como INTEGER (0/1)
            adressComplement TEXT,
            creationDate TIMESTAMP,
            contacts TEXT,  -- Armazenado como JSON string
            dateLastUpdate TIMESTAMP,
            uriAnexos TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'customers' criada com sucesso")
        
    def create_teams_table(self):
        """Cria a tabela de equipes baseada no endpoint /teams"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            description TEXT,
            teamUsers TEXT,  -- Armazenado como JSON string
            teamManagers TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'teams' criada com sucesso")
        
    def create_task_types_table(self):
        """Cria a tabela de tipos de tarefas baseada no endpoint /taskTypes"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_types (
            id INTEGER PRIMARY KEY,
            description TEXT,
            creatorId INTEGER,
            creationDate TIMESTAMP,
            standardTime TEXT,
            toleranceTime TEXT,
            standardQuestionnaireId INTEGER,
            active INTEGER,  -- Boolean como INTEGER (0/1)
            sendSatisfactionSurvey INTEGER,  -- Boolean como INTEGER (0/1)
            requirements TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'task_types' criada com sucesso")
        
    def create_segments_table(self):
        """Cria a tabela de segmentos baseada no endpoint /segments"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY,
            description TEXT,
            registrationDate TIMESTAMP
        )
        ''')
        self.conn.commit()
        print("Tabela 'segments' criada com sucesso")
        
    def create_questionnaires_table(self):
        """Cria a tabela de questionários baseada no endpoint /questionnaires"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS questionnaires (
            id INTEGER PRIMARY KEY,
            description TEXT,
            header TEXT,
            footer TEXT,
            creationDate TIMESTAMP,
            questions TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'questionnaires' criada com sucesso")
        
    def create_keywords_table(self):
        """Cria a tabela de palavras-chave baseada no endpoint /keywords"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY,
            description TEXT,
            registrationDate TIMESTAMP
        )
        ''')
        self.conn.commit()
        print("Tabela 'keywords' criada com sucesso")
        
    def create_webhooks_table(self):
        """Cria a tabela de webhooks baseada no endpoint /webHooks"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            id TEXT PRIMARY KEY,
            userId INTEGER,
            entity TEXT,
            action TEXT,
            urlResponse TEXT,
            creationDate TIMESTAMP,
            deleteDate TIMESTAMP,
            active INTEGER,  -- Boolean como INTEGER (0/1)
            FOREIGN KEY (userId) REFERENCES users(userId)
        )
        ''')
        self.conn.commit()
        print("Tabela 'webhooks' criada com sucesso")
        
    def create_expenses_table(self):
        """Cria a tabela de despesas baseada no endpoint /expenses"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            description TEXT,
            userToId INTEGER,
            userToName TEXT,
            typeId INTEGER,
            typeName TEXT,
            date TIMESTAMP,
            attachmentUrl TEXT,
            creationDate TIMESTAMP,
            amount REAL
        )
        ''')
        self.conn.commit()
        print("Tabela 'expenses' criada com sucesso")
        
    def create_expense_types_table(self):
        """Cria a tabela de tipos de despesas baseada no endpoint /expenseTypes"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_types (
            id INTEGER PRIMARY KEY,
            description TEXT,
            creatorId INTEGER,
            creationDate TIMESTAMP
        )
        ''')
        self.conn.commit()
        print("Tabela 'expense_types' criada com sucesso")
        
    def create_gps_table(self):
        """Cria a tabela de dados GPS baseada no endpoint /gps"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS gps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            positionDate TIMESTAMP,
            latitude REAL,
            longitude REAL,
            accuracy REAL,
            batteryLevel INTEGER,
            networkOperatorName TEXT
        )
        ''')
        self.conn.commit()
        print("Tabela 'gps' criada com sucesso")
        
    def create_satisfaction_surveys_table(self):
        """Cria a tabela de pesquisas de satisfação baseada no endpoint /satisfactionSurveys"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS satisfaction_surveys (
            id INTEGER PRIMARY KEY,
            taskID INTEGER,
            answerDescription TEXT,
            questionDescription TEXT,
            answerDate TIMESTAMP,
            itemId TEXT,
            email TEXT,
            answersItemQuantity INTEGER,
            scoreSum INTEGER,
            totalResponse INTEGER,
            totalSubmitted INTEGER
        )
        ''')
        self.conn.commit()
        print("Tabela 'satisfaction_surveys' criada com sucesso")
        
    def create_equipment_categories_table(self):
        """Cria a tabela de categorias de equipamentos baseada no endpoint /equipmentCategories"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_categories (
            id INTEGER PRIMARY KEY,
            description TEXT,
            externalId TEXT
        )
        ''')
        self.conn.commit()
        print("Tabela 'equipment_categories' criada com sucesso")
        
    def create_equipments_table(self):
        """Cria a tabela de equipamentos baseada no endpoint /equipments"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipments (
            id INTEGER PRIMARY KEY,
            externalId TEXT,
            parentEquipmentId INTEGER,
            associatedCustomerId INTEGER,
            associatedUserId INTEGER,
            categoryId INTEGER,
            name TEXT,
            identifier TEXT,
            urlImage TEXT,
            uriAnexos TEXT,  -- Armazenado como JSON string
            active INTEGER,  -- Boolean como INTEGER (0/1)
            creationDate TIMESTAMP,
            expirationDate TIMESTAMP,
            equipmentSpecifications TEXT,  -- Armazenado como JSON string
            description TEXT,
            warrantyStartDate TIMESTAMP,
            warrantyEndDate TIMESTAMP
        )
        ''')
        self.conn.commit()
        print("Tabela 'equipments' criada com sucesso")
        
    def create_product_categories_table(self):
        """Cria a tabela de categorias de produtos baseada no endpoint /productCategories"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY,
            description TEXT,
            externalId TEXT
        )
        ''')
        self.conn.commit()
        print("Tabela 'product_categories' criada com sucesso")
        
    def create_products_table(self):
        """Cria a tabela de produtos baseada no endpoint /products"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            productId TEXT PRIMARY KEY,
            externalId TEXT,
            code TEXT,
            name TEXT,
            associatedEquipmentId INTEGER,
            categoryId INTEGER,
            unitaryValue TEXT,
            unitaryCost TEXT,
            totalStock INTEGER,
            active INTEGER,  -- Boolean como INTEGER (0/1)
            minimumStock TEXT,
            base64Image TEXT,
            uriAnexos TEXT,  -- Armazenado como JSON string
            productSpecifications TEXT,  -- Armazenado como JSON string
            employeesStock TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'products' criada com sucesso")
        
    def create_quotations_table(self):
        """Cria a tabela de cotações baseada no endpoint /quotations"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
            publicId INTEGER PRIMARY KEY,
            customerId INTEGER,
            customerName TEXT,
            taskID INTEGER,
            descount TEXT,
            requesterUserId INTEGER,
            observations TEXT,
            registerDate TIMESTAMP,
            requestDate TIMESTAMP,
            aditionalCosts TEXT,  -- Armazenado como JSON string
            alterations TEXT,  -- Armazenado como JSON string
            products TEXT,  -- Armazenado como JSON string
            contacts TEXT,  -- Armazenado como JSON string
            summary TEXT,  -- Armazenado como JSON string
            currentStage TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'quotations' criada com sucesso")
        

        
    def create_tickets_table(self):
        """Cria a tabela de tickets baseada no endpoint /tickets"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY,
            creationDate TIMESTAMP,
            teamId INTEGER,
            teamName TEXT,
            userCreatorId INTEGER,
            userCreatorName TEXT,
            userResponsableId INTEGER,
            userResponsableName TEXT,
            title TEXT,
            customerId TEXT,
            customerName TEXT,
            customerEmail TEXT,
            customerPhoneNumber TEXT,
            equipmentId INTEGER,
            requestTypeDescription TEXT,
            priority TEXT,
            description TEXT,
            statusDescription TEXT,
            statusType TEXT,
            endDate TIMESTAMP,
            emailMenssageId TEXT,
            requesterEmail TEXT,
            requesterName TEXT,
            taskIDs TEXT,  -- Armazenado como JSON string
            urlAttachments TEXT,  -- Armazenado como JSON string
            customFields TEXT,  -- Armazenado como JSON string
            alterations TEXT,  -- Armazenado como JSON string
            interactions TEXT,  -- Armazenado como JSON string
            statusAlterations TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'tickets' criada com sucesso")
        
    def create_services_table(self):
        """Cria a tabela de serviços baseada no endpoint /services"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY,
            description TEXT,
            externalId TEXT,
            unitaryValue REAL,
            unitaryCost REAL,
            active INTEGER,  -- Boolean como INTEGER (0/1)
            uriAnexos TEXT,  -- Armazenado como JSON string
            serviceSpecifications TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'services' criada com sucesso")
        
    def create_service_orders_table(self):
        """Cria a tabela de ordens de serviço baseada no endpoint /serviceOrders"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_orders (
            id INTEGER PRIMARY KEY,
            customerId INTEGER,
            customerName TEXT,
            taskID INTEGER,
            discount REAL,
            requesterUserId INTEGER,
            observations TEXT,
            registerDate TIMESTAMP,
            requestDate TIMESTAMP,
            executionDate TIMESTAMP,
            executionEndDate TIMESTAMP,
            executionUserId INTEGER,
            executionUserName TEXT,
            aditionalCosts TEXT,  -- Armazenado como JSON string
            alterations TEXT,  -- Armazenado como JSON string
            services TEXT,  -- Armazenado como JSON string
            products TEXT,  -- Armazenado como JSON string
            contacts TEXT,  -- Armazenado como JSON string
            summary TEXT,  -- Armazenado como JSON string
            currentStage TEXT  -- Armazenado como JSON string
        )
        ''')
        self.conn.commit()
        print("Tabela 'service_orders' criada com sucesso")
        
    def create_all_tables(self):
        """Cria todas as tabelas do banco de dados na ordem correta"""
        try:
            # Desativar temporariamente a verificação de chaves estrangeiras
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Primeiro as tabelas independentes (sem foreign keys)
            print("\nCriando tabelas independentes...")
            self.create_users_table()
            self.create_segments_table()
            self.create_teams_table()
            self.create_keywords_table()
            self.create_questionnaires_table()
            self.create_equipment_categories_table()
            self.create_product_categories_table()
            self.create_services_table()
            
            # Depois as tabelas com dependências
            print("\nCriando tabelas com dependências...")
            self.create_customers_table()
            self.create_task_types_table()
            self.create_tasks_table()
            self.create_webhooks_table()
            self.create_expense_types_table()
            self.create_expenses_table()
            self.create_gps_table()
            self.create_satisfaction_surveys_table()
            self.create_equipments_table()
            self.create_products_table()
            self.create_quotations_table()
            self.create_tickets_table()
            self.create_service_orders_table()
            
            # Reativar a verificação de chaves estrangeiras
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
            
            print("\nTodas as tabelas foram criadas com sucesso!")
            return True
        except Exception as e:
            print(f"\nERRO ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()
            return False