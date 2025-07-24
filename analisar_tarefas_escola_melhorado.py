import sqlite3
import json

def detalhar_tarefas_equipamentos(cliente_id):
    """
    Lista todas as tarefas de uma escola com seus equipamentos associados.
    Similar à visualização da tela que o usuário compartilhou.
    """
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Obter nome da escola
    cursor.execute("SELECT description FROM customers WHERE id=?", (cliente_id,))
    result = cursor.fetchone()
    nome_escola = result[0] if result else "Escola não encontrada"
    
    print(f"\n=== DETALHAMENTO DE TAREFAS: {nome_escola} (ID={cliente_id}) ===\n")
    
    # Cabeçalho da tabela
    print(f"{'#':<4} | {'taskID':<10} | {'customerDescription':<40} | {'equipmentsId'}")
    print("-" * 100)
    
    # Buscar todas as tarefas da escola
    cursor.execute("""
        SELECT taskID, equipmentsId 
        FROM tasks 
        WHERE customerId = ? 
        ORDER BY taskID
    """, (cliente_id,))
    
    tarefas = cursor.fetchall()
    equip_unicos = set()
    total_equip_ocorrencias = 0
    tarefas_sem_equip = 0
    
    # Imprimir cada tarefa
    for i, (tarefa_id, equipments_str) in enumerate(tarefas, 1):
        # Extrair IDs dos equipamentos
        equip_ids = []
        if equipments_str:
            try:
                equip_ids = json.loads(equipments_str)
                if isinstance(equip_ids, list):
                    equip_unicos.update(equip_ids)
                    total_equip_ocorrencias += len(equip_ids)
                else:
                    equip_ids = []
            except:
                equip_ids = []
        else:
            tarefas_sem_equip += 1
        
        # Formatar como string para exibição
        equip_str = str(equip_ids) if equip_ids else "[]"
        
        # Limitar o tamanho da string para exibição
        if len(equip_str) > 50:
            equip_str = equip_str[:47] + "..."
        
        # Imprimir linha da tabela
        print(f"{i:<4} | {tarefa_id:<10} | {nome_escola[:38]:<40} | {equip_str}")
    
    tarefas_com_equip = len(tarefas) - tarefas_sem_equip
    
    # Análise adicional
    print("\nEstatísticas:")
    print(f"Total de tarefas: {len(tarefas)}")
    print(f"Total de ocorrências de equipamentos: {total_equip_ocorrencias}")
    print(f"Equipamentos únicos: {len(equip_unicos)}")
    print(f"Média de equipamentos por tarefa: {total_equip_ocorrencias/len(tarefas):.1f}")
    print(f"Tarefas com equipamentos: {tarefas_com_equip}")
    print(f"Tarefas sem equipamentos: {tarefas_sem_equip}")
    
    # Lista detalhada dos equipamentos únicos
    cursor.execute("""
        SELECT id, name, active FROM equipments
        WHERE id IN ({})
    """.format(",".join(str(id) for id in equip_unicos)))
    
    equipamentos = cursor.fetchall()
    
    print("\nEquipamentos Únicos Encontrados:")
    print(f"{'ID':<10} | {'Status':<8} | {'Nome':<50}")
    print("-" * 72)
    
    for equip_id, nome, ativo in equipamentos:
        status = "ATIVO" if ativo else "INATIVO"
        print(f"{equip_id:<10} | {status:<8} | {nome[:50]}")
    
    conn.close()

if __name__ == "__main__":
    cliente_id = 11828027  # ID da escola STS36693/22 - SEDUC UME PADRE LEONARDO NUNES
    detalhar_tarefas_equipamentos(cliente_id)
