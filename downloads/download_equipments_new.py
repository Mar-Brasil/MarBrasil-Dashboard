"""
Script para download completo de equipamentos da API Auvo
Baseado na documentação oficial da API v2
Criado para resolver problemas de equipamentos faltantes
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
import time

def login_to_auvo():
    """Faz login na API Auvo e retorna o token de acesso"""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("API_URL") or "https://api.auvo.com.br/v2"
    
    if not api_key or not api_token:
        print("❌ Credenciais da API não encontradas no arquivo .env!")
        sys.exit(1)
    
    print(f"🔑 Usando credenciais: API_KEY={api_key[:4]}...{api_key[-4:]}")
    
    login_url = f"{base_url}/login/?apiKey={api_key}&apiToken={api_token}"
    
    try:
        response = requests.get(login_url)
        data = response.json()
        
        if "result" in data and data["result"]["authenticated"]:
            token = data["result"]["accessToken"]
            expiration = data["result"]["expiration"]
            print(f"✅ Login realizado com sucesso! Token válido até: {expiration}")
            return token, base_url
        else:
            print("❌ Falha na autenticação!")
            print(f"Resposta: {data}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        sys.exit(1)

def create_equipments_table():
    """Cria ou atualiza a tabela de equipamentos com estrutura correta"""
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Verificar se a tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipments'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("📋 Criando tabela 'equipments' com estrutura completa...")
        cursor.execute("""
        CREATE TABLE equipments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            externalId TEXT,
            parentEquipmentId INTEGER,
            associatedCustomerId INTEGER,
            associatedUserId INTEGER,
            categoryId INTEGER,
            identifier TEXT,
            urlImage TEXT,
            uriAnexos TEXT,
            active INTEGER,
            creationDate TEXT,
            expirationDate TEXT,
            equipmentSpecifications TEXT,
            description TEXT,
            warrantyStartDate TEXT,
            warrantyEndDate TEXT,
            -- Campos legados (mantidos para compatibilidade, mas não utilizados)
            tipo TEXT,
            setor_id INTEGER,
            associated_customer_id INTEGER,
            ativo INTEGER,
            identificador TEXT
        )
        """)
        conn.commit()
        print("✅ Tabela 'equipments' criada com sucesso!")
    else:
        # Verificar e adicionar colunas que podem estar faltando
        cursor.execute("PRAGMA table_info(equipments)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = {
            'externalId': 'TEXT',
            'parentEquipmentId': 'INTEGER',
            'associatedCustomerId': 'INTEGER', 
            'associatedUserId': 'INTEGER',
            'categoryId': 'INTEGER',
            'identifier': 'TEXT',
            'urlImage': 'TEXT',
            'uriAnexos': 'TEXT',
            'active': 'INTEGER',
            'creationDate': 'TEXT',
            'expirationDate': 'TEXT',
            'equipmentSpecifications': 'TEXT',
            'description': 'TEXT',
            'warrantyStartDate': 'TEXT',
            'warrantyEndDate': 'TEXT'
        }
        
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                print(f"➕ Adicionando coluna '{column_name}' à tabela...")
                cursor.execute(f"ALTER TABLE equipments ADD COLUMN {column_name} {column_type}")
                conn.commit()
        
        print("✅ Estrutura da tabela verificada e atualizada!")
    
    conn.close()

def get_all_equipments(token, base_url):
    """
    Busca TODOS os equipamentos da API Auvo usando paginação
    Baseado na documentação oficial: GET /equipments/
    """
    url = f"{base_url}/equipments/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("API_KEY")
    }
    
    all_equipments = []
    page = 1
    page_size = 100  # Máximo recomendado
    total_found = 0
    
    print(f"\n🔍 Iniciando busca de equipamentos...")
    print(f"📡 URL base: {url}")
    
    try:
        while True:
            print(f"📄 Buscando página {page} (pageSize={page_size})...")
            
            # Parâmetros conforme documentação oficial
            params = {
                "page": page,
                "pageSize": page_size,
                "order": "asc"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"❌ Erro HTTP {response.status_code} ao buscar equipamentos")
                print(f"Resposta: {response.text[:500]}...")
                break
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON: {e}")
                print(f"Resposta bruta: {response.text[:200]}...")
                break
            
            # Extrair lista de equipamentos conforme documentação
            equipments_list = []
            if "result" in data:
                if isinstance(data["result"], dict) and "entityList" in data["result"]:
                    equipments_list = data["result"]["entityList"]
                    # Informações de paginação
                    paged_data = data["result"].get("pagedSearchReturnData", {})
                    total_items = paged_data.get("totalItems", 0)
                    if page == 1 and total_items > 0:
                        print(f"📊 Total de equipamentos disponíveis na API: {total_items}")
                elif isinstance(data["result"], list):
                    equipments_list = data["result"]
            
            if not equipments_list:
                print(f"⚠️  Nenhum equipamento encontrado na página {page}")
                if page == 1:
                    print(f"Estrutura da resposta: {json.dumps(data, indent=2)[:300]}...")
                break
            
            # Validar e filtrar equipamentos válidos
            valid_equipments = []
            for equipment in equipments_list:
                if isinstance(equipment, dict) and "id" in equipment:
                    valid_equipments.append(equipment)
                else:
                    print(f"⚠️  Equipamento inválido ignorado: {equipment}")
            
            all_equipments.extend(valid_equipments)
            total_found += len(valid_equipments)
            
            print(f"✅ Página {page}: {len(valid_equipments)} equipamentos válidos encontrados")
            print(f"📈 Total acumulado: {total_found} equipamentos")
            
            # Verificar se há mais páginas
            if len(equipments_list) < page_size:
                print(f"📋 Última página alcançada (retornou {len(equipments_list)} < {page_size})")
                break
            
            page += 1
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.1)
    
    except Exception as e:
        print(f"❌ Erro ao buscar equipamentos: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 Busca finalizada: {total_found} equipamentos encontrados no total")
    return all_equipments

def safe_json_dumps(value):
    """Converte valor para JSON string de forma segura"""
    if value is None:
        return None
    elif isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    else:
        return str(value)

def save_equipments_to_db(equipments):
    """Salva equipamentos no banco de dados SQLite"""
    if not equipments:
        print("⚠️  Nenhum equipamento para salvar!")
        return 0, 0
    
    print(f"\n💾 Salvando {len(equipments)} equipamentos no banco de dados...")
    
    conn = sqlite3.connect('auvo.db')
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()
    
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    try:
        for i, equipment in enumerate(equipments, 1):
            try:
                equipment_id = equipment.get("id")
                if not equipment_id:
                    print(f"⚠️  Equipamento {i} sem ID, ignorando...")
                    continue
                
                # Verificar se já existe
                cursor.execute("SELECT id FROM equipments WHERE id = ?", (equipment_id,))
                exists = cursor.fetchone() is not None
                
                # Preparar dados conforme documentação da API
                equipment_data = {
                    'id': equipment_id,
                    'name': equipment.get("name"),
                    'externalId': equipment.get("externalId"),
                    'parentEquipmentId': equipment.get("parentEquipmentId"),
                    'associatedCustomerId': equipment.get("associatedCustomerId"),
                    'associatedUserId': equipment.get("associatedUserId"),
                    'categoryId': equipment.get("categoryId"),
                    'identifier': equipment.get("identifier"),
                    'urlImage': equipment.get("urlImage"),
                    'uriAnexos': safe_json_dumps(equipment.get("uriAnexos")),
                    'active': 1 if equipment.get("active") else 0,
                    'creationDate': equipment.get("creationDate"),
                    'expirationDate': equipment.get("expirationDate"),
                    'equipmentSpecifications': safe_json_dumps(equipment.get("equipmentSpecifications")),
                    'description': equipment.get("description"),
                    'warrantyStartDate': equipment.get("warrantyStartDate"),
                    'warrantyEndDate': equipment.get("warrantyEndDate")
                }
                
                if exists:
                    # Atualizar equipamento existente
                    cursor.execute("""
                        UPDATE equipments SET
                            name=?, externalId=?, parentEquipmentId=?, associatedCustomerId=?,
                            associatedUserId=?, categoryId=?, identifier=?, urlImage=?,
                            uriAnexos=?, active=?, creationDate=?, expirationDate=?,
                            equipmentSpecifications=?, description=?, warrantyStartDate=?, warrantyEndDate=?
                        WHERE id = ?
                    """, (
                        equipment_data['name'], equipment_data['externalId'], 
                        equipment_data['parentEquipmentId'], equipment_data['associatedCustomerId'],
                        equipment_data['associatedUserId'], equipment_data['categoryId'],
                        equipment_data['identifier'], equipment_data['urlImage'],
                        equipment_data['uriAnexos'], equipment_data['active'],
                        equipment_data['creationDate'], equipment_data['expirationDate'],
                        equipment_data['equipmentSpecifications'], equipment_data['description'],
                        equipment_data['warrantyStartDate'], equipment_data['warrantyEndDate'],
                        equipment_id
                    ))
                    updated_count += 1
                else:
                    # Inserir novo equipamento
                    cursor.execute("""
                        INSERT INTO equipments (
                            id, name, externalId, parentEquipmentId, associatedCustomerId,
                            associatedUserId, categoryId, identifier, urlImage, uriAnexos,
                            active, creationDate, expirationDate, equipmentSpecifications,
                            description, warrantyStartDate, warrantyEndDate
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        equipment_data['id'], equipment_data['name'], equipment_data['externalId'],
                        equipment_data['parentEquipmentId'], equipment_data['associatedCustomerId'],
                        equipment_data['associatedUserId'], equipment_data['categoryId'],
                        equipment_data['identifier'], equipment_data['urlImage'],
                        equipment_data['uriAnexos'], equipment_data['active'],
                        equipment_data['creationDate'], equipment_data['expirationDate'],
                        equipment_data['equipmentSpecifications'], equipment_data['description'],
                        equipment_data['warrantyStartDate'], equipment_data['warrantyEndDate']
                    ))
                    inserted_count += 1
                
                # Log de progresso
                if i % 100 == 0:
                    print(f"📊 Processados {i}/{len(equipments)} equipamentos...")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Erro ao processar equipamento {equipment.get('id', 'desconhecido')}: {e}")
                continue
        
        conn.commit()
        print(f"\n✅ Operação concluída com sucesso!")
        print(f"➕ Equipamentos inseridos: {inserted_count}")
        print(f"🔄 Equipamentos atualizados: {updated_count}")
        print(f"❌ Erros: {error_count}")
        
    except Exception as e:
        print(f"❌ Erro crítico ao salvar no banco: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return inserted_count, updated_count

def verify_missing_equipment(equipment_name):
    """Verifica se um equipamento específico existe no banco"""
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM equipments WHERE name LIKE ?", (f"%{equipment_name}%",))
    results = cursor.fetchall()
    
    conn.close()
    return results

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 DOWNLOAD COMPLETO DE EQUIPAMENTOS - API AUVO v2")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Criar/verificar estrutura da tabela
    create_equipments_table()
    
    # Login na API
    token, base_url = login_to_auvo()
    
    # Buscar TODOS os equipamentos
    equipments = get_all_equipments(token, base_url)
    
    if not equipments:
        print("❌ Nenhum equipamento foi encontrado na API!")
        sys.exit(1)
    
    # Salvar no banco de dados
    inserted, updated = save_equipments_to_db(equipments)
    
    # Script otimizado para execução diária - download completo de todos os equipamentos
    
    print(f"\n" + "=" * 60)
    print(f"✅ DOWNLOAD FINALIZADO!")
    print(f"📊 Total processado: {len(equipments)} equipamentos")
    print(f"➕ Inseridos: {inserted}")
    print(f"🔄 Atualizados: {updated}")
    print(f"⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
