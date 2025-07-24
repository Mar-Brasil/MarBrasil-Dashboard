import sqlite3
import json
import traceback
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import bcrypt
from datetime import datetime, timedelta

# --- Configuração ---
app = FastAPI(title="Painel Auvo Mobile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'auvo.db')

# --- Models ---
class LoginRequest(BaseModel):
    username: str
    senha: str

class User(BaseModel):
    id: int
    nome_completo: str
    cpf: str
    data_nascimento: Optional[str]
    foto: Optional[str]
    username: str
    permissoes: List[str]
    contratos: List[int]

class DashboardBatchRequest(BaseModel):
    contract_ids: List[int]

class School(BaseModel):
    id: int
    name: str
    description: str
    equipments: List[dict]
    tasks: List[dict]
    progress_percentage: float

class Equipment(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tipo: Optional[str]
    active: bool

class Collaborator(BaseModel):
    id: int
    name: str
    email: Optional[str]
    tasks_completed: int
    tasks_pending: int
    total_tasks: int

class Task(BaseModel):
    id: int
    orientation: str
    status: str
    taskType: int
    taskTypeName: Optional[str]
    customerId: int
    customerName: Optional[str]
    idUserTo: int
    userName: Optional[str]
    checkInDate: Optional[str]
    lastUpdate: Optional[str]
    equipmentsId: Optional[str]
    equipmentNames: Optional[List[str]]

class KpiData(BaseModel):
    total_schools: int
    total_collaborators: int
    total_equipments: int
    tasks_completed: int
    tasks_pending: int
    tasks_in_progress: int
    overall_progress: float
    mensal_progress: float
    semestral_progress: float
    corretiva_count: int
    pmoc_progress: float

class DashboardData(BaseModel):
    contract_id: int
    contract_name: str
    schools: List[School]
    collaborators: List[Collaborator]
    kpis: KpiData
    tasks: List[Task]

class Contract(BaseModel):
    id: int
    description: str
    active: bool

# --- Helpers ---
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn

def get_task_status_text(status_code):
    """
    Converte código de status da tarefa para texto
    """
    if status_code is None:
        return "Pendente"
    
    status_map = {
        0: "Pendente",
        1: "Em Andamento",
        2: "Concluída",
        3: "Cancelada",
        4: "Pausada"
    }
    
    return status_map.get(status_code, "Pendente")

# --- Endpoints ---

@app.post("/login")
async def login(login_data: LoginRequest):
    """
    Endpoint de login para o app mobile
    """
    try:
        conn = get_db_connection()
        
        # Busca o usuário na tabela usuarios_painel
        cursor = conn.execute("""
            SELECT id, nome_completo, cpf, data_nascimento, foto, username, senha_hash, permissoes
            FROM usuarios_painel 
            WHERE username = ?
        """, (login_data.username,))
        
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Verifica a senha
        if not bcrypt.checkpw(login_data.senha.encode('utf-8'), user_row['senha_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Senha incorreta")
        
        # Busca os contratos do usuário
        cursor = conn.execute("""
            SELECT contrato_id FROM usuario_contratos WHERE usuario_id = ?
        """, (user_row['id'],))
        
        contratos = [row['contrato_id'] for row in cursor.fetchall()]
        
        # Converte permissões de JSON para lista
        permissoes = json.loads(user_row['permissoes']) if user_row['permissoes'] else []
        
        user = User(
            id=user_row['id'],
            nome_completo=user_row['nome_completo'],
            cpf=user_row['cpf'],
            data_nascimento=user_row['data_nascimento'],
            foto=user_row['foto'],
            username=user_row['username'],
            permissoes=permissoes,
            contratos=contratos
        )
        
        conn.close()
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/dashboard/batch")
async def get_dashboard_batch(request: DashboardBatchRequest):
    """
    Retorna dados do dashboard para múltiplos contratos (otimizado para mobile)
    """
    try:
        dashboard_data = []
        
        for contract_id in request.contract_ids:
            print(f"Processando contrato: {contract_id}")
            data = await get_dashboard_by_contract_mobile(contract_id)
            dashboard_data.append(data)
        
        return dashboard_data
        
    except Exception as e:
        print(f"Erro ao buscar dashboard batch: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dados do dashboard: {str(e)}")

async def get_dashboard_by_contract_mobile(contract_id: int) -> DashboardData:
    """
    Busca dados do dashboard para um contrato específico (usa a mesma lógica do backend principal)
    """
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # 1. Busca informações do contrato
        cursor.execute("SELECT * FROM customer_groups WHERE id = ?", (contract_id,))
        contract = cursor.fetchone()
        if not contract:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
        # 2. Busca escolas do contrato
        cursor.execute("SELECT * FROM customers WHERE groupsId LIKE ?", (f'%{contract_id}%',))
        schools_raw = cursor.fetchall()
        school_ids = [s['id'] for s in schools_raw]
        
        if not school_ids:
            return DashboardData(
                contract_id=contract_id,
                contract_name=contract['description'],
                schools=[],
                collaborators=[],
                kpis=KpiData(
                    total_schools=0, total_collaborators=0, total_equipments=0,
                    tasks_completed=0, tasks_pending=0, tasks_in_progress=0,
                    overall_progress=0, mensal_progress=0, semestral_progress=0,
                    corretiva_count=0, pmoc_progress=0
                ),
                tasks=[]
            )
        
        # 3. Busca tarefas (usa os mesmos filtros do backend principal)
        school_id_placeholders = ','.join('?' for _ in school_ids)
        allowed_task_type_ids = [175644, 175648, 175652, 175656, 175164, 175641, 175642, 175646, 175649, 175650, 175653, 175654, 177626, 184713, 184714, 184715, 184717]
        task_type_placeholders = ','.join('?' for _ in allowed_task_type_ids)
        
        tasks_query = f"SELECT * FROM tasks WHERE customerId IN ({school_id_placeholders}) AND taskStatus != 7 AND taskType IN ({task_type_placeholders})"
        params = school_ids + allowed_task_type_ids
        
        cursor.execute(tasks_query, params)
        tasks_to_process = cursor.fetchall()
        
        # 4. Busca tipos de tarefa para referência
        cursor.execute("SELECT id, description FROM task_types")
        task_type_map = {tt['id']: tt['description'] for tt in cursor.fetchall()}
        
        # 5. Processa dados por escola
        schools = []
        all_tasks = []
        
        for school_raw in schools_raw:
            school_id = school_raw['id']
            
            # Busca equipamentos ATIVOS da escola (mesma lógica do backend principal)
            cursor.execute("SELECT * FROM equipments WHERE associatedCustomerId = ? AND active = 1", (school_id,))
            equipments_raw = cursor.fetchall()
            
            equipments = [
                {
                    "id": eq['id'],
                    "name": eq['name'] or eq['description'] or f"Equipamento {eq['id']}",
                    "description": eq['description'],
                    "tipo": eq.get('tipo', ''),
                    "active": True
                }
                for eq in equipments_raw
            ]
            
            # Busca tarefas da escola
            school_tasks_raw = [t for t in tasks_to_process if t['customerId'] == school_id]
            
            school_tasks = []
            for task_row in school_tasks_raw:
                # Busca nome do usuário
                user_name = None
                if task_row['idUserTo']:
                    cursor.execute("SELECT name FROM users WHERE userId = ?", (task_row['idUserTo'],))
                    user_result = cursor.fetchone()
                    if user_result:
                        user_name = user_result['name']
                
                task = {
                    "id": task_row['taskID'],
                    "orientation": task_row['orientation'] or "Tarefa sem descrição",
                    "status": get_task_status_text(task_row['taskStatus']),
                    "taskStatus": task_row['taskStatus'],  # Mantém o código numérico também
                    "taskType": task_row['taskType'],
                    "taskTypeName": task_type_map.get(task_row['taskType'], f"Tipo {task_row['taskType']}"),
                    "customerId": task_row['customerId'],
                    "customerName": school_raw['description'],
                    "idUserTo": task_row['idUserTo'],
                    "userName": user_name,
                    "checkInDate": task_row['checkInDate'],
                    "lastUpdate": task_row['lastUpdate'],
                    "equipmentsId": task_row['equipmentsId'],
                    "equipmentNames": []
                }
                school_tasks.append(task)
                all_tasks.append(task)
            
            # Calcula progresso da escola (usa status numérico como o backend principal)
            completed_tasks = len([t for t in school_tasks if t['taskStatus'] in [5, 6]])
            total_tasks = len(school_tasks)
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            school = School(
                id=school_id,
                name=school_raw['description'],
                description=school_raw['description'],
                equipments=equipments,
                tasks=school_tasks,
                progress_percentage=progress_percentage
            )
            schools.append(school)
        
        # 6. Busca colaboradores
        user_ids = list(set([t['idUserTo'] for t in all_tasks if t['idUserTo']]))
        collaborators = []
        
        if user_ids:
            placeholders = ','.join(['?' for _ in user_ids])
            cursor.execute(f"SELECT userId, name, email FROM users WHERE userId IN ({placeholders})", user_ids)
            
            for user_row in cursor.fetchall():
                user_tasks = [t for t in all_tasks if t['idUserTo'] == user_row['userId']]
                completed = len([t for t in user_tasks if t['taskStatus'] in [5, 6]])
                pending = len([t for t in user_tasks if t['taskStatus'] == 0])
                in_progress = len([t for t in user_tasks if t['taskStatus'] == 1])
                
                collaborator = Collaborator(
                    id=user_row['userId'],
                    name=user_row['name'],
                    email=user_row.get('email'),
                    tasks_completed=completed,
                    tasks_pending=pending,
                    total_tasks=len(user_tasks)
                )
                collaborators.append(collaborator)
        
        # 7. Calcula KPIs (usa a mesma lógica do backend principal)
        total_equipments = sum(len(school.equipments) for school in schools)
        tasks_completed = len([t for t in all_tasks if t['taskStatus'] in [5, 6]])
        tasks_pending = len([t for t in all_tasks if t['taskStatus'] == 0])
        tasks_in_progress = len([t for t in all_tasks if t['taskStatus'] == 1])
        
        overall_progress = (tasks_completed / len(all_tasks) * 100) if all_tasks else 0
        
        # Calcula progresso por tipo de tarefa (baseado no tipo, não na orientação)
        mensal_task_types = [175644, 175648, 175652, 175656]  # IDs dos tipos mensais
        semestral_task_types = [175164, 175641, 175642]  # IDs dos tipos semestrais
        corretiva_task_types = [175646, 175649, 175650]  # IDs dos tipos corretivos
        pmoc_task_types = [177626, 184713, 184714, 184715, 184717]  # IDs dos tipos PMOC
        
        mensal_tasks = [t for t in all_tasks if t['taskType'] in mensal_task_types]
        mensal_completed = len([t for t in mensal_tasks if t['taskStatus'] in [5, 6]])
        mensal_progress = (mensal_completed / len(mensal_tasks) * 100) if mensal_tasks else 0
        
        semestral_tasks = [t for t in all_tasks if t['taskType'] in semestral_task_types]
        semestral_completed = len([t for t in semestral_tasks if t['taskStatus'] in [5, 6]])
        semestral_progress = (semestral_completed / len(semestral_tasks) * 100) if semestral_tasks else 0
        
        corretiva_tasks = [t for t in all_tasks if t['taskType'] in corretiva_task_types]
        corretiva_count = len([t for t in corretiva_tasks if t['taskStatus'] in [5, 6]])
        
        pmoc_tasks = [t for t in all_tasks if t['taskType'] in pmoc_task_types]
        pmoc_completed = len([t for t in pmoc_tasks if t['taskStatus'] in [5, 6]])
        pmoc_progress = (pmoc_completed / len(pmoc_tasks) * 100) if pmoc_tasks else 0
        
        kpis = KpiData(
            total_schools=len(schools),
            total_collaborators=len(collaborators),
            total_equipments=total_equipments,
            tasks_completed=tasks_completed,
            tasks_pending=tasks_pending,
            tasks_in_progress=tasks_in_progress,
            overall_progress=overall_progress,
            mensal_progress=mensal_progress,
            semestral_progress=semestral_progress,
            corretiva_count=corretiva_count,
            pmoc_progress=pmoc_progress
        )
        
        # 8. Converte tasks para o formato correto
        formatted_tasks = []
        for task in all_tasks[:50]:  # Limita a 50 tarefas mais recentes
            formatted_task = Task(
                id=task['id'],
                orientation=task['orientation'],
                status=task['status'],
                taskType=task['taskType'],
                taskTypeName=task['taskTypeName'],
                customerId=task['customerId'],
                customerName=task['customerName'],
                idUserTo=task['idUserTo'],
                userName=task['userName'],
                checkInDate=task['checkInDate'],
                lastUpdate=task['lastUpdate'],
                equipmentsId=task['equipmentsId'],
                equipmentNames=task['equipmentNames']
            )
            formatted_tasks.append(formatted_task)
        
        dashboard_data = DashboardData(
            contract_id=contract_id,
            contract_name=contract['description'],
            schools=schools,
            collaborators=collaborators,
            kpis=kpis,
            tasks=formatted_tasks
        )
        
        return dashboard_data
        
    finally:
        conn.close()

@app.get("/api/contracts")
async def get_contracts():
    """
    Retorna lista de contratos
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT id, description, 1 as active FROM customer_groups ORDER BY description
        """)
        
        contracts = [
            Contract(
                id=row['id'],
                description=row['description'],
                active=bool(row['active'])
            )
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return contracts
        
    except Exception as e:
        print(f"Erro ao buscar contratos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao carregar contratos")

@app.get("/api/tasks/pending")
async def get_pending_tasks(contract_ids: str):
    """
    Retorna tarefas pendentes para os contratos especificados
    """
    try:
        contract_id_list = [int(id.strip()) for id in contract_ids.split(',')]
        
        conn = get_db_connection()
        
        # Busca escolas dos contratos
        placeholders = ','.join(['?' for _ in contract_id_list])
        cursor = conn.execute(f"""
            SELECT id FROM customers 
            WHERE groupsId IN ({placeholders}) OR groupsId LIKE '%' || ? || '%'
        """, contract_id_list + [str(contract_id_list[0])])
        
        school_ids = [row['id'] for row in cursor.fetchall()]
        
        if not school_ids:
            return []
        
        # Busca tarefas pendentes
        school_placeholders = ','.join(['?' for _ in school_ids])
        cursor = conn.execute(f"""
            SELECT t.id, t.orientation, t.status, t.taskType, t.customerId, 
                   t.idUserTo, t.checkInDate, t.lastUpdate, t.equipmentsId,
                   tt.description as taskTypeName,
                   c.description as customerName,
                   u.name as userName
            FROM tasks t
            LEFT JOIN task_types tt ON t.taskType = tt.id
            LEFT JOIN customers c ON t.customerId = c.id
            LEFT JOIN users u ON t.idUserTo = u.userId
            WHERE t.customerId IN ({school_placeholders})
            AND (t.status IS NULL OR t.status = '' OR LOWER(t.status) IN ('pendente', 'pending'))
            ORDER BY t.lastUpdate DESC, t.checkInDate DESC
            LIMIT 100
        """, school_ids)
        
        tasks = []
        for row in cursor.fetchall():
            task = Task(
                id=row['id'],
                orientation=row['orientation'] or "Tarefa sem descrição",
                status=row['status'] or "Pendente",
                taskType=row['taskType'],
                taskTypeName=row['taskTypeName'],
                customerId=row['customerId'],
                customerName=row['customerName'],
                idUserTo=row['idUserTo'],
                userName=row['userName'],
                checkInDate=row['checkInDate'],
                lastUpdate=row['lastUpdate'],
                equipmentsId=row['equipmentsId'],
                equipmentNames=[]
            )
            tasks.append(task)
        
        conn.close()
        return tasks
        
    except Exception as e:
        print(f"Erro ao buscar tarefas pendentes: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao carregar tarefas pendentes")

@app.get("/api/tasks/due")
async def get_due_tasks(contract_ids: str, days_ahead: int = 7):
    """
    Retorna tarefas próximas do prazo
    """
    try:
        contract_id_list = [int(id.strip()) for id in contract_ids.split(',')]
        
        # Calcula data limite
        due_date = datetime.now() + timedelta(days=days_ahead)
        due_date_str = due_date.strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Busca escolas dos contratos
        placeholders = ','.join(['?' for _ in contract_id_list])
        cursor = conn.execute(f"""
            SELECT id FROM customers 
            WHERE groupsId IN ({placeholders}) OR groupsId LIKE '%' || ? || '%'
        """, contract_id_list + [str(contract_id_list[0])])
        
        school_ids = [row['id'] for row in cursor.fetchall()]
        
        if not school_ids:
            return []
        
        # Busca tarefas próximas do prazo
        school_placeholders = ','.join(['?' for _ in school_ids])
        cursor = conn.execute(f"""
            SELECT t.id, t.orientation, t.status, t.taskType, t.customerId, 
                   t.idUserTo, t.checkInDate, t.lastUpdate, t.equipmentsId,
                   tt.description as taskTypeName,
                   c.description as customerName,
                   u.name as userName
            FROM tasks t
            LEFT JOIN task_types tt ON t.taskType = tt.id
            LEFT JOIN customers c ON t.customerId = c.id
            LEFT JOIN users u ON t.idUserTo = u.userId
            WHERE t.customerId IN ({school_placeholders})
            AND (t.checkInDate <= ? OR t.lastUpdate <= ?)
            AND (t.status IS NULL OR t.status = '' OR LOWER(t.status) NOT IN ('concluída', 'concluida', 'completed'))
            ORDER BY t.checkInDate ASC, t.lastUpdate ASC
            LIMIT 50
        """, school_ids + [due_date_str, due_date_str])
        
        tasks = []
        for row in cursor.fetchall():
            task = Task(
                id=row['id'],
                orientation=row['orientation'] or "Tarefa sem descrição",
                status=row['status'] or "Pendente",
                taskType=row['taskType'],
                taskTypeName=row['taskTypeName'],
                customerId=row['customerId'],
                customerName=row['customerName'],
                idUserTo=row['idUserTo'],
                userName=row['userName'],
                checkInDate=row['checkInDate'],
                lastUpdate=row['lastUpdate'],
                equipmentsId=row['equipmentsId'],
                equipmentNames=[]
            )
            tasks.append(task)
        
        conn.close()
        return tasks
        
    except Exception as e:
        print(f"Erro ao buscar tarefas próximas do prazo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao carregar tarefas próximas do prazo")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)