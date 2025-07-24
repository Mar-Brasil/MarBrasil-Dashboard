import requests

API_URL = "https://api.auvo.com.br/v2/webHooks/{id}"  # Substitua {id} pelo id do webhook criado
API_TOKEN = "LNmsuTQ3EhRBeylyLz6QrSuY9t5S4ol"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

response = requests.delete(API_URL, headers=headers)
print("Status:", response.status_code)
print("Resposta:", response.text)