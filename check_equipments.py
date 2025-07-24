import sqlite3
import json

def analisar_escola(cliente_id):
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Obter nome da escola
    cursor.execute("SELECT description FROM customers WHERE id=?", (cliente_id,))
    result = cursor.fetchone()
    nome_cliente = result[0] if result else "Cliente não encontrado"
    
    print(f"\n=== Análise da Escola: {nome_cliente} (ID={cliente_id}) ===")
    
    # Total de equipamentos
    cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=?", (cliente_id,))
    total = cursor.fetchone()[0]
    
    # Equipamentos ativos
    cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=? AND active=1", (cliente_id,))
    ativos = cursor.fetchone()[0]
    
    # Equipamentos nas tasks
    cursor.execute("SELECT equipmentsId FROM tasks WHERE customerId=?", (cliente_id,))
    equip_ids_tasks = set()
    for row in cursor.fetchall():
        equipments_id_str = row[0]
        if equipments_id_str:
            try:
                equip_ids = json.loads(equipments_id_str)
                if isinstance(equip_ids, list):
                    equip_ids_tasks.update(equip_ids)
            except:
                pass
    
    # Verificar quantos equipamentos nas tasks são ativos
    ativos_tasks = []
    for equip_id in equip_ids_tasks:
        cursor.execute("SELECT id FROM equipments WHERE id=? AND active=1", (equip_id,))
        result = cursor.fetchone()
        if result:
            ativos_tasks.append(result[0])
    
    print(f"Total de equipamentos associados: {total}")
    print(f"Equipamentos ativos: {ativos}")
    print(f"Equipamentos mencionados em tarefas: {len(equip_ids_tasks)}")
    print(f"Equipamentos ativos mencionados em tarefas: {len(ativos_tasks)}")
    
    conn.close()

if __name__ == "__main__":
    cliente_id = 11828027  # ID da escola STS36693/22
    analisar_escola(cliente_id)
