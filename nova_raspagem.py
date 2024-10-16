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
import zipfile
from urllib.parse import urlparse
from io import BytesIO
import argparse
import pandas as pd

# Configurações
API_URL = "https://pncp.gov.br/api/search/"
TAM_PAGINA = 500
DELAY = 1
MAX_RETRIES = 1
MAX_PAGES = 21
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
items_saved = 0
arquivos_saved = 0
removed_duplicates = 0

# Flag para controle de cancelamento
cancel_flag = False

def fetch_data(page, ordenacao, modo):
    global error_count
    tipos_documento = "edital" if modo == "pregão" else "ata"
    params = {
        "pagina": page,
        "tam_pagina": TAM_PAGINA,
        "ordenacao": ordenacao,
        "q": "",
        "tipos_documento": tipos_documento,
        "status": "todos"
    }
    headers = {
        'User-Agent': 'PNCP Crawler - Academic Project'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(API_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
        except requests.RequestException as e:
            error_count += 1
            logging.error(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            print(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY * (2 ** attempt))
            else:
                logging.error(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                print(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                return None

def save_to_csv(data, filename):
    if not data:
        return
    
    fieldnames = sorted(data[0].keys())  # Ordena os campos para garantir a consistência
    file_path = os.path.join(data_dir, filename)
    file_exists = os.path.isfile(file_path)
    
    mode = 'a' if file_exists else 'w'
    with open(file_path, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
        
        if not file_exists:
            writer.writeheader()
        
        for item in data:
            ordered_item = {field: item.get(field, '') for field in fieldnames}
            writer.writerow(ordered_item)

def check_duplicate(items, filename):
    existing_ids = set()
    file_path = os.path.join(data_dir, filename)
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            existing_ids = set(row['numero_controle_pncp'] for row in reader)
    
    new_items = [item for item in items if item['numero_controle_pncp'] not in existing_ids]
    return new_items, len(items) - len(new_items)

def fetch_additional_data(orgao_cnpj, ano, numero_sequencial, data_type):
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
                time.sleep(DELAY * (2 ** attempt))
    
    return None

def check_for_cancel():
    global cancel_flag
    while not cancel_flag:
        if input() == 'q':
            cancel_flag = True
            print("Cancelamento solicitado. Finalizando o processo...")

def check_if_exists_in_csv(numero_controle_pncp, filename):
    file_path = os.path.join(data_dir, filename)
    if os.path.isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                if row['numero_controle_pncp'] == numero_controle_pncp:
                    return True
    return False

def download_additional_data(row, modo):
    global items_saved, arquivos_saved

    if cancel_flag:
        return
    
    orgao_cnpj = row['orgao_cnpj']
    ano = row['ano']
    numero_sequencial = row['numero_sequencial']
    numero_controle_pncp = row['numero_controle_pncp']
    description = row.get('description', 'N/A')
    
    print(f"{numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")
    
    itens_filename = f'pncp_itens_{modo}.csv'
    arquivos_filename = f'pncp_arquivos_{modo}.csv'
    
    if not check_if_exists_in_csv(numero_controle_pncp, itens_filename):
        itens = fetch_additional_data(orgao_cnpj, ano, numero_sequencial, 'itens')
        if itens:
            fieldnames = sorted(itens[0].keys())
            for item in itens:
                item['numero_controle_pncp'] = numero_controle_pncp
            save_to_csv(itens, itens_filename)
            items_saved += len(itens)
            print(f"Salvos {len(itens)} itens para compra {numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")
    else:
        print(f"Itens já existem para compra {numero_sequencial}/{ano} - Número de controle PNCP: {numero_controle_pncp}")
    
    if not check_if_exists_in_csv(numero_controle_pncp, arquivos_filename):
        arquivos = fetch_additional_data(orgao_cnpj, ano, numero_sequencial, 'arquivos')
        if arquivos:
            fieldnames = sorted(arquivos[0].keys())
            for arquivo in arquivos:
                arquivo['numero_controle_pncp'] = numero_controle_pncp
            save_to_csv(arquivos, arquivos_filename)
            arquivos_saved += len(arquivos)
            print(f"Salvos {len(arquivos)} arquivos para compra {numero_sequencial}/{ano} - Descrição: {description} - Número de controle PNCP: {numero_controle_pncp}")
    else:
        print(f"Arquivos já existem para compra {numero_sequencial}/{ano} - Número de controle PNCP: {numero_controle_pncp}")

def process_row(row, modo):
    download_additional_data(row, modo)

def inspect_url(url):
    try:
        response = requests.head(url, allow_redirects=True)
        content_disposition = response.headers.get('Content-Disposition', '')
        
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            filename = os.path.basename(urlparse(response.url).path)
        
        file_size = int(response.headers.get('Content-Length', 0))
        
        return {
            'filename': filename,
            'tamanho (MB)': file_size / (1024 * 1024)  # Convert to MB
        }
    except requests.RequestException as e:
        logging.error(f"Erro ao inspecionar URL {url}: {str(e)}")
        return None

def inspect_zip_content(url, depth=0):
    if depth > 5:  # Limit recursion depth to prevent infinite loops
        return []

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            file_list = []
            for file_info in zip_file.infolist():
                if file_info.filename.endswith(('.zip', '.rar', '.7z')):
                    # Recursively inspect compressed files
                    sub_files = inspect_zip_content(url + '/' + file_info.filename, depth + 1)
                    file_list.extend(sub_files)
                else:
                    file_list.append(file_info.filename)
            return file_list
    except (requests.RequestException, zipfile.BadZipFile) as e:
        logging.error(f"Erro ao inspecionar conteúdo ZIP da URL {url}: {str(e)}")
        return []

def process_urls(modo):
    arquivos_filename = f'pncp_arquivos_{modo}.csv'
    url_filename = f'pncp_url_{modo}.csv'
    arquivos_path = os.path.join(data_dir, arquivos_filename)
    url_path = os.path.join(data_dir, url_filename)
    
    processed_urls = set()
    if os.path.exists(url_path):
        with open(url_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            processed_urls = set(row['url'] for row in reader)
    
    new_data = []
    
    with open(arquivos_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        rows = list(reader)
        total_rows = len(rows)
        
        def process_single_url(index, row):
            if cancel_flag:
                return "cancelled"

            url = row['uri']
            if url not in processed_urls:
                print(f"Inspecionando URL {index} de {total_rows}: {url}")
                info = inspect_url(url)
                if info:
                    file_list = [info['filename']]
                    if info['filename'].lower().endswith(('.zip', '.rar', '.7z')):
                        print(f"Inspecionando conteúdo do arquivo comprimido: {url}")
                        compressed_files = inspect_zip_content(url)
                        file_list.extend(compressed_files)
                    
                    new_data.append({
                        'numero_controle_pncp': row['numero_controle_pncp'],
                        'url': url,
                        'files': ', '.join(file_list),
                        'tamanho (MB)': f"{info['tamanho (MB)']:.2f}"
                    })
                    print(f"URL {index} processada com sucesso")
                else:
                    print(f"Falha ao processar URL {index}")
            else:
                print(f"URL {index} já processada anteriormente: {url}")

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_single_url, index, row) for index, row in enumerate(rows, start=1)]
            for future in futures:
                if future.result() == "cancelled":
                    print("Processo de inspeção de URLs cancelado.")
                    return

        # Save results after all threads complete
        if new_data:
            save_to_csv(new_data, url_filename)
            print(f"Salvos {len(new_data)} novos registros de URL em {url_filename}")
            new_data = []  # Clear the list after saving

def sanitize_csv_files():
    global removed_duplicates
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            try:
                df = pd.read_csv(file_path, delimiter='\t', encoding='utf-8')
                before_dedup = len(df)
                df = df.drop_duplicates()
                after_dedup = len(df)
                removed_duplicates += (before_dedup - after_dedup)
                df.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
                print(f"Arquivo '{filename}' sanitizado. Linhas removidas: {before_dedup - after_dedup}")
            except Exception as e:
                logging.error(f"Erro ao sanitizar o arquivo {filename}: {str(e)}")
                print(f"Erro ao sanitizar o arquivo {filename}: {str(e)}")

def main():
    global total_items, new_items, duplicate_items, start_time, cancel_flag, items_saved

    parser = argparse.ArgumentParser(description="PNCP Crawler")
    parser.add_argument("--modo", choices=["pregão", "ata_de_registro_de_precos"], required=True, help="Modo de operação")
    parser.add_argument("--ordenacao", choices=["mais_recentes", "mais_antigos", "relevancia"], required=True, help="Parâmetro de ordenação")
    parser.add_argument("--inspecionar_urls", action="store_true", help="Inspecionar URLs dos arquivos")
    args = parser.parse_args()

    modo = args.modo
    ordenacao_map = {
        "mais_recentes": "-data",
        "mais_antigos": "data",
        "relevancia": "relevancia"
    }
    ordenacao = ordenacao_map[args.ordenacao]

    print(f"\nIniciando o crawler com ordenação: {args.ordenacao} e modo: {modo}")
    print("Digite 'q' e pressione Enter a qualquer momento para cancelar o processo.")

    threading.Thread(target=check_for_cancel, daemon=True).start()

    start_time = time.time()

    data_filename = f'pncp_data_{modo}.csv'

    for page in range(1, MAX_PAGES + 1):
        if cancel_flag:
            print("Processo cancelado pelo usuário.")
            break

        print(f"\nBuscando dados da página {page}")
        items = fetch_data(page, ordenacao, modo)
        
        if items is None:
            print(f"Nenhum dado retornado para a página {page}")
            continue
        
        if not items:
            print(f"Nenhum item encontrado na página {page}. Finalizando a busca.")
            break
        
        total_items += len(items)
        new_items_page, duplicates = check_duplicate(items, data_filename)
        
        if new_items_page:
            save_to_csv(new_items_page, data_filename)
            new_items += len(new_items_page)
            items_saved += len(new_items_page)
            print(f"Salvos {len(new_items_page)} novos itens da página {page}")
        else:
            print(f"Nenhum item novo na página {page}")
        
        duplicate_items += duplicates
        
        print(f"Progresso: {total_items} itens processados, {new_items} novos, {duplicate_items} duplicados")
        
        if not cancel_flag:
            print(f"Aguardando {DELAY} segundos antes da próxima requisição...")
            time.sleep(DELAY)

    if not cancel_flag:
        print("\nIniciando coleta de dados adicionais (itens e arquivos)...")
        
        file_path = os.path.join(data_dir, data_filename)
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            rows = list(reader)

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            executor.map(lambda row: process_row(row, modo), rows)

        if args.inspecionar_urls and not cancel_flag:
            print("\nIniciando inspeção de URLs...")
            process_urls(modo)

    sanitize_csv_files()

    end_time = time.time()
    execution_time = end_time - start_time
    
    print("\n--- Relatório Final ---")
    print(f"Tempo de execução: {execution_time:.2f} segundos")
    print(f"Total de itens processados (dados principais): {total_items}")
    print(f"Novos itens salvos (dados principais): {items_saved}")
    print(f"Itens duplicados (não salvos): {duplicate_items}")
    print(f"Número de erros encontrados: {error_count}")
    print(f"Páginas processadas: {page}")
    print(f"Parâmetro de ordenação utilizado: {args.ordenacao}")
    print(f"Total de arquivos complementares salvos: {arquivos_saved}")
    print(f"Total de linhas duplicadas removidas: {removed_duplicates}")
    print("Para mais detalhes, consulte o arquivo de log.")

    logging.info("Processo de crawling concluído")
    print("\nProcesso de crawling concluído. Verifique os arquivos CSV na pasta 'Dados_CSV' para os resultados.")

if __name__ == "__main__":
    main()