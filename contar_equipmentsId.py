import sqlite3
import json
from collections import Counter
import matplotlib.pyplot as plt
import os

def contar_equipamentos_tasks():
    """
    Analisa especificamente o campo equipmentsId da tabela tasks.
    Conta quantos equipamentos existem no total, identifica repetições,
    e analisa em detalhe as tarefas da escola PADRE LEONARDO NUNES.
    """
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    print("\n=== ANÁLISE DO CAMPO equipmentsId NA TABELA tasks ===\n")
    
    # 1. CONTAGEM GERAL
    print("1. CONTAGEM GERAL\n")
    
    # Total de tarefas
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tarefas = cursor.fetchone()[0]
    
    # Tarefas com equipamentos
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE equipmentsId IS NOT NULL AND equipmentsId != '[]' AND equipmentsId != ''")
    tarefas_com_equip = cursor.fetchone()[0]
    
    # Tarefas sem equipamentos
    tarefas_sem_equip = total_tarefas - tarefas_com_equip
    
    print(f"Total de tarefas: {total_tarefas}")
    print(f"Tarefas com equipamentos: {tarefas_com_equip} ({tarefas_com_equip/total_tarefas*100:.1f}%)")
    print(f"Tarefas sem equipamentos: {tarefas_sem_equip} ({tarefas_sem_equip/total_tarefas*100:.1f}%)")
    
    # 2. ANÁLISE DE EQUIPAMENTOS
    
    # Extrair todos os IDs de equipamentos
    cursor.execute("SELECT equipmentsId FROM tasks WHERE equipmentsId IS NOT NULL AND equipmentsId != '[]' AND equipmentsId != ''")
    
    todos_equips = []
    for row in cursor.fetchall():
        try:
            equips = json.loads(row[0])
            if isinstance(equips, list):
                todos_equips.extend(equips)
        except:
            pass
    
    # Contagem
    total_ocorrencias = len(todos_equips)
    equips_unicos = set(todos_equips)
    total_unicos = len(equips_unicos)
    
    print(f"\n2. ANÁLISE DE EQUIPAMENTOS\n")
    print(f"Total de ocorrências de equipamentos: {total_ocorrencias}")
    print(f"Total de equipamentos únicos: {total_unicos}")
    print(f"Média de repetições por equipamento: {total_ocorrencias/total_unicos:.2f}")
    
    # Equipamentos mais repetidos
    counter = Counter(todos_equips)
    mais_repetidos = counter.most_common(10)
    
    print(f"\nTOP 10 EQUIPAMENTOS MAIS UTILIZADOS:")
    print(f"{'ID':<10} {'Ocorrências':<12} {'% do Total':<12} {'Nome do Equipamento':<40}")
    print("-" * 80)
    
    for equip_id, count in mais_repetidos:
        # Buscar nome do equipamento
        cursor.execute("SELECT name FROM equipments WHERE id = ?", (equip_id,))
        result = cursor.fetchone()
        nome = result[0] if result else "Equipamento não encontrado"
        
        # Calcular porcentagem do total de ocorrências
        percentual = count / total_ocorrencias * 100
        
        print(f"{equip_id:<10} {count:<12} {percentual:.2f}%{'':<8} {nome[:40]}")
    
    # 3. ANÁLISE ESPECÍFICA DA ESCOLA PADRE LEONARDO NUNES
    cliente_id = 11828027  # ID da escola STS36693/22 - SEDUC UME PADRE LEONARDO NUNES
    
    # Buscar nome da escola
    cursor.execute("SELECT description FROM customers WHERE id = ?", (cliente_id,))
    result = cursor.fetchone()
    nome_escola = result[0] if result else "Escola não encontrada"
    
    print(f"\n3. ANÁLISE ESPECÍFICA: {nome_escola}\n")
    
    # Contagem de tarefas da escola
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE customerId = ?", (cliente_id,))
    tarefas_escola = cursor.fetchone()[0]
    
    # Tarefas da escola com equipamentos
    cursor.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE customerId = ? 
        AND equipmentsId IS NOT NULL 
        AND equipmentsId != '[]' 
        AND equipmentsId != ''
    """, (cliente_id,))
    tarefas_escola_com_equip = cursor.fetchone()[0]
    
    print(f"Total de tarefas da escola: {tarefas_escola}")
    print(f"Tarefas com equipamentos: {tarefas_escola_com_equip}")
    
    # Extrair todos os equipamentos das tarefas da escola
    cursor.execute("""
        SELECT equipmentsId FROM tasks 
        WHERE customerId = ? 
        AND equipmentsId IS NOT NULL 
        AND equipmentsId != '[]' 
        AND equipmentsId != ''
    """, (cliente_id,))
    
    equips_escola = []
    for row in cursor.fetchall():
        try:
            equips = json.loads(row[0])
            if isinstance(equips, list):
                equips_escola.extend(equips)
        except:
            pass
    
    total_ocorrencias_escola = len(equips_escola)
    equips_unicos_escola = set(equips_escola)
    
    print(f"Total de ocorrências de equipamentos nas tarefas: {total_ocorrencias_escola}")
    print(f"Total de equipamentos únicos nas tarefas: {len(equips_unicos_escola)}")
    
    # Equipamentos mais utilizados nesta escola
    counter_escola = Counter(equips_escola)
    mais_usados_escola = counter_escola.most_common()
    
    print(f"\nLISTA DE EQUIPAMENTOS NAS TAREFAS DA ESCOLA:")
    print(f"{'ID':<10} {'Ocorrências':<12} {'Nome':<40}")
    print("-" * 65)
    
    for equip_id, count in mais_usados_escola:
        # Buscar nome do equipamento
        cursor.execute("SELECT name FROM equipments WHERE id = ?", (equip_id,))
        result = cursor.fetchone()
        nome = result[0] if result else "Equipamento não encontrado"
        
        print(f"{equip_id:<10} {count:<12} {nome[:40]}")
    
    # 4. VERIFICAÇÃO DE CONSISTÊNCIA
    print(f"\n4. VERIFICAÇÃO DE CONSISTÊNCIA\n")
    
    # Equipamentos mencionados nas tarefas vs cadastrados
    cursor.execute("SELECT id FROM equipments WHERE associatedCustomerId = ?", (cliente_id,))
    equips_cadastrados = set([row[0] for row in cursor.fetchall()])
    
    # Comparar equipamentos nas tarefas com equipamentos cadastrados
    em_tarefas_nao_cadastrados = equips_unicos_escola - equips_cadastrados
    cadastrados_nao_em_tarefas = equips_cadastrados - equips_unicos_escola
    
    print(f"Equipamentos em tarefas que estão cadastrados: {len(equips_unicos_escola - em_tarefas_nao_cadastrados)}")
    print(f"Equipamentos em tarefas NÃO cadastrados para esta escola: {len(em_tarefas_nao_cadastrados)}")
    print(f"Equipamentos cadastrados que NÃO aparecem em tarefas: {len(cadastrados_nao_em_tarefas)}")
    
    if em_tarefas_nao_cadastrados:
        print("\nALERTA: Alguns equipamentos nas tarefas não estão cadastrados para esta escola!")
    
    # 5. VISUALIZAÇÃO DE TAREFAS POR QUANTIDADE DE EQUIPAMENTOS
    print(f"\n5. DISTRIBUIÇÃO DE EQUIPAMENTOS POR TAREFA\n")
    
    # Contar quantas tarefas têm 1, 2, 3... equipamentos
    cursor.execute("""
        SELECT equipmentsId FROM tasks 
        WHERE equipmentsId IS NOT NULL 
        AND equipmentsId != '[]' 
        AND equipmentsId != ''
    """)
    
    qtd_equips_por_tarefa = []
    for row in cursor.fetchall():
        try:
            equips = json.loads(row[0])
            if isinstance(equips, list):
                qtd_equips_por_tarefa.append(len(equips))
        except:
            pass
    
    counter_qtd = Counter(qtd_equips_por_tarefa)
    
    print("Quantidade de tarefas por número de equipamentos:")
    for qtd, count in sorted(counter_qtd.items()):
        print(f"{qtd} equipamento(s): {count} tarefas")
    
    conn.close()
    
    return total_tarefas, tarefas_com_equip, total_ocorrencias, total_unicos, mais_repetidos

if __name__ == "__main__":
    contar_equipamentos_tasks()
