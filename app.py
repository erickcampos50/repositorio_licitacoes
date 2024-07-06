import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote_plus


# URL base da API
API_URL = "https://pncp.gov.br/api/search/"
PNCP_URL = "https://pncp.gov.br/app/editais?"

st.title("Repositório nacional de contratações públicas")
st.caption("(EM FASE DE TESTES)")

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
st.markdown(f"###### Para pesquisar no site oficial do PNCP [Clique aqui]({pesquisa_url})", unsafe_allow_html=True)

# Botão de Busca Detalhada
with st.expander("Entenda a *Busca Detalhada*"):
    st.write("Acesse a Busca Detalhada para uma análise profunda das contratações públicas. Além de todos os dados básicos, esta busca expande suas informações incluindo detalhes de todos os arquivos relacionados à contratação, como documentos e registros oficiais, e um descritivo completo dos itens contratados. Apesar do maior tempo de execução, essa versão da busca permite uma visão mais clara e completa do processo evitando que tenha que clcar em multiplos links e abas para ter acesso a esses dados.")
    
# Botão de Busca Simples
with st.expander("Entenda a *Busca Rápida*"):
    st.write("Utilize a Busca Rápida para verificar rapidamente os dados básicos das contratações públicas disponíveis no PNCP. Este botão proporciona uma visão geral e rápida, sendo necessário acessar o PNCP para maiores informações.")
    



# Consulta principal
if st.button("Busca detalhada"):
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
                st.markdown(f"""
                        ### [{item['title']}]({link_url})
                
                        Descrição: {item['description']}

                        Órgão: {item['orgao_nome']}

                        Modalidade: {item['modalidade_licitacao_nome']}

                        Local: {item['municipio_nome']}/{item['uf']} 
                        """)
            
            
                
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

# Consulta 2
if st.button("Busca rápida"):
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
                st.markdown(f"""
                        ### [{item['title']}]({link_url})
                
                        Descrição: {item['description']}

                        Órgão: {item['orgao_nome']}

                        Modalidade: {item['modalidade_licitacao_nome']}

                        Local: {item['municipio_nome']}/{item['uf']} 
                        """)
            

    
        else:
            st.write("Nenhum resultado encontrado.")
    else:
        st.write("Erro na requisição à API.")