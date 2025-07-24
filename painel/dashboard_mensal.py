import streamlit as st
import sqlite3
import pandas as pd
import json
import os
from datetime import date, timedelta
from calendar import monthrange
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Dashboard Preventivas Semestrais",
    page_icon="📊",
    layout="wide"
)

# Caminhos dos bancos de dados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_TAREFAS = os.path.join(BASE_DIR, "data", "tarefas.sqlite3")
DB_EQUIPAMENTOS = os.path.join(BASE_DIR, "data", "db.sqlite3")
DB_CLIENTES = os.path.join(BASE_DIR, "data", "clientes_por_grupo.sqlite3")

if not all([
    os.path.exists(DB_TAREFAS),
    os.path.exists(DB_EQUIPAMENTOS),
    os.path.exists(DB_CLIENTES),
]):
    st.error("❌ Um ou mais bancos de dados necessários não foram encontrados.")
    st.stop()

@st.cache_data
def carregar_tarefas():
    conn = sqlite3.connect(DB_TAREFAS)
    df = pd.read_sql("SELECT * FROM tarefas_raw", conn)
    df["json"] = df["json"].apply(json.loads)
    conn.close()
    return df

@st.cache_data
def carregar_equipamentos():
    conn = sqlite3.connect(DB_EQUIPAMENTOS)
    df = pd.read_sql(
        "SELECT id, name, associated_customer_id, identificador FROM equipamentos WHERE ativo = 1",
        conn,
    )
    conn.close()
    return df

@st.cache_data
def carregar_clientes_por_setor():
    conn = sqlite3.connect(DB_CLIENTES)
    setores = {
        "Setor 1": pd.read_sql("SELECT id FROM clientes_grupo_156750", conn)["id"].tolist(),
        "Setor 2": pd.read_sql("SELECT id FROM clientes_grupo_156751", conn)["id"].tolist(),
        "Setor 3": pd.read_sql("SELECT id FROM clientes_grupo_156752", conn)["id"].tolist(),
        "Setor 4": pd.read_sql("SELECT id FROM clientes_grupo_156753", conn)["id"].tolist(),
        "Setor 5": pd.read_sql("SELECT id FROM clientes_grupo_156754", conn)["id"].tolist(),
    }
    conn.close()
    return setores

def processar_dados_tarefas(df_raw):
    df = pd.DataFrame([
        {
            "taskID": row["taskID"],
            "data": row["data_referencia"],
            "escola": row["json"].get("customerDescription"),
            "customer_id": row["json"].get("customerId"),
            "tipo": row["json"].get("taskTypeDescription"),
            "status_id": row["json"].get("taskStatus"),
            "equipamentos_id": row["json"].get("equipmentsId"),
            "questionarios": row["json"].get("questionnaires"),
            "deliveredDate": row["json"].get("deliveredDate", ""),
            "deliveredOnSmarthPhone": row["json"].get("deliveredOnSmarthPhone", False),
        }
        for _, row in df_raw.iterrows()
    ])
    # Filtrar tarefas inválidas
    df = df[~((df["deliveredOnSmarthPhone"] == True) & (df["deliveredDate"] == "0001-01-01T00:00:00"))]
    # Converter status
    df["status"] = df["status_id"].map({
        1: "Aberta",
        2: "Em Deslocamento",
        3: "Check-in",
        4: "Check-out",
        5: "Finalizada",
        6: "Pausada",
    }).fillna("Desconhecido")
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df

def detalhar_tarefas_semestrais(tarefas, equipamentos_df):
    detalhes = []
    for _, row in tarefas.iterrows():
        escola = row["escola"]
        data = row["data"]
        equipamentos_esperados = row["equipamentos_id"] or []
        questionarios = row.get("questionarios") or []
        equipamentos_respondidos = set()
        for q in questionarios:
            eq_id = q.get("questionnaireEquipamentId")
            if eq_id:
                equipamentos_respondidos.add(eq_id)
        df_respondidos = equipamentos_df[equipamentos_df["id"].isin(equipamentos_respondidos)]
        detalhes.append({
            "escola": escola,
            "data": data,
            "df_respondidos": df_respondidos
        })
    return detalhes

# Interface principal
st.title("📊 Preventivas Mensais - Lista Detalhada")

# Carregar dados
with st.spinner("🔄 Carregando dados..."):
    df_raw = carregar_tarefas()
    equipamentos_df = carregar_equipamentos()
    clientes_por_setor = carregar_clientes_por_setor()
    df = processar_dados_tarefas(df_raw)

# Adicionar opção 'Todos os setores'
setores_opcoes = ['Todos os setores'] + list(clientes_por_setor.keys())
setor_escolhido = st.selectbox("🏫 Escolha o setor", setores_opcoes)

if setor_escolhido == 'Todos os setores':
    clientes_do_setor = [cid for lista in clientes_por_setor.values() for cid in lista]
else:
    clientes_do_setor = clientes_por_setor[setor_escolhido]

df = df[df["customer_id"].isin(clientes_do_setor)]

# Remover seleção de status e tipo, deixar fixo
status_filtro = ["Finalizada"]
# Filtro robusto: qualquer tarefa cujo tipo contenha 'Preventiva Mensal'

hoje = date.today()
ano, mes = hoje.year, hoje.month
primeiro_dia_mes = date(ano, mes, 1)
ultimo_dia_mes = date(ano, mes, monthrange(ano, mes)[1])

col4, col5, _ = st.columns(3)
hoje = date.today()
primeiro_dia_mes = date(hoje.year, hoje.month, 1)
ultimo_dia_mes = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
with col4:
    data_ini = st.date_input("📅 De", value=primeiro_dia_mes)
with col5:
    data_fim = st.date_input("📅 Até", value=ultimo_dia_mes)

st.markdown(
    f"🗓️ **Período Selecionado:** {data_ini.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
)

df_filt = df[
    df["status"].isin(status_filtro)
    & df["tipo"].str.contains("Preventiva Mensal", case=False, na=False)
    & (df["data"] >= data_ini)
    & (df["data"] <= data_fim)
]

# --- CONSOLIDADO POR SETOR E GERAL ---
st.markdown("---")
st.subheader("Consolidado por Setor e Geral - Preventiva Mensal")

consolidado = []
equipamentos_feitos_geral = set()
equipamentos_esperados_geral = set()

for setor, clientes in clientes_por_setor.items():
    df_setor = df_raw.copy()
    df_setor = processar_dados_tarefas(df_setor)
    df_setor = df_setor[df_setor["customer_id"].isin(clientes)]
    df_setor = df_setor[
        (df_setor["status"] == "Finalizada") &
        (df_setor["tipo"].str.contains("Preventiva Mensal", case=False, na=False)) &
        (df_setor["data"] >= data_ini) & (df_setor["data"] <= data_fim)
    ]
    equipamentos_setor = equipamentos_df[equipamentos_df["associated_customer_id"].isin(clientes)]
    equipamentos_esperados = set(equipamentos_setor["id"].unique())
    equipamentos_feitos = set()
    for _, row in df_setor.iterrows():
        questionarios = row.get("questionarios") or []
        for q in questionarios:
            eq_id = q.get("questionnaireEquipamentId")
            if eq_id:
                equipamentos_feitos.add(eq_id)
    equipamentos_nao_feitos = equipamentos_esperados - equipamentos_feitos
    consolidado.append({
        "Setor": setor,
        "Total Equipamentos Esperados": len(equipamentos_esperados),
        "Total Equipamentos Feitos": len(equipamentos_feitos),
        "Total Equipamentos Não Feitos": len(equipamentos_nao_feitos),
        "IDs Feitos": equipamentos_feitos,
        "IDs Não Feitos": equipamentos_nao_feitos
    })
    equipamentos_feitos_geral.update(equipamentos_feitos)
    equipamentos_esperados_geral.update(equipamentos_esperados)

# Consolidado geral
equipamentos_nao_feitos_geral = equipamentos_esperados_geral - equipamentos_feitos_geral
consolidado.append({
    "Setor": "Todos",
    "Total Equipamentos Esperados": len(equipamentos_esperados_geral),
    "Total Equipamentos Feitos": len(equipamentos_feitos_geral),
    "Total Equipamentos Não Feitos": len(equipamentos_nao_feitos_geral),
    "IDs Feitos": equipamentos_feitos_geral,
    "IDs Não Feitos": equipamentos_nao_feitos_geral
})

# Exibir tabela resumo
st.dataframe(pd.DataFrame([
    {k: v for k, v in d.items() if not k.startswith('IDs')}
    for d in consolidado
]))

# Exibir listas detalhadas organizadas em expansores
for d in consolidado:
    setor_atual = d['Setor']
    st.markdown(f"## Setor: {setor_atual}")

    # --- Botões de Download e Faturar ---
    col_csv, col_excel, col_faturar = st.columns(3)

    # Preparar dados para CSV/Excel (SOMENTE NÃO Feitos)
    csv_data = []
    
    # Agrupar IDs Não Feitos por escola
    nao_feitos_por_escola_export = {}
    for eq in sorted(list(d['IDs Não Feitos'])):
        eq_row = equipamentos_df[equipamentos_df['id'] == eq]
        identificador = eq_row['identificador'].values[0] if not eq_row.empty and pd.notna(eq_row['identificador'].values[0]) else f"ID {eq}"
        nome_equipamento = eq_row['name'].values[0] if not eq_row.empty else f"Nome Desconhecido (ID {eq})"
        escola_nome = ""
        customer_id = eq_row['associated_customer_id'].values[0] if not eq_row.empty and pd.notna(eq_row['associated_customer_id'].values[0]) else None
        if customer_id:
             tarefa = df_raw[df_raw['json'].apply(lambda x: x.get('customerId') == customer_id)].head(1)
             if not tarefa.empty:
                 escola_nome = tarefa.iloc[0]['json'].get('customerDescription', '')
        
        if escola_nome not in nao_feitos_por_escola_export:
            nao_feitos_por_escola_export[escola_nome] = []
        # Armazenar identificador e nome do equipamento
        nao_feitos_por_escola_export[escola_nome].append({
            "Identificador": identificador, 
            "Equipamento": nome_equipamento
        })

    # Criar a estrutura para o Excel/CSV com a hierarquia
    excel_csv_linhas = []
    for escola, equipamentos_lista in nao_feitos_por_escola_export.items():
        # Adicionar linha da escola
        excel_csv_linhas.append({
            "Escola/Equipamento": escola, 
            "Identificador": "", 
            "Status": "",
            "Nível": 0 # Nível 0 para a escola
        })
        # Adicionar linhas dos equipamentos
        for eq_info in equipamentos_lista:
            # Buscar o link da tarefa associada a este equipamento
            eq_id = eq_info["Identificador"] if eq_info["Identificador"].startswith("ID ") else None
            link_tarefa = ""
            if eq_id:
                # Extrair apenas o número do ID
                id_num = int(eq_id.replace("ID ", ""))
                tarefa_row = df_raw[df_raw['json'].apply(lambda x: id_num in (x.get('equipmentsId') or []))]
                if not tarefa_row.empty:
                    link_tarefa = tarefa_row.iloc[0]['json'].get('taskUrl', '')
            excel_csv_linhas.append({
                "Escola/Equipamento": eq_info["Equipamento"], 
                "Identificador": eq_info["Identificador"], 
                "Status": "Não Feito",
                "Link": link_tarefa,
                "Nível": 1 # Nível 1 para o equipamento
            })

    df_export_final = pd.DataFrame(excel_csv_linhas)

    # Gerar CSV
    # Remover coluna 'Nível' para o CSV
    csv_string = df_export_final.drop(columns=['Nível'], errors='ignore').to_csv(index=False, sep=',')
    file_name_csv = f"preventivas_semestrais_{setor_atual.lower().replace(' ','_')}_nao_feitos.csv"

    with col_csv:
        st.download_button(
            label=f"⬇️ Gerar CSV Não Feitos ({setor_atual})",
            data=csv_string,
            file_name=file_name_csv,
            mime="text/csv",
            key=f"csv_nao_feitos_button_{setor_atual}"
        )

    # Gerar Excel com formatação
    file_name_excel = f"preventivas_semestrais_{setor_atual.lower().replace(' ','_')}_nao_feitos.xlsx"

    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
         df_export_final.to_excel(writer, sheet_name='Não Feitos', index=False, startrow=1, header=False) # Remover header padrão

         workbook = writer.book
         worksheet = writer.sheets['Não Feitos']

         # Formatos
         header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
         escola_format = workbook.add_format({'bold': True})

         # Escrever cabeçalho manual
         worksheet.write_row(0, 0, ['Escola/Equipamento', 'Identificador', 'Status'], header_format)

         # Aplicar formatação e agrupamento
         for row_num, row_data in df_export_final.iterrows():
              nivel = row_data['Nível']
              if nivel == 0: # Escola
                  worksheet.write(row_num + 1, 0, row_data['Escola/Equipamento'], escola_format) # +1 por causa do header manual
                  # Aplicar agrupamento (outline)
                  worksheet.set_row(row_num + 1, None, None, {'level': 0})
              else: # Equipamento
                  worksheet.write_row(row_num + 1, 0, row_data[['Escola/Equipamento', 'Identificador', 'Status', 'Link']].tolist()) # +1 por causa do header manual
                  worksheet.set_row(row_num + 1, None, None, {'level': 1, 'hidden': True, 'collapsed': True})

         # Ajustar largura das colunas
         worksheet.set_column('A:A', 40)
         worksheet.set_column('B:B', 25)
         worksheet.set_column('C:C', 15)

         # Ativar agrupamento (outline)
         worksheet.outline_settings(True, False, True, True)


    with col_excel:
         st.download_button(
             label=f"⬇️ Gerar Excel Não Feitos ({setor_atual})",
             data=output_excel.getvalue(),
             file_name=file_name_excel,
             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             key=f"excel_nao_feitos_button_{setor_atual}"
         )

    # --- Botão Faturar (Download Excel de Feitos) ---
    # Preparar dados para Excel de FEITOS (finalizadas)
    feitos_por_escola_export = {}
    for eq in sorted(list(d['IDs Feitos'])):
        eq_row = equipamentos_df[equipamentos_df['id'] == eq]
        identificador = eq_row['identificador'].values[0] if not eq_row.empty and pd.notna(eq_row['identificador'].values[0]) else f"ID {eq}"
        nome_equipamento = eq_row['name'].values[0] if not eq_row.empty else f"Nome Desconhecido (ID {eq})"
        escola_nome = ""
        customer_id = eq_row['associated_customer_id'].values[0] if not eq_row.empty and pd.notna(eq_row['associated_customer_id'].values[0]) else None
        if customer_id:
            tarefa = df_raw[df_raw['json'].apply(lambda x: x.get('customerId') == customer_id and eq in (x.get('equipmentsId') or []) and str(x.get('taskTypeDescription','')).lower().find('preventiva mensal') != -1 and x.get('taskStatus') == 5)].head(1)
            if not tarefa.empty:
                escola_nome = tarefa.iloc[0]['json'].get('customerDescription', '')
        if escola_nome not in feitos_por_escola_export:
            feitos_por_escola_export[escola_nome] = []
        feitos_por_escola_export[escola_nome].append({
            "Identificador": identificador,
            "Equipamento": nome_equipamento
        })

    # Estrutura para Excel igual à de não feitos
    excel_csv_linhas_feitos = []
    # Adicionar linha de total logo após o cabeçalho
    quantidade_feitos = len(d['IDs Feitos'])
    excel_csv_linhas_feitos.append({
        "Escola/Equipamento": "Total de equipamentos",
        "Identificador": quantidade_feitos,
        "Status": "",
        "Link": "",
        "Nível": -1
    })
    for escola, equipamentos_lista in feitos_por_escola_export.items():
        excel_csv_linhas_feitos.append({
            "Escola/Equipamento": escola,
            "Identificador": "",
            "Status": "",
            "Nível": 0
        })
        for eq_info in equipamentos_lista:
            # Buscar o ID real do equipamento a partir do nome do equipamento
            # eq_info["Identificador"] pode ser string, mas eq é o ID real
            link_tarefa = ""
            # Procurar o equipamento na lista de feitos_por_escola_export para obter o ID real
            eq_real_id = None
            for eq in d['IDs Feitos']:
                eq_row = equipamentos_df[equipamentos_df['id'] == eq]
                identificador = eq_row['identificador'].values[0] if not eq_row.empty and pd.notna(eq_row['identificador'].values[0]) else f"ID {eq}"
                if identificador == eq_info["Identificador"]:
                    eq_real_id = eq
                    break
            if eq_real_id is not None:
                tarefa_row = df_raw[df_raw['json'].apply(lambda x: eq_real_id in (x.get('equipmentsId') or []) and str(x.get('taskTypeDescription','')).lower().find('preventiva mensal') != -1 and x.get('taskStatus') == 5)]
                if not tarefa_row.empty:
                    link_tarefa = tarefa_row.iloc[0]['json'].get('taskUrl', '')
            excel_csv_linhas_feitos.append({
                "Escola/Equipamento": eq_info["Equipamento"],
                "Identificador": eq_info["Identificador"],
                "Status": "Feito",
                "Link": link_tarefa,
                "Nível": 1
            })
    df_export_feitos = pd.DataFrame(excel_csv_linhas_feitos)
    quantidade_feitos = len(d['IDs Feitos'])
    file_name_excel_feitos = f"preventivas_semestrais_{setor_atual.lower().replace(' ','_')}_feitos_{quantidade_feitos}_equipamentos.xlsx"
    output_excel_feitos = BytesIO()
    with pd.ExcelWriter(output_excel_feitos, engine='xlsxwriter') as writer:
        df_export_feitos.to_excel(writer, sheet_name='Feitos', index=False, startrow=1, header=False)
        workbook = writer.book
        worksheet = writer.sheets['Feitos']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
        escola_format = workbook.add_format({'bold': True})
        worksheet.write_row(0, 0, ['Escola/Equipamento', 'Identificador', 'Status', 'Link'], header_format)
        for row_num, row_data in df_export_feitos.iterrows():
            nivel = row_data['Nível']
            if nivel == -1:
                # Linha de total
                worksheet.write_row(row_num + 1, 0, [row_data['Escola/Equipamento'], row_data['Identificador'], '', ''], header_format)
                worksheet.set_row(row_num + 1, None, None, {'level': 0})
            elif nivel == 0:
                worksheet.write(row_num + 1, 0, row_data['Escola/Equipamento'], escola_format)
                worksheet.set_row(row_num + 1, None, None, {'level': 0})
            else:
                worksheet.write_row(row_num + 1, 0, row_data[['Escola/Equipamento', 'Identificador', 'Status', 'Link']].tolist())
                worksheet.set_row(row_num + 1, None, None, {'level': 1, 'hidden': True, 'collapsed': True})
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 40)
        worksheet.outline_settings(True, False, True, True)
    with col_faturar:
        st.download_button(
            label=f"💰 Faturar (Excel Feitos - {setor_atual}) ({quantidade_feitos} equipamentos)",
            data=output_excel_feitos.getvalue(),
            file_name=file_name_excel_feitos,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_feitos_button_{setor_atual}"
        )

    # --- Expansores de Listas (Feitos/Não Feitos) ---
    # --- Feitos ---
    if len(d['IDs Feitos']) > 0:
        st.markdown('''<div style="background: #16281e; border: 1.5px solid #27ae60; border-radius: 8px; padding: 18px 18px 8px 18px; margin-bottom: 18px;">
        <span style="color: #27ae60; font-size: 1.1em; font-weight: bold;">Equipamentos Concluídos</span>''', unsafe_allow_html=True)
        with st.expander(f"Equipamentos Feitos ({len(d['IDs Feitos'])})"):
            feitos_por_escola = {}
            for eq in d['IDs Feitos']:
                eq_row = equipamentos_df[equipamentos_df['id'] == eq]
                nome_equipamento = eq_row['name'].values[0] if not eq_row.empty else f"ID {eq}"
                identificador = eq_row['identificador'].values[0] if not eq_row.empty else f"ID {eq}"
                escola_nome = ""
                # Buscar tarefa feita do tipo Preventiva Mensal para este equipamento (robusto)
                tarefa = df_raw[df_raw['json'].apply(lambda x: eq in (x.get('equipmentsId') or []) and str(x.get('taskTypeDescription','')).lower().find('preventiva mensal') != -1 and x.get('taskStatus') == 5)]
                if not tarefa.empty:
                    escola_nome = tarefa.iloc[0]['json'].get('customerDescription', '')
                if escola_nome not in feitos_por_escola:
                    feitos_por_escola[escola_nome] = []
                link_tarefa = ""
                if not tarefa.empty:
                    link_tarefa = tarefa.iloc[0]['json'].get('taskUrl', '')
                feitos_por_escola[escola_nome].append({
                    "texto": f"{identificador}, \"{nome_equipamento}\"",
                    "link": link_tarefa
                })
            if feitos_por_escola:
                for escola, lista in feitos_por_escola.items():
                    # Buscar o primeiro link válido da lista de equipamentos daquela escola
                    link_tarefa = ""
                    for item in lista:
                        if item["link"]:
                            link_tarefa = item["link"]
                            break
                    if link_tarefa:
                        link_html = f' <a href="{link_tarefa}" target="_blank" style="color:#27ae60; font-weight:normal; text-decoration:underline;">🔗 Ver tarefa</a>'
                    else:
                        link_html = ""
                    html_escola = f"<details><summary><span style=\"font-weight:bold;\">{escola}</span>{link_html} <span>({len(lista)})</span></summary><ul>"
                    for item in lista:
                        item_escaped = item["texto"].replace('"', '&quot;')
                        html_escola += f"<li>{item_escaped}</li>"
                    html_escola += "</ul></details>"
                    st.markdown(html_escola, unsafe_allow_html=True)
            else:
                st.write("Nenhum equipamento feito.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        with st.expander(f"Equipamentos Feitos (0)"):
            st.write("Nenhum equipamento feito.")
        feitos_por_escola = {}
        for eq in d['IDs Feitos']:
            eq_row = equipamentos_df[equipamentos_df['id'] == eq]
            nome_equipamento = eq_row['name'].values[0] if not eq_row.empty else f"ID {eq}"
            identificador = eq_row['identificador'].values[0] if not eq_row.empty else f"ID {eq}"
            escola_nome = ""
            tarefa = df_raw[df_raw['json'].apply(lambda x: eq in (x.get('equipmentsId') or []))]
            if not tarefa.empty:
                escola_nome = tarefa.iloc[0]['json'].get('customerDescription', '')
            if escola_nome not in feitos_por_escola:
                feitos_por_escola[escola_nome] = []
            feitos_por_escola[escola_nome].append({
                "texto": f"{identificador}, \"{nome_equipamento}\"",
                "link": ""
            })
        if feitos_por_escola:
            for escola, lista in feitos_por_escola.items():
                # Buscar o primeiro link válido da lista de equipamentos daquela escola
                link_tarefa = ""
                for item in lista:
                    if item["link"]:
                        link_tarefa = item["link"]
                        break
                if link_tarefa:
                    link_html = f' <a href="{link_tarefa}" target="_blank" style="color:#27ae60; font-weight:normal; text-decoration:underline;">🔗 Ver tarefa</a>'
                else:
                    link_html = ""
                html_escola = f"<details><summary><span style=\"font-weight:bold;\">{escola}</span>{link_html} <span>({len(lista)})</span></summary><ul>"
                for item in lista:
                    item_escaped = item["texto"].replace('"', '&quot;')
                    html_escola += f"<li>{item_escaped}</li>"
                html_escola += "</ul></details>"
                st.markdown(html_escola, unsafe_allow_html=True)
        else:
            st.write("Nenhum equipamento feito.")
    # --- Não Feitos ---
    if len(d['IDs Não Feitos']) > 0:
        st.markdown('''<div style="background: #2d1a1a; border: 1.5px solid #e74c3c; border-radius: 8px; padding: 18px 18px 8px 18px; margin-bottom: 18px;">
        <span style="color: #e74c3c; font-size: 1.1em; font-weight: bold;">Equipamentos não concluídos</span>''', unsafe_allow_html=True)
        with st.expander(f"Equipamentos Não Feitos ({len(d['IDs Não Feitos'])})"):
            nao_feitos_por_escola = {}
            for eq in d['IDs Não Feitos']:
                eq_row = equipamentos_df[equipamentos_df['id'] == eq]
                nome_equipamento = eq_row['name'].values[0] if not eq_row.empty else f"ID {eq}"
                identificador = eq_row['identificador'].values[0] if not eq_row.empty else f"ID {eq}"
                escola_nome = ""
                tarefa = df_raw[df_raw['json'].apply(lambda x: eq in (x.get('equipmentsId') or []))]
                if not tarefa.empty:
                    escola_nome = tarefa.iloc[0]['json'].get('customerDescription', '')
                if escola_nome not in nao_feitos_por_escola:
                    nao_feitos_por_escola[escola_nome] = []
                link_tarefa = ""
                if not tarefa.empty:
                    link_tarefa = tarefa.iloc[0]['json'].get('taskUrl', '')
                nao_feitos_por_escola[escola_nome].append({
                    "texto": f"{identificador}, \"{nome_equipamento}\"",
                    "link": link_tarefa
                })
            if nao_feitos_por_escola:
                for escola, lista in nao_feitos_por_escola.items():
                    html_escola = f"<details><summary><span style=\"font-weight:bold;\">{escola}</span> <span>({len(lista)})</span></summary><ul>"
                    for item in lista:
                        item_escaped = item["texto"].replace('"', '&quot;')
                        html_escola += f"<li>{item_escaped}</li>"
                    html_escola += "</ul></details>"
                    st.markdown(html_escola, unsafe_allow_html=True)
            else:
                st.write("Nenhum equipamento pendente.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        with st.expander(f"Equipamentos Não Feitos (0)"):
            st.write("Nenhum equipamento pendente.")
