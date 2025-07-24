import requests
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais da API do arquivo .env
api_key = os.getenv("API_KEY")
api_token = os.getenv("API_TOKEN")
base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"

if not api_key or not api_token:
    print("Credenciais da API não encontradas no arquivo .env!")
    exit(1)

print(f"Usando credenciais: API_KEY={api_key[:4]}...{api_key[-4:]}")

# Fazer login
login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
try:
    login_response = requests.get(login_url)
    login_data = login_response.json()
    
    if "result" in login_data and login_data["result"]["authenticated"]:
        token = login_data["result"]["accessToken"]
        print(f"Login realizado com sucesso! Token válido até: {login_data['result']['expiration']}")
    else:
        print("Falha na autenticação!")
        exit(1)
except Exception as e:
    print(f"Erro ao fazer login: {e}")
    exit(1)

# Testar diferentes endpoints
endpoints = [
    "/users",
    "/tasks",
    "/customers",
    "/teams",
    "/services"
]

for endpoint in endpoints:
    print(f"\n\n=== TESTANDO ENDPOINT: {endpoint} ===")
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Tipo de resposta: {type(data)}")
            print(f"Chaves na resposta: {list(data.keys()) if isinstance(data, dict) else 'Não é um dicionário'}")
            
            # Imprimir uma amostra da resposta (limitada para não sobrecarregar o console)
            print("\nAmostra da resposta:")
            print(json.dumps(data, indent=2)[:1000] + "...")
            
            # Se for um dicionário com a chave 'result'
            if isinstance(data, dict) and 'result' in data:
                result = data['result']
                print(f"\nTipo do 'result': {type(result)}")
                if isinstance(result, list):
                    print(f"Número de itens em 'result': {len(result)}")
                    if len(result) > 0:
                        print(f"Tipo do primeiro item: {type(result[0])}")
                        if isinstance(result[0], dict):
                            print(f"Chaves do primeiro item: {list(result[0].keys())}")
            
            # Se for um dicionário com a chave 'entityList'
            if isinstance(data, dict) and 'entityList' in data:
                entity_list = data['entityList']
                print(f"\nTipo do 'entityList': {type(entity_list)}")
                if isinstance(entity_list, list):
                    print(f"Número de itens em 'entityList': {len(entity_list)}")
                    if len(entity_list) > 0:
                        print(f"Tipo do primeiro item: {type(entity_list[0])}")
                        if isinstance(entity_list[0], dict):
                            print(f"Chaves do primeiro item: {list(entity_list[0].keys())}")
        else:
            print(f"Erro ao acessar {endpoint}: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Erro na requisição para {endpoint}: {e}")

print("\nTeste concluído!")
