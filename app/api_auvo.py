import requests
from .env_reader import API_URL, API_KEY, API_TOKEN

def autenticar():
    """Realiza a autenticação na API da Auvo e retorna o accessToken."""
    try:
        url = f"{API_URL}/login/?apiKey={API_KEY}&apiToken={API_TOKEN}"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()["result"]["accessToken"]
        else:
            print(f"Erro ao autenticar: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exceção na autenticação: {str(e)}")
        return None

def get_user_json(user_id):
    """Recupera informações de um usuário pelo ID."""
    token = autenticar()
    if not token:
        return {"erro": "Falha na autenticação"}

    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    url = f"{API_URL}/users/{user_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        return {"erro": f"Erro {response.status_code}", "detalhes": response.text}

def get_user_tasks(user_id, data_inicio, data_fim):
    """Busca tarefas de um usuário no intervalo de datas informado via GET."""
    import json
    token = autenticar()
    if not token:
        return {"erro": "Falha na autenticação"}

    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    params = {
        "paramFilter": json.dumps({
            "idUserTo": user_id,
            "startDate": f"{data_inicio}T00:00:00",
            "endDate": f"{data_fim}T23:59:59"
        }),
        "page": 1,
        "pageSize": 50,
        "order": "asc"
    }

    url = f"{API_URL}/tasks/"
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get("result", {}).get("entityList", [])
    else:
        return {"erro": f"Erro {response.status_code}", "detalhes": response.text}
