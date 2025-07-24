"""
Funções comuns para os scripts de download de dados da API Auvo.
"""
import os
import sys
import json
import requests
from datetime import datetime

from downloads.utils import load_env_vars

def login_to_auvo():
    """
    Realiza login na API Auvo e retorna o token de acesso e a URL base.
    
    Returns:
        tuple: (token, base_url) - Token de acesso e URL base da API
    """
    # Carregar credenciais do arquivo .env
    env_vars = load_env_vars()
    api_key = env_vars["API_KEY"]
    api_token = env_vars["API_TOKEN"]
    base_url = env_vars["API_URL"]
    
    print(f"Usando credenciais do arquivo .env: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    # Fazer login
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    
    try:
        response = requests.get(login_url)
        data = response.json()
        
        if "result" in data and data["result"]["authenticated"]:
            token = data["result"]["accessToken"]
            expiration = data["result"]["expiration"]
            print(f"Login realizado com sucesso! Token válido até: {expiration}")
            return token, base_url
        else:
            print("Falha na autenticação!")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        sys.exit(1)

def get_api_headers(token):
    """
    Retorna os cabeçalhos padrão para requisições à API Auvo.
    
    Args:
        token (str): Token de acesso obtido pelo login
        
    Returns:
        dict: Cabeçalhos para requisições à API
    """
    env_vars = load_env_vars()
    api_key = env_vars["API_KEY"]
    
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

def safe_json_serialize(value):
    """
    Serializa valores complexos (dicionários, listas) para JSON.
    Útil para armazenar em campos de texto no SQLite.
    
    Args:
        value: Valor a ser serializado
        
    Returns:
        str ou valor original: String JSON se for dicionário ou lista, 
                              ou o valor original para tipos simples
    """
    if value is None:
        return ""
    elif isinstance(value, (dict, list)):
        return json.dumps(value)
    elif isinstance(value, (int, float, bool, str)):
        return value
    else:
        # Para qualquer outro tipo, converter para string
        return str(value)

def process_api_response(data, entity_name):
    """
    Processa a resposta da API Auvo, lidando com diferentes formatos de resposta.
    
    Args:
        data (dict): Resposta da API em formato JSON
        entity_name (str): Nome da entidade para mensagens de log
        
    Returns:
        list: Lista de entidades extraída da resposta
    """
    if "result" not in data or not data["result"]:
        return []
    
    # Verificar a estrutura da resposta
    if isinstance(data["result"], dict) and "entityList" in data["result"]:
        # Nova estrutura: result contém um dicionário com entityList
        entities = data["result"]["entityList"]
    else:
        # Estrutura antiga: result é diretamente a lista de entidades
        entities = data["result"]
        
    if not isinstance(entities, list):
        print(f"Formato de resposta inesperado para {entity_name}: {type(entities)}")
        return []
    
    return entities

def paginate_api_request(url, headers, entity_name, params=None):
    """
    Realiza requisições paginadas à API Auvo.
    
    Args:
        url (str): URL do endpoint da API
        headers (dict): Cabeçalhos da requisição
        entity_name (str): Nome da entidade para mensagens de log
        params (dict, optional): Parâmetros adicionais para a requisição
        
    Returns:
        list: Lista completa de entidades de todas as páginas
    """
    if params is None:
        params = {}
    
    all_entities = []
    page = 1
    page_size = 100
    total_entities = 0
    
    try:
        while True:
            # Adicionar parâmetros de paginação
            page_params = {
                "page": page,
                "pageSize": page_size,
                "order": "asc",
                **params
            }
            
            print(f"Buscando página {page}...")
            response = requests.get(url, headers=headers, params=page_params)
            
            if response.status_code != 200:
                print(f"Erro ao buscar {entity_name}: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            entities = process_api_response(data, entity_name)
            
            if not entities:
                break
                
            entities_count = len(entities)
            total_entities += entities_count
            all_entities.extend(entities)
            
            print(f"Encontrados {entities_count} {entity_name} na página {page}")
            
            if entities_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar {entity_name}: {e}")
    
    print(f"Total de {entity_name} encontrados: {total_entities}")
    return all_entities
