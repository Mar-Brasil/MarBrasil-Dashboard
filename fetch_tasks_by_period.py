import sqlite3
import requests
import json
import datetime
import sys
import time
import os
from dateutil.relativedelta import relativedelta
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
    
    def get_tasks(self, filters, page_size=100):
        """Busca tarefas com base nos filtros fornecidos"""
        if not self.token:
            print("Você precisa fazer login primeiro!")
            return None
        
        # Codificar o filtro como JSON string
        param_filter_json = json.dumps(filters)
        
        # Construir a URL com os parâmetros
        url = f"{self.base_url}/tasks/?paramFilter={param_filter_json}&pageSize={page_size}"
        
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

def get_customers_from_db(db_path):
    """Busca todos os clientes do banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, description, cpfCnpj FROM customers")
        customers = cursor.fetchall()
        
        conn.close()
        return customers
    except Exception as e:
        print(f"Erro ao buscar clientes do banco: {e}")
        return []

def save_tasks_to_db(db_path, tasks):
    """Salva as tarefas no banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contador de tarefas inseridas
        inserted_count = 0
        updated_count = 0
        
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
                    updated_count += 1
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
        
        return inserted_count, updated_count
    except Exception as e:
        print(f"Erro ao salvar tarefas no banco: {e}")
        return 0, 0

def parse_date(date_str):
    """Converte uma string de data para objeto datetime"""
    try:
        return datetime.datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        print("Formato de data inválido. Use o formato DD/MM/AAAA.")
        return None

def get_period_options():
    """Retorna opções de períodos predefinidos"""
    today = datetime.datetime.now()
    
    # Mês atual
    first_day_current = datetime.datetime(today.year, today.month, 1)
    if today.month == 12:
        last_day_current = datetime.datetime(today.year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day_current = datetime.datetime(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    
    # Mês anterior
    first_day_prev = first_day_current - relativedelta(months=1)
    last_day_prev = first_day_current - datetime.timedelta(days=1)
    
    # Últimos 30 dias
    last_30_days_start = today - datetime.timedelta(days=30)
    
    # Últimos 90 dias
    last_90_days_start = today - datetime.timedelta(days=90)
    
    return [
        ("1", "Mês atual", first_day_current, last_day_current),
        ("2", "Mês anterior", first_day_prev, last_day_prev),
        ("3", "Últimos 30 dias", last_30_days_start, today),
        ("4", "Últimos 90 dias", last_90_days_start, today),
        ("5", "Período personalizado", None, None)
    ]

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
    
    print("=== BUSCA DE TAREFAS POR PERÍODO ===")
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Inicializar API
    api = AuvoAPI(api_key, api_token)
    
    # Fazer login
    if not api.login():
        print("Não foi possível fazer login. Verifique suas credenciais.")
        sys.exit(1)
    
    # Definir filtros
    filters = {}
    
    # 1. Escolher período
    period_options = get_period_options()
    print("\nEscolha o período de busca:")
    for option in period_options:
        if option[2] and option[3]:
            print(f"{option[0]}. {option[1]} ({option[2].strftime('%d/%m/%Y')} a {option[3].strftime('%d/%m/%Y')})")
        else:
            print(f"{option[0]}. {option[1]}")
    
    period_choice = input("\nOpção: ")
    
    # Encontrar a opção escolhida
    selected_period = None
    for option in period_options:
        if option[0] == period_choice:
            selected_period = option
            break
    
    if not selected_period:
        print("Opção inválida!")
        sys.exit(1)
    
    # Se for período personalizado, solicitar datas
    if selected_period[0] == "5":
        start_date_str = input("Data inicial (DD/MM/AAAA): ")
        end_date_str = input("Data final (DD/MM/AAAA): ")
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        if not start_date or not end_date:
            sys.exit(1)
        
        if start_date > end_date:
            print("A data inicial não pode ser posterior à data final!")
            sys.exit(1)
    else:
        start_date = selected_period[2]
        end_date = selected_period[3]
    
    # Adicionar datas ao filtro
    filters["startDate"] = start_date.strftime("%Y-%m-%dT00:00:00")
    filters["endDate"] = end_date.strftime("%Y-%m-%dT23:59:59")
    
    # 2. Filtrar por usuário?
    filter_by_user = input("\nDeseja filtrar por usuário? (s/n): ")
    
    if filter_by_user.lower() == 's':
        # Buscar usuários do banco
        users = get_users_from_db(db_path)
        
        if not users:
            print("Nenhum usuário encontrado no banco de dados.")
            user_filter = input("Deseja informar um ID de usuário manualmente? (s/n): ")
            if user_filter.lower() == 's':
                try:
                    user_id = int(input("Digite o ID do usuário: "))
                    filters["idUserTo"] = user_id
                except ValueError:
                    print("ID inválido!")
                    sys.exit(1)
        else:
            # Mostrar lista de usuários
            print("\nUsuários disponíveis:")
            for i, user in enumerate(users, 1):
                # Verificar se o usuário está no arquivo .env para destacá-lo
                env_user_key = f"USUARIO_{user[0]}"
                env_user_name = os.getenv(env_user_key)
                
                if env_user_name:
                    print(f"{i}. ID: {user[0]} - Nome: {user[1]} - Email: {user[2]} [Usuário no .env: {env_user_name}]")
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
                filters["idUserTo"] = user_id
                print(f"Filtrando por usuário: {selected_user[1]} (ID: {user_id})")
            except ValueError:
                print("Por favor, digite um número válido.")
                sys.exit(1)
    
    # 3. Filtrar por cliente?
    filter_by_customer = input("\nDeseja filtrar por cliente? (s/n): ")
    
    if filter_by_customer.lower() == 's':
        # Buscar clientes do banco
        customers = get_customers_from_db(db_path)
        
        if not customers:
            print("Nenhum cliente encontrado no banco de dados.")
            customer_filter = input("Deseja informar um ID de cliente manualmente? (s/n): ")
            if customer_filter.lower() == 's':
                try:
                    customer_id = int(input("Digite o ID do cliente: "))
                    filters["customerId"] = customer_id
                except ValueError:
                    print("ID inválido!")
                    sys.exit(1)
        else:
            # Mostrar lista de clientes
            print("\nClientes disponíveis:")
            for i, customer in enumerate(customers, 1):
                print(f"{i}. ID: {customer[0]} - Nome: {customer[1]} - CPF/CNPJ: {customer[2] or 'N/A'}")
            
            # Solicitar escolha do cliente
            try:
                choice = int(input("\nEscolha um cliente pelo número (1-{}): ".format(len(customers))))
                if choice < 1 or choice > len(customers):
                    print("Escolha inválida!")
                    sys.exit(1)
                
                selected_customer = customers[choice - 1]
                customer_id = selected_customer[0]
                filters["customerId"] = customer_id
                print(f"Filtrando por cliente: {selected_customer[1]} (ID: {customer_id})")
            except ValueError:
                print("Por favor, digite um número válido.")
                sys.exit(1)
    
    # 4. Filtrar por status?
    filter_by_status = input("\nDeseja filtrar por status da tarefa? (s/n): ")
    
    if filter_by_status.lower() == 's':
        print("\nOpções de status:")
        print("1. Tarefas não finalizadas")
        print("2. Tarefas finalizadas automaticamente")
        print("3. Tarefas finalizadas manualmente")
        print("4. Tarefas finalizadas (automática ou manualmente)")
        print("5. Todas as tarefas")
        print("6. Tarefas com pendências")
        print("7. Tarefas iniciadas ou finalizadas")
        
        try:
            status_choice = int(input("\nEscolha uma opção (1-7): "))
            if status_choice < 1 or status_choice > 7:
                print("Escolha inválida!")
                sys.exit(1)
            
            # Ajustar para o valor esperado pela API (0-6)
            filters["status"] = status_choice - 1
        except ValueError:
            print("Por favor, digite um número válido.")
            sys.exit(1)
    
    # Mostrar resumo dos filtros
    print("\nResumo dos filtros:")
    print(f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    if "idUserTo" in filters:
        print(f"Usuário ID: {filters['idUserTo']}")
    
    if "customerId" in filters:
        print(f"Cliente ID: {filters['customerId']}")
    
    if "status" in filters:
        status_names = [
            "Não finalizadas", 
            "Finalizadas automaticamente", 
            "Finalizadas manualmente",
            "Finalizadas (automática ou manualmente)",
            "Todas",
            "Com pendências",
            "Iniciadas ou finalizadas"
        ]
        print(f"Status: {status_names[filters['status']]}")
    
    # Confirmar busca
    confirm = input("\nDeseja prosseguir com a busca? (s/n): ")
    
    if confirm.lower() != 's':
        print("Operação cancelada pelo usuário.")
        sys.exit(0)
    
    print("\nBuscando tarefas...")
    
    # Buscar tarefas
    response = api.get_tasks(filters)
    
    if not response or "result" not in response:
        print("Nenhuma tarefa encontrada ou erro na resposta da API.")
        sys.exit(1)
    
    tasks = response["result"]
    print(f"\nForam encontradas {len(tasks)} tarefas.")
    
    # Perguntar se deseja salvar no banco
    if tasks:
        save_option = input("\nDeseja salvar estas tarefas no banco de dados? (s/n): ")
        
        if save_option.lower() == 's':
            inserted, updated = save_tasks_to_db(db_path, tasks)
            print(f"\n{inserted} tarefas foram inseridas e {updated} foram atualizadas no banco de dados.")
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
            
            task_date = task.get("taskDate", "").split("T")[0] if task.get("taskDate") else "N/A"
            
            print(f"{i}. ID: {task.get('taskID')} - Data: {task_date} - Cliente: {task.get('customerDescription', 'N/A')} - Status: {status}")
        
        if len(tasks) > 10:
            print(f"... e mais {len(tasks) - 10} tarefas.")
    
    print("\nOperação concluída!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)
