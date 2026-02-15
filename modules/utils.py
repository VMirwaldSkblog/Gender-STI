# modules/utils.py
import pandas as pd

# Lista dos meses em português na ordem correta
meses_lista = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Mapeamento do nome dos meses do inglês para português
mes_map_en_to_pt = {
    "January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril",
    "May": "Maio", "June": "Junho", "July": "Julho", "August": "Agosto",
    "September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro"
}

# Retorna o nome de arquivo apropriado conforme o filtro
def gerar_nome_arquivo_exportacao(meses, anos):
    if not meses or not anos:
        return "Exportacao_Docentes.csv"

    meses_ordenados = ordenar_meses_pt(meses)
    anos_ordenados = sorted(anos)

    if len(meses) == 1 and len(anos) > 1:
        return f"Docentes_{meses[0]}_{'-'.join(map(str, anos_ordenados))}.csv"

    if len(anos) == 1 and len(meses) > 1:
        return f"Docentes_Meses_{anos[0]}.csv"

    if len(anos) == 1 and len(meses) == 1:
        return f"Docentes_{meses[0]}_{anos[0]}.csv"

    return f"Docentes_Filtros.csv"

# Ordena uma lista de nomes de meses em português na ordem correta
def ordenar_meses_pt(lista_meses):
    return sorted(lista_meses, key=lambda m: meses_lista.index(m))

# Verifica se um mês/ano já existe na base consolidada
def verificar_mes_ano_na_base(df_base, mes, ano):
    if "DataReferencia" not in df_base.columns:
        return False
    df_base["DataReferencia"] = pd.to_datetime(df_base["DataReferencia"], errors="coerce")
    return any(
        (df_base["DataReferencia"].dt.month == mes) &
        (df_base["DataReferencia"].dt.year == ano)
    )

# Formata a data no formato "Mês/Ano" em português
def formatar_data_referencia(data):
    if pd.isnull(data):
        return "Data inválida"
    return f"{meses_lista[data.month - 1]}/{data.year}"

# Retorna o mês e ano mais recentes da base
def obter_mes_ano_recente(df):
    data_mais_recente = pd.to_datetime(df["DataReferencia"], errors="coerce").max()
    nome_mes = meses_lista[data_mais_recente.month - 1]
    ano = data_mais_recente.year
    return nome_mes, ano
