import sqlite3
import json
from tabulate import tabulate

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
    
    # Buscar todas as tarefas da escola
    cursor.execute("""
        SELECT taskID, equipmentsId 
        FROM tasks 
        WHERE customerId = ? 
        ORDER BY taskID
    """, (cliente_id,))
    
    tarefas = cursor.fetchall()
    
    # Preparar dados para tabela
    tabela_dados = []
    
    for i, (tarefa_id, equipments_str) in enumerate(tarefas, 1):
        # Extrair IDs dos equipamentos
        equip_ids = []
        if equipments_str:
            try:
                equip_ids = json.loads(equipments_str)
                if not isinstance(equip_ids, list):
                    equip_ids = []
            except:
                equip_ids = []
        
        # Formatar como string para exibição
        equip_str = str(equip_ids) if equip_ids else "[]"
        
        # Adicionar à tabela
        tabela_dados.append([i, tarefa_id, nome_escola, equip_str])
    
    # Exibir tabela
    headers = ["#", "taskID", "customerDescription", "equipmentsId"]
    print(tabulate(tabela_dados, headers=headers, tablefmt="psql"))
    
    # Análise adicional
    total_equip_ocorrencias = sum(len(json.loads(e[1])) if e[1] and e[1] != '[]' else 0 for e in tarefas)
    equip_unicos = set()
    
    for _, equip_str in tarefas:
        if equip_str and equip_str != '[]':
            try:
                equips = json.loads(equip_str)
                if isinstance(equips, list):
                    equip_unicos.update(equips)
            except:
                pass
    
    print(f"\nEstatísticas:")
    print(f"Total de tarefas: {len(tarefas)}")
    print(f"Total de ocorrências de equipamentos: {total_equip_ocorrencias}")
    print(f"Equipamentos únicos: {len(equip_unicos)}")
    print(f"Média de equipamentos por tarefa: {total_equip_ocorrencias/len(tarefas):.1f}")
    
    # Verificar tarefas com e sem equipamentos
    tarefas_sem_equip = sum(1 for _, e in tarefas if not e or e == '[]')
    tarefas_com_equip = len(tarefas) - tarefas_sem_equip
    
    print(f"Tarefas com equipamentos: {tarefas_com_equip}")
    print(f"Tarefas sem equipamentos: {tarefas_sem_equip}")
    
    conn.close()

try:
    # Tentar importar tabulate - se não existir, usar uma versão simplificada
    from tabulate import tabulate
except ImportError:
    # Função simplificada para imprimir tabela
    def tabulate(data, headers, tablefmt=None):
        result = []
        # Adicionar cabeçalho
        header_line = " | ".join(str(h) for h in headers)
        result.append(header_line)
        result.append("-" * len(header_line))
        
        # Adicionar linhas
        for row in data:
            result.append(" | ".join(str(cell) for cell in row))
        
        return "\n".join(result)

if __name__ == "__main__":
    cliente_id = 11828027  # ID da escola STS36693/22 - SEDUC UME PADRE LEONARDO NUNES
    detalhar_tarefas_equipamentos(cliente_id)
