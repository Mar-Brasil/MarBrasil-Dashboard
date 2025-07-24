"""
Script aprimorado para análise detalhada do Excel vs Banco de Dados
Inclui correspondência por identificador e análise de discrepâncias
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
import numpy as np
import re

def load_excel_data(file_path):
    """Carrega e limpa dados do arquivo Excel"""
    print(f"📊 Carregando dados do Excel: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Excel carregado: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # Limpar dados - remover linha de cabeçalho duplicada
        if df.iloc[0]['Status'] == "Status do produto. 'Ativo' ou 'Inativo'":
            df = df.drop(0).reset_index(drop=True)
            print("🧹 Removida linha de cabeçalho duplicada")
        
        # Limpar coluna Status
        df['Status'] = df['Status'].replace("Status do produto. 'Ativo' ou 'Inativo'", np.nan)
        df = df.dropna(subset=['Status'])
        
        print(f"📋 Dados limpos: {df.shape[0]} linhas")
        return df
        
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return None

def load_database_data():
    """Carrega dados do banco SQLite"""
    print(f"🗄️  Carregando dados do banco SQLite...")
    
    try:
        conn = sqlite3.connect('auvo.db')
        query = """
        SELECT 
            id, name, identifier, active, externalId,
            associatedCustomerId, categoryId, description
        FROM equipments
        ORDER BY id
        """
        df_db = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✅ Banco carregado: {df_db.shape[0]} linhas")
        return df_db
        
    except Exception as e:
        print(f"❌ Erro ao carregar banco: {e}")
        return None

def match_by_identifier(df_excel, df_db):
    """Tenta fazer correspondência usando identificadores"""
    print(f"\n🔍 CORRESPONDÊNCIA POR IDENTIFICADOR")
    print("=" * 60)
    
    # Limpar identificadores do Excel
    excel_identifiers = df_excel['Identificador'].dropna().str.strip()
    db_identifiers = df_db['identifier'].dropna().str.strip()
    
    print(f"📋 Excel: {len(excel_identifiers)} identificadores válidos")
    print(f"🗄️  Banco: {len(db_identifiers)} identificadores válidos")
    
    # Encontrar correspondências exatas
    excel_id_set = set(excel_identifiers)
    db_id_set = set(db_identifiers)
    
    matches = excel_id_set & db_id_set
    excel_only = excel_id_set - db_id_set
    db_only = db_id_set - excel_id_set
    
    print(f"\n📊 Resultados da correspondência:")
    print(f"   🤝 Identificadores em ambos: {len(matches):,}")
    print(f"   📋 Apenas no Excel: {len(excel_only):,}")
    print(f"   🗄️  Apenas no Banco: {len(db_only):,}")
    
    if matches:
        match_rate = len(matches) / max(len(excel_id_set), len(db_id_set)) * 100
        print(f"   📈 Taxa de correspondência: {match_rate:.1f}%")
    
    return {
        'matches': matches,
        'excel_only': excel_only,
        'db_only': db_only,
        'excel_identifiers': excel_id_set,
        'db_identifiers': db_id_set
    }

def analyze_status_discrepancies(df_excel, df_db, match_data):
    """Analisa discrepâncias de status entre Excel e Banco"""
    print(f"\n⚖️  ANÁLISE DE DISCREPÂNCIAS DE STATUS")
    print("=" * 60)
    
    discrepancies = []
    
    # Para cada identificador que existe em ambos
    for identifier in match_data['matches']:
        # Buscar no Excel
        excel_row = df_excel[df_excel['Identificador'] == identifier]
        if len(excel_row) == 0:
            continue
        excel_status = excel_row.iloc[0]['Status']
        
        # Buscar no Banco
        db_row = df_db[df_db['identifier'] == identifier]
        if len(db_row) == 0:
            continue
        db_active = db_row.iloc[0]['active']
        db_status = 'Ativo' if db_active == 1 else 'Inativo'
        
        # Verificar discrepância
        if excel_status != db_status:
            discrepancies.append({
                'identificador': identifier,
                'nome': excel_row.iloc[0]['Nome'],
                'excel_status': excel_status,
                'banco_status': db_status,
                'banco_id': db_row.iloc[0]['id']
            })
    
    print(f"⚠️  Discrepâncias de status encontradas: {len(discrepancies)}")
    
    if discrepancies:
        print(f"\n📋 Primeiras 10 discrepâncias:")
        for i, disc in enumerate(discrepancies[:10], 1):
            print(f"   {i:2d}. {disc['identificador']} - {disc['nome'][:50]}")
            print(f"       Excel: {disc['excel_status']} | Banco: {disc['banco_status']}")
    
    return discrepancies

def analyze_missing_equipment(df_excel, df_db, match_data):
    """Analisa equipamentos que existem apenas em um dos sistemas"""
    print(f"\n🔍 ANÁLISE DE EQUIPAMENTOS FALTANTES")
    print("=" * 60)
    
    # Equipamentos apenas no Excel
    excel_only_data = []
    for identifier in list(match_data['excel_only'])[:20]:  # Limitar para não sobrecarregar
        excel_row = df_excel[df_excel['Identificador'] == identifier]
        if len(excel_row) > 0:
            excel_only_data.append({
                'identificador': identifier,
                'nome': excel_row.iloc[0]['Nome'],
                'status': excel_row.iloc[0]['Status'],
                'cliente': excel_row.iloc[0]['Cliente']
            })
    
    # Equipamentos apenas no Banco
    db_only_data = []
    for identifier in list(match_data['db_only'])[:20]:  # Limitar para não sobrecarregar
        db_row = df_db[df_db['identifier'] == identifier]
        if len(db_row) > 0:
            db_only_data.append({
                'identificador': identifier,
                'nome': db_row.iloc[0]['name'],
                'status': 'Ativo' if db_row.iloc[0]['active'] == 1 else 'Inativo',
                'id': db_row.iloc[0]['id']
            })
    
    print(f"📋 Exemplos de equipamentos apenas no Excel:")
    for i, item in enumerate(excel_only_data[:5], 1):
        print(f"   {i}. {item['identificador']} - {item['nome'][:50]} ({item['status']})")
    
    print(f"\n🗄️  Exemplos de equipamentos apenas no Banco:")
    for i, item in enumerate(db_only_data[:5], 1):
        print(f"   {i}. {item['identificador']} - {item['nome'][:50]} ({item['status']})")
    
    return excel_only_data, db_only_data

def generate_comprehensive_report(df_excel, df_db, match_data, discrepancies, excel_only, db_only):
    """Gera relatório abrangente"""
    print(f"\n📋 GERANDO RELATÓRIO ABRANGENTE")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Relatório principal
    report = {
        'timestamp': timestamp,
        'excel_total': len(df_excel),
        'database_total': len(df_db),
        'difference': len(df_db) - len(df_excel),
        'matched_identifiers': len(match_data['matches']),
        'excel_only_count': len(match_data['excel_only']),
        'database_only_count': len(match_data['db_only']),
        'status_discrepancies': len(discrepancies),
        'match_percentage': len(match_data['matches']) / max(len(match_data['excel_identifiers']), len(match_data['db_identifiers'])) * 100 if match_data['matches'] else 0
    }
    
    try:
        # 1. Relatório resumido
        report_df = pd.DataFrame([report])
        report_df.to_csv('relatorio_completo_excel_vs_banco.csv', index=False)
        print("✅ Relatório resumido salvo: relatorio_completo_excel_vs_banco.csv")
        
        # 2. Discrepâncias de status
        if discrepancies:
            disc_df = pd.DataFrame(discrepancies)
            disc_df.to_csv('discrepancias_status.csv', index=False, encoding='utf-8-sig')
            print("✅ Discrepâncias de status salvas: discrepancias_status.csv")
        
        # 3. Equipamentos apenas no Excel
        if excel_only:
            excel_only_df = pd.DataFrame(excel_only)
            excel_only_df.to_csv('equipamentos_apenas_excel.csv', index=False, encoding='utf-8-sig')
            print("✅ Equipamentos apenas no Excel salvos: equipamentos_apenas_excel.csv")
        
        # 4. Equipamentos apenas no Banco
        if db_only:
            db_only_df = pd.DataFrame(db_only)
            db_only_df.to_csv('equipamentos_apenas_banco.csv', index=False, encoding='utf-8-sig')
            print("✅ Equipamentos apenas no Banco salvos: equipamentos_apenas_banco.csv")
        
        # 5. Estatísticas de status
        excel_status_stats = df_excel['Status'].value_counts()
        db_status_stats = df_db['active'].map({1: 'Ativo', 0: 'Inativo'}).value_counts()
        
        status_comparison = pd.DataFrame({
            'Excel': excel_status_stats,
            'Banco': db_status_stats
        }).fillna(0)
        status_comparison.to_csv('comparacao_status.csv', encoding='utf-8-sig')
        print("✅ Comparação de status salva: comparacao_status.csv")
        
    except Exception as e:
        print(f"⚠️  Erro ao salvar alguns relatórios: {e}")
    
    return report

def main():
    """Função principal"""
    print("🚀 ANÁLISE ABRANGENTE: EXCEL vs BANCO DE DADOS")
    print("=" * 70)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar arquivos
    excel_paths = [
        'planilha/equipamentos_23_07_2025.xlsx',
        'downloads/equipamentos_23_07_2025.xlsx'
    ]
    
    excel_file = None
    for path in excel_paths:
        if os.path.exists(path):
            excel_file = path
            break
    
    if not excel_file:
        print("❌ Arquivo Excel não encontrado!")
        return
    
    if not os.path.exists('auvo.db'):
        print("❌ Banco de dados não encontrado!")
        return
    
    try:
        # 1. Carregar dados
        df_excel = load_excel_data(excel_file)
        if df_excel is None:
            return
        
        df_db = load_database_data()
        if df_db is None:
            return
        
        # 2. Correspondência por identificador
        match_data = match_by_identifier(df_excel, df_db)
        
        # 3. Análise de discrepâncias de status
        discrepancies = analyze_status_discrepancies(df_excel, df_db, match_data)
        
        # 4. Análise de equipamentos faltantes
        excel_only, db_only = analyze_missing_equipment(df_excel, df_db, match_data)
        
        # 5. Gerar relatório abrangente
        report = generate_comprehensive_report(df_excel, df_db, match_data, discrepancies, excel_only, db_only)
        
        # 6. Resumo final
        print(f"\n" + "=" * 70)
        print(f"✅ ANÁLISE ABRANGENTE CONCLUÍDA!")
        print(f"📊 Excel: {len(df_excel):,} equipamentos")
        print(f"🗄️  Banco: {len(df_db):,} equipamentos")
        print(f"🤝 Correspondências: {len(match_data['matches']):,}")
        print(f"📈 Taxa de correspondência: {report['match_percentage']:.1f}%")
        print(f"⚠️  Discrepâncias de status: {len(discrepancies):,}")
        print(f"📋 Apenas no Excel: {len(match_data['excel_only']):,}")
        print(f"🗄️  Apenas no Banco: {len(match_data['db_only']):,}")
        print(f"⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
