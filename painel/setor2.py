import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import plotly.graph_objects as go
from datetime import date
from calendar import monthrange
import re
from collections import Counter
import pydeck as pdk
import pandas as pd
from io import BytesIO
import xlsxwriter
import matplotlib.pyplot as plt
import altair as alt

# Configuração da página
st.set_page_config(
    page_title="Painel Técnico – Todos os Setores",
    page_icon="📌",
    layout="wide"
)

# Adicionar CSS para detecção automática de tema
st.markdown("""
<style>
    /* Variáveis CSS para cores adaptativas */
    :root {
        --text-color: #333333;
        --background-color: #ffffff;
    }
    
    /* Detecção automática de tema escuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #ffffff;
            --background-color: #1e1e1e;
        }
    }
    
    /* Classe para texto adaptativo que funciona em ambos os temas */
    .adaptive-text {
        color: var(--text-color) !important;
    }
</style>
""", unsafe_allow_html=True)

# Caminhos absolutos dos bancos de dados para uso no servidor Linux
DB_TAREFAS = os.path.join("..", "data", "tarefas.sqlite3")
DB_USUARIOS = os.path.join("..", "data", "usuarios.sqlite3")
DB_EQUIPAMENTOS = os.path.join("..", "data", "db.sqlite3")
DB_CLIENTES = os.path.join("..", "data", "clientes_por_grupo.sqlite3")


# Adicionar CSS personalizado
st.markdown("""
<style>
    /* Estilo para os cards de manutenção */
    .mensal-card {
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        background-color: rgba(46, 204, 113, 0.1);  /* Verde com 10% de opacidade */
        border-left: 5px solid #2ecc71;  /* Verde */
    }
    
    .semestral-card {
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        background-color: rgba(230, 126, 34, 0.1);  /* Laranja com 10% de opacidade */
        border-left: 5px solid #e67e22;  /* Laranja */
    }
    
    .corretiva-card {
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        background-color: rgba(52, 152, 219, 0.1);  /* Azul com 10% de opacidade */
        border-left: 5px solid #3498db;  /* Azul */
    }
    
    .card-title {
        font-weight: bold;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.2em;
    }
    
    .card-content {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏷️ Painel Técnico – Setor 2")

if not all(
    [
        os.path.exists(DB_TAREFAS),
        os.path.exists(DB_USUARIOS),
        os.path.exists(DB_EQUIPAMENTOS),
        os.path.exists(DB_CLIENTES),
    ]
):
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
def carregar_usuarios():
    conn = sqlite3.connect(DB_USUARIOS)
    df = pd.read_sql("SELECT user_id, nome FROM usuarios", conn)
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
        "Setor 1": pd.read_sql("SELECT id FROM clientes_grupo_156750", conn)[
            "id"
        ].tolist(),
        "Setor 2": pd.read_sql("SELECT id FROM clientes_grupo_156751", conn)[
            "id"
        ].tolist(),
        "Setor 3": pd.read_sql("SELECT id FROM clientes_grupo_156752", conn)[
            "id"
        ].tolist(),
        "Setor 4": pd.read_sql("SELECT id FROM clientes_grupo_156753", conn)[
            "id"
        ].tolist(),
        "Setor 5": pd.read_sql("SELECT id FROM clientes_grupo_156754", conn)[
            "id"
        ].tolist(),
    }
    conn.close()
    return setores


TIPOS_FIXOS = ["Preventiva Semestral", "Preventiva Mensal", "Corretiva", "Preventiva Levantamento de PMOC"]

with st.spinner("🔄 Carregando dados..."):
    df_raw = carregar_tarefas()
    df_usuarios = carregar_usuarios()
    equipamentos_df = carregar_equipamentos()
    equipamentos_dict = {}
    for _, row in equipamentos_df.iterrows():
        if row.get('identificador') and str(row['identificador']).strip():
            equipamentos_dict[row['id']] = f"{row['identificador']} - {row['name']}"
        else:
            equipamentos_dict[row['id']] = row['name']
    clientes_por_setor = carregar_clientes_por_setor()

    df = pd.DataFrame(
        [
            {
                "taskID": row["taskID"],
                "user_id": row["user_id"],
                "data": row["data_referencia"],
                "escola": row["json"].get("customerDescription"),
                "customer_id": row["json"].get("customerId"),
                "tipo": row["json"].get("taskTypeDescription"),
                "status_id": row["json"].get("taskStatus"),
                "checkin": row["json"].get("checkIn"),
                "checkout": row["json"].get("checkOut"),
                "assinatura": row["json"].get("signatureName"),
                "observacao": row["json"].get("report"),
                "equipamentos_id": row["json"].get("equipmentsId"),
                "questionarios": row["json"].get("questionnaires"),
                "taskUrl": row["json"].get("taskUrl"),
                "deliveredDate": row["json"].get("deliveredDate", ""),
                "deliveredOnSmarthPhone": row["json"].get(
                    "deliveredOnSmarthPhone", False
                ),
            }
            for _, row in df_raw.iterrows()
        ]
    )
    # ✅ Filtro oficial para ignorar tarefas inválidas ou canceladas
    df = df[
        ~(
            (df["deliveredOnSmarthPhone"] == True)
            & (df["deliveredDate"] == "0001-01-01T00:00:00")
        )
    ]

    df["status"] = (
        df["status_id"]
        .map(
            {
                1: "Aberta",
                2: "Em Deslocamento",
                3: "Check-in",
                4: "Check-out",
                5: "Finalizada",
                6: "Pausada",
            }
        )
        .fillna("Desconhecido")
    )

    df = pd.merge(df, df_usuarios, how="left", on="user_id")
    df["data"] = pd.to_datetime(df["data"]).dt.date

setor_escolhido = "Setor 2"
clientes_do_setor = clientes_por_setor[setor_escolhido]
df = df[df["customer_id"].isin(clientes_do_setor)]

col2, col3 = st.columns(2)
with col2:
    status_filtro = st.multiselect(
        "📌 Status",
        sorted(df["status"].dropna().unique()),
        default=sorted(df["status"].dropna().unique()),
    )
with col3:
    tipo_filtro = st.multiselect("🧰 Tipo da Tarefa", TIPOS_FIXOS, default=TIPOS_FIXOS)

hoje = date.today()
ano, mes = hoje.year, hoje.month
primeiro_dia_mes = date(ano, mes, 1)
ultimo_dia_mes = date(ano, mes, monthrange(ano, mes)[1])

col4, col5, _ = st.columns(3)
with col4:
    data_ini = st.date_input("📅 De", value=primeiro_dia_mes)
with col5:
    data_fim = st.date_input("📅 Até", value=ultimo_dia_mes)

st.markdown(
    f"🗓️ **Período Selecionado:** {data_ini.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
)

df_filt = df[
    df["status"].isin(status_filtro)
    & df["tipo"].apply(lambda x: any(t in x for t in tipo_filtro if isinstance(x, str)))
    & (df["data"] >= data_ini)
    & (df["data"] <= data_fim)
]

# Filtro visual para remover tarefas duplicadas por escola+equipamento
if not df_filt.empty:
    # Cria coluna auxiliar para deduplicação
    def get_first_equip_id(equip):
        if isinstance(equip, list) and equip:
            return str(equip[0])
        return str(equip) if equip is not None else ''
    df_filt["equipamento_id_unico"] = df_filt["equipamentos_id"].apply(get_first_equip_id)
    df_filt = df_filt.drop_duplicates(subset=["escola", "equipamento_id_unico"])


# Função para contar equipamentos respondidos
def contar_equipamentos_respondidos(df_status):
    return sum(
        len(
            {
                q.get("questionnaireEquipamentId")
                for q in row["questionarios"]
                if q.get("questionnaireEquipamentId")
            }
        )
        for _, row in df_status.iterrows()
    )


# Equipamentos finalizados (respondidos em tarefas finalizadas)
finalizadas = contar_equipamentos_respondidos(
    df_filt[df_filt["status"] == "Finalizada"]
)

# Equipamentos em pausa (respondidos em tarefas pausadas)
pausadas = contar_equipamentos_respondidos(df_filt[df_filt["status"] == "Pausada"])

# Equipamentos em aberto (esperados em tarefas nem finalizadas nem pausadas)
em_aberto = sum(
    len(row["equipamentos_id"] or [])
    for _, row in df_filt[~df_filt["status"].isin(["Finalizada", "Pausada"])].iterrows()
)

# Exibir no painel
st.info(
    f"📊 Equipamentos Finalizados: **{finalizadas}** | Em Pausa: **{pausadas}** | Em Aberto: **{em_aberto}**"
)


# --- NOVA LÓGICA DE PREVENTIVA MENSAL E SEMESTRAL ---
# Total de equipamentos das escolas do setor
qtde_equipamentos_setor = equipamentos_df[equipamentos_df["associated_customer_id"].isin(clientes_do_setor)]["id"].nunique()

# --- PREVENTIVA SEMESTRAL ---
# Total previsto = total de equipamentos // 6
semestral_previsto = qtde_equipamentos_setor // 6 if qtde_equipamentos_setor > 0 else 0
# Tarefas semestrais finalizadas
semestral_realizados = 0
# Filtra tarefas semestrais

df_semestral = df_filt[
    df_filt["tipo"].str.contains("Preventiva Semestral", case=False, na=False)
]
# Conta equipamentos únicos respondidos nas tarefas semestrais finalizadas
semestral_finalizadas = df_semestral[df_semestral["status"] == "Finalizada"]
ids_equipamentos_semestral = set()
# --- PREVENTIVA MENSAL ---
# Total previsto = total de equipamentos
mensal_previsto = qtde_equipamentos_setor
# Tarefas mensais finalizadas
mensal_realizados = 0
# Filtra tarefas mensais

# Processamento dos dados primeiro
df_mensal = df_filt[
    df_filt["tipo"].str.contains("Preventiva Mensal", case=False, na=False)
]

# Inicializa os conjuntos
ids_equipamentos_realizados = set()
ids_equipamentos_semestral = set()

# Conta equipamentos únicos respondidos nas tarefas mensais finalizadas
mensal_finalizadas = df_mensal[df_mensal["status"] == "Finalizada"]
for _, row in mensal_finalizadas.iterrows():
    if isinstance(row.get("questionarios"), list):
        ids_equipamentos_realizados.update(
            q.get("questionnaireEquipamentId")
            for q in row["questionarios"]
            if q.get("questionnaireEquipamentId")
        )
mensal_realizados = len(ids_equipamentos_realizados)

# Conta equipamentos únicos respondidos nas tarefas semestrais finalizadas
for _, row in semestral_finalizadas.iterrows():
    if isinstance(row.get("questionarios"), list):
        ids_equipamentos_semestral.update(
            q.get("questionnaireEquipamentId")
            for q in row["questionarios"]
            if q.get("questionnaireEquipamentId")
        )
semestral_realizados = len(ids_equipamentos_semestral)

# --- CARD RESUMO SUPERIOR ---
total_equipamentos = qtde_equipamentos_setor
total_previsto = semestral_previsto
total_mensal = total_equipamentos - total_previsto

# Card roxo responsivo, igual aos outros cards
st.markdown(
    f'''
    <style>
    @media (max-width: 900px) {{
        .resumo-roxo-grid {{
            flex-direction: column !important;
            gap: 12px !important;
            align-items: flex-start !important;
        }}
        .resumo-roxo-col {{
            min-width: unset !important;
            width: 100% !important;
        }}
    }}
    </style>
    <div style="padding:20px; border-radius:8px; margin-bottom:20px; background-color:rgba(142,68,173,0.12); border-left: 5px solid #8e44ad;">
        <div class="card-title" style="font-weight:bold; font-size:1.2em; color:#8e44ad; display:flex; align-items:center; gap:8px; margin-bottom:10px;">
            <span>📊 Resumo Equipamentos do Ciclo</span>
        </div>
        <div class="resumo-roxo-grid" style="display:flex; gap:40px; justify-content:center; align-items:center; flex-wrap:wrap;">
            <div class="resumo-roxo-col" style="flex:1; min-width:170px; text-align:center;">
                <span style="font-weight:600; color:#2ecc71;">📋 Total de Equipamentos</span><br>
                <span style="font-size:2em; font-weight:bold;">{total_equipamentos}</span>
            </div>
            <div class="resumo-roxo-col" style="flex:1; min-width:170px; text-align:center;">
                <span style="font-weight:600; color:#2ecc71;">📋 Total Mensal</span><br>
                <span style="font-size:2em; font-weight:bold;">{total_mensal}</span>
            </div>
            <div class="resumo-roxo-col" style="flex:1; min-width:170px; text-align:center;">
                <span style="font-weight:600; color:#2ecc71;">📋 Total Semestral</span><br>
                <span style="font-size:2em; font-weight:bold;">{total_previsto}</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# Cálculo correto: Total Equipamentos - Total Previsto (semestral_previsto) - Prev. Mensal Realizada
faltam_mensal = qtde_equipamentos_setor - semestral_previsto - mensal_realizados
label_faltam = "⚠️ Faltam Prev. Mensal"

# Conta equipamentos únicos respondidos nas tarefas semestrais finalizadas
for _, row in semestral_finalizadas.iterrows():
    if isinstance(row.get("questionarios"), list):
        ids_equipamentos_semestral.update(
            q.get("questionnaireEquipamentId")
            for q in row["questionarios"]
            if q.get("questionnaireEquipamentId")
        )
semestral_realizados = len(ids_equipamentos_semestral)

# Adicionar CSS para detecção automática de tema
st.markdown("""
<style>
    /* Variáveis CSS para cores adaptativas */
    :root {
        --text-color: #333333;
        --background-color: #ffffff;
    }
    
    /* Detecção automática de tema escuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #ffffff;
            --background-color: #1e1e1e;
        }
    }
    
    /* Classe para texto adaptativo que funciona em ambos os temas */
    .adaptive-text {
        color: var(--text-color) !important;
    }
</style>
""", unsafe_allow_html=True)

# Criação do card estilizado para Preventiva Mensal com as métricas dentro
st.markdown(f"""
<div class="mensal-card">
    <div class="card-title">
        <span></span>
        <span>Preventiva Mensal</span>
    </div>
    <hr style="margin: 15px 0; border-color: rgba(46, 204, 113, 0.2);">
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Previsto Mensal</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{total_mensal}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Prev. Mensal Realizada</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{mensal_realizados}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text">{label_faltam}</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{faltam_mensal}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Criação do card estilizado para Preventiva Semestral com as métricas dentro
st.markdown(f"""
<div class="semestral-card">
    <div class="card-title">
        <span></span>
        <span>Preventiva Semestral</span>
    </div>
    <hr style="margin: 15px 0; border-color: rgba(230, 126, 34, 0.2);">
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Previsto Semestral</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{semestral_previsto}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Prev. Semestral Realizada</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{semestral_realizados}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Faltam Prev. Semestral</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{max(semestral_previsto - semestral_realizados, 0)}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- FIM NOVA LÓGICA ---


# Linha de baixo – Acompanhamento de Corretivas
st.markdown("---")

# Filtra somente tarefas do tipo Corretiva
df_corretiva = df_filt[
    df_filt["tipo"].str.contains("Corretiva", case=False, na=False)
]

# Conta equipamentos respondidos nas tarefas corretivas
corretiva_realizados = sum(
    len(
        {
            q.get("questionnaireEquipamentId")
            for q in (row.get("questionarios") or [])
            if q.get("questionnaireEquipamentId")
        }
    )
    for _, row in df_corretiva.iterrows()
)

# Conta quantos equipamentos eram esperados nas tarefas corretivas
corretiva_esperados = sum(
    len(row.get("equipamentos_id") or []) for _, row in df_corretiva.iterrows()
)

# Conta o número total de tarefas corretivas no período
total_tarefas_corretivas = len(df_corretiva)

# Criação do card estilizado para Corretivas com as métricas dentro
st.markdown(f"""
<div class="corretiva-card">
    <div class="card-title">
        <span></span>
        <span>Corretivas</span>
    </div>
    <hr style="margin: 15px 0; border-color: rgba(52, 152, 219, 0.2);">
    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Total de Tarefas Corretivas</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{total_tarefas_corretivas}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Equipamentos em Corretivas</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{corretiva_esperados}</div>
        </div>
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.9em;" class="adaptive-text"> Equipamentos Atendidos</div>
            <div style="font-size: 1.5em; font-weight: bold;" class="adaptive-text">{corretiva_realizados}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

from datetime import date
# Filtra tarefas de PMOC pelo nome específico no tipo e data de março até hoje
pmoc_nome = "Preventiva Levantamento de PMOC"
data_inicio_pmoc = date(date.today().year, 3, 1)
data_fim_pmoc = date.today()
df_pmoc = df[
    df["tipo"].str.contains(pmoc_nome, case=False, na=False)
    & (df["data"] >= data_inicio_pmoc)
    & (df["data"] <= data_fim_pmoc)
]

# Contar tarefas por status relevante
pmoc_finalizadas = df_pmoc[df_pmoc["status"] == "Finalizada"].shape[0]
pmoc_pausadas = df_pmoc[df_pmoc["status"] == "Pausada"].shape[0]
pmoc_abertas = df_pmoc[df_pmoc["status"] == "Aberta"].shape[0]

# Card PMOC (usa o mesmo estilo do card de corretiva)
st.markdown(f"""
<div class="corretiva-card" style="background-color: rgba(255,184,77,0.15); border-left: 5px solid #ffb84d;">
    <div class="card-title">
        <span>Levantamento de PMOC</span>
    </div>
    <div class="card-content">
        <div style="display: flex; justify-content: space-between; margin-top: 10px;">
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 0.9em; color: #fff;" class="adaptive-text">PMOC Realizadas</div>
                <div style="font-size: 1.5em; font-weight: bold; color: #fff;" class="adaptive-text">{pmoc_finalizadas}</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 0.9em; color: #fff;" class="adaptive-text">PMOC em Pausa</div>
                <div style="font-size: 1.5em; font-weight: bold; color: #fff;" class="adaptive-text">{pmoc_pausadas}</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 0.9em; color: #fff;" class="adaptive-text">PMOC Não Realizadas</div>
                <div style="font-size: 1.5em; font-weight: bold; color: #fff;" class="adaptive-text">{pmoc_abertas}</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Botão Streamlit para exibir tarefas em pausa (fora do HTML)
# Três botões exclusivos, só um expander aberto por vez
col_realizadas, col_pausa, col_nao_realizadas = st.columns([1,1,1])

# Estado para controle do botão ativo
if 'pmoc_btn_ativo' not in st.session_state:
    st.session_state['pmoc_btn_ativo'] = None

with col_realizadas:
    btn_realizadas = st.button("Exibir PMOC Realizadas", key="btn_pmoc_realizadas")
    if btn_realizadas:
        st.session_state['pmoc_btn_ativo'] = 'realizadas'
with col_pausa:
    btn_pausa = st.button("Exibir PMOC em Pausa", key="btn_pmoc_pausa")
    if btn_pausa:
        st.session_state['pmoc_btn_ativo'] = 'pausa'
with col_nao_realizadas:
    btn_nao_realizadas = st.button("Exibir PMOC Não Realizadas", key="btn_pmoc_nao_realizadas")
    if btn_nao_realizadas:
        st.session_state['pmoc_btn_ativo'] = 'nao_realizadas'

# Expander exclusivo
if st.session_state['pmoc_btn_ativo'] == 'realizadas' and pmoc_finalizadas > 0:
    with st.expander("Tarefas de Levantamento de PMOC Realizadas", expanded=True):
        df_pmoc_realizadas = df_pmoc[df_pmoc["status"] == "Finalizada"].copy()
        table_html = """
        <table style='width:100%; border-collapse:collapse;'>
            <thead>
                <tr>
                    <th style='border:1px solid #444;padding:4px;'>ID</th>
                    <th style='border:1px solid #444;padding:4px;'>Escola</th>
                    <th style='border:1px solid #444;padding:4px;'>Data</th>
                    <th style='border:1px solid #444;padding:4px;'>Status</th>
                    <th style='border:1px solid #444;padding:4px;'>Link</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, row in df_pmoc_realizadas.sort_values("data").iterrows():
            link = f"<a href='{row['taskUrl']}' target='_blank'>Abrir tarefa #{row['taskID']}</a>" if row.get("taskUrl") else ""
            table_html += f"<tr>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['taskID']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['escola']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['data']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['status']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{link}</td>"
            table_html += "</tr>"
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.caption("Apenas tarefas do tipo 'Preventiva Levantamento de PMOC' FINALIZADAS no período exibido.")

elif st.session_state['pmoc_btn_ativo'] == 'nao_realizadas' and pmoc_abertas > 0:
    with st.expander("Tarefas de Levantamento de PMOC Não Realizadas", expanded=True):
        df_pmoc_nao_realizadas = df_pmoc[df_pmoc["status"] == "Aberta"].copy()
        table_html = """
        <table style='width:100%; border-collapse:collapse;'>
            <thead>
                <tr>
                    <th style='border:1px solid #444;padding:4px;'>ID</th>
                    <th style='border:1px solid #444;padding:4px;'>Escola</th>
                    <th style='border:1px solid #444;padding:4px;'>Data</th>
                    <th style='border:1px solid #444;padding:4px;'>Status</th>
                    <th style='border:1px solid #444;padding:4px;'>Link</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, row in df_pmoc_nao_realizadas.sort_values("data").iterrows():
            link = f"<a href='{row['taskUrl']}' target='_blank'>Abrir tarefa #{row['taskID']}</a>" if row.get("taskUrl") else ""
            table_html += f"<tr>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['taskID']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['escola']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['data']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['status']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{link}</td>"
            table_html += "</tr>"
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.caption("Apenas tarefas do tipo 'Preventiva Levantamento de PMOC' NÃO REALIZADAS no período exibido.")

elif st.session_state['pmoc_btn_ativo'] == 'pausa' and pmoc_pausadas > 0:
    with st.expander("Tarefas de Levantamento de PMOC em Pausa", expanded=True):
        df_pmoc_pausa = df_pmoc[df_pmoc["status"] == "Pausada"].copy()
        table_html = """
        <table style='width:100%; border-collapse:collapse;'>
            <thead>
                <tr>
                    <th style='border:1px solid #444;padding:4px;'>ID</th>
                    <th style='border:1px solid #444;padding:4px;'>Escola</th>
                    <th style='border:1px solid #444;padding:4px;'>Data</th>
                    <th style='border:1px solid #444;padding:4px;'>Status</th>
                    <th style='border:1px solid #444;padding:4px;'>Link</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, row in df_pmoc_pausa.sort_values("data").iterrows():
            link = f"<a href='{row['taskUrl']}' target='_blank'>Abrir tarefa #{row['taskID']}</a>" if row.get("taskUrl") else ""
            table_html += f"<tr>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['taskID']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['escola']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['data']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{row['status']}</td>"
            table_html += f"<td style='border:1px solid #444;padding:4px;'>{link}</td>"
            table_html += "</tr>"
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.caption("Apenas tarefas do tipo 'Preventiva Levantamento de PMOC' em pausa no período exibido.")

# Conta equipamentos respondidos nas tarefas corretivas
corretiva_realizados = sum(
    len(
        {
            q.get("questionnaireEquipamentId")
            for q in (row.get("questionarios") or [])
            if q.get("questionnaireEquipamentId")
        }
    )
    for _, row in df_corretiva.iterrows()
)

# Conta quantos equipamentos eram esperados nas tarefas corretivas
corretiva_esperados = sum(
    len(row.get("equipamentos_id") or []) for _, row in df_corretiva.iterrows()
)

# Conta o número total de tarefas corretivas no período
total_tarefas_corretivas = len(df_corretiva)

# As métricas já estão sendo exibidas dentro do card de Corretivas

# Adicionar botão para gerar gráfico consolidado
st.markdown("---")
st.subheader("📊 Gráfico Consolidado do Setor")

# Calcular totais de equipamentos esperados e realizados
if st.button("📈 Gerar Gráfico Consolidado do Setor"):
    # Obter totais de equipamentos do setor
    total_equipamentos_setor = qtde_equipamentos_setor
    
    # Calcular equipamentos realizados
    total_mensal = len(ids_equipamentos_realizados)
    total_semestral = len(ids_equipamentos_semestral)
    
    # Contar equipamentos em tarefas corretivas finalizadas
    df_corretiva_finalizadas = df_corretiva[df_corretiva['status'] == 'Finalizada']
    ids_equipamentos_corretiva = set()
    for _, row in df_corretiva_finalizadas.iterrows():
        if isinstance(row.get("questionarios"), list):
            ids_equipamentos_corretiva.update(
                q.get("questionnaireEquipamentId")
                for q in row["questionarios"]
                if q.get("questionnaireEquipamentId")
            )
    total_corretiva = len(ids_equipamentos_corretiva)
    
    # Calcular totais esperados (considerando que semestral é 1/6 do total)
    total_prev_mensal = total_equipamentos_setor
    total_prev_semestral = total_equipamentos_setor // 6
    total_prev_corretiva = total_equipamentos_setor  # Máximo teórico
    
    # Criar dados para o gráfico
    categorias = ['Preventiva Mensal', 'Preventiva Semestral', 'Corretiva']
    
    equipamentos_esperados = [total_prev_mensal, total_prev_semestral, total_prev_corretiva]
    equipamentos_realizados = [total_mensal, total_semestral, total_corretiva]
    
    # Criar DataFrame para o gráfico
    df_grafico = pd.DataFrame({
        'Categoria': categorias,
        'Equipamentos Esperados': equipamentos_esperados,
        'Equipamentos Realizados': equipamentos_realizados,
        'Porcentagem': [f"{r/e*100:.1f}%" if e > 0 else "0%" for r, e in zip(equipamentos_realizados, equipamentos_esperados)]
    })
    
    # Configurar o gráfico
    fig = go.Figure()
    
    # Adicionar barras para equipamentos esperados
    fig.add_trace(go.Bar(
        x=df_grafico['Categoria'],
        y=df_grafico['Equipamentos Esperados'],
        name='Esperados',
        marker_color='#4285F4',
        text=df_grafico['Equipamentos Esperados'],
        textposition='auto',
    ))
    
    # Adicionar barras para equipamentos realizados
    fig.add_trace(go.Bar(
        x=df_grafico['Categoria'],
        y=df_grafico['Equipamentos Realizados'],
        name='Realizados',
        marker_color='#34A853',
        text=df_grafico['Porcentagem'],
        textposition='auto',
    ))
    
    # Atualizar layout do gráfico
    fig.update_layout(
        title='Visão Consolidada por Tipo de Manutenção',
        xaxis_title='Tipo de Manutenção',
        yaxis_title='Quantidade de Equipamentos',
        barmode='group',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    # Adicionar anotações com as porcentagens
    for i, row in df_grafico.iterrows():
        fig.add_annotation(
            x=row['Categoria'],
            y=row['Equipamentos Realizados'] + 10,
            text=row['Porcentagem'],
            showarrow=False,
            font=dict(size=12, color='black')
        )
    
    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Adicionar métricas resumidas
    st.subheader(" Resumo de Desempenho")
    
    st.write(f"### Dados Consolidados do {setor_escolhido}")
    # Renomear colunas para refletir melhor os dados
    df_grafico = df_grafico.rename(columns={'Equipamentos Esperados': 'Equipamentos Ativos'})
    st.dataframe(df_grafico)
    
    # Criar gráfico de barras
    st.write(f"### Gráfico de Equipamentos por Tipo de Tarefa - {setor_escolhido}")
    
    # Criar duas colunas para os gráficos
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        # Gráfico de barras comparando ativos vs realizados
        st.write("**Equipamentos Ativos vs. Realizados**")
        
        # Criar DataFrame para gráfico de barras nativo do Streamlit
        totais = {
            'Preventiva Mensal': [total_prev_mensal, total_mensal],
            'Preventiva Semestral': [total_prev_semestral, total_semestral],
            'Corretiva': [total_prev_corretiva, total_corretiva]
        }
        chart_data = pd.DataFrame(totais, index=['Ativos', 'Realizados'])
        
        # Transpor para melhor visualização
        chart_data = chart_data.T
        
        # Exibir gráfico de barras
        st.bar_chart(chart_data)
    
    with col_graf2:
        # Gráfico de porcentagem de realização
        st.write("**Porcentagem de Realização**")
        
        # Criar DataFrame para gráfico de porcentagem
        porcentagem_data = pd.DataFrame({
            'Porcentagem': [float(p.replace('%', '')) for p in df_grafico['Porcentagem']]
        }, index=df_grafico['Categoria'])
        
        # Exibir gráfico de barras de porcentagem
        st.bar_chart(porcentagem_data)
    
    # Criar colunas para os gráficos de distribuição usando gráficos nativos do Streamlit
    st.write("### Gráficos de Distribuição")
    col_pizza1, col_pizza2 = st.columns(2)
    
    with col_pizza1:
        # Gráfico de distribuição de equipamentos esperados
        st.write("**Equipamentos Esperados por Tipo**")
        
        # Dados para o gráfico de pizza
        tipos_tarefas = ['Prev. Mensal', 'Prev. Semestral', 'Corretiva']
        qtd_tarefas = [total_prev_mensal, total_prev_semestral, total_prev_corretiva]
        
        # Definir as cores para cada tipo de tarefa - usar as mesmas em todo o dashboard
        cores = {'Prev. Mensal': '#3498db', 'Prev. Semestral': '#2ecc71', 'Corretiva': '#e74c3c'}
        
        # Criar DataFrame para gráfico nativo do Streamlit
        df_pizza1 = pd.DataFrame({
            'Tipo': tipos_tarefas,
            'Quantidade': qtd_tarefas
        })
        
        # Usar gráfico nativo do Streamlit com tamanho controlado
        # Definir altura fixa para o gráfico
        st.container().style = "height: 150px;"
        with st.container():
            # Usar gráfico de barras horizontais que ocupa menos espaço
            # Criar um mapeamento de cores para o Altair
            domain = list(cores.keys())
            range_ = list(cores.values())
            
            chart = alt.Chart(df_pizza1).mark_bar().encode(
                y=alt.Y('Tipo:N', sort=None),
                x='Quantidade:Q',
                color=alt.Color('Tipo:N', scale=alt.Scale(domain=domain, range=range_))
            ).properties(
                height=100  # Altura fixa em pixels
            )
            st.altair_chart(chart, use_container_width=True)
        
        # Usar as cores definidas anteriormente
        
        # Exibir números abaixo do gráfico com as cores correspondentes
        for tipo, valor in zip(tipos_tarefas, [total_prev_mensal, total_prev_semestral, total_prev_corretiva]):
            cor = cores[tipo]
            if tipo == 'Corretiva':
                st.markdown(f"<span style='color:{cor}'><b>{tipo}:</b> {valor} tarefas</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:{cor}'><b>{tipo}:</b> {valor} equipamentos ativos</span>", unsafe_allow_html=True)
    
    with col_pizza2:
        # Gráfico de distribuição de equipamentos realizados
        st.write("**Equipamentos Realizados por Tipo**")
        
        # Dados para o gráfico
        equip_dados = [mensal_realizados, semestral_realizados, corretiva_realizados]
        
        # Criar DataFrame para gráfico nativo do Streamlit
        df_pizza2 = pd.DataFrame({
            'Tipo': tipos_tarefas,
            'Quantidade': equip_dados
        })
        
        # Usar gráfico nativo do Streamlit com tamanho controlado
        # Definir altura fixa para o gráfico
        st.container().style = "height: 150px;"
        with st.container():
            # Usar gráfico de barras horizontais que ocupa menos espaço
            # Usar o mesmo mapeamento de cores do gráfico anterior
            chart = alt.Chart(df_pizza2).mark_bar().encode(
                y=alt.Y('Tipo:N', sort=None),
                x='Quantidade:Q',
                color=alt.Color('Tipo:N', scale=alt.Scale(domain=domain, range=range_))
            ).properties(
                height=100  # Altura fixa em pixels
            )
            st.altair_chart(chart, use_container_width=True)
        
        # Usar as mesmas cores definidas anteriormente
        # Exibir números abaixo do gráfico com as cores correspondentes
        for tipo, qtd in zip(tipos_tarefas, equip_dados):
            cor = cores[tipo]
            if tipo == 'Corretiva':
                st.markdown(f"<span style='color:{cor}'><b>{tipo}:</b> {qtd} tarefas atendidas</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:{cor}'><b>{tipo}:</b> {qtd} equipamentos realizados</span>", unsafe_allow_html=True)
    
    # Resumo textual
    st.markdown("### Resumo do Setor")
    st.markdown(f"**Total de equipamentos ativos no setor:** {total_prev_mensal}")
    st.markdown(f"**Total de tarefas no período:** {len(df_filt) if 'df_filt' in locals() else 0}")
    
    # Verificar se as variáveis existem antes de usá-las
    if 'df_mensal' in locals():
        st.markdown(f"**Preventivas Mensais:** {len(df_mensal)} tarefas / {mensal_realizados} equipamentos atendidos ({round(mensal_realizados/total_prev_mensal*100 if total_prev_mensal > 0 else 0, 1)}%)")
    if 'df_semestral' in locals():
        st.markdown(f"**Preventivas Semestrais:** {len(df_semestral)} tarefas / {semestral_realizados} equipamentos atendidos ({round(semestral_realizados/total_prev_semestral*100 if total_prev_semestral > 0 else 0, 1)}%)")
    if 'df_corretiva' in locals():
        st.markdown(f"**Corretivas:** {len(df_corretiva)} tarefas / {total_corretiva} equipamentos atendidos ({round(total_corretiva/total_prev_corretiva*100 if total_prev_corretiva > 0 else 0, 1)}%)")
    
    # Consolidado de Preventivas Mensais e Semestrais
    # Extrair IDs de equipamentos respondidos em cada tipo de preventiva
    equipamentos_mensais = set()
    equipamentos_semestrais = set()
    
    for _, row in df_mensal.iterrows():
        questionarios = row.get("questionarios") or []
        for q in questionarios:
            eq_id = q.get("questionnaireEquipamentId")
            if eq_id:
                equipamentos_mensais.add(eq_id)
    
    for _, row in df_semestral.iterrows():
        questionarios = row.get("questionarios") or []
        for q in questionarios:
            eq_id = q.get("questionnaireEquipamentId")
            if eq_id:
                equipamentos_semestrais.add(eq_id)
    
    # Encontrar equipamentos que receberam ambos os tipos de preventiva
    equipamentos_duplicados = equipamentos_mensais.intersection(equipamentos_semestrais)
    
    # Calcular o total consolidado (sem duplicatas)
    total_consolidado = len(equipamentos_mensais.union(equipamentos_semestrais))
    
    # Calcular porcentagem consolidada
    total_prev_consolidado = total_prev_mensal + total_prev_semestral
    porcentagem_consolidada = round((total_consolidado / total_prev_consolidado) * 100, 1) if total_prev_consolidado > 0 else 0
    
    # Exibir consolidado
    st.markdown(f"**Consolidado Mensal/Semestral no Mês:** {total_consolidado} equipamentos atendidos ({porcentagem_consolidada}%)")
    
    # Exibir equipamentos duplicados se houver
    if equipamentos_duplicados:
        nomes_duplicados = [equipamentos_dict.get(eq_id, f"ID {eq_id}") for eq_id in equipamentos_duplicados]
        st.markdown(f"**Equipamentos com preventiva mensal e semestral no mesmo mês:** {len(equipamentos_duplicados)}")
        with st.expander("Ver equipamentos duplicados"):
            for nome in nomes_duplicados:
                st.markdown(f"- {nome}")
    else:
        st.markdown("**Equipamentos com preventiva mensal e semestral no mesmo mês:** 0")
    
    # Explicação dos valores das métricas de corretivas
    st.markdown("---")
    st.markdown("### Explicação dos Valores de Corretivas")
    st.markdown(f"**{total_tarefas_corretivas}** = Número total de tarefas do tipo 'Corretiva' no período filtrado")
    st.markdown(f"**{corretiva_esperados}** = Soma de todos os equipamentos listados nas tarefas corretivas")
    st.markdown(f"**{corretiva_realizados}** = Soma de todos os equipamentos que foram efetivamente respondidos")


def obter_status_predominante(df_tarefas):
    contagem = Counter(df_tarefas["status"])
    if contagem:
        return contagem.most_common(1)[0][0]
    return "Desconhecido"


def definir_cor(status):
    if status == "Finalizada":
        return [0, 200, 0]  # Verde
    elif status == "Pausada":
        return [255, 165, 0]  # Laranja
    elif status == "Aberta":
        return [200, 0, 0]  # Vermelho
    else:
        return [150, 150, 150]  # Cinza para status desconhecidos


# Mapa interativo
with st.expander("🗺️ Visualizar Mapa de Escolas e Equipamentos"):
    conn = sqlite3.connect(DB_CLIENTES)
    escolas_df = pd.read_sql(
        """
        SELECT id, description AS nome, latitude, longitude FROM clientes_grupo_156750
        UNION ALL SELECT id, description AS nome, latitude, longitude FROM clientes_grupo_156751
        UNION ALL SELECT id, description AS nome, latitude, longitude FROM clientes_grupo_156752
        UNION ALL SELECT id, description AS nome, latitude, longitude FROM clientes_grupo_156753
        UNION ALL SELECT id, description AS nome, latitude, longitude FROM clientes_grupo_156754
        """,
        conn,
    )
    conn.close()

    escolas_filtradas = escolas_df[
        escolas_df["id"].isin(df_filt["customer_id"].unique())
    ]

    if not escolas_filtradas.empty:
        dados_mapa = []

        for _, row_escola in escolas_filtradas.iterrows():
            escola_id = row_escola["id"]
            nome_escola = row_escola["nome"]
            lat = row_escola["latitude"]
            lon = row_escola["longitude"]

            # Filtrar tarefas para esta escola
            tarefas_escola = df_filt[df_filt["customer_id"] == escola_id]

            # Contar equipamentos e pendências
            equipamentos_total = sum(
                [
                    (
                        len(t["equipamentos_id"])
                        if isinstance(t["equipamentos_id"], list)
                        else 0
                    )
                    for _, t in tarefas_escola.iterrows()
                ]
            )

            pendencias_total = 0
            pausadas_total = len(tarefas_escola[tarefas_escola["status"] == "Pausada"])
            equipamentos_lista = []

            for _, t in tarefas_escola.iterrows():
                eq_ids = t["equipamentos_id"] or []
                questionarios = t["questionarios"] or []
                eq_q = [
                    q.get("questionnaireEquipamentId")
                    for q in questionarios
                    if q.get("questionnaireEquipamentId")
                ]
                pendencias_total += len(set(eq_ids) - set(eq_q))
                equipamentos_lista.extend(
                    [equipamentos_dict.get(eq, f"ID {eq}") for eq in eq_ids]
                )

            # Criar tooltip HTML
            equipamentos_html = "<br>".join(
                [f"- {nome}" for nome in equipamentos_lista]
            )
            tooltip = (
                f"<b>{nome_escola}</b><br>"
                f"Total de equipamentos: {equipamentos_total}<br>"
                f"🔧 Pendências: {pendencias_total}<br>"
                f"⏸️ Em Pausa: {pausadas_total}<br>"
                f"📊 Finalizadas: {len(tarefas_escola[tarefas_escola['status'] == 'Finalizada'])} | "
                f"Em Pausa: {pausadas_total} | "
                f"Em Aberto: {len(tarefas_escola) - len(tarefas_escola[tarefas_escola['status'] == 'Finalizada']) - pausadas_total}"
            )

            if equipamentos_html:
                tooltip += f"<br><br>{equipamentos_html}"

            # Determinar status predominante
            status_predominante = obter_status_predominante(tarefas_escola)

            # Adicionar à lista de dados do mapa
            dados_mapa.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "tooltip": tooltip,
                    "status": status_predominante,
                }
            )

        # Criar DataFrame do mapa
        mapa_df = pd.DataFrame(dados_mapa)

        # Definir cores baseadas no status
        mapa_df["cor"] = mapa_df["status"].apply(definir_cor)

        # Criar layer para o mapa
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=mapa_df,
            get_position="[lon, lat]",
            get_color="cor",
            get_radius=100,
            pickable=True,
        )

        # Exibir o mapa
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=mapa_df["lat"].mean(),
                    longitude=mapa_df["lon"].mean(),
                    zoom=11,
                    pitch=0,
                ),
                layers=[layer],
                tooltip={"html": "{tooltip}"},
            )
        )
    else:
        st.warning("Nenhuma escola com dados disponíveis para exibir no mapa.")

# Exibir informações detalhadas das tarefas

for _, row in df_filt.iterrows():
    equipamentos_ids = list(set(row.get("equipamentos_id") or []))  # remove duplicatas
    qtd_equip = len(equipamentos_ids)
    questionarios = row.get("questionarios") or []

    equipamentos_q = list(
        {
            q.get("questionnaireEquipamentId")
            for q in questionarios
            if q.get("questionnaireEquipamentId")
        }
    )

    tipo_limpo = (
        re.sub(r"^# .*? - ", "", row["tipo"].strip())
        if isinstance(row["tipo"], str)
        else row["tipo"]
    )

    pendentes = list(set(equipamentos_ids) - set(equipamentos_q))
    pendentes_count = len(pendentes)
    pendente_icone = " ⚠️" if pendentes_count > 0 else " 🟢"

    data_formatada = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")

    titulo = (
        f"🏫 Escola: {row['escola']} - {tipo_limpo} (por {row['nome']}) "
        f"- Equipamentos - {qtd_equip} ({pendentes_count} pendentes){pendente_icone}"
    )

    with st.expander(titulo):
        if row.get("taskUrl"):
            tarefa_numero = row.get("taskID", "Sem número")
            st.markdown(
                f"[🔗 Abrir tarefa na Auvo, #{tarefa_numero}]({row['taskUrl']})"
            )

        st.markdown(f"**📅 Data:** {data_formatada}")
        st.markdown(f"**📌 Status:** {row['status']}")
        st.markdown(f"**✅ Check-in:** {'Sim' if row['checkin'] else 'Não'}")
        st.markdown(f"**✅ Check-out:** {'Sim' if row['checkout'] else 'Não'}")
        st.markdown(f"**🔢 Equipamentos esperados:** {qtd_equip}")
        st.markdown(f"**📝 Observação:** {row['observacao'] or '-'}")
        st.markdown(f"**✍️ Assinatura:** {row['assinatura'] or 'Não assinado'}")

        col_eq1, col_eq2 = st.columns(2)

        html_equipamentos = f"<details><summary><span style='font-weight:bold; font-size:1.35em;'>🧩 Equipamentos do Local ({len(equipamentos_ids)})</span></summary><ul>"
        if equipamentos_ids:
            for eq in equipamentos_ids:
                nome = equipamentos_dict.get(eq, f"ID {eq} ⚠️ Inativo na Auvo")
                icone = "🟢" if eq in equipamentos_q else "⚠️"
                html_equipamentos += f"<li>{nome} {icone}</li>"
            html_equipamentos += "</ul></details>"
        else:
            html_equipamentos += "<li><span style='color:#e67e22;'>Nenhum equipamento registrado no local.</span></li></ul></details>"
        st.markdown(html_equipamentos, unsafe_allow_html=True)

        st.markdown("<span style='font-size:0.95em; font-weight:500;'>⚠️ Equipamentos pendentes (não respondidos)</span>", unsafe_allow_html=True)
        if pendentes:
            for p in pendentes:
                nome = equipamentos_dict.get(p, f"ID {p} ⚠️ Inativo na Auvo")
                st.error(f"- {nome}")
        else:
            st.success("Todos os equipamentos foram respondidos.")


# Exportar dados
df_export = df_filt[
    [
        "data",
        "nome",
        "escola",
        "tipo",
        "status",
        "observacao",
        "taskUrl",
        "equipamentos_id",
        "questionarios",
    ]
].copy()
df_export["Equipamentos Esperados"] = df_export["equipamentos_id"].apply(
    lambda x: len(x) if isinstance(x, list) else 0
)
df_export["Equipamentos Respondidos"] = df_export["questionarios"].apply(
    lambda qs: (
        len([q for q in qs if q.get("questionnaireEquipamentId")])
        if isinstance(qs, list)
        else 0
    )
)
df_export.rename(
    columns={
        "data": "Data",
        "nome": "Prestador",
        "escola": "Escola",
        "tipo": "Tipo da Tarefa",
        "status": "Status",
        "observacao": "Observação",
        "taskUrl": "Link da Tarefa",
        "equipamentos_id": "_equip",
        "questionarios": "_quest",
    },
    inplace=True,
)
df_export = df_export[
    [
        "Data",
        "Prestador",
        "Escola",
        "Tipo da Tarefa",
        "Status",
        "Observação",
        "Equipamentos Esperados",
        "Equipamentos Respondidos",
        "Link da Tarefa",
        "_equip",
    ]
]


# 🔍 Função para converter IDs de equipamentos em nomes
def listar_equipamentos(equip_ids):
    if not equip_ids:
        return ""
    return ", ".join([equipamentos_dict.get(e, f"ID {e}") for e in equip_ids])


total_equipamentos = sum(
    len(row.get("equipamentos_id") or []) for _, row in df_filt.iterrows()
)
total_escolas = df_filt["escola"].nunique()

with st.expander(
    f"📦 Ver lista de equipamentos ({total_escolas} escolas / {total_equipamentos} equipamentos)"
):
    equipamentos_lista = []

    for _, row in df_filt.iterrows():
        escola = row["escola"]
        equipamentos_ids = row.get("equipamentos_id") or []
        nomes = [equipamentos_dict.get(e, f"ID {e}") for e in equipamentos_ids]

        equipamentos_lista.append(
            f"🏫 {escola}: {', '.join(nomes) if nomes else 'Sem equipamentos cadastrados'}"
        )

    for linha in equipamentos_lista:
        st.markdown(f"- {linha}")

df_export["Lista de Equipamentos"] = df_export["_equip"].apply(listar_equipamentos)
df_export.drop(columns=["_equip"], inplace=True)
df_export["Data"] = pd.to_datetime(df_export["Data"]).dt.strftime("%d/%m/%Y")

# 🔥 Gerar DataFrame formatado com sublinhas de equipamentos

linhas = []

for _, row in df_export.iterrows():
    equipamentos = (
        row["Lista de Equipamentos"].split(", ")
        if row["Lista de Equipamentos"]
        else ["Sem equipamentos"]
    )

    primeira = True
    for equipamento in equipamentos:
        if primeira:
            linhas.append(
                {
                    "Data": row["Data"],
                    "Prestador": row["Prestador"],
                    "Escola": row["Escola"],
                    "Tipo da Tarefa": row["Tipo da Tarefa"],
                    "Status": row["Status"],
                    "Observação": row["Observação"],
                    "Equipamentos Esperados": row["Equipamentos Esperados"],
                    "Equipamentos Respondidos": row["Equipamentos Respondidos"],
                    "Link da Tarefa": row["Link da Tarefa"],
                    "Equipamento": equipamento,
                }
            )
            primeira = False
        else:
            linhas.append(
                {
                    "Data": "",
                    "Prestador": "",
                    "Escola": "",
                    "Tipo da Tarefa": "",
                    "Status": "",
                    "Observação": "",
                    "Equipamentos Esperados": "",
                    "Equipamentos Respondidos": "",
                    "Link da Tarefa": "",
                    "Equipamento": equipamento,
                }
            )

df_final_export = pd.DataFrame(linhas)

csv = df_final_export.to_csv(index=False, sep=";").encode("utf-8")

# 🔧 Dados de exemplo com equipamentos agrupados
dados = [
    [
        "06/05/2025",
        "Pako Ruhan",
        "Escola A",
        "Preventiva Mensal",
        "Finalizada",
        "Observação",
        5,
        5,
        "link",
        "Equipamento 1",
    ],
    ["", "", "", "", "", "", "", "", "", "Equipamento 2"],
    ["", "", "", "", "", "", "", "", "", "Equipamento 3"],
    [
        "09/05/2025",
        "Pako Ruhan",
        "Escola B",
        "Preventiva Semestral",
        "Finalizada",
        "Observação",
        3,
        3,
        "link",
        "Equipamento 1",
    ],
    ["", "", "", "", "", "", "", "", "", "Equipamento 2"],
]

colunas = [
    "Data",
    "Prestador",
    "Escola",
    "Tipo da Tarefa",
    "Status",
    "Observação",
    "Equipamentos Esperados",
    "Equipamentos Respondidos",
    "Link da Tarefa",
    "Equipamento",
]

# 🔥 -> Usa o DataFrame que já está filtrado na tela:
df_base = df_filt.copy()

# Prepara lista de linhas para exportação
linhas = []

# Verifica se há tarefas na data selecionada
if df_base.empty:
    st.warning("Sem tarefas nessa data. Selecione outra data ou ajuste os filtros.")
    # Define equipamentos como vazio para evitar erro
    equipamentos = []
    equipamentos_dict = {}
    row = {}
    primeira = True

# Garante que a variável equipamentos esteja sempre definida
if 'equipamentos' not in locals():
    equipamentos = []

for equipamento in equipamentos if equipamentos else ["Sem equipamentos"]:
    nome_equipamento = (
        equipamentos_dict.get(equipamento, f"ID {equipamento}")
        if equipamento
        else "Sem equipamentos"
    )

    if primeira and 'row' in locals() and row and 'data' in row:
        linhas.append(
            {
                "Data": row["data"].strftime("%d/%m/%Y") if isinstance(row.get("data"), datetime) else "",
                "Prestador": row.get("nome", ""),
                "Escola": row.get("escola", ""),
                "Tipo da Tarefa": row.get("tipo", ""),
                "Status": row.get("status", ""),
                "Observação": row.get("observacao", ""),
                "Link da Tarefa": row.get("taskUrl", ""),
                "Equipamento": nome_equipamento,
                "Nível": 0,
            }
        )
        primeira = False
    else:
        linhas.append(
            {
                "Data": "",
                "Prestador": "",
                "Escola": "",
                "Tipo da Tarefa": "",
                "Status": "",
                "Observação": "",
                "Link da Tarefa": "",
                "Equipamento": nome_equipamento,
                "Nível": 1,
            }
        )

df_final = pd.DataFrame(linhas)

# 🎯 Gerar Excel com expansores
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_final.to_excel(writer, sheet_name="Tarefas", index=False, startrow=1)

    workbook = writer.book
    worksheet = writer.sheets["Tarefas"]

    header_format = workbook.add_format({"bold": True, "bg_color": "#D9D9D9"})
    for col_num, value in enumerate(df_final.columns[:-1]):  # Exclui coluna 'Nível'
        worksheet.write(0, col_num, value, header_format)

    # 🔗 Definir agrupamento de linhas no Excel
    row_num = 1
    while row_num < len(df_final) + 1:
        nivel = df_final.iloc[row_num - 1]["Nível"]

        if nivel == 0:
            start = row_num
            end = row_num
            # Conta quantas linhas filhas tem
            for next_row in range(row_num + 1, len(df_final) + 1):
                if df_final.iloc[next_row - 1]["Nível"] == 1:
                    end = next_row
                else:
                    break

            if end > start:
                worksheet.set_row(start - 1, None, None, {"level": 0})
                for r in range(start, end + 1):
                    worksheet.set_row(r - 1, None, None, {"level": 1})
            else:
                worksheet.set_row(start - 1, None, None, {"level": 0})

            row_num = end + 1
        else:
            row_num += 1

    worksheet.outline_settings(True, False, False, False)

# Seção de Faturamento
st.markdown("---")
st.subheader("💰 Informações para Faturamento")

# Criar dois botões lado a lado
col_btn1, col_btn2 = st.columns(2)

if col_btn1.button("📊 Gerar Relatório de Faturamento"):
    # Criar DataFrame para faturamento
    linhas_faturamento = []
    
    # Agrupar por escola
    escolas_agrupadas = df_filt.groupby("escola")
    
    for escola, grupo in escolas_agrupadas:
        # Obter todos os equipamentos únicos desta escola
        todos_equipamentos = set()
        for _, row in grupo.iterrows():
            if row.get("equipamentos_id"):
                todos_equipamentos.update(row.get("equipamentos_id"))
        
        # Contar equipamentos finalizados
        equipamentos_finalizados = set()
        for _, row in grupo.iterrows():
            if row.get("questionarios"):
                for q in row.get("questionarios"):
                    if q.get("questionnaireEquipamentId"):
                        equipamentos_finalizados.add(q.get("questionnaireEquipamentId"))
        
        # Obter links das tarefas - apenas os links diretos sem formatação
        links_tarefas = [row.get("taskUrl", "") for _, row in grupo.iterrows() if row.get("taskUrl")]
        # Apenas os links separados por vírgula
        link_texto = ", ".join(links_tarefas)
        
        # Listar nomes dos equipamentos
        nomes_equipamentos = [equipamentos_dict.get(eq_id, f"ID {eq_id}") for eq_id in todos_equipamentos]
        equipamentos_texto = ", ".join(nomes_equipamentos)
        
        # Adicionar linha ao relatório
        # Calcular porcentagem com formatação correta
        porcentagem = round(len(equipamentos_finalizados) / len(todos_equipamentos) * 100 if todos_equipamentos else 0, 1)
        porcentagem_formatada = f"{porcentagem:.1f}%".replace('.', ',')
        
        linhas_faturamento.append({
            "Escola": escola,
            "Total de Equipamentos": len(todos_equipamentos),
            "Equipamentos Finalizados": len(equipamentos_finalizados),
            "Porcentagem Concluída": porcentagem_formatada,
            "Links das Tarefas": link_texto,
            "Lista de Equipamentos": equipamentos_texto
        })
    
    # Criar DataFrame
    df_faturamento = pd.DataFrame(linhas_faturamento)
    
    # Exibir tabela
    st.write("### Resumo de Faturamento por Escola")
    st.dataframe(df_faturamento[["Escola", "Total de Equipamentos", "Equipamentos Finalizados", "Porcentagem Concluída"]])
    
    # Gerar Excel
    output_faturamento = BytesIO()
    with pd.ExcelWriter(output_faturamento, engine="xlsxwriter") as writer:
        df_faturamento.to_excel(writer, sheet_name="Faturamento", index=False)
        
        # Formatar planilha
        workbook = writer.book
        worksheet = writer.sheets["Faturamento"]
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            "bold": True, 
            "bg_color": "#4B0082",  # Roxo escuro
            "font_color": "white",
            "border": 1
        })
        
        # Formato para células normais
        cell_format = workbook.add_format({
            "border": 1
        })
        
        # Aplicar formatos
        for col_num, value in enumerate(df_faturamento.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Ajustar largura das colunas
        worksheet.set_column("A:A", 30)  # Escola
        worksheet.set_column("B:C", 15)  # Total e Finalizados
        worksheet.set_column("D:D", 15)  # Porcentagem
        worksheet.set_column("E:E", 40)  # Links
        worksheet.set_column("F:F", 50)  # Lista de equipamentos
        
        # Adicionar totais no final
        ultima_linha = len(df_faturamento) + 1
        worksheet.write(ultima_linha, 0, "TOTAL", header_format)
        worksheet.write_formula(ultima_linha, 1, f"=SUM(B2:B{ultima_linha})", header_format)
        worksheet.write_formula(ultima_linha, 2, f"=SUM(C2:C{ultima_linha})", header_format)
        # Calcular a porcentagem total diretamente para garantir formatação correta
        total_equipamentos = sum(df_faturamento["Total de Equipamentos"])
        total_finalizados = sum(df_faturamento["Equipamentos Finalizados"])
        porcentagem_total = round(total_finalizados / total_equipamentos * 100 if total_equipamentos > 0 else 0, 1)
        
        # Escrever o valor formatado diretamente
        worksheet.write(
            ultima_linha, 3, 
            f"{porcentagem_total:.1f}%".replace('.', ','), 
            workbook.add_format({"bold": True, "bg_color": "#4B0082", "font_color": "white", "border": 1})
        )
    
    # Botão para download
    st.download_button(
        label="💰 Baixar Relatório de Faturamento",
        data=output_faturamento.getvalue(),
        file_name=f"faturamento_{setor_escolhido}_{data_ini.strftime('%d-%m-%Y')}_a_{data_fim.strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    
    # Resumo geral
    total_escolas = len(df_faturamento)
    total_equipamentos = df_faturamento["Total de Equipamentos"].sum()
    total_finalizados = df_faturamento["Equipamentos Finalizados"].sum()
    porcentagem_geral = round(total_finalizados / total_equipamentos * 100 if total_equipamentos else 0, 1)
    porcentagem_formatada = f"{porcentagem_geral:.1f}%".replace('.', ',')
    
    st.markdown("### Resumo Geral para Faturamento")
    st.markdown(f"**Total de Escolas:** {total_escolas}")
    st.markdown(f"**Total de Equipamentos Previstos:** {total_equipamentos}")
    st.markdown(f"**Total de Equipamentos Finalizados:** {total_finalizados}")
    st.markdown(f"**Porcentagem Geral Concluída:** {porcentagem_formatada}")

# Segundo botão para relatório detalhado por escola
if col_btn2.button("📂 Gerar Relatório Detalhado por Escola"):
    # Criar DataFrame para relatório detalhado
    linhas_detalhadas = []
    
    # Agrupar por escola
    escolas_agrupadas = df_filt.groupby("escola")
    
    for escola, grupo in escolas_agrupadas:
        # Obter todos os equipamentos únicos desta escola
        todos_equipamentos = set()
        for _, row in grupo.iterrows():
            if row.get("equipamentos_id"):
                todos_equipamentos.update(row.get("equipamentos_id"))
        
        # Para cada equipamento, adicionar uma linha
        for eq_id in todos_equipamentos:
            # Verificar se o equipamento foi finalizado
            finalizado = False
            for _, row in grupo.iterrows():
                if row.get("questionarios"):
                    for q in row.get("questionarios"):
                        if q.get("questionnaireEquipamentId") == eq_id:
                            finalizado = True
                            break
            
            # Obter nome do equipamento
            nome_equipamento = equipamentos_dict.get(eq_id, f"ID {eq_id}")
            
            # Adicionar linha ao relatório
            linhas_detalhadas.append({
                "Escola": escola,
                "Equipamento": nome_equipamento,
                "Finalizado": "Sim" if finalizado else "Não",
                "ID": eq_id
            })
    
    # Criar DataFrame
    df_detalhado = pd.DataFrame(linhas_detalhadas)
    
    # Exibir tabela
    st.write("### Relatório Detalhado por Escola")
    st.dataframe(df_detalhado)
    
    # Gerar Excel com abordagem simplificada
    output_detalhado = BytesIO()
    with pd.ExcelWriter(output_detalhado, engine="xlsxwriter") as writer:
        # Agrupar por escola para criar páginas separadas
        escolas_unicas = df_detalhado["Escola"].unique()
        
        # Criar uma página resumo
        resumo_escolas = []
        for escola in escolas_unicas:
            df_escola = df_detalhado[df_detalhado["Escola"] == escola]
            total_eq = len(df_escola)
            finalizados = len(df_escola[df_escola["Finalizado"] == "Sim"])
            porcentagem = round(finalizados / total_eq * 100 if total_eq > 0 else 0, 1)
            porcentagem_fmt = f"{porcentagem:.1f}%".replace('.', ',')
            
            resumo_escolas.append({
                "Escola": escola,
                "Total de Equipamentos": total_eq,
                "Finalizados": finalizados,
                "Porcentagem": porcentagem_fmt
            })
        
        # Criar DataFrame de resumo no formato da imagem
        df_resumo = pd.DataFrame()
        df_resumo["Escola"] = [escola for escola in escolas_unicas]
        df_resumo["Total de Equipam"] = [df_detalhado[df_detalhado["Escola"] == escola].shape[0] for escola in escolas_unicas]
        df_resumo["Equipamentos Fin"] = [len(df_detalhado[(df_detalhado["Escola"] == escola) & (df_detalhado["Finalizado"] == "Sim")]) for escola in escolas_unicas]
        
        # Calcular porcentagem
        porcentagens = []
        for i, escola in enumerate(escolas_unicas):
            total = df_resumo["Total de Equipam"][i]
            finalizados = df_resumo["Equipamentos Fin"][i]
            if total > 0:
                porcentagem = round((finalizados / total) * 100, 1)
                porcentagens.append(f"{porcentagem:.1f}%".replace('.', ','))
            else:
                porcentagens.append("0,0%")
        df_resumo["Porcentagem Con"] = porcentagens
        
        # Obter links das tarefas - um link por linha
        links_por_escola = {}
        for escola in escolas_unicas:
            grupo = df_filt[df_filt["escola"] == escola]
            links = [row.get("taskUrl", "") for _, row in grupo.iterrows() if row.get("taskUrl")]
            # Usar quebra de linha para separar os links
            links_por_escola[escola] = "\n".join(links)
        df_resumo["Links das Tarefas"] = [links_por_escola.get(escola, "") for escola in escolas_unicas]
        
        # Adicionar coluna de lista de equipamentos (será preenchida depois)
        df_resumo["Lista de Equipamentos"] = ""
        
        # Calcular totais
        total_equipamentos = df_resumo["Total de Equipam"].sum()
        total_finalizados = df_resumo["Equipamentos Fin"].sum()
        porcentagem_total = round((total_finalizados / total_equipamentos) * 100, 1) if total_equipamentos > 0 else 0
        porcentagem_total_fmt = f"{porcentagem_total:.1f}%".replace('.', ',')
        
        # Adicionar linha de total
        df_resumo.loc["TOTAL"] = [
            "TOTAL", 
            total_equipamentos, 
            total_finalizados, 
            porcentagem_total_fmt,
            "",  # Links das Tarefas
            ""   # Lista de Equipamentos
        ]
        
        # Salvar na planilha
        df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
        
        # Formatar página de resumo
        workbook = writer.book
        worksheet = writer.sheets["Resumo"]
        
        # Formato para cabeçalho
        header_format = workbook.add_format({
            "bold": True, 
            "bg_color": "#4B0082",
            "font_color": "white",
            "border": 1
        })
        
        # Formato para linha de total
        total_format = workbook.add_format({
            "bold": True,
            "bg_color": "#4B0082",
            "font_color": "white",
            "border": 1
        })
        
        # Formato para títulos de escola
        escola_format = workbook.add_format({
            "bold": True,
            "font_size": 14,
            "font_color": "#4B0082"
        })
        
        # Aplicar formatos
        for col_num, value in enumerate(df_resumo.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Formatar linha de total
        ultima_linha = len(df_resumo)
        for col in range(6):  # 6 colunas no total
            valor = df_resumo.iloc[-1, col] if col < len(df_resumo.columns) else ""
            worksheet.write(ultima_linha, col, valor, total_format)
        
        # Ajustar largura das colunas
        worksheet.set_column("A:A", 40)  # Escola
        worksheet.set_column("B:C", 15)  # Total e Finalizados
        worksheet.set_column("D:D", 15)  # Porcentagem
        worksheet.set_column("E:E", 60)  # Links - coluna mais larga para acomodar os links
        worksheet.set_column("F:F", 40)  # Lista de Equipamentos
        
        # Formato para células com quebra de linha
        wrap_format = workbook.add_format({
            'text_wrap': True,  # Habilitar quebra de texto
            'valign': 'top'     # Alinhar texto ao topo
        })
        
        # Aplicar formato de quebra de linha na coluna de links
        for row in range(1, len(df_resumo) + 1):  # Pular o cabeçalho
            worksheet.write(row, 4, df_resumo.iloc[row-1, 4] if row <= len(df_resumo) else "", wrap_format)  # Coluna E (links)
        
        # Criar uma única página com todos os equipamentos agrupados por escola
        # Isso evita problemas com a mescla de células
        linhas_agrupadas = []
        linha_atual = 0
        
        for escola in escolas_unicas:
            df_escola = df_detalhado[df_detalhado["Escola"] == escola]
            
            # Adicionar linha com nome da escola em negrito
            linhas_agrupadas.append({
                "linha": linha_atual,
                "conteudo": f"ESCOLA: {escola}",
                "formato": escola_format,
                "tipo": "titulo"
            })
            linha_atual += 1
            
            # Adicionar cabeçalho
            for col_num, coluna in enumerate(["Equipamento", "Finalizado", "ID"]):
                linhas_agrupadas.append({
                    "linha": linha_atual,
                    "coluna": col_num,
                    "conteudo": coluna,
                    "formato": header_format,
                    "tipo": "cabecalho"
                })
            linha_atual += 1
            
            # Adicionar dados dos equipamentos
            for _, row in df_escola.iterrows():
                # Coluna Equipamento
                linhas_agrupadas.append({
                    "linha": linha_atual,
                    "coluna": 0,
                    "conteudo": row["Equipamento"],
                    "tipo": "dado"
                })
                
                # Coluna Finalizado
                linhas_agrupadas.append({
                    "linha": linha_atual,
                    "coluna": 1,
                    "conteudo": row["Finalizado"],
                    "tipo": "dado"
                })
                
                # Coluna ID
                linhas_agrupadas.append({
                    "linha": linha_atual,
                    "coluna": 2,
                    "conteudo": row["ID"],
                    "tipo": "dado"
                })
                
                linha_atual += 1
            
            # Adicionar linha em branco entre escolas
            linha_atual += 1
        
        # Criar página detalhada
        worksheet = workbook.add_worksheet("Detalhado")
        
        # Escrever dados na página
        for item in linhas_agrupadas:
            if item["tipo"] == "titulo":
                # Escrever título em toda a linha
                worksheet.write(item["linha"], 0, item["conteudo"], item["formato"])
            elif item["tipo"] == "cabecalho" or item["tipo"] == "dado":
                # Escrever cabeçalho ou dado na célula específica
                formato = item.get("formato", None)
                if formato:
                    worksheet.write(item["linha"], item["coluna"], item["conteudo"], formato)
                else:
                    worksheet.write(item["linha"], item["coluna"], item["conteudo"])
        
        # Ajustar largura das colunas
        worksheet.set_column("A:A", 40)  # Equipamento
        worksheet.set_column("B:B", 15)  # Finalizado
        worksheet.set_column("C:C", 10)  # ID
    
    # Botão para download
    st.download_button(
        label="📂 Baixar Relatório Detalhado por Escola",
        data=output_detalhado.getvalue(),
        file_name=f"detalhado_{setor_escolhido}_{data_ini.strftime('%d-%m-%Y')}_a_{data_fim.strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    
    # Exibir resumo por escola
    st.write("### Resumo por Escola")
    for escola in escolas_unicas:
        df_escola = df_detalhado[df_detalhado["Escola"] == escola]
        total_eq = len(df_escola)
        finalizados = len(df_escola[df_escola["Finalizado"] == "Sim"])
        
        with st.expander(f"**{escola}** - {finalizados}/{total_eq} equipamentos finalizados"):
            # Filtrar apenas os equipamentos desta escola
            st.write("#### Equipamentos Finalizados")
            df_finalizados = df_escola[df_escola["Finalizado"] == "Sim"]
            if not df_finalizados.empty:
                for _, row in df_finalizados.iterrows():
                    st.write(f"- {row['Equipamento']}")
            else:
                st.warning("Nenhum equipamento finalizado.")
            
            st.write("#### Equipamentos Pendentes")
            df_pendentes = df_escola[df_escola["Finalizado"] == "Não"]
            if not df_pendentes.empty:
                for _, row in df_pendentes.iterrows():
                    st.write(f"- {row['Equipamento']}")
            else:
                st.success("Nenhum equipamento pendente.")
