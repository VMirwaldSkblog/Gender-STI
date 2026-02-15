# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from modules.utils import (
    meses_lista,
    mes_map_en_to_pt,
    gerar_nome_arquivo_exportacao,
    ordenar_meses_pt,
    obter_mes_ano_recente
)
import numpy as np

st.set_page_config(page_title="Dashboard Docentes USP", layout="wide")

# --- Constantes e Inicialização ---
BASE_PATH = "Data/USP/Consolidados/USP_Long_Geral.parquet"

# --- Funções Auxiliares ---
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data(path):
    """Carrega e cacheia a base de dados principal."""
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df["DataReferencia"] = pd.to_datetime(df["DataReferencia"], errors="coerce")
        return df
    return None

# --- Carregamento e Exibição dos Dados ---
st.title("📊 Dashboard de Docentes da USP")
df_docentes = load_data(BASE_PATH)

if df_docentes is None:
    st.error("Arquivo da base de dados (`USP_Long_Geral.parquet`) não encontrado. Verifique o caminho.")
    st.stop()

st.success("Dados carregados com sucesso!")

# --- Layout da Barra Lateral (Sidebar) ---
st.sidebar.title("Filtros e Exportação")

# Filtros de navegação: mês e ano
df_docentes["NomeMes"] = df_docentes["DataReferencia"].dt.month_name().map(mes_map_en_to_pt)
meses_disponiveis = df_docentes["NomeMes"].dropna().unique().tolist()
meses_disponiveis = ordenar_meses_pt(meses_disponiveis)
anos_disponiveis = sorted([y for y in df_docentes["DataReferencia"].dt.year.unique() if not pd.isna(y)])

ultimo_mes_nome, ultimo_ano = obter_mes_ano_recente(df_docentes)

# --- Layout Principal com Abas ---
tab_comparativo, tab_carreira = st.tabs(["Comparativo entre Períodos", "Análise de Carreira"])

with tab_comparativo:
    st.header("Comparativo de Gênero entre Períodos")

    col_filt_1, col_filt_2 = st.columns(2)
    with col_filt_1:
        st.markdown("##### 📅 Período 1")
        mes1 = st.selectbox("Mês (Período 1):", options=meses_disponiveis, index=len(meses_disponiveis)-2 if len(meses_disponiveis) > 1 else 0, key="mes1")
        ano1 = st.selectbox("Ano (Período 1):", options=anos_disponiveis, index=len(anos_disponiveis)-1, key="ano1")

    with col_filt_2:
        st.markdown("##### 📅 Período 2")
        mes2 = st.selectbox("Mês (Período 2):", options=meses_disponiveis, index=len(meses_disponiveis)-1, key="mes2")
        ano2 = st.selectbox("Ano (Período 2):", options=anos_disponiveis, index=len(anos_disponiveis)-1, key="ano2")

    # Filtros
    df1 = df_docentes[(df_docentes["NomeMes"] == mes1) & (df_docentes["DataReferencia"].dt.year == ano1)]
    df2 = df_docentes[(df_docentes["NomeMes"] == mes2) & (df_docentes["DataReferencia"].dt.year == ano2)]

    if df1.empty or df2.empty:
        st.warning("Dados não disponíveis para um dos períodos selecionados.")
    elif 'classification' not in df_docentes.columns:
        st.error("A coluna 'classification' (gênero) não foi encontrada na base de dados.")
    else:
        # Cálculos
        total1, mulheres1, homens1 = len(df1), len(df1[df1['classification'] == 'F']), len(df1[df1['classification'] == 'M'])
        perc_mulheres1 = (mulheres1 / total1) * 100 if total1 > 0 else 0
        total2, mulheres2, homens2 = len(df2), len(df2[df2['classification'] == 'F']), len(df2[df2['classification'] == 'M'])
        perc_mulheres2 = (mulheres2 / total2) * 100 if total2 > 0 else 0
        delta_perc_mulheres = perc_mulheres2 - perc_mulheres1

        st.markdown("---")
        st.markdown(f"#### Comparando **{mes1}/{ano1}** com **{mes2}/{ano2}**")
        st.metric(
            label=f"% de Mulheres em {mes2}/{ano2}",
            value=f"{perc_mulheres2:.2f}%",
            delta=f"{delta_perc_mulheres:.2f} p.p. (vs {mes1}/{ano1})"
        )
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Análise de {mes1}/{ano1}**")
            st.metric("Total de Docentes", f"{total1:,}")
            st.metric("Mulheres", f"{mulheres1:,} ({perc_mulheres1:.1f}%)")
            st.metric("Homens", f"{homens1:,} ({(100-perc_mulheres1):.1f}%)")

        with col2:
            st.markdown(f"**Análise de {mes2}/{ano2}**")
            st.metric("Total de Docentes", f"{total2:,}")
            st.metric("Mulheres", f"{mulheres2:,} ({perc_mulheres2:.1f}%)")
            st.metric("Homens", f"{homens2:,} ({(100-perc_mulheres2):.1f}%)")

        # Gráfico Comparativo
        df_chart = pd.DataFrame([
            {'Periodo': f"{mes1}/{ano1}", 'Gênero': 'Mulheres', 'Quantidade': mulheres1},
            {'Periodo': f"{mes1}/{ano1}", 'Gênero': 'Homens', 'Quantidade': homens1},
            {'Periodo': f"{mes2}/{ano2}", 'Gênero': 'Mulheres', 'Quantidade': mulheres2},
            {'Periodo': f"{mes2}/{ano2}", 'Gênero': 'Homens', 'Quantidade': homens2},
        ])

        fig = px.bar(df_chart, x="Periodo", y="Quantidade", color="Gênero", barmode="group",
                     title="Comparativo de Quantidade de Docentes por Gênero",
                     labels={'Quantidade': 'Número de Docentes'},
                     color_discrete_map={'Mulheres': '#FFA07A', 'Homens': '#20B2AA'})
        st.plotly_chart(fig, use_container_width=True)
        
        csv_comparativo = df_chart.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Baixar dados do gráfico comparativo",
            data=csv_comparativo,
            file_name=f"Comparativo_{mes1.replace('/','')}{ano1}_vs_{mes2.replace('/','')}{ano2}.csv",
            mime="text/csv"
        )

with tab_carreira:
    st.header("Análise de Gênero por Nível de Carreira")
    
    col_filt_c1, col_filt_c2 = st.columns(2)
    with col_filt_c1:
        mes_carreira = st.selectbox("Mês:", options=meses_disponiveis, index=len(meses_disponiveis)-1, key="mes_carreira")
    with col_filt_c2:
        ano_carreira = st.selectbox("Ano:", options=anos_disponiveis, index=len(anos_disponiveis)-1, key="ano_carreira")

    df_carreira = df_docentes[(df_docentes["NomeMes"] == mes_carreira) & (df_docentes["DataReferencia"].dt.year == ano_carreira)].copy()

    if df_carreira.empty:
        st.warning(f"Nenhum dado encontrado para {mes_carreira}/{ano_carreira}.")
    elif 'classification' not in df_carreira.columns:
        st.error("A coluna 'classification' (gênero) não foi encontrada na base de dados.")
    else:
        st.markdown(f"Analisando dados de **{mes_carreira}/{ano_carreira}**")
        
        def analisar_e_exibir(dataframe, coluna, titulo, top_n=15):
            with st.expander(f"Análise por {titulo}", expanded=False):
                if coluna not in dataframe.columns:
                    st.info(f"A coluna '{coluna}' não foi encontrada para gerar esta análise.")
                    return

                df_proc = dataframe.dropna(subset=[coluna])
                if pd.api.types.is_string_dtype(df_proc[coluna]):
                    df_proc = df_proc[df_proc[coluna].str.strip() != '']
                
                if df_proc.empty:
                    st.info(f"Não há dados válidos na coluna '{coluna}' para gerar esta análise.")
                    return

                df_agg = df_proc.groupby([coluna, 'classification']).size().unstack(fill_value=0)
                if 'F' not in df_agg.columns: df_agg['F'] = 0
                if 'M' not in df_agg.columns: df_agg['M'] = 0
                
                df_agg['Total'] = df_agg['F'] + df_agg['M']
                df_agg['% Mulheres'] = np.where(df_agg['Total'] > 0, (df_agg['F'] / df_agg['Total']) * 100, 0)
                df_agg = df_agg.sort_values(by='Total', ascending=False).reset_index()

                # Gráfico
                df_chart = df_agg.head(top_n)
                fig = px.bar(df_chart, y=coluna, x=['F', 'M'],
                                      title=f'Distribuição de Gênero nos {top_n} Principais Itens de "{titulo}"',
                                      labels={'value': 'Quantidade de Docentes', coluna: titulo, 'variable': 'Gênero'},
                                      barmode='stack', orientation='h',
                                      color_discrete_map={'F': '#FFA07A', 'M': '#20B2AA'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

                # Tabela e Download
                st.markdown(f"**Dados detalhados por {titulo}**")
                st.dataframe(df_agg.rename(columns={'F': 'Mulheres', 'M': 'Homens'}).style.format({'% Mulheres': '{:.1f}%'}), use_container_width=True)
                
                csv_data = df_agg.to_csv(index=False, sep=";").encode("utf-8-sig")
                st.download_button(
                    label=f"📥 Baixar dados de {titulo}",
                    data=csv_data,
                    file_name=f"Analise_{titulo.replace('/','')}_{mes_carreira.replace('/','')}{ano_carreira}.csv",
                    mime="text/csv",
                    key=f"download_{coluna}"
                )

        # Chamando a função para cada coluna de análise
        analisar_e_exibir(df_carreira, 'Função de Estrutura', 'Função de Estrutura')
        analisar_e_exibir(df_carreira, 'Ref/MS', 'Referência/MS', top_n=len(df_carreira['Ref/MS'].unique()))
        analisar_e_exibir(df_carreira, 'Unid/Orgão', 'Unidade/Órgão')
        analisar_e_exibir(df_carreira, 'Jornada', 'Jornada', top_n=len(df_carreira['Jornada'].unique()))
        analisar_e_exibir(df_carreira, 'Classe', 'Classe', top_n=len(df_carreira['Classe'].unique()))
