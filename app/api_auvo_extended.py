import requests
import json
from .api_auvo import autenticar
from .env_reader import API_URL, API_KEY

def get_all_users():
    """
    Busca todos os usuários disponíveis na API da Auvo.
    
    Returns:
        list: Lista de usuários com seus IDs e nomes
    """
    token = autenticar()
    if not token:
        return {"erro": "Falha na autenticação"}

    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    # Parâmetros para buscar todos os usuários
    params = {
        "page": 1,
        "pageSize": 100,  # Buscar 100 usuários por página
        "order": "asc"
    }

    url = f"{API_URL}/users/"
    
    todos_usuarios = []
    tem_mais_paginas = True
    
    while tem_mais_paginas:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            resultado = response.json().get("result", {})
            usuarios_pagina = resultado.get("entityList", [])
            
            # Adicionar usuários desta página à lista completa
            for usuario in usuarios_pagina:
                todos_usuarios.append({
                    "id": usuario.get("id"),
                    "nome": usuario.get("name"),
                    "email": usuario.get("email"),
                    "ativo": usuario.get("active", False)
                })
            
            # Verificar se há mais páginas
            pagina_atual = resultado.get("page", 1)
            total_paginas = resultado.get("pageCount", 1)
            
            if pagina_atual < total_paginas:
                params["page"] = pagina_atual + 1
            else:
                tem_mais_paginas = False
        else:
            return {"erro": f"Erro {response.status_code}", "detalhes": response.text}
    
    return todos_usuarios

def get_tasks_by_date(data_inicio, data_fim):
    """
    Busca todas as tarefas no intervalo de datas especificado para todos os usuários.
    
    Args:
        data_inicio: Data inicial no formato YYYY-MM-DD
        data_fim: Data final no formato YYYY-MM-DD
        
    Returns:
        dict: Dicionário com as tarefas agrupadas por usuário
    """
    # Primeiro, buscar todos os usuários
    usuarios = get_all_users()
    if isinstance(usuarios, dict) and "erro" in usuarios:
        return usuarios  # Retornar o erro se não conseguir buscar usuários
    
    token = autenticar()
    if not token:
        return {"erro": "Falha na autenticação"}

    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Parâmetros base para buscar tarefas
    params_base = {
        "page": 1,
        "pageSize": 50,
        "order": "asc"
    }
    
    url = f"{API_URL}/tasks/"
    
    # Dicionário para armazenar as tarefas por usuário
    tarefas_por_usuario = {}
    
    # Buscar tarefas para cada usuário
    for usuario in usuarios:
        user_id = usuario["id"]
        nome = usuario["nome"]
        
        if not usuario["ativo"]:
            continue  # Pular usuários inativos
        
        tarefas_usuario = []
        tem_mais_paginas = True
        params = params_base.copy()
        
        # Adicionar filtro de usuário e datas
        params["paramFilter"] = json.dumps({
            "idUserTo": user_id,
            "startDate": f"{data_inicio}T00:00:00",
            "endDate": f"{data_fim}T23:59:59"
        })
        
        while tem_mais_paginas:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                resultado = response.json().get("result", {})
                tarefas_pagina = resultado.get("entityList", [])
                
                # Adicionar tarefas desta página à lista do usuário
                tarefas_usuario.extend(tarefas_pagina)
                
                # Verificar se há mais páginas
                pagina_atual = resultado.get("page", 1)
                total_paginas = resultado.get("pageCount", 1)
                
                if pagina_atual < total_paginas:
                    params["page"] = pagina_atual + 1
                else:
                    tem_mais_paginas = False
            else:
                return {"erro": f"Erro ao buscar tarefas para {nome}: {response.status_code}", "detalhes": response.text}
        
        # Adicionar tarefas do usuário ao dicionário final se houver tarefas
        if tarefas_usuario:
            tarefas_por_usuario[user_id] = {
                "nome": nome,
                "tarefas": tarefas_usuario
            }
    
    return tarefas_por_usuario
