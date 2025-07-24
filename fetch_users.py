import sqlite3
import requests
import json
import sys
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
    
    def get_users(self):
        """Busca todos os usuários disponíveis na API"""
        if not self.token:
            print("Você precisa fazer login primeiro!")
            return None
        
        url = f"{self.base_url}/users"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Verificar se a resposta contém a chave 'entityList'
                if 'entityList' in data:
                    return data['entityList']
                else:
                    print("Formato de resposta inesperado da API. Chave 'entityList' não encontrada.")
                    print(f"Resposta: {data}")
                    return []
            else:
                print(f"Erro ao buscar usuários: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

def save_users_to_db(db_path, users):
    """Salva os usuários no banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Tabela 'users' não encontrada no banco de dados!")
            print("Criando tabela 'users'...")
            
            cursor.execute("""
            CREATE TABLE users (
                userId INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                active INTEGER,
                isAdmin INTEGER,
                isManager INTEGER,
                isOperator INTEGER,
                isCustomer INTEGER,
                isSupplier INTEGER,
                isExternalUser INTEGER,
                isPartner INTEGER,
                isTeamLeader INTEGER,
                isFinancial INTEGER,
                isCommercial INTEGER,
                isHumanResources INTEGER,
                isReceiving INTEGER,
                isStockist INTEGER,
                isProduction INTEGER,
                isQualityControl INTEGER,
                isShipping INTEGER,
                isDriver INTEGER,
                isHelper INTEGER,
                isCollector INTEGER,
                isAuditor INTEGER,
                isDirector INTEGER,
                isBoard INTEGER,
                isPartnerManager INTEGER,
                isPartnerOperator INTEGER,
                isPartnerCommercial INTEGER,
                isPartnerFinancial INTEGER,
                isPartnerDirector INTEGER,
                isPartnerBoard INTEGER,
                isPartnerAuditor INTEGER,
                isPartnerTeamLeader INTEGER,
                isPartnerDriver INTEGER,
                isPartnerHelper INTEGER,
                isPartnerCollector INTEGER,
                isPartnerHumanResources INTEGER,
                isPartnerReceiving INTEGER,
                isPartnerStockist INTEGER,
                isPartnerProduction INTEGER,
                isPartnerQualityControl INTEGER,
                isPartnerShipping INTEGER,
                isCustomerManager INTEGER,
                isCustomerOperator INTEGER,
                isCustomerCommercial INTEGER,
                isCustomerFinancial INTEGER,
                isCustomerDirector INTEGER,
                isCustomerBoard INTEGER,
                isCustomerAuditor INTEGER,
                isCustomerTeamLeader INTEGER,
                isCustomerDriver INTEGER,
                isCustomerHelper INTEGER,
                isCustomerCollector INTEGER,
                isCustomerHumanResources INTEGER,
                isCustomerReceiving INTEGER,
                isCustomerStockist INTEGER,
                isCustomerProduction INTEGER,
                isCustomerQualityControl INTEGER,
                isCustomerShipping INTEGER,
                isSupplierManager INTEGER,
                isSupplierOperator INTEGER,
                isSupplierCommercial INTEGER,
                isSupplierFinancial INTEGER,
                isSupplierDirector INTEGER,
                isSupplierBoard INTEGER,
                isSupplierAuditor INTEGER,
                isSupplierTeamLeader INTEGER,
                isSupplierDriver INTEGER,
                isSupplierHelper INTEGER,
                isSupplierCollector INTEGER,
                isSupplierHumanResources INTEGER,
                isSupplierReceiving INTEGER,
                isSupplierStockist INTEGER,
                isSupplierProduction INTEGER,
                isSupplierQualityControl INTEGER,
                isSupplierShipping INTEGER,
                dateLastUpdate TEXT
            )
            """)
            conn.commit()
        
        # Contador de usuários inseridos/atualizados
        inserted_count = 0
        updated_count = 0
        
        # Para cada usuário na resposta da API
        for user in users:
            try:
                # Verificar se o usuário é um dicionário
                if not isinstance(user, dict):
                    print(f"Pulando usuário em formato inválido: {user}")
                    continue
                    
                # Verificar se o usuário tem userId
                if "userId" not in user:
                    print(f"Pulando usuário sem userId: {user}")
                    continue
                    
                # Verificar se o usuário já existe
                # Converter chaves para minúsculas para garantir compatibilidade
                user_id = user.get("userId") or user.get("userID") or user.get("userid")
                if not user_id:
                    print(f"Pulando usuário sem ID: {user}")
                    continue
                    
                # Normalizar os dados do usuário
                normalized_user = {}
                for key, value in user.items():
                    # Converter chaves para o formato esperado pelo banco
                    if key.lower() == "userid" or key.lower() == "id":
                        normalized_user["userId"] = value
                    else:
                        normalized_user[key] = value
                        
                user = normalized_user
                cursor.execute("SELECT userId FROM users WHERE userId = ?", (user["userId"],))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    print(f"Usuário {user['userId']} ({user.get('name', 'Sem nome')}) já existe no banco. Atualizando...")
                    
                    # Construir a consulta de atualização dinamicamente
                    update_fields = []
                    update_values = []
                    
                    for key, value in user.items():
                        # Tratar campos especiais (listas, dicionários)
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                    
                    # Adicionar o ID para a cláusula WHERE
                    update_values.append(user["userId"])
                    
                    # Executar a atualização
                    cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)} WHERE userId = ?",
                        update_values
                    )
                    updated_count += 1
                else:
                    print(f"Inserindo novo usuário {user['userId']} ({user.get('name', 'Sem nome')})...")
                    
                    # Construir a consulta de inserção dinamicamente
                    columns = []
                    placeholders = []
                    values = []
                    
                    for key, value in user.items():
                        # Tratar campos especiais (listas, dicionários)
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        
                        columns.append(key)
                        placeholders.append("?")
                        values.append(value)
                    
                    # Executar a inserção
                    cursor.execute(
                        f"INSERT INTO users ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                        values
                    )
                    inserted_count += 1
            except Exception as e:
                print(f"Erro ao processar usuário {user.get('userId', 'desconhecido')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count, updated_count
    except Exception as e:
        print(f"Erro ao salvar usuários no banco: {e}")
        return 0, 0

def check_env_users(users):
    """Verifica quais usuários estão no arquivo .env"""
    env_users = {}
    
    # Buscar todas as variáveis que começam com USUARIO_
    for key, value in os.environ.items():
        if key.startswith("USUARIO_"):
            try:
                user_id = int(key.split("_")[1])
                env_users[user_id] = value
            except (ValueError, IndexError):
                continue
    
    # Verificar quais usuários da API estão no .env
    env_matches = []
    missing_in_env = []
    
    for user in users:
        # Verificar se o usuário é um dicionário
        if not isinstance(user, dict):
            print(f"Aviso: Encontrado usuário em formato inválido: {user}")
            continue
            
        user_id = user.get("userId") or user.get("userID") or user.get("userid")
        if user_id in env_users:
            env_matches.append((user_id, user.get("name", ""), env_users[user_id]))
        else:
            missing_in_env.append((user_id, user.get("name", "")))
    
    return env_matches, missing_in_env

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
    
    print("=== BUSCA DE USUÁRIOS DA API AUVO ===")
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Inicializar API
    api = AuvoAPI(api_key, api_token)
    
    # Fazer login
    if not api.login():
        print("Não foi possível fazer login. Verifique suas credenciais.")
        sys.exit(1)
    
    print("\nBuscando usuários da API Auvo...")
    
    # Buscar usuários
    users = api.get_users()
    
    if users is None or len(users) == 0:
        print("Nenhum usuário encontrado ou erro na resposta da API.")
        sys.exit(1)
    
    # Verificar se users é uma lista
    if not isinstance(users, list):
        print(f"Erro: A resposta da API não retornou uma lista de usuários. Tipo recebido: {type(users)}")
        print(f"Resposta: {users}")
        sys.exit(1)
        
    # Filtrar apenas os usuários que são dicionários
    valid_users = [user for user in users if isinstance(user, dict)]
    invalid_count = len(users) - len(valid_users)
    
    if invalid_count > 0:
        print(f"Aviso: {invalid_count} usuários foram ignorados por estarem em formato inválido.")
    
    users = valid_users
    print(f"\nForam encontrados {len(users)} usuários válidos na API Auvo.")
    
    # Verificar usuários no arquivo .env
    env_matches, missing_in_env = check_env_users(users)
    
    print(f"\nUsuários encontrados no arquivo .env: {len(env_matches)}")
    for user_id, api_name, env_name in env_matches:
        print(f"- ID: {user_id} | Nome API: {api_name} | Nome .env: {env_name}")
    
    if missing_in_env:
        print(f"\nUsuários ativos não encontrados no arquivo .env: {len(missing_in_env)}")
        for user_id, name in missing_in_env[:10]:  # Mostrar apenas os 10 primeiros
            # Verificar se o usuário está ativo
            for user in users:
                if isinstance(user, dict) and user.get("userId") == user_id and user.get("active", 0) == 1:
                    print(f"- ID: {user_id} | Nome: {name}")
                    break
        
        if len(missing_in_env) > 10:
            print(f"... e mais {len(missing_in_env) - 10} usuários.")
    
    # Perguntar se deseja salvar no banco
    save_option = input("\nDeseja salvar estes usuários no banco de dados? (s/n): ")
    
    if save_option.lower() == 's':
        inserted, updated = save_users_to_db(db_path, users)
        print(f"\n{inserted} usuários foram inseridos e {updated} foram atualizados no banco de dados.")
    else:
        print("\nOs usuários não foram salvos no banco de dados.")
    
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
