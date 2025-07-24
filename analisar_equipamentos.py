import sqlite3
import json
from datetime import datetime

def analisar_equipamentos_cliente(cliente_id):
    """Analisa detalhadamente os equipamentos associados a um cliente específico"""
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    print(f"\n=== ANÁLISE DE EQUIPAMENTOS DO CLIENTE ID {cliente_id} ===")
    
    # Contagem total
    cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=?", (cliente_id,))
    total = cursor.fetchone()[0]
    
    # Contagem de ativos
    cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=? AND active=1", (cliente_id,))
    ativos = cursor.fetchone()[0]
    
    # Contagem de inativos
    cursor.execute("SELECT COUNT(*) FROM equipments WHERE associatedCustomerId=? AND active=0", (cliente_id,))
    inativos = cursor.fetchone()[0]
    
    # Nome do cliente
    cursor.execute("SELECT description FROM customers WHERE id=?", (cliente_id,))
    result = cursor.fetchone()
    nome_cliente = result[0] if result else "Cliente não encontrado"
    
    print(f"Cliente: {nome_cliente}")
    print(f"Total de equipamentos: {total}")
    print(f"Equipamentos ativos: {ativos}")
    print(f"Equipamentos inativos: {inativos}")
    
    # Lista detalhada
    print("\n=== LISTA DETALHADA DE EQUIPAMENTOS ===")
    print(f"{'ID':<10} {'Nome':<40} {'Status':<10} {'Data Criação':<25}")
    print("-" * 85)
    
    cursor.execute("""
        SELECT id, name, active, creationDate 
        FROM equipments 
        WHERE associatedCustomerId=? 
        ORDER BY active DESC, name
    """, (cliente_id,))
    
    for row in cursor.fetchall():
        id_equip, nome, ativo, data_criacao = row
        status = "ATIVO" if ativo == 1 else "INATIVO"
        data_formatada = data_criacao if data_criacao else "N/A"
        print(f"{id_equip:<10} {nome[:38]:<40} {status:<10} {data_formatada:<25}")
    
    # Verificar nas tasks
    print("\n=== EQUIPAMENTOS NAS TASKS ===")
    cursor.execute("""
        SELECT equipmentsId FROM tasks 
        WHERE customerId=?
    """, (cliente_id,))
    
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
    
    print(f"Total de equipamentos únicos encontrados nas tasks: {len(equip_ids_tasks)}")
    
    # Verificar quantos equipamentos nas tasks são ativos
    ativos_tasks = []
    for equip_id in equip_ids_tasks:
        cursor.execute("SELECT id, name, active FROM equipments WHERE id=?", (equip_id,))
        result = cursor.fetchone()
        if result and result[2] == 1:  # active=1
            ativos_tasks.append(result)
    
    print(f"Equipamentos ativos encontrados nas tasks: {len(ativos_tasks)}")
    
    print("\n=== CONCLUSÃO ===")
    print(f"O cliente {nome_cliente} (ID={cliente_id}) possui:")
    print(f"- {total} equipamentos no banco de dados")
    print(f"- {ativos} equipamentos ativos")
    print(f"- {inativos} equipamentos inativos")
    print(f"- {len(equip_ids_tasks)} equipamentos mencionados em tarefas")
    print(f"- {len(ativos_tasks)} equipamentos ativos mencionados em tarefas")
    
    conn.close()

if __name__ == "__main__":
    cliente_id = 11828027  # ID da escola STS36693/22
    analisar_equipamentos_cliente(cliente_id)
