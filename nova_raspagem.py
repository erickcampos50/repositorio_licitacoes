import requests
import json
import csv
import time
import logging
from datetime import datetime
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile
from urllib.parse import urlparse
from io import BytesIO
import argparse
import pandas as pd
from functools import lru_cache

# Configurações
API_URL = "https://pncp.gov.br/api/search/"
TAM_PAGINA = 50
DELAY = 1
MAX_RETRIES = 1  # Aumentado para melhorar a robustez
MAX_PAGES = 1
MAX_THREADS = 10

# Criação de pastas para logs e dados
log_dir = 'Logs'
data_dir = 'Dados_CSV'
os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# Configuração de logging
log_file = os.path.join(log_dir, f'crawler_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

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

def load_existing_ids(filename):
    """
    Carrega os IDs existentes de um arquivo CSV para um conjunto em memória.
    """
    existing_ids = set()
    file_path = os.path.join(data_dir, filename)
    if os.path.isfile(file_path):
        try:
            df = pd.read_csv(file_path, delimiter='\t', usecols=['numero_controle_pncp'], dtype=str)
            existing_ids = set(df['numero_controle_pncp'].dropna().unique())
            logger.info(f"Carregados {len(existing_ids)} IDs existentes de {filename}.")
        except Exception as e:
            logger.error(f"Erro ao carregar IDs existentes de {filename}: {str(e)}")
    return existing_ids

def save_to_csv_bulk(data, filename):
    """
    Salva dados em lote utilizando pandas para eficiência.
    """
    if not data:
        return
    file_path = os.path.join(data_dir, filename)
    df_new = pd.DataFrame(data)
    if not os.path.isfile(file_path):
        df_new.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
        logger.info(f"Arquivo {filename} criado e {len(df_new)} registros salvos.")
    else:
        df_new.to_csv(file_path, sep='\t', index=False, mode='a', header=False, encoding='utf-8')
        logger.info(f"{len(df_new)} registros adicionados ao arquivo {filename}.")

@lru_cache(maxsize=1000)
def fetch_additional_data_cached(orgao_cnpj, ano, numero_sequencial, data_type):
    """
    Função com cache para buscar dados adicionais, evitando requisições repetidas.
    """
    return fetch_additional_data(orgao_cnpj, ano, numero_sequencial, data_type)

def fetch_data(page, ordenacao, modo):
    """
    Busca dados da API com tratamento de erros e logging de performance.
    """
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
            start_time_fetch = time.time()
            response = requests.get(API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            elapsed = time.time() - start_time_fetch
            logger.debug(f"Página {page} fetchada em {elapsed:.2f} segundos.")
            return data.get('items', [])
        except requests.RequestException as e:
            error_count += 1
            logger.error(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            print(f"Erro na tentativa {attempt + 1} para a página {page}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY * (2 ** attempt))
            else:
                logger.error(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                print(f"Falha após {MAX_RETRIES} tentativas para a página {page}")
                return None

def fetch_additional_data(orgao_cnpj, ano, numero_sequencial, data_type):
    """
    Busca dados adicionais da API com tratamento de erros e logging.
    """
    url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_cnpj}/compras/{ano}/{numero_sequencial}/{data_type}?pagina=1&tamanhoPagina=20"
    for attempt in range(MAX_RETRIES):
        try:
            start_time_fetch = time.time()
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            elapsed = time.time() - start_time_fetch
            logger.debug(f"Dados adicionais '{data_type}' para {numero_sequencial}/{ano} fetchados em {elapsed:.2f} segundos.")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erro na tentativa {attempt + 1} para {data_type}: {str(e)}")
            print(f"Erro na tentativa {attempt + 1} para {data_type}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY * (2 ** attempt))
    return None

def check_for_cancel():
    """
    Thread para monitorar o cancelamento do processo.
    """
    global cancel_flag
    while not cancel_flag:
        user_input = input()
        if user_input.strip().lower() == 'q':
            cancel_flag = True
            logger.info("Cancelamento solicitado pelo usuário.")
            print("Cancelamento solicitado. Finalizando o processo...")

def inspect_url(url):
    """
    Inspeciona a URL para obter informações do arquivo.
    """
    try:
        start_time_inspect = time.time()
        response = requests.head(url, allow_redirects=True, timeout=10)
        content_disposition = response.headers.get('Content-Disposition', '')
        
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        else:
            filename = os.path.basename(urlparse(response.url).path)
        
        file_size = int(response.headers.get('Content-Length', 0))
        
        elapsed = time.time() - start_time_inspect
        logger.debug(f"URL {url} inspecionada em {elapsed:.2f} segundos.")
        
        return {
            'filename': filename,
            'tamanho (MB)': file_size / (1024 * 1024)  # Convert to MB
        }
    except requests.RequestException as e:
        logger.error(f"Erro ao inspecionar URL {url}: {str(e)}")
        print(f"Erro ao inspecionar URL {url}: {str(e)}")
        return None

def inspect_zip_content(url, depth=0, max_depth=3):
    """
    Inspeciona o conteúdo de arquivos ZIP recursivamente até uma profundidade máxima.
    """
    if depth > max_depth:
        logger.warning(f"Profundidade máxima atingida para URL {url}")
        return []
    try:
        start_time_zip = time.time()
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            file_list = []
            for file_info in zip_file.infolist():
                if file_info.filename.lower().endswith(('.zip', '.rar', '.7z')):
                    sub_url = f"{url}/{file_info.filename}"
                    file_list.append(file_info.filename)  # Adiciona o nome do arquivo comprimido
                    print(f"    * Encontrado arquivo comprimido: {file_info.filename} em {url}")
                    logger.info(f"Encontrado arquivo comprimido: {file_info.filename} em {url}")
                    # Inspecionar o conteúdo do arquivo comprimido
                    sub_files = inspect_zip_content(sub_url, depth + 1, max_depth)
                    file_list.extend(sub_files)
                else:
                    file_list.append(file_info.filename)
        elapsed = time.time() - start_time_zip
        logger.debug(f"Conteúdo ZIP de {url} inspecionado em {elapsed:.2f} segundos.")
        return file_list
    except (requests.RequestException, zipfile.BadZipFile) as e:
        logger.error(f"Erro ao inspecionar conteúdo ZIP da URL {url}: {str(e)}")
        print(f"Erro ao inspecionar conteúdo ZIP da URL {url}: {str(e)}")
        return []

def download_additional_data(row, modo, arquivos_filename, itens_filename):
    """
    Baixa dados adicionais (itens e arquivos) para uma determinada linha.
    """
    global items_saved, arquivos_saved
    if cancel_flag:
        return
    
    orgao_cnpj = row['orgao_cnpj']
    ano = row['ano']
    numero_sequencial = row['numero_sequencial']
    numero_controle_pncp = row['numero_controle_pncp']
    description = row.get('description', 'N/A')
    
    print(f"\nIniciando download de dados adicionais para PNCP {numero_controle_pncp}...")
    logger.info(f"Iniciando download de dados adicionais para PNCP {numero_controle_pncp}.")
    logger.debug(f"Descrição: {description}")
    
    # Processar Itens
    if numero_controle_pncp not in existing_ids_itens:
        print(f"  - Buscando itens para PNCP {numero_controle_pncp}...")
        logger.info(f"Buscando itens para PNCP {numero_controle_pncp}.")
        itens = fetch_additional_data_cached(orgao_cnpj, ano, numero_sequencial, 'itens')
        if itens:
            try:
                for item in itens:
                    item['numero_controle_pncp'] = numero_controle_pncp
                save_to_csv_bulk(itens, itens_filename)
                items_saved += len(itens)
                existing_ids_itens.add(numero_controle_pncp)
                print(f"  - Salvos {len(itens)} itens para PNCP {numero_controle_pncp}.")
                logger.info(f"Salvos {len(itens)} itens para PNCP {numero_controle_pncp}.")
            except Exception as e:
                logger.error(f"Erro ao salvar itens para PNCP {numero_controle_pncp}: {str(e)}")
                print(f"  - Erro ao salvar itens para PNCP {numero_controle_pncp}: {str(e)}")
        else:
            print(f"  - Nenhum item encontrado para PNCP {numero_controle_pncp}.")
            logger.warning(f"Nenhum item encontrado para PNCP {numero_controle_pncp}.")
    else:
        print(f"  - Itens já existentes para PNCP {numero_controle_pncp}.")
        logger.info(f"Itens já existentes para PNCP {numero_controle_pncp}.")
    
    # Processar Arquivos
    if numero_controle_pncp not in existing_ids_arquivos:
        print(f"  - Buscando arquivos para PNCP {numero_controle_pncp}...")
        logger.info(f"Buscando arquivos para PNCP {numero_controle_pncp}.")
        arquivos = fetch_additional_data_cached(orgao_cnpj, ano, numero_sequencial, 'arquivos')
        if arquivos:
            try:
                for arquivo in arquivos:
                    arquivo['numero_controle_pncp'] = numero_controle_pncp
                save_to_csv_bulk(arquivos, arquivos_filename)
                arquivos_saved += len(arquivos)
                existing_ids_arquivos.add(numero_controle_pncp)
                print(f"  - Salvos {len(arquivos)} arquivos para PNCP {numero_controle_pncp}.")
                logger.info(f"Salvos {len(arquivos)} arquivos para PNCP {numero_controle_pncp}.")
            except Exception as e:
                logger.error(f"Erro ao salvar arquivos para PNCP {numero_controle_pncp}: {str(e)}")
                print(f"  - Erro ao salvar arquivos para PNCP {numero_controle_pncp}: {str(e)}")
        else:
            print(f"  - Nenhum arquivo encontrado para PNCP {numero_controle_pncp}.")
            logger.warning(f"Nenhum arquivo encontrado para PNCP {numero_controle_pncp}.")
    else:
        print(f"  - Arquivos já existentes para PNCP {numero_controle_pncp}.")
        logger.info(f"Arquivos já existentes para PNCP {numero_controle_pncp}.")

def process_urls(modo, arquivos_filename, url_filename, new_ids_set):
    """
    Processa e inspeciona URLs dos arquivos somente para os novos IDs.
    """
    if cancel_flag:
        logger.info("Processo de inspeção de URLs cancelado antes do início.")
        return

    print("\nIniciando inspeção de URLs...")
    logger.info("Iniciando inspeção de URLs.")
    arquivos_path = os.path.join(data_dir, arquivos_filename)
    url_path = os.path.join(data_dir, url_filename)
    
    # Carregar URLs já processadas
    processed_urls = load_processed_urls(url_filename)
    
    new_data = []
    
    try:
        df_arquivos = pd.read_csv(arquivos_path, delimiter='\t', dtype=str)
    except Exception as e:
        logger.error(f"Erro ao ler {arquivos_filename}: {str(e)}")
        print(f"Erro ao ler {arquivos_filename}: {str(e)}")
        return
    
    # Filtrar apenas os novos IDs
    df_novos_arquivos = df_arquivos[df_arquivos['numero_controle_pncp'].isin(new_ids_set)]
    total_rows = len(df_novos_arquivos)
    
    print(f"Total de URLs a inspecionar para novos IDs: {total_rows}")
    logger.info(f"Total de URLs a inspecionar para novos IDs: {total_rows}")
    
    # Contadores para novos itens e arquivos a serem buscados
    novos_itens = len(df_novos_arquivos[~df_novos_arquivos['numero_controle_pncp'].isin(existing_ids_itens)])
    novos_arquivos = len(df_novos_arquivos[~df_novos_arquivos['numero_controle_pncp'].isin(existing_ids_arquivos)])
    
    print(f"Total de novos itens a serem buscados para inspeção de URLs: {novos_itens}")
    print(f"Total de novos arquivos a serem buscados para inspeção de URLs: {novos_arquivos}")
    logger.info(f"Total de novos itens a serem buscados para inspeção de URLs: {novos_itens}")
    logger.info(f"Total de novos arquivos a serem buscados para inspeção de URLs: {novos_arquivos}")
    
    def process_single_url(index, row):
        if cancel_flag:
            return None
        
        url = row['uri']
        numero_controle_pncp = row['numero_controle_pncp']
        
        if url in processed_urls:
            logger.debug(f"URL já processada anteriormente: {url}")
            return None
        
        print(f"  - Inspecionando URL {index} de {total_rows}: {url}")
        logger.info(f"Inspecionando URL {index} de {total_rows}: {url}")
        info = inspect_url(url)
        if info:
            file_list = [info['filename']]
            if info['filename'].lower().endswith(('.zip', '.rar', '.7z')):
                print(f"    * Inspecionando conteúdo do arquivo comprimido: {url}")
                logger.info(f"Inspecionando conteúdo do arquivo comprimido: {url}")
                compressed_files = inspect_zip_content(url)
                file_list.extend(compressed_files)
            
            return {
                'numero_controle_pncp': numero_controle_pncp,
                'url': url,
                'files': ', '.join(file_list),
                'tamanho (MB)': f"{info['tamanho (MB)']:.2f}"
            }
        else:
            print(f"  - Falha ao processar URL {index}: {url}")
            logger.warning(f"Falha ao processar URL {index}: {url}")
            return None
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(process_single_url, idx + 1, row): idx 
            for idx, row in df_novos_arquivos.iterrows()
        }
        for future in as_completed(futures):
            if cancel_flag:
                logger.info("Cancelamento detectado. Encerrando inspeção de URLs.")
                executor.shutdown(wait=False)
                return
            result = future.result()
            if result:
                new_data.append(result)
                print(f"  - URL processada com sucesso: {result['url']}")
                logger.debug(f"URL processada com sucesso: {result['url']}")

    if new_data:
        try:
            save_to_csv_bulk(new_data, url_filename)
            print(f"Salvos {len(new_data)} novos registros de URL em {url_filename}.")
            logger.info(f"Salvos {len(new_data)} novos registros de URL em {url_filename}.")
        except Exception as e:
            logger.error(f"Erro ao salvar registros de URL em {url_filename}: {str(e)}")
            print(f"Erro ao salvar registros de URL em {url_filename}: {str(e)}")

def load_processed_urls(filename):
    """
    Carrega URLs já processadas de um arquivo CSV para um conjunto.
    """
    processed_urls = set()
    file_path = os.path.join(data_dir, filename)
    if os.path.isfile(file_path):
        try:
            df = pd.read_csv(file_path, delimiter='\t', usecols=['url'], dtype=str)
            processed_urls = set(df['url'].dropna().unique())
            logger.info(f"Carregadas {len(processed_urls)} URLs já processadas de {filename}.")
        except Exception as e:
            logger.error(f"Erro ao carregar URLs processadas de {filename}: {str(e)}")
    return processed_urls

def sanitize_csv_files():
    """
    Remove duplicatas de todos os arquivos CSV na pasta de dados.
    """
    global removed_duplicates
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            try:
                df = pd.read_csv(file_path, delimiter='\t', dtype=str)
                before_dedup = len(df)
                df = df.drop_duplicates()
                after_dedup = len(df)
                removed = before_dedup - after_dedup
                if removed > 0:
                    removed_duplicates += removed
                    df.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
                    logger.info(f"Arquivo '{filename}' sanitizado. Linhas removidas: {removed}.")
                    print(f"Arquivo '{filename}' sanitizado. Linhas removidas: {removed}.")
            except Exception as e:
                logger.error(f"Erro ao sanitizar o arquivo {filename}: {str(e)}")
                print(f"Erro ao sanitizar o arquivo {filename}: {str(e)}")

def main():
    global total_items, new_items, duplicate_items, start_time, cancel_flag, items_saved, arquivos_saved
    global existing_ids_itens, existing_ids_arquivos
    
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

    logger.info(f"Iniciando o crawler com ordenação: {args.ordenacao} e modo: {modo}")
    logger.info("Processo iniciado pelo usuário.")

    # Iniciar thread para monitorar cancelamento
    threading.Thread(target=check_for_cancel, daemon=True).start()

    start_time = time.time()

    data_filename = f'pncp_data_{modo}.csv'
    itens_filename = f'pncp_itens_{modo}.csv'
    arquivos_filename = f'pncp_arquivos_{modo}.csv'
    url_filename = f'pncp_url_{modo}.csv'

    # Carregar IDs existentes em memória
    print("Carregando IDs existentes em memória...")
    logger.info("Carregando IDs existentes em memória.")
    existing_ids = load_existing_ids(data_filename)
    existing_ids_itens = load_existing_ids(itens_filename)
    existing_ids_arquivos = load_existing_ids(arquivos_filename)
    print(f"Total de IDs carregados para dados principais: {len(existing_ids)}")
    print(f"Total de IDs carregados para itens: {len(existing_ids_itens)}")
    print(f"Total de IDs carregados para arquivos: {len(existing_ids_arquivos)}")
    logger.info(f"Total de IDs carregados para dados principais: {len(existing_ids)}")
    logger.info(f"Total de IDs carregados para itens: {len(existing_ids_itens)}")
    logger.info(f"Total de IDs carregados para arquivos: {len(existing_ids_arquivos)}")

    # Conjunto para armazenar novos IDs identificados
    novos_ids_set = set()

    for page in range(1, MAX_PAGES + 1):
        if cancel_flag:
            print("Processo cancelado pelo usuário.")
            logger.info("Processo cancelado pelo usuário durante a coleta de dados principais.")
            break

        print(f"\nBuscando dados da página {page}...")
        logger.info(f"Buscando dados da página {page}.")

        items = fetch_data(page, ordenacao, modo)
        
        if items is None:
            print(f"Nenhum dado retornado para a página {page}.")
            logger.warning(f"Nenhum dado retornado para a página {page}.")
            continue
        
        if not items:
            print(f"Nenhum item encontrado na página {page}. Finalizando a busca.")
            logger.info(f"Nenhum item encontrado na página {page}. Finalizando a busca.")
            break
        
        total_items += len(items)
        # Verificar duplicatas em memória
        new_items_page = [item for item in items if item['numero_controle_pncp'] not in existing_ids]
        duplicates = len(items) - len(new_items_page)
        
        if new_items_page:
            save_to_csv_bulk(new_items_page, data_filename)
            # Atualizar o conjunto de IDs existentes
            existing_ids.update(item['numero_controle_pncp'] for item in new_items_page)
            # Adicionar ao conjunto de novos IDs para buscar dados adicionais
            novos_ids_set.update(item['numero_controle_pncp'] for item in new_items_page)
            new_items += len(new_items_page)
            items_saved += len(new_items_page)
            logger.info(f"Salvos {len(new_items_page)} novos itens da página {page}.")
            print(f"Salvos {len(new_items_page)} novos itens da página {page}.")
        else:
            print(f"Nenhum item novo na página {page}.")
            logger.info(f"Nenhum item novo na página {page}.")

        duplicate_items += duplicates
        logger.info(f"Progresso: {total_items} itens processados, {new_items} novos, {duplicate_items} duplicados.")
        print(f"Progresso: {total_items} itens processados, {new_items} novos, {duplicate_items} duplicados.")
        
        if not cancel_flag:
            logger.debug(f"Aguardando {DELAY} segundos antes da próxima requisição.")
            print(f"Aguardando {DELAY} segundos antes da próxima requisição...")
            time.sleep(DELAY)
    
    if not cancel_flag:
        print("\nIniciando coleta de dados adicionais (itens e arquivos)...")
        logger.info("Iniciando coleta de dados adicionais (itens e arquivos).")
        
        # Exibir quantos novos itens e arquivos serão buscados
        novos_itens = len(novos_ids_set)
        novos_arquivos = len(novos_ids_set)
        
        print(f"Total de novos itens a serem buscados: {novos_itens}")
        print(f"Total de novos arquivos a serem buscados: {novos_arquivos}")
        logger.info(f"Total de novos itens a serem buscados: {novos_itens}")
        logger.info(f"Total de novos arquivos a serem buscados: {novos_arquivos}")
        
        # Processar dados adicionais apenas para os novos IDs
        if novos_ids_set:
            # Filtrar o DataFrame para apenas os novos IDs
            try:
                df_novos = pd.read_csv(os.path.join(data_dir, data_filename), delimiter='\t', dtype=str)
                df_novos = df_novos[df_novos['numero_controle_pncp'].isin(novos_ids_set)]
                print(f"Total de registros para coleta adicional: {len(df_novos)}")
                logger.info(f"Total de registros para coleta adicional: {len(df_novos)}")
            except Exception as e:
                logger.error(f"Erro ao ler {data_filename}: {str(e)}")
                print(f"Erro ao ler {data_filename}: {str(e)}")
                df_novos = pd.DataFrame()
            
            # Processar dados adicionais utilizando ThreadPoolExecutor
            print("Iniciando processamento paralelo dos dados adicionais...")
            logger.info("Iniciando processamento paralelo dos dados adicionais.")
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = []
                for _, row in df_novos.iterrows():
                    if cancel_flag:
                        logger.info("Processo cancelado pelo usuário durante o processamento de dados adicionais.")
                        break
                    futures.append(executor.submit(
                        download_additional_data, row, modo, arquivos_filename, itens_filename
                    ))
                # Aguardar a conclusão das tarefas
                for future in as_completed(futures):
                    if cancel_flag:
                        logger.info("Cancelamento detectado. Encerrando processamento de dados adicionais.")
                        executor.shutdown(wait=False)
                        break

        if args.inspecionar_urls and not cancel_flag:
            print("\nIniciando inspeção de URLs...")
            logger.info("Iniciando inspeção de URLs.")
            process_urls(modo, arquivos_filename, url_filename, novos_ids_set)
    
    # Sanitizar arquivos CSV removendo duplicatas
    print("\nSanitizando arquivos CSV para remover duplicatas...")
    logger.info("Sanitizando arquivos CSV para remover duplicatas.")
    sanitize_csv_files()

    end_time = time.time()
    execution_time = end_time - start_time
    
    # Relatório Final
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
    
    logger.info("Processo de crawling concluído.")
    logger.info(f"Tempo de execução: {execution_time:.2f} segundos.")
    logger.info(f"Total de itens processados (dados principais): {total_items}")
    logger.info(f"Novos itens salvos (dados principais): {items_saved}")
    logger.info(f"Itens duplicados (não salvos): {duplicate_items}")
    logger.info(f"Número de erros encontrados: {error_count}")
    logger.info(f"Páginas processadas: {page}")
    logger.info(f"Parâmetro de ordenação utilizado: {args.ordenacao}")
    logger.info(f"Total de arquivos complementares salvos: {arquivos_saved}")
    logger.info(f"Total de linhas duplicadas removidas: {removed_duplicates}")
    logger.info("Processo de crawling concluído. Verifique os arquivos CSV na pasta 'Dados_CSV' para os resultados.")
    
    print("\nProcesso de crawling concluído. Verifique os arquivos CSV na pasta 'Dados_CSV' para os resultados.")

if __name__ == "__main__":
    main()
