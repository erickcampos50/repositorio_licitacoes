import streamlit as st
import requests
import pandas as pd


# URL base da API
API_URL = "https://pncp.gov.br/api/search/"

st.title("Repositório nacional de obras públicas")

# Criação de campos de entrada para os parâmetros da busca
query = st.text_input("Palavra-chave", "galpão")
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

# if st.button("Buscar"):
#     params = {
#         "q": query,
#         "tipos_documento": tipos_documento,
#         "ordenacao": ordenacao,
#         "pagina": pagina,
#         "tam_pagina": tam_pagina,
#         "status": status,
#         "esferas": esferas,
#         "modalidades": modalidade_id, # Usando o ID da modalidade selecionada
#     }
#     response = requests.get(API_URL, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         items = data.get("items", [])
#         if items:
#             for item in items:
#                 st.write(f"### {item['title']}")
#                 st.write(f"Descrição: {item['description']}")
#                 st.write(f"URL: {item['item_url']}")
#         else:
#             st.write("Nenhum resultado encontrado.")
        
#         # Exibição da URL de requisição
#         request_url = f"{response.url}"
#         st.markdown(f"<a href='{request_url}' target='_blank'>Clique aqui para executar a consulta na API</a>", unsafe_allow_html=True)
#     else:
#         st.write("Erro na requisição à API.")
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
# Consulta principal
if st.button("Buscar"):
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
                st.write(f"### {item['title']}")
                st.write(f"Descrição: {item['description']}")
                
                # Extraindo dados necessários para as consultas adicionais
                orgao_id, ano, numero_sequencial = item['item_url'].split('/')[-3:]
                
                # Consulta adicional 1: Itens
                itens = get_itens(orgao_id, ano, numero_sequencial)
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