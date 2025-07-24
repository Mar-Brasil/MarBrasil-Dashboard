import requests

API_URL = "https://api.auvo.com.br/v2/webHooks/"
API_TOKEN = "LNmsuTQ3EhRBeylyLz6QrSuY9t5S4ol"  # Pegue do seu .env
# Seu endpoint público (ngrok ou servidor exposto)
TARGET_URL = "http://SEU_IP_OU_NGROK:4000/webhook/auvo"

payload = {
    "userId": 0,  # 0 para todos os usuários, ou coloque um ID específico
    "entity": "Task",  # Monitorar tarefas
    "action": "Inclusao",  # Abertura de tarefa
    "targetUrl": TARGET_URL,
    "active": True
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

response = requests.post(API_URL, json=payload, headers=headers)
print("Status:", response.status_code)
print("Resposta:", response.text)