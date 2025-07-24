"""
Script para comparar lista-teste.txt com banco de dados de equipamentos
Faz um "de-para" entre os dados do arquivo e os equipamentos no banco
"""

import sqlite3
import re
from collections import defaultdict
import pandas as pd

def parse_lista_teste(file_path):
    """Parse do arquivo lista-teste.txt para extrair dados estruturados"""
    print("📋 Analisando arquivo lista-teste.txt...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    data = []
    current_school = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('Rótulos'):
            continue
            
        # Detectar linha de escola (começa com STS36693/22)
        if line.startswith('STS36693/22'):
            # Extrair nome da escola e quantidade total
            parts = line.split('\t')
            if len(parts) >= 2:
                school_name = parts[0].strip()
                try:
                    total_count = int(parts[1])
                    current_school = {
                        'school_name': school_name,
                        'total_count': total_count,
                        'ativo': 0,
                        'inativo': 0
                    }
                except ValueError:
                    continue
        
        # Detectar linhas de status (Ativo/Inativo)
        elif line.startswith('Ativo') or line.startswith('Inativo'):
            if current_school:
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0].strip()
                    try:
                        count = int(parts[1])
                        if status == 'Ativo':
                            current_school['ativo'] = count
                        elif status == 'Inativo':
                            current_school['inativo'] = count
                    except ValueError:
                        continue
                
                # Se temos ativo e inativo, ou só um deles, adicionar à lista
                if current_school['ativo'] > 0 or current_school['inativo'] > 0:
                    data.append(current_school.copy())
                    current_school = None
    
    print(f"✅ Encontradas {len(data)} escolas no arquivo lista-teste.txt")
    return data

def get_equipment_from_db():
    """Busca equipamentos do banco de dados agrupados por escola"""
    print("🗄️  Consultando equipamentos no banco de dados...")
    
    conn = sqlite3.connect('auvo.db')
    cursor = conn.cursor()
    
    # Buscar todos os equipamentos com STS36693/22
    cursor.execute("""
        SELECT name, active 
        FROM equipments 
        WHERE name LIKE 'STS36693/22%'
        ORDER BY name
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    # Agrupar por escola
    schools_db = defaultdict(lambda: {'ativo': 0, 'inativo': 0, 'total': 0})
    
    for name, active in results:
        # Extrair nome da escola com nova lógica
        # Exemplos:
        # "STS36693/22 - SEDUC / UME PADRE LEONARDO NUNES / ESTUDIOTECA" -> "STS36693/22 - SEDUC UME PADRE LEONARDO NUNES"
        # "STS36693/22 - SEDUC / ALMOXARIFADO MERENDA ESCOLAR / ANEXO" -> "STS36693/22 - SEDUC ALMOXARIFADO MERENDA ESCOLAR"
        
        # Dividir por barras e pegar as duas primeiras partes
        parts = name.split(' / ')
        if len(parts) >= 2:
            # Primeira parte: "STS36693/22 - SEDUC"
            # Segunda parte: "UME NOME DA ESCOLA" ou "NOME DO LOCAL"
            school_name = f"{parts[0].strip()} {parts[1].strip()}"
        else:
            # Se não tem barras, usar regex como fallback
            school_match = re.match(r'(STS36693/22[^/]+)', name)
            if school_match:
                school_name = school_match.group(1).strip()
            else:
                continue
        
        # Limpar espaços extras
        school_name = re.sub(r'\s+', ' ', school_name)
        
        schools_db[school_name]['total'] += 1
        if active == 1:
            schools_db[school_name]['ativo'] += 1
        else:
            schools_db[school_name]['inativo'] += 1
    
    print(f"✅ Encontradas {len(schools_db)} escolas no banco de dados")
    return dict(schools_db)

def compare_data(lista_data, db_data):
    """Compara dados do arquivo com dados do banco"""
    print("\n🔍 Comparando dados...")
    
    comparison_results = []
    
    # Criar dicionário para busca mais eficiente
    db_lookup = {}
    for db_school in db_data.keys():
        # Normalizar nome para comparação
        normalized = re.sub(r'\s+', ' ', db_school.upper().strip())
        db_lookup[normalized] = db_school
    
    for lista_item in lista_data:
        school_name = lista_item['school_name']
        normalized_name = re.sub(r'\s+', ' ', school_name.upper().strip())
        
        # Buscar correspondência no banco
        db_match = None
        db_school_name = None
        
        # Busca exata
        if normalized_name in db_lookup:
            db_school_name = db_lookup[normalized_name]
            db_match = db_data[db_school_name]
        else:
            # Busca parcial (para casos de diferenças menores)
            for db_norm, db_orig in db_lookup.items():
                if normalized_name in db_norm or db_norm in normalized_name:
                    db_school_name = db_orig
                    db_match = db_data[db_orig]
                    break
        
        result = {
            'escola_lista': school_name,
            'escola_db': db_school_name if db_match else 'NÃO ENCONTRADA',
            'lista_total': lista_item['total_count'],
            'lista_ativo': lista_item['ativo'],
            'lista_inativo': lista_item['inativo'],
            'db_total': db_match['total'] if db_match else 0,
            'db_ativo': db_match['ativo'] if db_match else 0,
            'db_inativo': db_match['inativo'] if db_match else 0,
            'diferenca_total': (db_match['total'] if db_match else 0) - lista_item['total_count'],
            'status': 'MATCH' if db_match and db_match['total'] == lista_item['total_count'] else 'DIFERENÇA'
        }
        
        comparison_results.append(result)
    
    return comparison_results

def generate_report(comparison_results):
    """Gera relatório detalhado da comparação"""
    print("\n📊 Gerando relatório...")
    
    # Estatísticas gerais
    total_schools = len(comparison_results)
    matches = sum(1 for r in comparison_results if r['status'] == 'MATCH')
    differences = total_schools - matches
    not_found = sum(1 for r in comparison_results if r['escola_db'] == 'NÃO ENCONTRADA')
    
    print(f"\n{'='*80}")
    print(f"📋 RELATÓRIO DE COMPARAÇÃO - LISTA-TESTE.TXT vs BANCO DE DADOS")
    print(f"{'='*80}")
    print(f"🏫 Total de escolas analisadas: {total_schools}")
    print(f"✅ Escolas com dados idênticos: {matches}")
    print(f"⚠️  Escolas com diferenças: {differences}")
    print(f"❌ Escolas não encontradas no banco: {not_found}")
    print(f"{'='*80}")
    
    # Detalhes das diferenças
    print(f"\n🔍 DETALHES DAS DIFERENÇAS:")
    print(f"{'='*80}")
    
    for result in comparison_results:
        if result['status'] != 'MATCH':
            print(f"\n🏫 {result['escola_lista']}")
            print(f"   📋 Lista: {result['lista_total']} total ({result['lista_ativo']} ativos, {result['lista_inativo']} inativos)")
            print(f"   🗄️  Banco: {result['db_total']} total ({result['db_ativo']} ativos, {result['db_inativo']} inativos)")
            print(f"   📊 Diferença: {result['diferenca_total']:+d}")
            if result['escola_db'] == 'NÃO ENCONTRADA':
                print(f"   ❌ Status: ESCOLA NÃO ENCONTRADA NO BANCO")
            else:
                print(f"   ⚠️  Status: DIFERENÇA DE QUANTIDADE")
    
    # Salvar em CSV para análise detalhada
    df = pd.DataFrame(comparison_results)
    csv_filename = 'comparacao_equipamentos.csv'
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"\n💾 Relatório detalhado salvo em: {csv_filename}")
    
    return comparison_results

def main():
    """Função principal"""
    print("🚀 COMPARAÇÃO LISTA-TESTE.TXT vs BANCO DE DADOS")
    print("="*60)
    
    try:
        # 1. Parse do arquivo lista-teste.txt
        lista_data = parse_lista_teste('downloads/lista-teste.txt')
        
        # 2. Consulta do banco de dados
        db_data = get_equipment_from_db()
        
        # 3. Comparação dos dados
        comparison_results = compare_data(lista_data, db_data)
        
        # 4. Geração do relatório
        generate_report(comparison_results)
        
        print(f"\n✅ Comparação concluída com sucesso!")
        
    except FileNotFoundError:
        print("❌ Arquivo lista-teste.txt não encontrado em downloads/")
    except Exception as e:
        print(f"❌ Erro durante a comparação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
