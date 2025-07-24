# Auvo API Data Download

Este projeto contém scripts para baixar e armazenar dados da API Auvo em um banco de dados SQLite local.

## Estrutura do Projeto

- `downloads/`: Pasta contendo todos os scripts de download individuais
- `download_all.py`: Script principal para executar todos os downloads em sequência
- `auvo.db`: Banco de dados SQLite local onde os dados são armazenados

## Requisitos

- Python 3.6+
- Bibliotecas Python: requests, sqlite3, python-dotenv

## Configuração

1. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   API_KEY=sua_chave_api
   API_TOKEN=seu_token_api
   API_URL=https://api.auvo.com.br/v2
   ```

2. Instale as dependências:
   ```
   pip install requests python-dotenv
   ```

## Como Usar

### Executar todos os downloads

Para baixar todos os dados da API Auvo em sequência:

```
python download_all.py
```

### Executar scripts individuais

Para executar um script específico:

```
python -c "from downloads import download_teams; download_teams.main()"
```

## Scripts Disponíveis

- `download_users.py`: Baixa usuários
- `download_teams.py`: Baixa times
- `download_segments.py`: Baixa segmentos
- `download_task_types.py`: Baixa tipos de tarefas
- `download_services.py`: Baixa serviços
- `download_products.py`: Baixa produtos
- `download_customers.py`: Baixa clientes
- `download_keywords.py`: Baixa palavras-chave
- `download_equipments.py`: Baixa equipamentos
- `download_questionnaires.py`: Baixa questionários
- `download_tasks.py`: Baixa tarefas
- `download_tasks_this_month.py`: Baixa tarefas do mês atual
- `download_all_user_tasks.py`: Baixa todas as tarefas de usuários

## Características dos Scripts

- Autenticação automática na API Auvo
- Criação e atualização automática das tabelas no banco de dados
- Tratamento robusto de respostas da API
- Paginação para lidar com grandes volumes de dados
- Serialização de campos complexos para armazenamento no SQLite
