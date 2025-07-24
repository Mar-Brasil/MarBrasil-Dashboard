"""
Utilitários para os scripts de download de dados da API Auvo.
"""
import os
import sys
from dotenv import load_dotenv

# Diretório raiz do projeto (um nível acima da pasta downloads)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminho para o banco de dados
DB_PATH = os.path.join(ROOT_DIR, 'auvo.db')

# Caminho para o arquivo .env
ENV_PATH = os.path.join(ROOT_DIR, '.env')

def load_env_vars():
    """Carrega variáveis de ambiente do arquivo .env."""
    dotenv_path = ENV_PATH
    load_dotenv(dotenv_path)
    
    # Verificar se as variáveis necessárias estão definidas
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    
    return {
        "API_KEY": api_key,
        "API_TOKEN": api_token,
        "API_URL": os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    }

def get_db_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    import sqlite3
    return sqlite3.connect(DB_PATH)
