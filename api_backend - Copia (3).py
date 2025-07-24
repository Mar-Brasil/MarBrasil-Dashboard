import sqlite3
import json
import traceback
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from downloads.download_all_user_tasks_v2 import baixar_tarefas_periodo

# --- Configuração ---
app = FastAPI(title="Painel Admin API Auvo")

@app.on_event("startup")
async def startup_event():
    initialize_database()
    # Criação automática da tabela de usuários
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_painel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            data_nascimento TEXT,
            foto TEXT,
            username TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            permissoes TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DB_PATH = os.path.join(os.path.dirname(__file__), 'auvo.db')

# --- Helpers ---
import bcrypt
from typing import List, Optional

class UsuarioIn(BaseModel):
    nome_completo: str
    cpf: str
    data_nascimento: Optional[str]
    foto: Optional[str]
    username: str
    senha: str  # plaintext para criação, será armazenada como hash
    permissoes: List[str]

class UsuarioOut(BaseModel):
    id: int
    nome_completo: str
    cpf: str
    data_nascimento: Optional[str]
    foto: Optional[str]
    username: str
    permissoes: List[str]

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn

# --- Endpoints Usuários ---
from fastapi import status
from fastapi.encoders import jsonable_encoder

@app.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM usuarios_painel").fetchall()
    for u in users:
        u["permissoes"] = json.loads(u["permissoes"])
        del u["senha_hash"]
    conn.close()
    return users

@app.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: UsuarioIn):
    conn = get_db_connection()
    senha_hash = bcrypt.hashpw(usuario.senha.encode(), bcrypt.gensalt()).decode()
    permissoes_json = json.dumps(usuario.permissoes)
    try:
        cur = conn.execute(
            """
            INSERT INTO usuarios_painel (nome_completo, cpf, data_nascimento, foto, username, senha_hash, permissoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                usuario.nome_completo,
                usuario.cpf,
                usuario.data_nascimento,
                usuario.foto,
                usuario.username,
                senha_hash,
                permissoes_json
            )
        )
        conn.commit()
        user_id = cur.lastrowid
        user = conn.execute("SELECT * FROM usuarios_painel WHERE id = ?", (user_id,)).fetchone()
        user["permissoes"] = json.loads(user["permissoes"])
        del user["senha_hash"]
        return user
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Usuário ou CPF já cadastrado.")
    finally:
        conn.close()

@app.put("/usuarios/{id}", response_model=UsuarioOut)
def editar_usuario(id: int, usuario: UsuarioIn):
    conn = get_db_connection()
    senha_hash = bcrypt.hashpw(usuario.senha.encode(), bcrypt.gensalt()).decode()
    permissoes_json = json.dumps(usuario.permissoes)
    try:
        conn.execute(
            """
            UPDATE usuarios_painel SET nome_completo=?, cpf=?, data_nascimento=?, foto=?, username=?, senha_hash=?, permissoes=? WHERE id=?
            """,
            (
                usuario.nome_completo,
                usuario.cpf,
                usuario.data_nascimento,
                usuario.foto,
                usuario.username,
                senha_hash,
                permissoes_json,
                id
            )
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        user["permissoes"] = json.loads(user["permissoes"])
        del user["senha_hash"]
        return user
    finally:
        conn.close()

@app.delete("/usuarios/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario(id: int):
    conn = get_db_connection()
    cur = conn.execute("DELETE FROM usuarios_painel WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return None

def initialize_database():
    """Cria as tabelas personalizadas de faturamento se elas não existirem."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Tabela para armazenar taxas e valores por tipo de serviço
            cur.execute("""
                CREATE TABLE IF NOT EXISTS billing_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    unit_price REAL DEFAULT 0,
                    additional_price REAL DEFAULT 0,
                    UNIQUE(contract_id, description)
                )
            """)
            # Tabela para ajustes gerais (incentivos, particulares, etc.)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS billing_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    value REAL DEFAULT 0,
                    UNIQUE(contract_id, description)
                )
            """)
            print("Banco de dados inicializado com sucesso. Tabelas de faturamento verificadas/criadas.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

# --- Endpoints ---

# --- Billing Admin Endpoints ---

@app.get("/api/billing/task-types")
def get_billable_task_types():
    """Retorna os tipos de tarefa que são configuráveis para faturamento."""
    try:
        # IDs fornecidos pelo usuário que são relevantes para faturamento
        billable_ids = [175644, 175648, 175652, 175656, 175164, 175641, 175642, 175646, 175649, 175650, 175653, 175654, 177626, 184713, 184714, 184715, 184717]
        placeholders = ','.join('?' for _ in billable_ids)
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            query = f"SELECT id, description FROM task_types WHERE id IN ({placeholders}) ORDER BY description"
            cur.execute(query, billable_ids)
            task_types = cur.fetchall()
            return task_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tipos de tarefa: {e}")


class Rate(BaseModel):
    contract_id: int
    description: str
    unit_price: float
    additional_price: float

@app.get("/api/billing/rates/{contract_id}")
def get_billing_rates(contract_id: int):
    """Busca as taxas de faturamento para um contrato específico."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM billing_rates WHERE contract_id = ?", (contract_id,))
            rates = cur.fetchall()
            return rates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar taxas: {e}")

@app.post("/api/billing/rates")
def save_billing_rates(rate: Rate):
    """Cria ou atualiza uma taxa de faturamento."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO billing_rates (contract_id, description, unit_price, additional_price)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(contract_id, description) DO UPDATE SET
                    unit_price = excluded.unit_price,
                    additional_price = excluded.additional_price
            """, (rate.contract_id, rate.description, rate.unit_price, rate.additional_price))
            conn.commit()
            return {"status": "success", "data": rate.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar taxa: {e}")


class DownloadTasksRequest(BaseModel):
    start_date: str
    end_date: str

@app.post("/api/download-tasks")
async def download_tasks(req: DownloadTasksRequest):
    try:
        status, progress, file_path = baixar_tarefas_periodo(req.start_date, req.end_date)
        return {"status": status, "progress": progress, "file": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar tarefas: {e}")

@app.get("/api/download-tasks/file")
def get_downloaded_file(path: str):
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, filename=os.path.basename(path))


@app.get("/api/escola/{school_id}/equipamentos-debug")
def get_school_equipments_debug(school_id: int):
    """
    Endpoint de depuração: retorna todos os equipamentos associados a uma escola específica.
    NÃO altera nenhuma lógica existente.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM equipments WHERE associatedCustomerId = ?", (school_id,))
            equipamentos = cur.fetchall()
            return [dict(e) for e in equipamentos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar equipamentos: {e}")

@app.get("/api/faturamento")
def get_billing_report(group_id: int, start_date: str, end_date: str):
    """Gera um relatório de faturamento por colaborador para um contrato e período."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            # 1. Obter IDs das escolas do contrato
            cur.execute("SELECT id FROM customers WHERE groupsId LIKE ?", (f'%{group_id}%',))
            schools = cur.fetchall()
            if not schools:
                return []
            school_ids = [s['id'] for s in schools]
            placeholders = ','.join('?' for _ in school_ids)

            # 2. Buscar TODOS os colaboradores que já tiveram tarefas no contrato (independente da data)
            all_collaborators_query = f"""
                SELECT DISTINCT
                    t.idUserTo as user_id,
                    u.name as user_name
                FROM tasks t
                JOIN users u ON t.idUserTo = u.id
                WHERE t.idCustomer IN ({placeholders}) AND t.idUserTo IS NOT NULL
            """
            cur.execute(all_collaborators_query, school_ids)
            all_collaborators = cur.fetchall()

            # 3. Buscar tarefas no período para calcular a produtividade
            end_date_inclusive = f"{end_date} 23:59:59"
            tasks_in_period_query = f"""
                SELECT
                    t.idUserTo as user_id,
                    t.status
                FROM tasks t
                WHERE t.idCustomer IN ({placeholders}) AND t.date BETWEEN ? AND ?
            """
            cur.execute(tasks_in_period_query, school_ids + [start_date, end_date_inclusive])
            tasks_in_period = cur.fetchall()

            # 4. Estruturar o relatório inicial com todos os colaboradores
            report = {{
                collab['user_id']: {
                    "user_id": collab['user_id'],
                    "user_name": collab['user_name'],
                    "tasks_completed": 0,
                    "tasks_total": 0,
                    "productivity": 0
                }
                for collab in all_collaborators
            }}

            # 5. Preencher com os dados das tarefas do período
            for task in tasks_in_period:
                user_id = task['user_id']
                if user_id in report:
                    report[user_id]['tasks_total'] += 1
                    if task['status'] == 'Finalizada':
                        report[user_id]['tasks_completed'] += 1

            # 6. Calcular produtividade e formatar a saída
            final_report = []
            for user_id, user_data in report.items():
                total = user_data['tasks_total']
                completed = user_data['tasks_completed']
                user_data['productivity'] = (completed / total * 100) if total > 0 else 0
                final_report.append(user_data)

            return sorted(final_report, key=lambda x: x['user_name'])

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório de faturamento: {e}")

@app.get("/api/contracts")
def get_contracts():
    """Retorna os contratos relevantes."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            allowed_contract_ids = [156750, 156751, 156752, 156753, 156754, 146168, 120805, 144297, 115503]
            placeholders = ','.join('?' for _ in allowed_contract_ids)
            query = f"SELECT id, description as name FROM customer_groups WHERE id IN ({placeholders}) ORDER BY name"
            cur.execute(query, allowed_contract_ids)
            return cur.fetchall()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {e}")

def _get_dashboard_by_contract_data(group_id: int, start_date: str = None, end_date: str = None):
    def _extract_manager_ids(school):
        managers = school.get('managersId', '[]')
        try:
            manager_ids = json.loads(managers if managers else '[]')
            if isinstance(manager_ids, list): return [int(mid) for mid in manager_ids if str(mid).isdigit()]
        except (json.JSONDecodeError, TypeError):
            if isinstance(managers, str): return [int(mid.strip()) for mid in managers.split(',') if mid.strip().isdigit()]
        return []

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # 1. Obter contrato e escolas
            cur.execute("SELECT * FROM customer_groups WHERE id = ?", (group_id,))
            contract = cur.fetchone()
            if not contract: raise HTTPException(status_code=404, detail="Contrato não encontrado")
            cur.execute("SELECT * FROM customers WHERE groupsId LIKE ?", (f'%{group_id}%',))
            schools_raw = cur.fetchall()
            school_ids = [s['id'] for s in schools_raw]

            if not school_ids:
                return {
                    "contract": dict(contract),
                    "indicators": {
                        "total_schools": 0, "total_collaborators": 0,
                        "total_equipments": 0, "total_tasks": 0,
                        "completion_rate": 0, "task_type_kpis": []
                    },
                    "schools": [],
                    "collaborators": [],
                    "tasks": []
                }
            
            # Obter ID da tarefa 'Levantamento de PMOC' para exclusão das métricas
            cur.execute("SELECT id FROM task_types WHERE description LIKE ?", ('%Levantamento de PMOC%',))
            pmoc_task_type = cur.fetchone()
            pmoc_task_type_id = pmoc_task_type['id'] if pmoc_task_type else None

            # Obter mapa de tipos de tarefa para referência posterior
            cur.execute("SELECT id, description FROM task_types")
            task_type_map = {tt['id']: tt['description'] for tt in cur.fetchall()}

            # 2. Obter todos os dados relacionados
            school_id_placeholders = ','.join('?' for _ in school_ids)
            allowed_task_type_ids = [175644, 175648, 175652, 175656, 175164, 175641, 175642, 175646, 175649, 175650, 175653, 175654, 177626, 184713, 184714, 184715, 184717]
            task_type_placeholders = ','.join('?' for _ in allowed_task_type_ids)

            # Tarefas (apenas tipos permitidos e não canceladas)
            tasks_query = f"SELECT * FROM tasks WHERE customerId IN ({school_id_placeholders}) AND taskStatus != 7 AND taskType IN ({task_type_placeholders})"
            params = school_ids + allowed_task_type_ids

            if start_date and end_date:
                end_date_inclusive = f"{end_date} 23:59:59"
                tasks_query += " AND date BETWEEN ? AND ?"
                params.extend([start_date, end_date_inclusive])

            cur.execute(tasks_query, params)
            tasks_to_process = cur.fetchall()

            # 3. Processar e agrupar dados por escola
            schools_data = []
            all_tasks = []
            # Processar todas as escolas, não apenas as que têm tarefas
            schools_to_process = schools_raw

            print("\n" + "="*50)
            print("INICIANDO PROCESSAMENTO DE DADOS POR ESCOLA")
            print("="*50)
            for school_raw in schools_to_process:
                school_id = school_raw['id']
                print(f"\n--- PROCESSANDO ESCOLA ID: {school_id} ({school_raw['description']}) ---")
                # Obter tarefas para esta escola (pode ser uma lista vazia)
                school_tasks = [t for t in tasks_to_process if t['customerId'] == school_id]
                all_tasks.extend(school_tasks)

                # Buscar apenas os equipamentos ativos da escola
                cur.execute("SELECT * FROM equipments WHERE associatedCustomerId = ? AND active = 1", (school_id,))
                equipments_to_process = cur.fetchall()
                total_ativos = len(equipments_to_process)

                print(f"[LOG] Total de equipamentos ativos: {total_ativos}")

                # Anexar status de tarefas concluídas a cada equipamento
                equipments_with_status = []
                for equip in equipments_to_process:
                    equip_dict = dict(equip)
                    equip_dict['completed_tasks'] = []
                    for task in school_tasks:
                        if task.get('taskStatus') in [5, 6]:  # Tarefa Finalizada ou Concluída
                            try:
                                task_equip_ids_str = task.get('equipmentsId', '[]')
                                task_equip_ids = json.loads(task_equip_ids_str if task_equip_ids_str else '[]')
                                if equip_dict['id'] in task_equip_ids:
                                    task_type_id = task.get('taskType')
                                    task_type_desc = task_type_map.get(task_type_id, "Desconhecido")
                                    equip_dict['completed_tasks'].append({
                                        'task_type_id': task_type_id,
                                        'task_type_description': task_type_desc,
                                        'task_id': task.get('taskID')
                                    })
                            except (json.JSONDecodeError, TypeError):
                                continue
                        # Adicionar informação se é ativo ou não para facilitar filtragem no frontend
                    equipments_with_status.append(equip_dict)
                
                # Log extra para depuração
                if 'WALDERY' in school_raw['description'] or 'CELY' in school_raw['description']:
                    print(f"======= ESCOLA ESPECIAL: {school_raw['description']} =======")
                    print(f">>> Equipamentos na lista: {len(equipments_with_status)}")
                    if len(equipments_with_status) > 0:
                        first_equip = equipments_with_status[0]
                        print(f">>> Primeiro equipamento: ID={first_equip['id']}, Nome={first_equip.get('name', 'N/A')}, Ativo={first_equip.get('ativo', 'N/A')}")
                    print("====================================================")
                    
                print(f"[LOG] Lista final de equipamentos para esta escola contém: {len(equipments_with_status)} itens.")

                # Filtra tarefas para cálculo de métricas (exclui PMOC)
                tasks_for_metrics = [t for t in school_tasks if t.get('taskType') != pmoc_task_type_id]
                answered_equipments_ids = set()
                for task in tasks_for_metrics:
                    if task['taskStatus'] == 5 and task.get('questionnaires'):
                        try:
                            questionnaires_list = json.loads(task['questionnaires'])
                            if isinstance(questionnaires_list, list):
                                for q in questionnaires_list:
                                    if q and q.get('questionnaireEquipamentId'):
                                        answered_equipments_ids.add(q['questionnaireEquipamentId'])
                        except (json.JSONDecodeError, TypeError): pass
                
                total_realizadas = len(answered_equipments_ids)
                percentual = round((total_realizadas / total_ativos) * 100) if total_ativos > 0 else 0

                school_data_entry = {
                    "school_info": dict(school_raw),
                    "equipments": equipments_with_status,
                    "tasks": [dict(t) for t in school_tasks],
                    "metrics": {"ativos": total_ativos, "realizadas": total_realizadas, "percentual": percentual}
                }
                
                # Verificar se os equipamentos estão sendo adicionados corretamente aos dados da escola
                if 'WALDERY' in school_raw['description'] or 'CELY' in school_raw['description']:
                    print(f">>> Equipamentos adicionados aos dados da escola {school_raw['description']}: {len(school_data_entry['equipments'])}")
                    
                schools_data.append(school_data_entry)

            # Log para debug - verificar estrutura de dados
            print("\n=== RESUMO DAS ESCOLAS PROCESSADAS ===\n")
            for school_data in schools_data:
                try:
                    school_name = school_data['school_info']['description']
                    equip_count = len(school_data.get('equipments', [])) 
                    print(f"Escola: {school_name}, Total de equipamentos: {equip_count}")
                    if equip_count > 0 and 'CAMARA' in school_name:
                        print(f"  Amostra de equipamento: {school_data['equipments'][0]}")
                except Exception as e:
                    print(f"Erro ao processar escola: {e}")
            
            # 4. Filtrar colaboradores a partir das tarefas (idUserTo), como estava originalmente
            final_collaborator_ids = list({task['idUserTo'] for task in all_tasks if task.get('idUserTo')})
            final_collaborators = []
            if final_collaborator_ids:
                placeholders = ','.join('?' for _ in final_collaborator_ids)
                cur.execute(f"SELECT userId, name as userName FROM users WHERE userId IN ({placeholders})", final_collaborator_ids)
                final_collaborators = [dict(c) for c in cur.fetchall()]

            # 5. Calcular KPIs globais
            total_tasks = len(all_tasks)
            tasks_for_global_metrics = [t for t in all_tasks if t.get('taskType') != pmoc_task_type_id]
            completed_tasks = sum(1 for t in tasks_for_global_metrics if t.get('taskStatus') == 6)
            completion_rate = (completed_tasks / len(tasks_for_global_metrics) * 100) if tasks_for_global_metrics else 0
            
            tasks_by_type = {}
            for t in all_tasks:
                type_id = t.get('taskType')
                if type_id is not None:
                    tasks_by_type[type_id] = tasks_by_type.get(type_id, 0) + 1
            task_type_kpis = [{"id": tid, "description": task_type_map.get(tid, "Desconhecido"), "count": count} for tid, count in tasks_by_type.items()]

            print("\n" + "="*50)
            print("FINALIZANDO CÁLCULO DOS INDICADORES GERAIS")
            print("="*50)
            total_equipments_in_view = sum(s['metrics']['ativos'] for s in schools_data)
            print(f"[LOG] Soma de 's['metrics']['ativos']' de todas as escolas processadas: {total_equipments_in_view}")
            print(f"[LOG] Valor final a ser enviado para o KPI 'Total de Equipamentos': {total_equipments_in_view}")

            indicators = {
                "total_schools": len(schools_data),
                "total_collaborators": len(final_collaborators),
                "total_equipments": total_equipments_in_view,
                "total_tasks": total_tasks,
                "completion_rate": round(completion_rate, 2),
                "task_type_kpis": sorted(task_type_kpis, key=lambda x: x['count'], reverse=True)
            }

            # Função para garantir que objetos SQLite sejam convertidos para Python nativos
            def sanitize_for_json(obj):
                if isinstance(obj, dict):
                    return {k: sanitize_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize_for_json(item) for item in obj]
                elif isinstance(obj, sqlite3.Row):
                    # Converter sqlite3.Row para dict
                    return {key: row[key] for key in row.keys()}
                else:
                    # Valores primitivos são retornados como estão
                    return obj
            
            # LOG: Conferir se 'equipments' está presente em cada escola antes da sanitização
            print('\n===== DEBUG schools_data antes da sanitização =====')
            for idx, school in enumerate(schools_data):
                print(f"Escola #{idx+1}: {school['school_info'].get('description', 'N/A')}")
                print(f"  school.keys: {list(school.keys())}")
                print(f"  Tem campo 'equipments'? {'equipments' in school}")
                if 'equipments' in school:
                    print(f"  Quantidade de equipamentos: {len(school['equipments'])}")
                else:
                    print("  ALERTA: Campo 'equipments' NÃO presente nesta escola!")
            print('===============================================\n')

            # Sanitizar todos os dados para garantir serialização
            sanitized_schools = []
            for school in schools_data:
                try:
                    sanitized_school = {
                        "school_info": dict(school["school_info"]),
                        "equipments": [dict(equip) for equip in school.get("equipments", [])],
                        "tasks": [
                            {**dict(task), "userId": task.get("idUserTo"), "userName": task.get("userToName")}
                            for task in school.get("tasks", [])
                        ],
                        "metrics": school.get("metrics", {})
                    }
                    sanitized_schools.append(sanitized_school)
                except Exception as e:
                    print(f"Erro ao sanitizar escola: {e}")
                    print(f"Dados da escola com erro: {school}")
            
            # Criar a resposta final com dados sanitizados
            final_response = {
                "contract": dict(contract),
                "indicators": indicators,
                "schools": sanitized_schools,
                "collaborators": [dict(c) for c in final_collaborators],
                "tasks": [dict(t) for t in all_tasks]
            }
            
            print("\n==== VERIFICAÇÃO FINAL DE RESPOSTA PARA O FRONTEND =====\n")
            print(f"Total de escolas sanitizadas: {len(final_response['schools'])}")
            
            try:
                if final_response['schools']:
                    first_school = final_response['schools'][0]
                    print(f"Primeira escola: {first_school['school_info']['description']}")
                    print(f"Equipamentos na primeira escola: {len(first_school.get('equipments', []))}")
                
                # Teste de serialização
                json_str = json.dumps(final_response)
                print("Serialização para JSON bem-sucedida!")
            except Exception as json_err:
                print(f"ERRO DE SERIALIZAÇÃO: {json_err}")
                # Em caso de erro, retornar uma resposta simplificada
                return {"error": "Erro ao serializar dados", "detail": str(json_err)}
            
            return final_response
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado: {e}")

@app.get("/api/dashboard/{group_id}")
def get_dashboard_by_contract(group_id: int):
    return _get_dashboard_by_contract_data(group_id)

@app.get("/api/faturamento-report/{group_id}")
def get_faturamento_report(group_id: int, start_date: str, end_date: str):
    return _get_dashboard_by_contract_data(group_id, start_date=start_date, end_date=end_date)

@app.get("/api/contract-collaborators/{group_id}")
def get_contract_collaborators(group_id: int):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE groupsId LIKE ?", (f'%{group_id}%',))
        schools = cur.fetchall()
        all_manager_ids = set()
        for school in schools:
            managers_field = school.get('managersId', '[]')
            try:
                ids = json.loads(managers_field if managers_field else '[]')
                if isinstance(ids, list):
                    all_manager_ids.update(int(mid) for mid in ids if str(mid).isdigit())
            except (json.JSONDecodeError, TypeError):
                if isinstance(managers_field, str):
                    all_manager_ids.update(int(mid.strip()) for mid in managers_field.split(',') if mid.strip().isdigit())
        collaborators = []
        if all_manager_ids:
            placeholders = ','.join('?' for _ in all_manager_ids)
            cur.execute(f"SELECT userId, name as userName, cpf FROM users WHERE userId IN ({placeholders})", list(all_manager_ids))
            collaborators = [dict(c) for c in cur.fetchall()]
        return {"collaborators": collaborators}

@app.get("/api/billing/financial-summary/{group_id}")
def get_financial_summary(group_id: int, start_date: str, end_date: str):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Buscar as taxas de faturamento para o contrato
        cur.execute("SELECT description, unit_price, additional_price FROM billing_rates WHERE contract_id = ?", (group_id,))
        rates_rows = cur.fetchall()
        if not rates_rows:
            conn.close()
            return {"summary": [], "grand_total": 0} # Retorna vazio se não houver taxas

        rates_map = {rate['description']: {'unit_price': rate['unit_price'], 'additional_price': rate['additional_price']} for rate in rates_rows}

        # 2. Buscar tarefas executadas (status 5) no período
        cur.execute("""
            SELECT taskTypeDescription, COUNT(*) as executed_count
            FROM tasks
            WHERE customer_group_id = ? 
              AND taskStatus = 5
              AND date(taskDate) BETWEEN ? AND ?
            GROUP BY taskTypeDescription
        """, (group_id, start_date, end_date))
        executed_tasks = cur.fetchall()

        financial_summary = []
        grand_total = 0

        # 3. Calcular o total para cada tipo de tarefa
        for task in executed_tasks:
            task_desc = task['taskTypeDescription']
            executed_count = task['executed_count']
            rate = rates_map.get(task_desc)

            if rate:
                total_line = (executed_count * rate['unit_price']) + rate['additional_price']
                financial_summary.append({
                    "description": task_desc,
                    "executed": executed_count,
                    "unit_price": rate['unit_price'],
                    "additional_price": rate['additional_price'],
                    "total": total_line
                })
                grand_total += total_line

        conn.close()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo financeiro: {e}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
