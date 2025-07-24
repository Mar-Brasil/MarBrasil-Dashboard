-- Esquema inicial do banco de dados SQLite para sincronização completa com a API Auvo

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    userId INTEGER,
    name TEXT,
    email TEXT,
    active BOOLEAN,
    userType TEXT,
    externalId TEXT,
    smartPhoneNumber TEXT,
    created TEXT,
    updated TEXT,
    json TEXT
);

-- Tabela de Tarefas
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    description TEXT,
    taskStatus TEXT,
    startDate TEXT,
    endDate TEXT,
    customerId INTEGER,
    teamId INTEGER,
    typeId INTEGER,
    created TEXT,
    updated TEXT,
    json TEXT
);

-- Tabela de Clientes
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    description TEXT,
    segmentId INTEGER,
    groupId INTEGER,
    active BOOLEAN,
    creationDate TEXT,
    dateLastUpdate TEXT,
    externalId TEXT,
    json TEXT
);

-- Tabela de Grupos de Clientes
CREATE TABLE IF NOT EXISTS customer_groups (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Equipes
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Tipos de Tarefas
CREATE TABLE IF NOT EXISTS task_types (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Segmentos
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Questionários
CREATE TABLE IF NOT EXISTS questionnaires (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Palavras-chave
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Tabela de Equipamentos
CREATE TABLE IF NOT EXISTS equipments (
    id INTEGER PRIMARY KEY,
    description TEXT,
    json TEXT
);

-- Relacionamentos e tabelas auxiliares podem ser criados conforme necessidade futura.

