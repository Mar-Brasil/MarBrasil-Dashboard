import os
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()

# Variáveis de ambiente
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
API_TOKEN = os.getenv("API_TOKEN")

# Busca todos os usuários cadastrados dinamicamente
USUARIOS = {}
for key, value in os.environ.items():
    if key.startswith("USUARIO_"):
        user_id = int(key.split("_")[1])
        USUARIOS[user_id] = value

