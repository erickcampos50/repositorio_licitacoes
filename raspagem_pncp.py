#%%
import requests
import json
import os
import time


#%%
# Configurações iniciais
API_URL = "https://pncp.gov.br/api/search/"
TAM_PAGINA = 500  # Número de resultados por página a serem solicitados da API
OUTPUT_DIR = "pncp_dados_json"  # Diretório onde os arquivos JSON individuais serão salvos
LOG_FILE = "raspagem_log.json"  # Arquivo para armazenar o log de datas de raspagem
DELAY = 10  # Tempo de espera entre requisições (em segundos) para evitar sobrecarga do servidor
MAX_RETRIES = 3  # Máximo de tentativas para repetição em caso de erro
MAX_PAGES = 250  # Limitar a execução a um número máximo de páginas por execução
#%%
# Criar diretório de saída se não existir
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Carregar o log de raspagem, se existir, ou inicializar um novo log
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r') as log_file:
        raspagem_log = json.load(log_file)
else:
    raspagem_log = {}
#%%
def fetch_data(page, last_date):
    """
    Faz uma requisição à API para obter dados de uma página específica,
    ordenados pela data de publicação no PNCP, e filtrados por uma data mais recente que a última raspagem.

    :param page: Número da página a ser requisitada.
    :param last_date: Data da última raspagem registrada no log para filtrar as raspagens.
    :return: Dados JSON retornados pela API, ou None em caso de erro.
    """
    params = {
        "pagina": page,
        "tam_pagina": TAM_PAGINA,
        "ordenacao": "data",  # Ordenar por data mais antigo
        "data_publicacao_pncp": f">{last_date}",  # Filtrar por data mais recente que a última raspagem
        "q":"",
        "tipos_documento":"edital",
        "status":"todos"

    }
    
    attempts = 0
    while attempts < MAX_RETRIES:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            attempts += 1
            time.sleep(DELAY)
            print(f"Tentativa {attempts}/{MAX_RETRIES} falhou. Erro: {response.status_code}")
    
    print("Máximo de tentativas alcançado. Pulando esta página.")
    return None

def save_item(item):
    """
    Salva um item individual em um arquivo JSON, se ainda não existir no diretório de saída.

    :param item: Dados do item a serem salvos.
    """
    item_id = item.get('id')  # Obter o ID do item (utilizado como nome do arquivo JSON)
    file_path = os.path.join(OUTPUT_DIR, f"{item_id}.json")  # Caminho completo do arquivo JSON

    # Verificar se o arquivo já existe antes de salvar
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(item, file, ensure_ascii=False, indent=4)  # Salvar o item em formato JSON
        print(f"Item {item_id} salvo.")
    else:
        print(f"Item {item_id} já existe. Pulando...")

def update_log(new_date):
    """
    Atualiza o log de raspagem com a data da última raspagem.

    :param new_date: A data mais recente entre os itens raspados.
    """
    raspagem_log['last_raspagem'] = new_date  # Atualizar a data no log
    with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
        json.dump(raspagem_log, log_file, ensure_ascii=False, indent=4)  # Salvar o log atualizado

def main():
    """
    Função principal que coordena a raspagem dos dados, salva os itens em arquivos JSON,
    e atualiza o log de raspagem para evitar redundâncias futuras.
    """
    # Verificar a última data de raspagem registrada no log, ou usar uma data padrão antiga
    last_raspagem = raspagem_log.get('last_raspagem', "1970-01-01T00:00:00")

    page = 1  # Iniciar a raspagem na primeira página
    total_items = 0  # Contador de itens salvos
    newest_date = last_raspagem  # Variável para armazenar a data mais recente encontrada na raspagem atual

    while page <= MAX_PAGES:
        print(f"Buscando dados na página {page} a partir de {last_raspagem}...")
        data = fetch_data(page, last_raspagem)  # Requisitar os dados da página atual

        if data and "items" in data:
            items = data["items"]
            if not items:
                print("Nenhum dado novo encontrado, encerrando.")
                break  # Se não houver mais itens novos, encerrar o loop

            for item in items:
                save_item(item)  # Salvar cada item individualmente como JSON
                total_items += 1

                # Atualizar a data mais recente encontrada durante a raspagem
                item_date = item.get('data_publicacao_pncp', "1970-01-01T00:00:00")
                if item_date > newest_date:
                    newest_date = item_date

            # Atualizar o log de raspagem após cada página processada
            update_log(newest_date)
            page += 1  # Avançar para a próxima página
            time.sleep(DELAY)  # Aguardar antes de realizar a próxima requisição

        else:
            print("Erro na busca ou fim dos dados.")
            break  # Encerrar o loop em caso de erro ou ausência de dados

    print(f"Raspagem concluída. Total de {total_items} registros salvos.")
#%%
if __name__ == "__main__":
    main()  # Executar o script

    # %%
