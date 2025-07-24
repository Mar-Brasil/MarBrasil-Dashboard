import sqlite3
import requests
import json
import datetime
import sys
import time
import os
from dotenv import load_dotenv

class AuvoAPI:
    """Classe para interagir com a API Auvo"""
    
    def __init__(self, api_key, api_token):
        self.api_key = api_key
        self.api_token = api_token
        self.base_url = "https://api.auvo.com.br/v2"
        self.token = None
    
    def login(self):
        """Faz login na API Auvo e obtém o token de autenticação"""
        url = f"{self.base_url}/login/?apiKey={self.api_key}&apiToken={self.api_token}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if "result" in data and data["result"]["authenticated"]:
                self.token = data["result"]["accessToken"]
                print(f"Login realizado com sucesso! Token válido até: {data['result']['expiration']}")
                return True
            else:
                print("Falha na autenticação!")
                return False
        except Exception as e:
            print(f"Erro ao fazer login: {e}")
            return False
    
    def get_tasks_by_user(self, user_id, start_date, end_date):
        """Busca tarefas de um usuário específico em um período"""
        if not self.token:
            print("Você precisa fazer login primeiro!")
            return None
        
        # Parâmetros para filtrar tarefas por usuário e período
        param_filter = {
            "idUserTo": user_id,
            "startDate": start_date.strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date.strftime("%Y-%m-%dT23:59:59")
        }
        
        # Codificar o filtro como JSON string
        param_filter_json = json.dumps(param_filter)
        
        # Construir a URL com os parâmetros
        url = f"{self.base_url}/tasks/?paramFilter={param_filter_json}&pageSize=100"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao buscar tarefas: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

def get_users_from_db(db_path):
    """Busca todos os usuários do banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT userId, name, email FROM users")
        users = cursor.fetchall()
        
        conn.close()
        return users
    except Exception as e:
        print(f"Erro ao buscar usuários do banco: {e}")
        return []

def save_tasks_to_db(db_path, tasks, user_id):
    """Salva as tarefas no banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contador de tarefas inseridas
        inserted_count = 0
        
        # Para cada tarefa na resposta da API
        for task in tasks:
            try:
                # Verificar se a tarefa já existe
                cursor.execute("SELECT taskID FROM tasks WHERE taskID = ?", (task["taskID"],))
                existing_task = cursor.fetchone()
                
                if existing_task:
                    print(f"Tarefa {task['taskID']} já existe no banco. Atualizando...")
                    
                    # Construir a consulta de atualização dinamicamente
                    update_fields = []
                    update_values = []
                    
                    for key, value in task.items():
                        # Tratar campos especiais (listas, dicionários)
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                    
                    # Adicionar o ID para a cláusula WHERE
                    update_values.append(task["taskID"])
                    
                    # Executar a atualização
                    cursor.execute(
                        f"UPDATE tasks SET {', '.join(update_fields)} WHERE taskID = ?",
                        update_values
                    )
                else:
                    print(f"Inserindo nova tarefa {task['taskID']}...")
                    
                    # Construir a consulta de inserção dinamicamente
                    columns = []
                    placeholders = []
                    values = []
                    
                    for key, value in task.items():
                        # Tratar campos especiais (listas, dicionários)
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        
                        columns.append(key)
                        placeholders.append("?")
                        values.append(value)
                    
                    # Executar a inserção
                    cursor.execute(
                        f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                        values
                    )
                
                inserted_count += 1
            except Exception as e:
                print(f"Erro ao processar tarefa {task.get('taskID', 'desconhecida')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count
    except Exception as e:
        print(f"Erro ao salvar tarefas no banco: {e}")
        return 0

def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurações
    db_path = "auvo.db"
    
    # Obter credenciais da API do arquivo .env
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        print("Verifique se o arquivo .env existe e contém as variáveis API_KEY e API_TOKEN.")
        sys.exit(1)
    
    print("=== BUSCA DE TAREFAS POR USUÁRIO ===")
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Inicializar API
    api = AuvoAPI(api_key, api_token)
    
    # Fazer login
    if not api.login():
        print("Não foi possível fazer login. Verifique suas credenciais.")
        sys.exit(1)
    
    # Buscar usuários do banco
    users = get_users_from_db(db_path)
    
    if not users:
        print("Nenhum usuário encontrado no banco de dados.")
        sys.exit(1)
    
    # Mostrar lista de usuários
    print("\nUsuários disponíveis:")
    for i, user in enumerate(users, 1):
        # Verificar se o usuário está no arquivo .env para destacá-lo
        env_user_key = f"USUARIO_{user[0]}"
        env_user_name = os.getenv(env_user_key)
        
        if env_user_name:
            print(f"{i}. ID: {user[0]} - Nome: {user[1]} - Email: {user[2]} [Usuário no .env]")
        else:
            print(f"{i}. ID: {user[0]} - Nome: {user[1]} - Email: {user[2]}")
    
    # Solicitar escolha do usuário
    try:
        choice = int(input("\nEscolha um usuário pelo número (1-{}): ".format(len(users))))
        if choice < 1 or choice > len(users):
            print("Escolha inválida!")
            sys.exit(1)
        
        selected_user = users[choice - 1]
        user_id = selected_user[0]
        user_name = selected_user[1]
    except ValueError:
        print("Por favor, digite um número válido.")
        sys.exit(1)
    
    # Definir período (mês atual)
    today = datetime.datetime.now()
    first_day = datetime.datetime(today.year, today.month, 1)
    
    # Último dia do mês atual
    if today.month == 12:
        last_day = datetime.datetime(today.year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.datetime(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    
    print(f"\nBuscando tarefas para o usuário {user_name} (ID: {user_id})")
    print(f"Período: {first_day.strftime('%d/%m/%Y')} a {last_day.strftime('%d/%m/%Y')}")
    
    # Buscar tarefas
    response = api.get_tasks_by_user(user_id, first_day, last_day)
    
    if not response or "result" not in response:
        print("Nenhuma tarefa encontrada ou erro na resposta da API.")
        sys.exit(1)
    
    tasks = response["result"]
    print(f"\nForam encontradas {len(tasks)} tarefas para o usuário {user_name}.")
    
    # Perguntar se deseja salvar no banco
    save_option = input("\nDeseja salvar estas tarefas no banco de dados? (s/n): ")
    
    if save_option.lower() == 's':
        inserted = save_tasks_to_db(db_path, tasks, user_id)
        print(f"\n{inserted} tarefas foram salvas/atualizadas no banco de dados.")
    else:
        print("\nAs tarefas não foram salvas no banco de dados.")
    
    # Mostrar resumo das tarefas
    print("\nResumo das tarefas encontradas:")
    for i, task in enumerate(tasks[:10], 1):  # Mostrar apenas as 10 primeiras
        status = {
            1: "Aberta",
            2: "Em deslocamento",
            3: "Check-in",
            4: "Check-out",
            5: "Finalizada",
            6: "Pausada"
        }.get(task.get("taskStatus", 0), "Desconhecido")
        
        print(f"{i}. ID: {task.get('taskID')} - Cliente: {task.get('customerDescription', 'N/A')} - Status: {status}")
    
    if len(tasks) > 10:
        print(f"... e mais {len(tasks) - 10} tarefas.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
