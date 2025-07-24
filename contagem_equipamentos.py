import sqlite3
import json

def main():
    db_path = 'auvo.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    contrato_id = input('Digite o ID do contrato (customer_groups.id): ').strip()
    print(f'\nBuscando escolas associadas ao contrato {contrato_id}...')

    # 1. Buscar escolas (customers) associadas ao contrato
    cursor.execute("SELECT id, description, groupsId FROM customers")
    escolas = []
    for row in cursor.fetchall():
        escola_id, escola_nome, groupsId = row
        try:
            grupos = json.loads(groupsId)
        except:
            continue
        if int(contrato_id) in grupos:
            escolas.append({'id': escola_id, 'nome': escola_nome})
    print(f'Total de escolas encontradas: {len(escolas)}')

    total_equip_assoc = 0
    total_equip_task = 0
    equipamentos_associados_set = set()
    equipamentos_task_set = set()

    for escola in escolas:
        escola_id = escola['id']
        escola_nome = escola['nome']
        # 2. Contagem pela association (equipments.associatedCustomerId)
        cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=? AND active=1", (escola_id,))
        qtd_assoc = cursor.fetchone()[0]
        total_equip_assoc += qtd_assoc

        # 3. Contagem via tasks->equipmentsId
        cursor.execute("SELECT equipmentsId FROM tasks WHERE customerId=?", (escola_id,))
        equip_ids = set()
        for (equipmentsId_str,) in cursor.fetchall():
            try:
                ids = json.loads(equipmentsId_str)
                if isinstance(ids, list):
                    equip_ids.update(ids)
            except:
                continue
        # Filtra só equipamentos ativos
        ativos = set()
        for eid in equip_ids:
            cursor.execute("SELECT active FROM equipments WHERE id=?", (eid,))
            row = cursor.fetchone()
            if row and row[0] == 1:
                ativos.add(eid)
        equipamentos_task_set.update(ativos)
        equipamentos_associados_set.update([escola_id]*qtd_assoc)  # só para mostrar total
        print(f'Escola: {escola_nome} (id={escola_id}) | Equip. associados: {qtd_assoc} | Equip. nas tasks (ativos): {len(ativos)}')

    print('\nResumo final:')
    print(f'Total de escolas: {len(escolas)}')
    print(f'Total de equipamentos ativos por associatedCustomerId: {total_equip_assoc}')
    print(f'Total de equipamentos ativos encontrados nas tasks: {len(equipamentos_task_set)}')

if __name__ == '__main__':
    main()
