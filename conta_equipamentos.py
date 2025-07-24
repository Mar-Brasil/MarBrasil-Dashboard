import sqlite3
from collections import Counter

# CONFIGURAÇÕES
DB_PATH = 'auvo.db'  # Altere se o banco estiver em outro local
CONTRACT_ID = input('Digite o ID do contrato desejado (ex: 146168): ').strip()

# --- Conexão ---
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# --- 1. Equipamentos cadastrados para as escolas do contrato ---
# Busca todas as escolas (customers) do contrato
# Busca todas as escolas (customers) onde groupsId contém o contrato
cur.execute("SELECT id, groupsId FROM customers")
school_ids = []
for row in cur.fetchall():
    raw = row['groupsId']
    # Pode ser lista (ex: '[112846, 156750]') ou string
    if raw:
        # Remove colchetes e espaços, separa por vírgula
        ids = [x.strip() for x in str(raw).replace('[','').replace(']','').split(',') if x.strip().isdigit()]
        if CONTRACT_ID in ids:
            school_ids.append(row['id'])

if not school_ids:
    print(f'Nenhuma escola encontrada para o contrato {CONTRACT_ID}.')
    exit(1)

school_ids_str = ','.join(str(x) for x in school_ids)

# Busca todos os equipamentos associados a essas escolas
cur.execute(f'SELECT id FROM equipments WHERE associated_customer_id IN ({school_ids_str})')
equip_ids_cadastrados = set(row['id'] for row in cur.fetchall())

print(f"\n[1] Total de equipamentos cadastrados para o contrato {CONTRACT_ID}: {len(equip_ids_cadastrados)}")

# --- 2. Equipamentos nas tarefas do contrato ---
# Busca todas as tarefas do contrato
cur.execute(f'SELECT equipmentsId FROM tasks WHERE customerId IN ({school_ids_str})')
equip_ids_em_tarefas = []
for row in cur.fetchall():
    raw = row['equipmentsId']
    if raw:
        # Pode ser string separada por vírgula, espaço, ou lista JSON
        ids = []
        if raw.startswith('[') and raw.endswith(']'):
            try:
                import json
                ids = json.loads(raw)
            except Exception:
                pass
        else:
            ids = [x.strip() for x in raw.replace(';',',').replace(' ', ',').split(',') if x.strip().isdigit()]
        equip_ids_em_tarefas.extend(ids)

# Contagem por diferentes métodos
contagem_total_associacoes = len(equip_ids_em_tarefas)
contagem_distintos_tarefas = len(set(equip_ids_em_tarefas))

print(f"[2] Total de associações equipamento-tarefa: {contagem_total_associacoes}")
print(f"[3] Total de equipamentos únicos presentes nas tarefas: {contagem_distintos_tarefas}")

# --- Equipamentos ativos únicos nas tarefas ---
# Buscar status 'active' dos equipamentos
if equip_ids_em_tarefas:
    # Buscar todos os equipamentos ativos
    cur.execute(f"SELECT id FROM equipments WHERE active = 1 AND id IN ({','.join(['?']*len(set(equip_ids_em_tarefas)))})", list(set(equip_ids_em_tarefas)))
    ativos_nas_tarefas = set(row['id'] for row in cur.fetchall())
    print(f"[4] Total de equipamentos ATIVOS únicos presentes nas tarefas: {len(ativos_nas_tarefas)}")
else:
    print("[4] Nenhum equipamento ativo encontrado nas tarefas.")

# Equipamentos que aparecem nas tarefas mas não estão cadastrados
extras = set(equip_ids_em_tarefas) - equip_ids_cadastrados
if extras:
    # Buscar status ativo/inativo dos extras
    cur.execute(f"SELECT id, active FROM equipments WHERE id IN ({','.join(['?']*len(extras))})", list(extras))
    ativos = set()
    inativos = set()
    for row in cur.fetchall():
        if row['active'] == 1:
            ativos.add(row['id'])
        else:
            inativos.add(row['id'])
    print(f"[!] Equipamentos presentes nas tarefas mas não cadastrados para o contrato: {extras}")
    print(f"[5] Total de equipamentos presentes nas tarefas mas não cadastrados: {len(extras)}")
    print(f"[5.1] Quantidade de ATIVOS: {len(ativos)}")
    print(f"IDs ativos: {sorted(ativos)}")
    print(f"[5.2] Quantidade de INATIVOS: {len(inativos)}")
    print(f"IDs inativos: {sorted(inativos)}")

# Equipamentos cadastrados mas nunca aparecem em tarefas
nao_usados = equip_ids_cadastrados - set(equip_ids_em_tarefas)
if nao_usados:
    print(f"[!] Equipamentos cadastrados para o contrato mas nunca aparecem em tarefas: {nao_usados}")

conn.close()
