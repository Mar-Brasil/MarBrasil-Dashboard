"""
Script para análise completa do arquivo Excel equipamentos_23_07_2025.xlsx
vs banco de dados SQLite (auvo.db)
Comparação detalhada de todos os equipamentos
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
import numpy as np

def load_excel_data(file_path):
    """Carrega dados do arquivo Excel"""
    print(f"📊 Carregando dados do Excel: {file_path}")
    
    try:
        # Tentar carregar o Excel
        df = pd.read_excel(file_path)
        print(f"✅ Excel carregado com sucesso!")
        print(f"📋 Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # Mostrar informações das colunas
        print(f"\n📝 Colunas encontradas:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Mostrar algumas linhas de exemplo
        print(f"\n🔍 Primeiras 3 linhas:")
        print(df.head(3).to_string())
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return None

def load_database_data():
    """Carrega dados do banco SQLite"""
    print(f"\n🗄️  Carregando dados do banco SQLite...")
    
    try:
        conn = sqlite3.connect('auvo.db')
        
        # Carregar todos os equipamentos
        query = """
        SELECT 
            id,
            name,
            externalId,
            parentEquipmentId,
            associatedCustomerId,
            associatedUserId,
            categoryId,
            identifier,
            urlImage,
            uriAnexos,
            active,
            creationDate,
            expirationDate,
            equipmentSpecifications,
            description,
            warrantyStartDate,
            warrantyEndDate
        FROM equipments
        ORDER BY id
        """
        
        df_db = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✅ Banco carregado com sucesso!")
        print(f"📋 Dimensões: {df_db.shape[0]} linhas x {df_db.shape[1]} colunas")
        
        return df_db
        
    except Exception as e:
        print(f"❌ Erro ao carregar banco: {e}")
        return None

def analyze_excel_structure(df_excel):
    """Analisa a estrutura do arquivo Excel"""
    print(f"\n🔬 ANÁLISE DETALHADA DO EXCEL")
    print("=" * 60)
    
    # Informações gerais
    print(f"📊 Total de registros: {len(df_excel)}")
    print(f"📋 Total de colunas: {len(df_excel.columns)}")
    
    # Verificar valores únicos em colunas importantes
    key_columns = []
    for col in df_excel.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['id', 'nome', 'name', 'ativo', 'active', 'status']):
            key_columns.append(col)
    
    print(f"\n🔑 Colunas-chave identificadas:")
    for col in key_columns:
        unique_count = df_excel[col].nunique()
        null_count = df_excel[col].isnull().sum()
        print(f"   📌 {col}: {unique_count} valores únicos, {null_count} nulos")
        
        # Mostrar alguns valores de exemplo
        sample_values = df_excel[col].dropna().head(3).tolist()
        print(f"      Exemplos: {sample_values}")
    
    # Verificar se há coluna de ID
    id_columns = [col for col in df_excel.columns if 'id' in col.lower()]
    if id_columns:
        print(f"\n🆔 Colunas de ID encontradas: {id_columns}")
        for id_col in id_columns:
            print(f"   {id_col}: {df_excel[id_col].nunique()} valores únicos")
    
    return key_columns

def compare_datasets(df_excel, df_db):
    """Compara os datasets do Excel e do banco"""
    print(f"\n🔄 COMPARAÇÃO ENTRE EXCEL E BANCO")
    print("=" * 60)
    
    # Estatísticas básicas
    excel_count = len(df_excel)
    db_count = len(df_db)
    
    print(f"📊 Contagem de registros:")
    print(f"   📋 Excel: {excel_count:,} equipamentos")
    print(f"   🗄️  Banco: {db_count:,} equipamentos")
    print(f"   📊 Diferença: {db_count - excel_count:+,}")
    
    # Tentar identificar coluna de ID no Excel
    id_column = None
    for col in df_excel.columns:
        if 'id' in col.lower() and df_excel[col].dtype in ['int64', 'float64']:
            id_column = col
            break
    
    if id_column:
        print(f"\n🆔 Usando coluna '{id_column}' como ID do Excel")
        
        # Converter para int e remover NaN
        excel_ids = set(df_excel[id_column].dropna().astype(int))
        db_ids = set(df_db['id'])
        
        # Análise de interseção
        common_ids = excel_ids & db_ids
        excel_only = excel_ids - db_ids
        db_only = db_ids - excel_ids
        
        print(f"\n🔍 Análise de IDs:")
        print(f"   🤝 IDs em ambos: {len(common_ids):,}")
        print(f"   📋 Apenas no Excel: {len(excel_only):,}")
        print(f"   🗄️  Apenas no Banco: {len(db_only):,}")
        
        # Mostrar alguns exemplos
        if excel_only:
            print(f"\n📋 Exemplos de IDs apenas no Excel:")
            examples = list(excel_only)[:5]
            print(f"   {examples}")
        
        if db_only:
            print(f"\n🗄️  Exemplos de IDs apenas no Banco:")
            examples = list(db_only)[:5]
            print(f"   {examples}")
        
        return {
            'id_column': id_column,
            'excel_ids': excel_ids,
            'db_ids': db_ids,
            'common_ids': common_ids,
            'excel_only': excel_only,
            'db_only': db_only
        }
    else:
        print(f"\n⚠️  Não foi possível identificar coluna de ID no Excel")
        return None

def analyze_active_status(df_excel, df_db, comparison_data):
    """Analisa status ativo/inativo"""
    print(f"\n📊 ANÁLISE DE STATUS ATIVO/INATIVO")
    print("=" * 60)
    
    # Verificar coluna de status no Excel
    status_columns = []
    for col in df_excel.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['ativo', 'active', 'status']):
            status_columns.append(col)
    
    if status_columns:
        print(f"📌 Colunas de status encontradas no Excel: {status_columns}")
        
        for status_col in status_columns:
            print(f"\n🔍 Análise da coluna '{status_col}':")
            value_counts = df_excel[status_col].value_counts()
            print(f"   Distribuição de valores:")
            for value, count in value_counts.items():
                print(f"     {value}: {count:,} ({count/len(df_excel)*100:.1f}%)")
    
    # Análise do banco
    print(f"\n🗄️  Status no banco de dados:")
    db_active_counts = df_db['active'].value_counts()
    for value, count in db_active_counts.items():
        status_text = "Ativo" if value == 1 else "Inativo"
        print(f"   {status_text} ({value}): {count:,} ({count/len(df_db)*100:.1f}%)")

def generate_detailed_report(df_excel, df_db, comparison_data):
    """Gera relatório detalhado"""
    print(f"\n📋 GERANDO RELATÓRIO DETALHADO")
    print("=" * 60)
    
    # Criar relatório
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'excel_file': 'equipamentos_23_07_2025.xlsx',
        'excel_records': len(df_excel),
        'database_records': len(df_db),
        'difference': len(df_db) - len(df_excel)
    }
    
    if comparison_data:
        report.update({
            'common_ids': len(comparison_data['common_ids']),
            'excel_only_ids': len(comparison_data['excel_only']),
            'database_only_ids': len(comparison_data['db_only']),
            'match_percentage': len(comparison_data['common_ids']) / max(len(comparison_data['excel_ids']), len(comparison_data['db_ids'])) * 100
        })
    
    # Salvar relatório em CSV
    try:
        # Relatório resumido
        report_df = pd.DataFrame([report])
        report_df.to_csv('relatorio_excel_vs_banco.csv', index=False)
        print(f"✅ Relatório resumido salvo: relatorio_excel_vs_banco.csv")
        
        # Se temos dados de comparação, salvar detalhes
        if comparison_data:
            # IDs apenas no Excel
            if comparison_data['excel_only']:
                excel_only_df = pd.DataFrame(list(comparison_data['excel_only']), columns=['id_apenas_excel'])
                excel_only_df.to_csv('ids_apenas_excel.csv', index=False)
                print(f"✅ IDs apenas no Excel salvos: ids_apenas_excel.csv")
            
            # IDs apenas no Banco
            if comparison_data['db_only']:
                db_only_df = pd.DataFrame(list(comparison_data['db_only']), columns=['id_apenas_banco'])
                db_only_df.to_csv('ids_apenas_banco.csv', index=False)
                print(f"✅ IDs apenas no Banco salvos: ids_apenas_banco.csv")
        
    except Exception as e:
        print(f"⚠️  Erro ao salvar relatórios: {e}")
    
    return report

def main():
    """Função principal"""
    print("🚀 ANÁLISE COMPLETA: EXCEL vs BANCO DE DADOS")
    print("=" * 70)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar se os arquivos existem
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
        
        # 2. Analisar estrutura do Excel
        key_columns = analyze_excel_structure(df_excel)
        
        # 3. Comparar datasets
        comparison_data = compare_datasets(df_excel, df_db)
        
        # 4. Analisar status ativo/inativo
        analyze_active_status(df_excel, df_db, comparison_data)
        
        # 5. Gerar relatório detalhado
        report = generate_detailed_report(df_excel, df_db, comparison_data)
        
        # 6. Resumo final
        print(f"\n" + "=" * 70)
        print(f"✅ ANÁLISE CONCLUÍDA!")
        print(f"📊 Excel: {len(df_excel):,} registros")
        print(f"🗄️  Banco: {len(df_db):,} registros")
        if comparison_data:
            print(f"🤝 Correspondência: {len(comparison_data['common_ids']):,} IDs")
            print(f"📈 Taxa de correspondência: {report.get('match_percentage', 0):.1f}%")
        print(f"⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
