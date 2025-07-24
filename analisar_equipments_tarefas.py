import sqlite3
import json
from collections import Counter

def analisar_equipamentos_tarefas():
    """
    Analisa os equipamentos nas tarefas do banco de dados.
    - Conta equipamentos por tarefa
    - Identifica equipamentos repetidos
    - Totaliza equipamentos únicos e repetidos
    """
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    print("\n=== ANÁLISE DE EQUIPAMENTOS NAS TAREFAS ===\n")
    
    # Verificar quantas tarefas existem no total
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tarefas = cursor.fetchone()[0]
    print(f"Total de tarefas no banco: {total_tarefas}")
    
    # Verificar quantas tarefas têm equipamentos associados
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE equipmentsId IS NOT NULL AND equipmentsId != '[]' AND equipmentsId != ''")
    tarefas_com_equip = cursor.fetchone()[0]
    print(f"Tarefas com equipamentos: {tarefas_com_equip}")
    
    # Buscar todas as tarefas com equipamentos
    cursor.execute("SELECT taskID, equipmentsId, customerId FROM tasks WHERE equipmentsId IS NOT NULL AND equipmentsId != '[]' AND equipmentsId != ''")
    tarefas = cursor.fetchall()
    
    # Contadores
    todos_equipamentos = []       # Lista com todos os IDs (com repetições)
    equip_por_cliente = {}        # Equipamentos por cliente
    tarefas_por_equipamento = {}  # Quantas tarefas cada equipamento aparece
    
    # Processar cada tarefa
    print("\nProcessando tarefas com equipamentos...")
    for tarefa_id, equipments_str, cliente_id in tarefas:
        try:
            # Converter a string JSON para lista
            equipments = json.loads(equipments_str)
            
            # Verificar se é uma lista válida
            if isinstance(equipments, list) and equipments:
                # Adicionar à lista total
                todos_equipamentos.extend(equipments)
                
                # Adicionar à contagem por cliente
                if cliente_id not in equip_por_cliente:
                    equip_por_cliente[cliente_id] = set()
                equip_por_cliente[cliente_id].update(equipments)
                
                # Contar em quantas tarefas cada equipamento aparece
                for equip_id in equipments:
                    if equip_id not in tarefas_por_equipamento:
                        tarefas_por_equipamento[equip_id] = 0
                    tarefas_por_equipamento[equip_id] += 1
                    
        except Exception as e:
            print(f"Erro ao processar tarefa {tarefa_id}: {e}")
    
    # Análise de resultados
    total_ocorrencias = len(todos_equipamentos)
    equipamentos_unicos = set(todos_equipamentos)
    total_unicos = len(equipamentos_unicos)
    
    print("\n=== RESULTADOS DA ANÁLISE ===\n")
    print(f"Total de ocorrências de equipamentos nas tarefas: {total_ocorrencias}")
    print(f"Total de equipamentos únicos nas tarefas: {total_unicos}")
    print(f"Equipamentos aparecem em média {total_ocorrencias/total_unicos:.2f} vezes")
    
    # Equipamentos mais repetidos
    counter = Counter(todos_equipamentos)
    mais_repetidos = counter.most_common(10)
    
    print("\n=== EQUIPAMENTOS MAIS UTILIZADOS ===\n")
    print(f"{'ID':<10} {'Ocorrências':<12} {'Nome do Equipamento':<40} {'Status'}")
    print("-" * 80)
    
    for equip_id, count in mais_repetidos:
        # Buscar informações do equipamento
        cursor.execute("SELECT name, active FROM equipments WHERE id = ?", (equip_id,))
        result = cursor.fetchone()
        nome = result[0] if result else "Equipamento não encontrado"
        status = "ATIVO" if result and result[1] == 1 else "INATIVO"
        
        print(f"{equip_id:<10} {count:<12} {nome[:38]:<40} {status}")
    
    # Clientes com mais equipamentos
    print("\n=== TOP 10 CLIENTES COM MAIS EQUIPAMENTOS EM TAREFAS ===\n")
    print(f"{'Cliente ID':<12} {'Equipamentos':<15} {'Nome do Cliente'}")
    print("-" * 80)
    
    # Ordenar clientes pelo número de equipamentos
    top_clientes = sorted(equip_por_cliente.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    
    for cliente_id, equipamentos in top_clientes:
        # Buscar nome do cliente
        cursor.execute("SELECT description FROM customers WHERE id = ?", (cliente_id,))
        result = cursor.fetchone()
        nome_cliente = result[0] if result else "Cliente não encontrado"
        
        print(f"{cliente_id:<12} {len(equipamentos):<15} {nome_cliente}")
    
    # Mostrar detalhes para um cliente específico
    if len(top_clientes) > 0:
        cliente_destacado_id = top_clientes[0][0]  # ID do primeiro cliente da lista
        cursor.execute("SELECT description FROM customers WHERE id = ?", (cliente_destacado_id,))
        result = cursor.fetchone()
        nome_cliente_destacado = result[0] if result else "Cliente não encontrado"
        
        print(f"\n=== DETALHES DO CLIENTE {nome_cliente_destacado} (ID={cliente_destacado_id}) ===\n")
        
        # Contagem de equipamentos específicos
        cursor.execute("""
            SELECT COUNT(*) FROM equipments 
            WHERE associatedCustomerId = ?
        """, (cliente_destacado_id,))
        total_equip_assoc = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM equipments 
            WHERE associatedCustomerId = ? AND active = 1
        """, (cliente_destacado_id,))
        equip_ativos = cursor.fetchone()[0]
        
        equip_nas_tasks = len(equip_por_cliente.get(cliente_destacado_id, set()))
        
        print(f"Equipamentos associados ao cliente: {total_equip_assoc}")
        print(f"Equipamentos ativos associados: {equip_ativos}")
        print(f"Equipamentos em tarefas: {equip_nas_tasks}")
        
        # Verificar se existem equipamentos em tarefas que não estão associados ao cliente
        if cliente_destacado_id in equip_por_cliente:
            equip_cliente_tarefas = equip_por_cliente[cliente_destacado_id]
            equip_realmente_associados = set()
            
            for equip_id in equip_cliente_tarefas:
                cursor.execute("SELECT id FROM equipments WHERE id = ? AND associatedCustomerId = ?", 
                              (equip_id, cliente_destacado_id))
                if cursor.fetchone():
                    equip_realmente_associados.add(equip_id)
            
            equip_nao_associados = equip_cliente_tarefas - equip_realmente_associados
            
            print(f"Equipamentos em tarefas realmente associados ao cliente: {len(equip_realmente_associados)}")
            print(f"Equipamentos em tarefas NÃO associados ao cliente: {len(equip_nao_associados)}")
            
            if len(equip_nao_associados) > 0:
                print("\nALERTA: Foram encontrados equipamentos em tarefas que não estão associados a este cliente!")
    
    conn.close()

if __name__ == "__main__":
    analisar_equipamentos_tarefas()
