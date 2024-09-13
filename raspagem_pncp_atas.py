#%%
import requests
import json
import os
import time

#%%
# Configurações iniciais para o novo endpoint
API_URL_NEW = "https://pncp.gov.br/api/search/"
TAM_PAGINA_NEW = 500  # Número de resultados por página a serem solicitados da API
OUTPUT_DIR_NEW = "pncp_atas_json"  # Diretório onde os arquivos JSON individuais serão salvos
LOG_FILE_NEW = "raspagem_atas_log.json"  # Arquivo para armazenar o log de datas de raspagem
DELAY_NEW = 10  # Tempo de espera entre requisições (em segundos) para evitar sobrecarga do servidor
MAX_RETRIES_NEW = 3  # Máximo de tentativas para repetição em caso de erro
MAX_PAGES_NEW = 21  # Limitar a execução a um número máximo de páginas por execução

#%%
# Criar diretório de saída se não existir
if not os.path.exists(OUTPUT_DIR_NEW):
    os.makedirs(OUTPUT_DIR_NEW)

# Carregar o log de raspagem, se existir, ou inicializar um novo log
if os.path.exists(LOG_FILE_NEW):
    with open(LOG_FILE_NEW, 'r', encoding='utf-8') as log_file:
        raspagem_log_new = json.load(log_file)
else:
    raspagem_log_new = {}

#%%
def fetch_data_new(page, last_date):
    """
    Faz uma requisição à API para obter dados de uma página específica,
    ordenados pela data de publicação no PNCP (mais recente primeiro),
    e filtrados por uma data mais recente que a última raspagem.

    :param page: Número da página a ser requisitada.
    :param last_date: Data da última raspagem registrada no log para filtrar as raspagens.
    :return: Dados JSON retornados pela API, ou None em caso de erro.
    """
    params = {
        "q": "",
        "tipos_documento": "ata",
        "ordenacao": "-data",   # Ordenar por data mais recente. Existem as opções "relevancia","data" (mais antigo) e "-data" para data mais recente
        "pagina": page,
        "tam_pagina": TAM_PAGINA_NEW,
        "status": "vigente",
        # "ufs": "MG",
        # "modalidades": "9"
    }

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ja;q=0.5',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    attempts = 0
    while attempts < MAX_RETRIES_NEW:
        try:
            response = requests.get(API_URL_NEW, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                attempts += 1
                time.sleep(DELAY_NEW)
                print(f"Tentativa {attempts}/{MAX_RETRIES_NEW} falhou. Erro: {response.status_code}")
        except requests.exceptions.RequestException as e:
            attempts += 1
            time.sleep(DELAY_NEW)
            print(f"Tentativa {attempts}/{MAX_RETRIES_NEW} falhou com exceção: {e}")

    print("Máximo de tentativas alcançado. Pulando esta página.")
    return None

def save_item_new(item):
    """
    Salva um item individual em um arquivo JSON, se ainda não existir no diretório de saída.

    :param item: Dados do item a serem salvos.
    """
    item_id = item.get('id')  # Obter o ID do item (utilizado como nome do arquivo JSON)
    file_path = os.path.join(OUTPUT_DIR_NEW, f"{item_id}.json")  # Caminho completo do arquivo JSON

    # Verificar se o arquivo já existe antes de salvar
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(item, file, ensure_ascii=False, indent=4)  # Salvar o item em formato JSON
        print(f"Item {item_id} salvo.")
    else:
        print(f"Item {item_id} já existe. Pulando...")

def update_log_new(new_date):
    """
    Atualiza o log de raspagem com a data da última raspagem.

    :param new_date: A data mais recente entre os itens raspados.
    """
    raspagem_log_new['last_raspagem'] = new_date  # Atualizar a data no log
    with open(LOG_FILE_NEW, 'w', encoding='utf-8') as log_file:
        json.dump(raspagem_log_new, log_file, ensure_ascii=False, indent=4)  # Salvar o log atualizado

def main_new():
    """
    Função principal que coordena a raspagem dos dados do novo endpoint,
    salva os itens em arquivos JSON, e atualiza o log de raspagem para evitar redundâncias futuras.
    """
    global raspagem_log_new  # Garantir que estamos modificando a variável global

    # Verificar a última data de raspagem registrada no log, ou usar uma data padrão antiga
    last_raspagem = raspagem_log_new.get('last_raspagem', "1970-01-01T00:00:00")

    page = 1  # Iniciar a raspagem na primeira página
    total_items = 0  # Contador de itens salvos
    newest_date = last_raspagem  # Variável para armazenar a data mais recente encontrada na raspagem atual

    while page <= MAX_PAGES_NEW:
        print(f"Buscando dados na página {page} a partir de {last_raspagem}...")
        data = fetch_data_new(page, last_raspagem)  # Requisitar os dados da página atual

        if data and "items" in data:
            items = data["items"]
            if not items:
                print("Nenhum dado novo encontrado, encerrando.")
                break  # Se não houver mais itens novos, encerrar o loop

            for item in items:
                save_item_new(item)  # Salvar cada item individualmente como JSON
                total_items += 1

                # Atualizar a data mais recente encontrada durante a raspagem
                item_date = item.get('data_publicacao_pncp', "1970-01-01T00:00:00")
                if item_date > newest_date:
                    newest_date = item_date

            # Atualizar o log de raspagem após cada página processada
            update_log_new(newest_date)
            page += 1  # Avançar para a próxima página
            time.sleep(DELAY_NEW)  # Aguardar antes de realizar a próxima requisição

        else:
            print("Erro na busca ou fim dos dados.")
            break  # Encerrar o loop em caso de erro ou ausência de dados

    print(f"Raspagem concluída. Total de {total_items} registros salvos.")

#%%
if __name__ == "__main__":
    main_new()
    # Se desejar executar também o script existente para o endpoint anterior, descomente abaixo:
    # main()  # Assegure-se de que a função main() do código original esteja definida no mesmo script ou importada adequadamente

# %%
