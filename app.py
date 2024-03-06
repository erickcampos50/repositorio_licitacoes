import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote_plus


# URL base da API
API_URL = "https://pncp.gov.br/api/search/"
PNCP_URL = "https://pncp.gov.br/app/editais?"

st.title("Repositório nacional de contratações públicas (EM FASE DE TESTES)")

# Criação de campos de entrada para os parâmetros da busca
query = st.text_input("Digite os termos para buscar no Portal Nacional de Compras Públicas")
# tipos_documento = st.selectbox("Tipo de Documento", ["edital"], index=0)
# ordenacao = st.selectbox("Ordenação", ["-relevancia", "relevancia"], index=0)
tam_pagina = st.number_input("Resultados exibidos por página", min_value=1, max_value=100, value=50)
# status = st.selectbox("Status", ["todos", "divulgada", "em andamento"], index=0)


# Modalidades de Licitação
modalidades = {
    "Dispensa de Licitação": "8",
    "Pregão - Eletrônico": "6",
    "Inexigibilidade": "9",
    "Dispensa": "8",
    "Concorrência - Eletrônica": "4",
    "Credenciamento": "12",
    "Pregão - Presencial": "7",
    "Concorrência - Presencial": "5",
    "Leilão - Eletrônico": "1",
    "Leilão - Presencial": "13",
}

modalidade_nome = st.multiselect("Exibir somente resultados da seguinte modalidade de licitação (deixe em branco para exibir todos)", list(modalidades.keys()))
modalidade_id = "|".join([modalidades[nome] for nome in modalidade_nome])

# Modificação para o campo "esferas"
esfera_nomes = ["Federal", "Estadual", "Municipal"]
esfera_valores = {"Federal": "F", "Estadual": "E", "Municipal": "M"}
esfera_selecionada = st.selectbox("Esfera", esfera_nomes)
esfera_id = esfera_valores[esfera_selecionada]

#%%
        
# Definição de funções para as consultas adicionais
def get_itens(orgao_id, ano, numero_sequencial):
    url_itens = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_id}/compras/{ano}/{numero_sequencial}/itens?pagina=1&tamanhoPagina=50"
    response = requests.get(url_itens)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_arquivos(orgao_id, ano, numero_sequencial):
    url_arquivos = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_id}/compras/{ano}/{numero_sequencial}/arquivos?pagina=1&tamanhoPagina=50"
    response = requests.get(url_arquivos)
    if response.status_code == 200:
        return response.json()
    else:
        return None
pagina = st.number_input("Exibir a página:", min_value=1, value=1)


query_url_formatado = quote_plus(query)

# Construindo a URL de pesquisa
pesquisa_url = (
    f"{PNCP_URL}"
    f"q={query_url_formatado}&"
    f"tipos_documento=edital&"
    f"ordenacao=relevancia&"
    f"pagina={pagina}&"
    f"tam_pagina={tam_pagina}&"
    f"status=todos&"
    f"esferas={esfera_id}&"
    f"modalidades={modalidade_id}"
)

# Exibindo a URL
st.markdown(f"Para pesquisar no site oficial do PNCP [Clique aqui]({pesquisa_url})", unsafe_allow_html=True)


# Consulta principal
if st.button("Busca completa"):
    params = {
        "q": query,
        "tipos_documento": "edital",
        "ordenacao": "relevancia",
        "pagina": pagina,
        "tam_pagina": tam_pagina,
        "status": "todos",
        "esferas": esfera_id,
        "modalidades": modalidade_id, # Usando o ID da modalidade selecionada
    }    
    response = requests.get(API_URL, params=params)
    


    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            for item in items:
                st.divider()
                
                # Extraindo dados necessários para as consultas adicionais
                orgao_id, ano, numero_sequencial = item['item_url'].split('/')[-3:]
                
                # Consulta adicional 1: Itens
                itens = get_itens(orgao_id, ano, numero_sequencial)

                link_url = f"https://pncp.gov.br/app/editais/{orgao_id}/{ano}/{numero_sequencial}"
                st.write(f"### [{item['title']}]({link_url})")
                
                
                st.write(f"Descrição: {item['description']}")
            
            
            
                
                if itens:
                    itens_df = pd.DataFrame(itens)
                    # Formatação de 'valorTotal' como monetário e 'quantidade' com duas casas decimais
                    itens_df['valorTotal'] = itens_df['valorTotal'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'temp').replace('.', ',').replace('temp', '.'))
                    itens_df['quantidade'] = itens_df['quantidade'].apply(lambda x: f"{x:.2f}")
                    st.write("#### Itens da Contratação:")
                    st.table(itens_df[['descricao', 'valorTotal', 'quantidade', 'unidadeMedida']])
                
                # Consulta adicional 2: Arquivos
                arquivos = get_arquivos(orgao_id, ano, numero_sequencial)
                if arquivos:
                    st.write("#### Arquivos da contratação:")
                    for arquivo in arquivos:
                        st.link_button(arquivo['titulo'], arquivo['url'],type="secondary", disabled=False, use_container_width=True)
    
        else:
            st.write("Nenhum resultado encontrado.")
    else:
        st.write("Erro na requisição à API.")
# Consulta principal
if st.button("Busca simples"):
    params = {
        "q": query,
        "tipos_documento": "edital",
        "ordenacao": "relevancia",
        "pagina": pagina,
        "tam_pagina": tam_pagina,
        "status": "todos",
        "esferas": esfera_id,
        "modalidades": modalidade_id, # Usando o ID da modalidade selecionada
    }    
    response = requests.get(API_URL, params=params)
    


    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            for item in items:
                st.divider()

                # Extraindo dados necessários para as consultas adicionais
                orgao_id, ano, numero_sequencial = item['item_url'].split('/')[-3:]
                
                # Consulta adicional 1: Itens
                itens = get_itens(orgao_id, ano, numero_sequencial)

                link_url = f"https://pncp.gov.br/app/editais/{orgao_id}/{ano}/{numero_sequencial}"
                st.write(f"### [{item['title']}]({link_url})")
                
                


                st.write(f"Descrição: {item['description']}")

    
        else:
            st.write("Nenhum resultado encontrado.")
    else:
        st.write("Erro na requisição à API.")