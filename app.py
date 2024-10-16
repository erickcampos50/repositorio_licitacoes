import streamlit as st
import pandas as pd
import sqlite3
from rapidfuzz import process, fuzz
import numpy as np
import os
import unicodedata
import nltk
from nltk.corpus import stopwords

# Função para baixar recursos do NLTK, se necessário
def download_nltk_resources():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

# Chamar a função para garantir que as stop words estão disponíveis
download_nltk_resources()

# Lista de stop words em português do NLTK
PORTUGUESE_STOP_WORDS = stopwords.words('portuguese')

# Configuração da página
st.set_page_config(page_title="Busca Fuzzy em Licitações", layout="wide")

# Função para normalizar o texto (minúsculas e remover acentos)
def preprocess_text(text):
    if not isinstance(text, str):
        return ''
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text

# Função para criar a tabela no banco de dados e adicionar índices
def create_table():
    with sqlite3.connect('dados.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER,
                cancelado INTEGER,
                createdAt TEXT,
                data_assinatura TEXT,
                data_atualizacao_pncp TEXT,
                data_fim_vigencia TEXT,
                data_inicio_vigencia TEXT,
                data_publicacao_pncp TEXT,
                description TEXT,
                doc_type TEXT,
                document_type TEXT,
                esfera_id TEXT,
                esfera_nome TEXT,
                item_id TEXT,
                index_col TEXT,
                item_url TEXT,
                modalidade_licitacao_id INTEGER,
                modalidade_licitacao_nome TEXT,
                municipio_id INTEGER,
                municipio_nome TEXT,
                numero TEXT,
                numero_controle_pncp TEXT,
                numero_sequencial INTEGER,
                numero_sequencial_compra_ata TEXT,
                orgao_cnpj TEXT,
                orgao_id INTEGER,
                orgao_nome TEXT,
                orgao_subrogado_id TEXT,
                orgao_subrogado_nome TEXT,
                poder_id TEXT,
                poder_nome TEXT,
                situacao_id INTEGER,
                situacao_nome TEXT,
                tem_resultado INTEGER,
                tipo_contrato_id TEXT,
                tipo_contrato_nome TEXT,
                tipo_id INTEGER,
                tipo_nome TEXT,
                title TEXT,
                uf TEXT,
                unidade_codigo INTEGER,
                unidade_id INTEGER,
                unidade_nome TEXT,
                valor_global REAL
            )
        ''')
        # Adicionar índices para acelerar consultas
        c.execute('CREATE INDEX IF NOT EXISTS idx_modalidade ON items (modalidade_licitacao_nome)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_esfera ON items (esfera_nome)')
        conn.commit()

# Função para verificar se os dados já foram carregados
@st.cache_data
def check_data_loaded():
    with sqlite3.connect('dados.db') as conn:
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM items")
            count = c.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            st.error(f"Erro ao verificar dados: {e}")
            return False

# Função para inserir dados no banco de dados
def insert_data(df):
    with sqlite3.connect('dados.db') as conn:
        try:
            df.to_sql('items', conn, if_exists='append', index=False)
        except ValueError as ve:
            st.error(f"Erro ao inserir dados: {ve}")
        except sqlite3.Error as e:
            st.error(f"Erro no banco de dados: {e}")

# Função para buscar dados no banco de dados com ou sem filtros
@st.cache_data
def search_data(modalidade=None, esfera=None):
    with sqlite3.connect('dados.db') as conn:
        c = conn.cursor()
        base_query = '''
            SELECT description, orgao_nome, municipio_nome 
            FROM items 
        '''
        params = []
        conditions = []
        if modalidade:
            conditions.append("modalidade_licitacao_nome = ?")
            params.append(modalidade)
        if esfera:
            conditions.append("esfera_nome = ?")
            params.append(esfera)
        if conditions:
            base_query += "WHERE " + " AND ".join(conditions)
        try:
            c.execute(base_query, params)
            results = c.fetchall()
            return results
        except sqlite3.Error as e:
            st.error(f"Erro ao buscar dados: {e}")
            return []

# Função para calcular a similaridade (não será mais usada)
# Removida conforme a mudança para busca fuzzy

# Função para realizar a busca fuzzy
def fuzzy_search(query, descriptions, limit=20, score_cutoff=60):
    """
    Realiza uma busca fuzzy usando RapidFuzz.
    Retorna uma lista de tuplas (descrição, órgão, município, score).
    """
    # Pré-processar o texto de busca
    processed_query = preprocess_text(query)
    # Realizar a busca fuzzy
    results = process.extract(
        processed_query,
        descriptions,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=score_cutoff
    )
    # Processar os resultados
    final_results = []
    for match in results:
        description = match[0]
        score = match[1]
        # Encontrar os dados correspondentes no banco
        # Supondo que a descrição seja única (se não for, ajustar conforme necessário)
        # Poderia usar um dicionário para mapear descrições para orgao_nome e municipio_nome
        # Para melhorar a performance, criar um dicionário no início
        final_results.append((description, score))
    return final_results

# Função para mapear colunas do DataFrame para a tabela SQLite
def map_columns(df):
    # Renomear 'index' para 'index_col' para evitar conflito com palavra reservada
    if 'index' in df.columns:
        df = df.rename(columns={'index': 'index_col'})
    # Garantir que todas as colunas existam no DataFrame
    expected_columns = [
        'ano', 'cancelado', 'createdAt', 'data_assinatura', 'data_atualizacao_pncp',
        'data_fim_vigencia', 'data_inicio_vigencia', 'data_publicacao_pncp',
        'description', 'doc_type', 'document_type', 'esfera_id', 'esfera_nome',
        'item_id', 'index_col', 'item_url', 'modalidade_licitacao_id',
        'modalidade_licitacao_nome', 'municipio_id', 'municipio_nome', 'numero',
        'numero_controle_pncp', 'numero_sequencial', 'numero_sequencial_compra_ata',
        'orgao_cnpj', 'orgao_id', 'orgao_nome', 'orgao_subrogado_id',
        'orgao_subrogado_nome', 'poder_id', 'poder_nome', 'situacao_id',
        'situacao_nome', 'tem_resultado', 'tipo_contrato_id', 'tipo_contrato_nome',
        'tipo_id', 'tipo_nome', 'title', 'uf', 'unidade_codigo', 'unidade_id',
        'unidade_nome', 'valor_global'
    ]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None  # Preencher com valores nulos se a coluna não existir
    return df[expected_columns]

# Função para carregar dados (padrão ou upload)
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep='\t')  # Especifica separador de tabulação
            df = map_columns(df)
            insert_data(df)
            st.success("Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar arquivo CSV: {e}")
    else:
        # Carregar dados do arquivo CSV padrão
        default_csv_path = os.path.join('Dados_CSV', 'pncp_data_pregão.csv')
        if os.path.exists(default_csv_path):
            try:
                df = pd.read_csv(default_csv_path, sep='\t')  # Especifica separador de tabulação
                df = map_columns(df)
                insert_data(df)
                st.success("Dados padrão carregados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao carregar dados padrão: {e}")
        else:
            st.warning("Arquivo CSV padrão não encontrado. Por favor, faça o upload de um arquivo CSV separado por tabulações.")

# Inicializar a tabela e adicionar índices
create_table()

# Verificar se os dados já foram carregados
if not check_data_loaded():
    load_data()

# Interface principal
st.title("Busca Fuzzy em Licitações")

# Upload de arquivo CSV
uploaded_file = st.file_uploader("Escolha um arquivo CSV separado por tabulações", type="csv")
if uploaded_file is not None:
    load_data(uploaded_file)

# Busca por similaridade (agora Fuzzy)
st.header("Busca Fuzzy")

# Adicionar opções de busca e filtros
with st.form("search_form"):
    # Opção para selecionar o tipo de busca (Fuzzy ou Simples)
    search_fuzzy = st.checkbox("Realizar Busca Fuzzy", value=True)
    
    # Opção para aplicar filtros
    apply_filters = st.checkbox("Aplicar Filtros na Busca", value=False)
    
    # Controle de limite de resultados
    result_limit = st.slider("Número de Resultados", min_value=1, max_value=100, value=20)
    
    # Se aplicar filtros, mostrar os selectboxes
    if apply_filters:
        # Obter opções únicas para os filtros
        with sqlite3.connect('dados.db') as conn:
            try:
                df_modalidades = pd.read_sql_query("SELECT DISTINCT modalidade_licitacao_nome FROM items", conn)
                modalidades = sorted(df_modalidades['modalidade_licitacao_nome'].dropna().unique().tolist())
            except sqlite3.Error as e:
                st.error(f"Erro ao obter modalidades: {e}")
                modalidades = []
        
        with sqlite3.connect('dados.db') as conn:
            try:
                df_esferas = pd.read_sql_query("SELECT DISTINCT esfera_nome FROM items", conn)
                esferas = sorted(df_esferas['esfera_nome'].dropna().unique().tolist())
            except sqlite3.Error as e:
                st.error(f"Erro ao obter esferas: {e}")
                esferas = []

        modalidade = st.selectbox("Modalidade de Licitação", ["-- Sem Filtro --"] + modalidades)
        esfera = st.selectbox("Esfera", ["-- Sem Filtro --"] + esferas)
    else:
        modalidade = None
        esfera = None

    # Campo de busca
    query = st.text_input("Digite sua busca:")

    # Botão de busca
    submitted = st.form_submit_button("Buscar")

# Inicializar session_state para armazenar resultados
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'filtered_results' not in st.session_state:
    st.session_state['filtered_results'] = None

# Executar busca quando o botão for clicado
if submitted:
    if not query.strip():
        st.warning("Por favor, insira um termo de busca.")
    else:
        # Determinar se filtros devem ser aplicados
        selected_modalidade = modalidade if apply_filters and modalidade != "-- Sem Filtro --" else None
        selected_esfera = esfera if apply_filters and esfera != "-- Sem Filtro --" else None

        # Realizar a busca
        if search_fuzzy:
            # Busca Fuzzy
            results = search_data(selected_modalidade, selected_esfera)
            if results:
                descriptions = [str(r[0]) if r[0] else "" for r in results]  # Tratar descrições nulas
                # Criação de um dicionário para mapear descrições a orgao_nome e municipio_nome
                description_map = {preprocess_text(r[0]): (r[1], r[2]) for r in results if r[0]}
                # Realizar a busca fuzzy
                fuzzy_results = process.extract(
                    preprocess_text(query),
                    description_map.keys(),
                    scorer=fuzz.WRatio,
                    limit=result_limit
                )
                # Filtrar os resultados com score adequado
                filtered_fuzzy_results = [
                    (desc, description_map[desc], score)
                    for desc, score, _ in fuzzy_results
                    if score >= 60  # Ajustar o score_cutoff conforme necessário
                ]
                # Armazenar no session_state
                st.session_state['results'] = filtered_fuzzy_results
                st.session_state['filtered_results'] = filtered_fuzzy_results  # Inicialmente, sem filtros adicionais
            else:
                st.session_state['results'] = []
                st.session_state['filtered_results'] = []
        else:
            # Busca Simples
            results = search_data(selected_modalidade, selected_esfera)
            if results:
                # Armazenar no session_state sem similaridade
                st.session_state['results'] = [(r[0], r[1], r[2], None) for r in results]
                st.session_state['filtered_results'] = st.session_state['results']
            else:
                st.session_state['results'] = []
                st.session_state['filtered_results'] = []

# Se houver resultados armazenados, exibir
if st.session_state['results']:
    # Opção para aplicar filtros adicionais nos resultados
    st.subheader("Filtros Adicionais nos Resultados")
    with st.expander("Aplicar Filtros Adicionais"):
        # Obter todas as modalidades e esferas dos resultados
        modalidades_results = sorted(list(set([res[1][0] for res in st.session_state['results'] if res[1][0]])))
        esferas_results = sorted(list(set([res[1][1] for res in st.session_state['results'] if res[1][1]])))

        # Filtros adicionais
        modalidade_filter = st.selectbox("Filtrar por Modalidade de Licitação", ["-- Sem Filtro --"] + modalidades_results)
        esfera_filter = st.selectbox("Filtrar por Esfera", ["-- Sem Filtro --"] + esferas_results)

        # Botão para aplicar filtros adicionais
        apply_additional_filters = st.button("Aplicar Filtros Adicionais")

    # Aplicar filtros adicionais se o botão for clicado
    if apply_additional_filters:
        filtered_results = st.session_state['results']
        if modalidade_filter != "-- Sem Filtro --":
            filtered_results = [res for res in filtered_results if res[1][0] == modalidade_filter]
        if esfera_filter != "-- Sem Filtro --":
            filtered_results = [res for res in filtered_results if res[1][1] == esfera_filter]
        # Atualizar os resultados para exibição
        st.session_state['filtered_results'] = filtered_results

    # Exibir os resultados filtrados
    st.subheader("Resultados:")
    if st.session_state['filtered_results']:
        for res in st.session_state['filtered_results']:
            desc, orgao, municipio, score = res
            if search_fuzzy and score is not None:
                st.markdown(f"**Similaridade:** {score:.2f}")
            st.markdown(f"**Descrição:** {desc}")
            st.markdown(f"**Órgão:** {orgao}")
            st.markdown(f"**Município:** {municipio}")
            st.markdown("---")
    else:
        st.write("Nenhum resultado encontrado após aplicar os filtros.")
elif st.session_state['results'] == []:
    st.write("Nenhum resultado encontrado.")
