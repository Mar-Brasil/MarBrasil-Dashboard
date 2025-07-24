import sqlite3
import json
from collections import Counter

def contar_equipmentsId():
    """
    Script específico para contar e analisar os equipamentos no campo equipmentsId da tabela tasks
    """
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    print("\n=== CONTAGEM DE EQUIPAMENTOS NA TABELA TASKS (equipmentsId) ===\n")
    
    # 1. Obter todos os equipmentsId não vazios
    cursor.execute("SELECT equipmentsId FROM tasks WHERE equipmentsId IS NOT NULL AND equipmentsId != '[]' AND equipmentsId != ''")
    
    # Listas para armazenar todos os IDs encontrados
    todos_equipamentos = []  # Com repetições
    equip_unicos = set()     # Sem repetições
    
    # Processar cada registro
    for row in cursor.fetchall():
        equipments_str = row[0]
        try:
            equips = json.loads(equipments_str)
            if isinstance(equips, list):
                todos_equipamentos.extend(equips)
                equip_unicos.update(equips)
        except:
            pass
    
    print(f"1. CONTAGEM GERAL")
    print(f"   Total de ocorrências de equipamentos: {len(todos_equipamentos)}")
    print(f"   Total de equipamentos únicos: {len(equip_unicos)}")
    print(f"   Número de repetições: {len(todos_equipamentos) - len(equip_unicos)}")
    
    # 2. Análise de repetições
    print(f"\n2. ANÁLISE DE REPETIÇÕES")
    
    # Contar ocorrências de cada equipamento
    counter = Counter(todos_equipamentos)
    
    # Equipamentos repetidos (aparecem mais de uma vez)
    repetidos = {equip: count for equip, count in counter.items() if count > 1}
    
    print(f"   Equipamentos que aparecem em mais de uma tarefa: {len(repetidos)}")
    
    # Estatísticas de repetição
    print("\n   Distribuição de repetições:")
    repeticoes = Counter(counter.values())
    for ocorrencias, qtd_equips in sorted(repeticoes.items()):
        print(f"   {ocorrencias} {'vez' if ocorrencias == 1 else 'vezes'}: {qtd_equips} equipamentos")
    
    # 3. Top equipamentos mais repetidos
    print(f"\n3. TOP 20 EQUIPAMENTOS MAIS UTILIZADOS")
    print(f"   {'ID':<10} {'Ocorrências':<12} {'% do Total':<12} {'Nome do Equipamento':<40} {'Status'}")
    print("   " + "-" * 85)
    
    mais_repetidos = counter.most_common(20)
    for equip_id, count in mais_repetidos:
        # Buscar nome do equipamento
        cursor.execute("SELECT name, active FROM equipments WHERE id = ?", (equip_id,))
        result = cursor.fetchone()
        nome = result[0] if result else "Equipamento não encontrado"
        status = "ATIVO" if result and result[1] == 1 else "INATIVO"
        
        # Calcular porcentagem do total de ocorrências
        percentual = count / len(todos_equipamentos) * 100
        
        print(f"   {equip_id:<10} {count:<12} {percentual:.2f}%{'':<8} {nome[:40]:<40} {status}")
    
    conn.close()
    
    return todos_equipamentos, equip_unicos

if __name__ == "__main__":
    contar_equipmentsId()
