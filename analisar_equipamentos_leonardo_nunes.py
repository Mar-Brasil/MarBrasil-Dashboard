import sqlite3
import json
from collections import Counter

def analisar_equipamentos_escola(cliente_id):
    """
    Analisa detalhadamente os equipamentos associados a uma escola específica nas tarefas
    """
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Obter dados da escola
    cursor.execute("SELECT description FROM customers WHERE id=?", (cliente_id,))
    result = cursor.fetchone()
    nome_escola = result[0] if result else "Escola não encontrada"
    
    print(f"\n=== ANÁLISE DETALHADA: {nome_escola} (ID={cliente_id}) ===\n")
    
    # 1. Equipamentos cadastrados para a escola
    cursor.execute("""
        SELECT id, name, active FROM equipments 
        WHERE associatedCustomerId=? 
        ORDER BY active DESC, name
    """, (cliente_id,))
    equipamentos = cursor.fetchall()
    
    equip_ativos = [e for e in equipamentos if e[2] == 1]
    equip_inativos = [e for e in equipamentos if e[2] == 0]
    
    print(f"1. EQUIPAMENTOS CADASTRADOS")
    print(f"   Total: {len(equipamentos)}")
    print(f"   Ativos: {len(equip_ativos)}")
    print(f"   Inativos: {len(equip_inativos)}")
    
    # 2. Equipamentos nas tarefas
    cursor.execute("SELECT taskID, equipmentsId FROM tasks WHERE customerId=?", (cliente_id,))
    tarefas = cursor.fetchall()
    
    equipamentos_tarefas = []
    equip_por_tarefa = {}
    
    for tarefa_id, equipments_str in tarefas:
        try:
            if equipments_str:
                equips = json.loads(equipments_str)
                if isinstance(equips, list):
                    equipamentos_tarefas.extend(equips)
                    equip_por_tarefa[tarefa_id] = equips
        except:
            pass
    
    total_tarefas = len(tarefas)
    tarefas_com_equip = len(equip_por_tarefa)
    
    # Contagem de equipamentos únicos e repetidos nas tarefas
    equip_unicos = set(equipamentos_tarefas)
    counter = Counter(equipamentos_tarefas)
    
    print(f"\n2. TAREFAS DA ESCOLA")
    print(f"   Total de tarefas: {total_tarefas}")
    print(f"   Tarefas com equipamentos: {tarefas_com_equip}")
    print(f"   Total de ocorrências de equipamentos: {len(equipamentos_tarefas)}")
    print(f"   Equipamentos únicos nas tarefas: {len(equip_unicos)}")
    
    # 3. Verificar repetições
    print("\n3. ANÁLISE DE REPETIÇÕES")
    
    # Equipamentos que aparecem em múltiplas tarefas
    repetidos = {equip: count for equip, count in counter.items() if count > 1}
    print(f"   Equipamentos que aparecem em mais de uma tarefa: {len(repetidos)}")
    
    # Top equipamentos mais repetidos
    mais_repetidos = counter.most_common(10)
    
    print("\n   TOP 10 EQUIPAMENTOS MAIS UTILIZADOS NAS TAREFAS:")
    print(f"   {'ID':<10} {'Ocorrências':<12} {'Nome':<40} {'Status'}")
    print("   " + "-" * 75)
    
    for equip_id, count in mais_repetidos:
        # Buscar informações do equipamento
        cursor.execute("SELECT name, active FROM equipments WHERE id = ?", (equip_id,))
        result = cursor.fetchone()
        nome = result[0] if result else "Equipamento não encontrado"
        status = "ATIVO" if result and result[1] == 1 else "INATIVO"
        
        print(f"   {equip_id:<10} {count:<12} {nome[:38]:<40} {status}")
    
    # 4. Detalhamento das tarefas com múltiplos equipamentos
    tarefas_multi_equip = {t_id: equips for t_id, equips in equip_por_tarefa.items() if len(equips) > 1}
    
    print(f"\n4. TAREFAS COM MÚLTIPLOS EQUIPAMENTOS")
    print(f"   Total: {len(tarefas_multi_equip)}")
    
    if tarefas_multi_equip:
        print("\n   TOP 5 TAREFAS COM MAIS EQUIPAMENTOS:")
        print(f"   {'Tarefa ID':<15} {'Qtd Equip':<12} {'Lista de Equipamentos'}")
        print("   " + "-" * 75)
        
        # Ordenar por número de equipamentos
        top_tarefas = sorted(tarefas_multi_equip.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        
        for tarefa_id, equips in top_tarefas:
            print(f"   {tarefa_id:<15} {len(equips):<12} {str(equips)[:50]}...")
    
    # 5. Validação cruzada
    print("\n5. VALIDAÇÃO CRUZADA")
    
    # Equipamentos cadastrados vs equipamentos em tarefas
    equip_cadastrados_ids = {e[0] for e in equipamentos}
    equip_tarefas_validos = equip_unicos.intersection(equip_cadastrados_ids)
    equip_tarefas_invalidos = equip_unicos - equip_cadastrados_ids
    
    print(f"   Equipamentos em tarefas que estão cadastrados para esta escola: {len(equip_tarefas_validos)}")
    print(f"   Equipamentos em tarefas NÃO cadastrados para esta escola: {len(equip_tarefas_invalidos)}")
    
    if equip_tarefas_invalidos:
        print("\n   ALERTA: Alguns equipamentos nas tarefas não estão cadastrados para esta escola!")
        print("   Exemplo de IDs: " + ", ".join(str(id) for id in list(equip_tarefas_invalidos)[:5]))
    
    conn.close()

if __name__ == "__main__":
    cliente_id = 11828027  # ID da escola STS36693/22 - SEDUC UME PADRE LEONARDO NUNES
    analisar_equipamentos_escola(cliente_id)
