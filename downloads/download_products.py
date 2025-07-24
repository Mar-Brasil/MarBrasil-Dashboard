import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

def login_to_auvo():
    # Carregar credenciais do arquivo .env
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    
    if not api_key or not api_token:
        print("Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    
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

def create_products_table():
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Criando tabela 'products'...")
        cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL,
            active INTEGER,
            creationDate TEXT,
            dateLastUpdate TEXT,
            externalId TEXT,
            categoryId INTEGER,
            minimumStock REAL,
            currentStock REAL,
            unit TEXT,
            barCode TEXT,
            associatedEquipmentId INTEGER
        )
        ''')
        conn.commit()
        print("Tabela 'products' criada com sucesso!")
    else:
        print("Tabela 'products' já existe.")
    
    conn.close()

def get_products(token, base_url):
    url = f"{base_url}/products"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_products = []
    page = 1
    page_size = 100
    total_products = 0
    
    try:
        while True:
            params = {
                "paramFilter": json.dumps({}),  # Filtro vazio para trazer todos
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }
            
            print(f"Buscando página {page}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Erro ao buscar produtos: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            
            if "result" not in data or not data["result"]:
                break
            
            products = data["result"]
            products_count = len(products)
            total_products += products_count
            all_products.extend(products)
            
            print(f"Encontrados {products_count} produtos na página {page}")
            
            if products_count < page_size:
                break
            
            page += 1
    
    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
    
    print(f"Total de produtos encontrados: {total_products}")
    return all_products

def save_products_to_db(products):
    # Filtrar apenas dicionários para evitar erro de 'str' object has no attribute 'get'
    products = [p for p in products if isinstance(p, dict)]
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    try:
        for product in products:
            product_id = product.get("id")
            
            # Verificar se o produto já existe
            cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            existing_product = cursor.fetchone()
            
            # Preparar os dados para inserção/atualização
            product_data = (
                product_id,
                product.get("name", ""),
                product.get("description", ""),
                product.get("price", 0.0),
                1 if product.get("active", False) else 0,
                product.get("creationDate", ""),
                product.get("dateLastUpdate", ""),
                product.get("externalId", ""),
                product.get("categoryId", 0),
                product.get("minimumStock", 0.0),
                product.get("currentStock", 0.0),
                product.get("unit", ""),
                product.get("barCode", ""),
                product.get("associatedEquipmentId", 0)
            )
            
            if existing_product:
                # Atualizar produto existente
                cursor.execute('''
                UPDATE products
                SET name = ?, description = ?, price = ?, active = ?, 
                    creationDate = ?, dateLastUpdate = ?, externalId = ?,
                    categoryId = ?, minimumStock = ?, currentStock = ?,
                    unit = ?, barCode = ?, associatedEquipmentId = ?
                WHERE id = ?
                ''', (product_data[1], product_data[2], product_data[3], product_data[4], 
                      product_data[5], product_data[6], product_data[7], product_data[8],
                      product_data[9], product_data[10], product_data[11], product_data[12],
                      product_data[13], product_id))
                updated += 1
            else:
                # Inserir novo produto
                cursor.execute('''
                INSERT INTO products (id, name, description, price, active, 
                                     creationDate, dateLastUpdate, externalId,
                                     categoryId, minimumStock, currentStock,
                                     unit, barCode, associatedEquipmentId)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', product_data)
                inserted += 1
        
        conn.commit()
        print(f"Produtos inseridos: {inserted}, atualizados: {updated}")
    
    except Exception as e:
        print(f"Erro ao salvar produtos no banco de dados: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    print("=== DOWNLOAD DE PRODUTOS ===")
    print(f"Iniciando em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar tabela products se não existir
    create_products_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar produtos
    products = get_products(token, base_url)
    
    # Salvar produtos no banco de dados
    save_products_to_db(products)
    
    print("=== RESUMO DA OPERAÇÃO ===")
    print(f"Tempo total de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de produtos processados: {len(products)}")
    print("Operação concluída com sucesso!")

if __name__ == "__main__":
    main()
