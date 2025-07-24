import os
import sys
import sqlite3
from datetime import datetime
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def obter_datas_distintas_do_mes_atual():
    conn = sqlite3.connect(DB_TAREFAS)
    cursor = conn.cursor()
    # Considera datas no formato 'YYYY-MM-DD'. Ajuste se necessário.
    mes_atual = datetime.now().strftime('%Y-%m')
    cursor.execute("SELECT DISTINCT data_referencia FROM tarefas_raw WHERE data_referencia LIKE ?", (f'{mes_atual}%',))
    datas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return datas


def obter_task_ids_banco():
    conn = sqlite3.connect(DB_TAREFAS)
    cursor = conn.cursor()
    cursor.execute("SELECT taskID FROM tarefas_raw")
    task_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return task_ids


def buscar_tarefas_atuais_api_mes_atual():
    tarefas_atuais = set()
    datas = obter_datas_distintas_do_mes_atual()

    for user_id, nome in USUARIOS.items():
        print(f"\n🔄 Buscando tarefas atuais do usuário: {nome} (ID {user_id}) (mês atual)")
        for data in datas:
            tarefas = get_user_tasks(user_id, data, data)
            if isinstance(tarefas, list):
                for tarefa in tarefas:
                    task_id = tarefa.get("taskID")
                    if task_id:
                        tarefas_atuais.add(str(task_id))
                print(f"✔️ {len(tarefas)} tarefa(s) encontradas em {data}")
            else:
                print(f"⚠️ Erro ao buscar tarefas de {nome} em {data}: {tarefas}")

    return tarefas_atuais


def limpar_tarefas_inexistentes_mes_atual(task_ids_atuais):
    conn = sqlite3.connect(DB_TAREFAS)
    cursor = conn.cursor()
    mes_atual = datetime.now().strftime('%Y-%m')
    # Seleciona apenas tarefas do mês atual
    cursor.execute("SELECT taskID FROM tarefas_raw WHERE data_referencia LIKE ?", (f'{mes_atual}%',))
    tarefas_banco = {str(row[0]) for row in cursor.fetchall()}

    tarefas_para_remover = tarefas_banco - task_ids_atuais

    removidas = 0
    for task_id in tarefas_para_remover:
        cursor.execute("DELETE FROM tarefas_raw WHERE taskID = ? AND data_referencia LIKE ?", (task_id, f'{mes_atual}%'))
        removidas += cursor.rowcount

    conn.commit()
    conn.close()

    print(f"\n✅ Limpeza concluída (mês atual). Total de tarefas removidas: {removidas}")


if __name__ == "__main__":
    print("\n🔍 Iniciando comparação com API (apenas mês atual)...")
    task_ids_atuais = buscar_tarefas_atuais_api_mes_atual()
    print(f"\n🔢 Total de tarefas reconhecidas na API para o mês atual: {len(task_ids_atuais)}")
    limpar_tarefas_inexistentes_mes_atual(task_ids_atuais)
    print("\n✅ Banco atualizado com apenas tarefas existentes na Auvo para o mês atual.")
