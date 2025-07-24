-- Esquema inicial do banco de dados relacional para sincronização da API Auvo
-- Este arquivo pode ser expandido conforme necessário

CREATE TABLE IF NOT EXISTS users (
    userId INTEGER PRIMARY KEY,
    id INTEGER UNIQUE,
    externalId TEXT,
    name TEXT,
    email TEXT,
    login TEXT,
    jobPosition TEXT
    -- outros campos relevantes
);

CREATE TABLE IF NOT EXISTS customers (
    customerId INTEGER PRIMARY KEY,
    externalId TEXT,
    name TEXT,
    email TEXT,
    phone TEXT,
    segmentId INTEGER,
    -- outros campos relevantes
    FOREIGN KEY (segmentId) REFERENCES segments(segmentId)
);

CREATE TABLE IF NOT EXISTS equipments (
    equipmentId INTEGER PRIMARY KEY,
    name TEXT,
    associatedUserId INTEGER,
    associatedCustomerId INTEGER,
    parentEquipmentId INTEGER,
    categoryId INTEGER,
    active BOOLEAN,
    creationDate TEXT,
    expirationDate TEXT,
    -- outros campos relevantes
    FOREIGN KEY (associatedUserId) REFERENCES users(userId),
    FOREIGN KEY (associatedCustomerId) REFERENCES customers(customerId),
    FOREIGN KEY (parentEquipmentId) REFERENCES equipments(equipmentId),
    FOREIGN KEY (categoryId) REFERENCES equipmentCategories(categoryId)
);

CREATE TABLE IF NOT EXISTS equipmentCategories (
    categoryId INTEGER PRIMARY KEY,
    description TEXT,
    externalId TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    taskID INTEGER PRIMARY KEY,
    idUserFrom INTEGER,
    idUserTo INTEGER,
    customerId INTEGER,
    taskType INTEGER,
    creationDate TEXT,
    taskDate TEXT,
    address TEXT,
    priority TEXT,
    -- outros campos relevantes
    FOREIGN KEY (idUserFrom) REFERENCES users(userId),
    FOREIGN KEY (idUserTo) REFERENCES users(userId),
    FOREIGN KEY (customerId) REFERENCES customers(customerId)
);

CREATE TABLE IF NOT EXISTS products (
    productId TEXT PRIMARY KEY,
    code TEXT,
    name TEXT,
    associatedEquipmentId INTEGER,
    categoryId INTEGER,
    unitaryValue TEXT,
    totalStock INTEGER,
    active BOOLEAN,
    -- outros campos relevantes
    FOREIGN KEY (associatedEquipmentId) REFERENCES equipments(equipmentId),
    FOREIGN KEY (categoryId) REFERENCES productCategories(categoryId)
);

CREATE TABLE IF NOT EXISTS productCategories (
    categoryId INTEGER PRIMARY KEY,
    description TEXT,
    externalId TEXT
);

CREATE TABLE IF NOT EXISTS serviceorders (
    id TEXT PRIMARY KEY,
    customerId INTEGER,
    defaultResponsibleId INTEGER,
    statusId TEXT,
    description TEXT,
    priority INTEGER,
    -- outros campos relevantes
    FOREIGN KEY (customerId) REFERENCES customers(customerId),
    FOREIGN KEY (defaultResponsibleId) REFERENCES users(userId)
);

CREATE TABLE IF NOT EXISTS teams (
    teamId INTEGER PRIMARY KEY,
    description TEXT
    -- outros campos relevantes
);

CREATE TABLE IF NOT EXISTS segments (
    segmentId INTEGER PRIMARY KEY,
    description TEXT
);

CREATE TABLE IF NOT EXISTS keywords (
    keywordId INTEGER PRIMARY KEY,
    description TEXT
);

-- Tabelas auxiliares para relacionamentos muitos-para-muitos (exemplo)
CREATE TABLE IF NOT EXISTS task_equipments (
    taskID INTEGER,
    equipmentId INTEGER,
    PRIMARY KEY (taskID, equipmentId),
    FOREIGN KEY (taskID) REFERENCES tasks(taskID),
    FOREIGN KEY (equipmentId) REFERENCES equipments(equipmentId)
);

-- Outras tabelas podem ser adicionadas conforme endpoints e necessidades futuras
-- Adicione índices e constraints conforme necessário para performance e integridade
