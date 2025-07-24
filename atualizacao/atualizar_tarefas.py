import os
import sys
import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path
from calendar import monthrange

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api_auvo import get_user_tasks
from app.env_reader import USUARIOS

# Detectar o sistema operacional
is_windows = os.name == 'nt'

# Definir caminhos dos bancos de dados baseado no sistema operacional
if is_windows:
    # Caminhos locais para Windows
    DB_TAREFAS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "tarefas.sqlite3"))
    DB_USUARIOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "usuarios.sqlite3"))
    DB_EQUIPAMENTOS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "db.sqlite3"))
    DB_CLIENTES = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "clientes_por_grupo.sqlite3"))
    
    # Garante que a pasta data existe
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
else:
    # Caminhos do servidor Linux
    DB_TAREFAS = "/root/auvo-git/data/tarefas.sqlite3"
    DB_USUARIOS = "/root/auvo-git/data/usuarios.sqlite3"
    DB_EQUIPAMENTOS = "/root/auvo-git/data/db.sqlite3"
    DB_CLIENTES = "/root/auvo-git/data/clientes_por_grupo.sqlite3"
    
    # Garante que a pasta data existe
    os.makedirs("/root/auvo-git/data", exist_ok=True)

def criar_tabela_tarefas():
    conn = sqlite3.connect(DB_TAREFAS)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefas_raw (
            taskID TEXT,
            user_id INTEGER,
            data_referencia TEXT,
            json TEXT,
            PRIMARY KEY (taskID, user_id)
        )
    """)
    conn.commit()
    conn.close()

def salvar_tarefa(task, user_id, data_ref):
    conn = sqlite3.connect(DB_TAREFAS)
    cursor = conn.cursor()
    task_id = task.get("taskID")
    if task_id:
        cursor.execute("""
            INSERT OR REPLACE INTO tarefas_raw (taskID, user_id, data_referencia, json)
            VALUES (?, ?, ?, ?)
        """, (task_id, user_id, data_ref, json.dumps(task)))
    conn.commit()
    conn.close()

def baixar_tarefas_mes_atual():
    criar_tabela_tarefas()

    hoje = datetime.now()
    data_inicio = hoje.replace(day=1)
    data_fim = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])

    datas = [data_inicio + timedelta(days=i) for i in range((data_fim - data_inicio).days + 1)]

    for user_id, nome in USUARIOS.items():
        print(f"\n🔍 Buscando tarefas de {nome} (ID {user_id})")
        for data in datas:
            data_str = data.strftime("%Y-%m-%d")
            tarefas = get_user_tasks(user_id, data_str, data_str)
            if isinstance(tarefas, list):
                for tarefa in tarefas:
                    salvar_tarefa(tarefa, user_id, data_str)
                print(f"✔️ {len(tarefas)} tarefa(s) salvas em {data_str} para {nome}")
            else:
                print(f"⚠️ Erro ao buscar tarefas de {nome} em {data_str}: {tarefas}")

if __name__ == "__main__":
    baixar_tarefas_mes_atual()
    print("\n✅ Atualização concluída: banco tarefas.sqlite3 atualizado com sucesso.")
