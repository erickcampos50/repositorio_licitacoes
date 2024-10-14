import requests
import json
import csv
import time
import logging
from datetime import datetime
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Configurações
API_URL = "https://pncp.gov.br/api/search/"
TAM_PAGINA = 500
DELAY = 1
MAX_RETRIES = 3
MAX_PAGES = 1
MAX_THREADS = 10

# Criação de pastas para logs e dados
log_dir = 'Logs'
data_dir = 'Dados_CSV'
os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# Configuração de logging
log_file = os.path.join(log_dir, f'crawler_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Variáveis globais para estatísticas
total_items = 0
new_items = 0
duplicate_items = 0
error_count = 0
start_time = None

# Flag para controle de cancelamento
cancel_flag = False

def fetch_data(page, ordenacao):
    """
    Função para buscar dados da API principal.
    """
    global error_count
    params = {
        "pagina": page,
        "tam_pagina": TAM_PAGINA,
        "ordenacao": ordenacao,
        "q": "",
        "tipos_documento": "edital",
        "status": "todos"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            error_count += 1
            logging.error(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            print(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY)
            else:
                logging.error(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                print(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                return None

def save_to_csv(data, filename, include_numero_controle_pncp=False):
    """
    Função para salvar dados em arquivo CSV.
    """
    fieldnames = data[0].keys() if data else []
    if include_numero_controle_pncp:
        fieldnames = ['numero_controle_pncp'] + list(fieldnames)

    file_path = os.path.join(data_dir, filename)
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for item in data:
            if include_numero_controle_pncp:
                new_item = {'numero_controle_pncp': item.get('numero_controle_pncp', '')}
                new_item.update(item)
                writer.writerow(new_item)
            else:
                writer.writerow(item)

def check_duplicate(items, filename='pncp_data.csv'):
    """
    Função para verificar duplicatas baseado no número de controle PNCP.
    """
    existing_ids = set()
    file_path = os.path.join(data_dir, filename)
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_ids = set(row['numero_controle_pncp'] for row in reader)
    
    new_items = [item for item in items if item['numero_controle_pncp'] not in existing_ids]
    return new_items, len(items) - len(new_items)

def fetch_additional_data(orgao_cnpj, ano, numero_sequencial, data_type):
    """
    Função para buscar dados adicionais (itens ou arquivos) da API.
    """
    url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_cnpj}/compras/{ano}/{numero_sequencial}/{data_type}?pagina=1&tamanhoPagina=20"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Erro na tentativa {attempt + 1} para {data_type}: {str(e)}")
            print(f"Erro na tentativa {attempt + 1} para {data_type}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY)
    
    return None

def check_for_cancel():
    """
    Função para verificar se o usuário deseja cancelar o processo.
    """
    global cancel_flag
    while not cancel_flag:
        if input() == 'q':
            cancel_flag = True
            print("Cancelamento solicitado. Aguarde o término da operação atual...")

def download_additional_data(row):
    """
    Função para fazer o download de dados adicionais de forma concorrente.
    """
    if cancel_flag:
        return
    
    orgao_cnpj = row['orgao_cnpj']
    ano = row['ano']
    numero_sequencial = row['numero_sequencial']
    numero_controle_pncp = row['numero_controle_pncp']
    description = row.get('description', 'N/A')
    
    print(f"Iniciando download para compra {numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")
    
    itens = fetch_additional_data(orgao_cnpj, ano, numero_sequencial, 'itens')
    if itens:
        for item in itens:
            item['numero_controle_pncp'] = numero_controle_pncp
        save_to_csv(itens, 'pncp_itens.csv', include_numero_controle_pncp=True)
        print(f"Salvos {len(itens)} itens para compra {numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")
    
    arquivos = fetch_additional_data(orgao_cnpj, ano, numero_sequencial, 'arquivos')
    if arquivos:
        for arquivo in arquivos:
            arquivo['numero_controle_pncp'] = numero_controle_pncp
        save_to_csv(arquivos, 'pncp_arquivos.csv', include_numero_controle_pncp=True)
        print(f"Salvos {len(arquivos)} arquivos para compra {numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")

def main():
    global total_items, new_items, duplicate_items, start_time, cancel_flag

    # Opções de ordenação
    ordenacao_opcoes = {
        '1': ('-data', 'Mais recentes primeiro'),
        '2': ('data', 'Mais antigos primeiro'),
        '3': ('relevancia', 'Ordenados por relevância')
    }

    print("Escolha o parâmetro de ordenação:")
    for key, (_, desc) in ordenacao_opcoes.items():
        print(f"{key}. {desc}")

    escolha = input("Digite o número da opção desejada: ").strip()
    while escolha not in ordenacao_opcoes:
        print("Opção inválida. Por favor, escolha um número válido.")
        escolha = input("Digite o número da opção desejada: ").strip()

    ordenacao, desc = ordenacao_opcoes[escolha]
    print(f"\nIniciando o crawler com ordenação: {desc}")
    print("Digite 'q' e pressione Enter a qualquer momento para cancelar o processo.")

    threading.Thread(target=check_for_cancel, daemon=True).start()

    start_time = time.time()

    for page in range(1, MAX_PAGES + 1):
        if cancel_flag:
            print("Processo cancelado pelo usuário.")
            break

        print(f"\nBuscando dados da página {page}")
        items = fetch_data(page, ordenacao)
        
        if items is None:
            print(f"Nenhum dado retornado para a página {page}")
            continue
        
        if not items:
            print(f"Nenhum item encontrado na página {page}. Finalizando a busca.")
            break
        
        total_items += len(items)
        new_items_page, duplicates = check_duplicate(items)
        
        if new_items_page:
            save_to_csv(new_items_page, 'pncp_data.csv')
            new_items += len(new_items_page)
            print(f"Salvos {len(new_items_page)} novos itens da página {page}")
        else:
            print(f"Nenhum item novo na página {page}")
        
        duplicate_items += duplicates
        
        print(f"Progresso: {total_items} itens processados, {new_items} novos, {duplicate_items} duplicados")
        
        if not cancel_flag:
            print(f"Aguardando {DELAY} segundos antes da próxima requisição...")
            time.sleep(DELAY)

    print("\nIniciando coleta de dados adicionais (itens e arquivos)...")
    
    file_path = os.path.join(data_dir, 'pncp_data.csv')
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(download_additional_data, rows)

    # Relatório final
    end_time = time.time()
    execution_time = end_time - start_time
    
    print("\n--- Relatório Final ---")
    print(f"Tempo de execução: {execution_time:.2f} segundos")
    print(f"Total de itens processados: {total_items}")
    print(f"Novos itens salvos: {new_items}")
    print(f"Itens duplicados (não salvos): {duplicate_items}")
    print(f"Número de erros encontrados: {error_count}")
    print(f"Páginas processadas: {page}")
    print(f"Parâmetro de ordenação utilizado: {desc}")
    print("Para mais detalhes, consulte o arquivo de log.")

    logging.info("Processo de crawling concluído")
    print("\nProcesso de crawling concluído. Verifique os arquivos CSV na pasta 'Dados_CSV' para os resultados.")

if __name__ == "__main__":
    main()