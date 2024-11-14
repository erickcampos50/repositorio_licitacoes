#!/usr/bin/env python
# -*- coding: utf-8 -*-
#%%
"""
Script para raspagem de dados de licitações do PNCP (Portal Nacional de Contratações Públicas). Este script realiza a raspagem de dados de licitações, itens e arquivos disponibilizados pela API do PNCP.
"""

# Importação das bibliotecas necessárias
import asyncio
import aiohttp
import argparse
import configparser
import logging
import os
import pandas as pd
import random
import sys
import time
import zipfile
import rarfile
import py7zr
import tempfile

#%%
# ---------------------------- Módulo de Configuração ---------------------------- #

def load_config(args):
    """
    Carrega as configurações do arquivo config.ini e aplica os parâmetros da CLI.

    Args:
        args: Argumentos da linha de comando.

    Returns:
        config: Dicionário com as configurações atualizadas.
    """
    # Carrega o arquivo de configuração
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Seção 'DEFAULT' do arquivo de configuração
    default_config = config['DEFAULT'] if 'DEFAULT' in config else {}

    # Atualiza as configurações com os argumentos da CLI, se fornecidos
    config_dict = {
        'pagina_inicial': int(args.pagina_inicial or default_config.get('pagina_inicial', 1)),
        'pagina_final': int(args.pagina_final or default_config.get('pagina_final', 20)),
        'tam_pagina': int(args.tam_pagina or default_config.get('tam_pagina', 500)),
        'ordenacao': (args.ordenacao or default_config.get('ordenacao', 'data,-data,relevancia')).split(','),
        'tipos_documento': (args.tipos_documento or default_config.get('tipos_documento', 'edital,ata')).split(','),
        'tamanho_pagina_itens': int(default_config.get('tamanho_pagina_itens', 20)),
        'tamanho_pagina_arquivos': int(default_config.get('tamanho_pagina_arquivos', 20)),
        'numero_maximo_conexoes': int(args.max_conexoes or default_config.get('numero_maximo_conexoes', 10)),
        'tempo_espera_inicial': int(default_config.get('tempo_espera_inicial', 1)),
        'tentativas_maximas': int(args.tentativas_maximas or default_config.get('tentativas_maximas', 5)),
        'verbose': args.verbose
    }

    return config_dict

# ---------------------------- Interface de Linha de Comando (CLI) ---------------------------- #

def parse_arguments():
    """
    Define e analisa os argumentos da linha de comando.

    Returns:
        args: Argumentos analisados.
    """
    parser = argparse.ArgumentParser(description='Script para raspagem de dados de licitações do PNCP.')
    parser.add_argument('--pagina-inicial', type=int, help='Página     inicial para iniciar a raspagem.')
    parser.add_argument('--pagina-final', type=int, help='Página final para concluir a raspagem.')
    parser.add_argument('--tam-pagina', type=int, help='Tamanho da página (número de registros por requisição).')
    parser.add_argument('--ordenacao', type=str, help='Critério de ordenação dos registros.')
    parser.add_argument('--tipos-documento', type=str, help='Tipos de documento a serem buscados (edital, ata ou ambos).')
    parser.add_argument('--max-conexoes', type=int, help='Número máximo de requisições simultâneas.')
    parser.add_argument('--tentativas-maximas', type=int, help='Número máximo de tentativas em caso de falha.')
    parser.add_argument('--verbose', action='store_true', help='Ativa o modo verboso.')
    args = parser.parse_args()
    return args

# ---------------------------- Módulo de Logs ---------------------------- #

def setup_logging(log_file):
    """
    Configura o sistema de logs.

    Args:
        log_file: Caminho do arquivo de log.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Também adiciona um handler para exibir logs no console se necessário
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)  # Ajuste o nível conforme necessário
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

# ---------------------------- Módulo de Diretórios e Arquivos ---------------------------- #

def setup_directories():
    """
    Verifica a existência dos diretórios e arquivos necessários e os cria se não existirem.

    Returns:
        paths: Dicionário com os caminhos dos arquivos.
    """
    # Define o diretório principal
    main_directory = 'raspagem'

    # Verifica se o diretório existe, se não, cria
    if not os.path.exists(main_directory):
        os.makedirs(main_directory)
        print(f"Diretório '{main_directory}' criado.")
        logging.info(f"Diretório '{main_directory}' criado.")

    # Define os caminhos completos para os arquivos
    paths = {
        'main_directory': main_directory,
        'licitacoes_csv': os.path.join(main_directory, 'licitacoes.csv'),
        'itens_csv': os.path.join(main_directory, 'itens.csv'),
        'resultados_csv': os.path.join(main_directory, 'resultados.csv'),
        'arquivos_csv': os.path.join(main_directory, 'arquivos.csv'),
        'log_file': os.path.join(main_directory, 'raspagem_pncp.log')
    }

    return paths

# ---------------------------- Módulo de Armazenamento ---------------------------- #
def load_dataframes(paths):
    """
    Carrega os dataframes existentes ou cria novos se não existirem.

    Args:
        paths: Dicionário com os caminhos dos arquivos.

    Returns:
        df_licitacoes: DataFrame principal de licitações.
        df_itens: DataFrame de itens.
        df_arquivos: DataFrame de arquivos.
    """
    # Inicializa dataframes vazios
    df_licitacoes = pd.DataFrame()
    df_itens = pd.DataFrame()
    df_arquivos = pd.DataFrame()
    df_resultados = pd.DataFrame()

    # Tenta carregar os dataframes existentes
    try:
        if os.path.exists(paths['licitacoes_csv']):
            df_licitacoes = pd.read_csv(paths['licitacoes_csv'], dtype=str,sep='\t')
            # Verifica se as colunas de controle existem, se não, as cria
            if 'detalhes_baixados' not in df_licitacoes.columns:
                df_licitacoes['detalhes_baixados'] = False
                logging.info("Coluna 'detalhes_baixados' adicionada ao DataFrame de licitações.")
            if 'documentos_baixados' not in df_licitacoes.columns:
                df_licitacoes['documentos_baixados'] = False
                logging.info("Coluna 'documentos_baixados' adicionada ao DataFrame de licitações.")
            # Remove duplicatas com base em 'numero_controle_pncp'
            df_licitacoes.drop_duplicates(subset='numero_controle_pncp', keep='last', inplace=True)
    except Exception as e:
        logging.error(f"Erro ao carregar {paths['licitacoes_csv']}: {str(e)}")

    try:
        if os.path.exists(paths['itens_csv']):
            df_itens = pd.read_csv(paths['itens_csv'], dtype=str,sep='\t')
            # Verifica se a coluna 'Resultados verificados' existe, se não, a cria
            if 'Resultados verificados' not in df_itens.columns:
                df_itens['Resultados verificados'] = False
                logging.info("Coluna 'Resultados verificados' adicionada ao DataFrame de itens.")
                # Salva o DataFrame atualizado para garantir que a coluna exista no CSV
                df_itens.to_csv(paths['itens_csv'], index=False,sep='\t')
    except Exception as e:
        logging.error(f"Erro ao carregar {paths['itens_csv']}: {str(e)}")

    try:
        if os.path.exists(paths['resultados_csv']):
            df_resultados = pd.read_csv(paths['resultados_csv'],dtype=str,sep='\t')
    except Exception as e:
        logging.error(f"Erro ao carregar {paths['resultados_csv']}: {str(e)}")


    try:
        if os.path.exists(paths['arquivos_csv']):
            df_arquivos = pd.read_csv(paths['arquivos_csv'],dtype=str,sep='\t')
    except Exception as e:
        logging.error(f"Erro ao carregar {paths['arquivos_csv']}: {str(e)}")

    return df_licitacoes, df_itens, df_arquivos, df_resultados

def save_dataframes(df_licitacoes, df_itens, df_arquivos, paths):
    """
    Salva os dataframes em arquivos CSV.

    Args:
        df_licitacoes: DataFrame principal de licitações.
        df_itens: DataFrame de itens.
        df_arquivos: DataFrame de arquivos.
        paths: Dicionário com os caminhos dos arquivos.
    """
    try:
        df_licitacoes.to_csv(paths['licitacoes_csv'], index=False,sep='\t')
        logging.info(f"DataFrame de licitações salvo em {paths['licitacoes_csv']}.")
    except Exception as e:
        logging.error(f"Erro ao salvar {paths['licitacoes_csv']}: {str(e)}")

    try:
        df_itens.to_csv(paths['itens_csv'], index=False,sep='\t')
        logging.info(f"DataFrame de itens salvo em {paths['itens_csv']}.")
    except Exception as e:
        logging.error(f"Erro ao salvar {paths['itens_csv']}: {str(e)}")

    try:
        df_arquivos.to_csv(paths['arquivos_csv'], index=False,sep='\t')
        logging.info(f"DataFrame de arquivos salvo em {paths['arquivos_csv']}.")
    except Exception as e:
        logging.error(f"Erro ao salvar {paths['arquivos_csv']}: {str(e)}")

# ---------------------------- Módulo de Requisições ---------------------------- #

async def fetch_with_retry(session, url, params, config, tentativa=1):
    """
    Realiza uma requisição HTTP com retentativas e backoff exponencial.

    Args:
        session: Sessão HTTP.
        url: URL da requisição.
        params: Parâmetros da requisição.
        config: Configurações do sistema.
        tentativa: Número da tentativa atual.

    Returns:
        response_data: Dados da resposta em formato JSON, ou None em caso de falha.
    """
    try:
        async with session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            json_response = await response.json()
            return json_response
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        if tentativa <= config['tentativas_maximas']:
            tempo_espera = config['tempo_espera_inicial'] * (2 ** (tentativa - 1)) + random.uniform(0, 1)
            await asyncio.sleep(tempo_espera)
            if config['verbose']:
                print(f"Tentativa {tentativa} falhou para {url}. Retentando em {tempo_espera:.2f} segundos...")
            logging.warning(f"Tentativa {tentativa} falhou para {url}: {str(e)}")
            return await fetch_with_retry(session, url, params, config, tentativa + 1)
        else:
            logging.error(f"Falha na requisição após {config['tentativas_maximas']} tentativas: {str(e)}")
            return None

async def limited_fetch(semaphore, session, url, params, config):
    """
    Controla o número máximo de conexões simultâneas.

    Args:
        semaphore: Semáforo para limitar conexões.
        session: Sessão HTTP.
        url: URL da requisição.
        params: Parâmetros da requisição.
        config: Configurações do sistema.

    Returns:
        response_data: Dados da resposta em formato JSON, ou None em caso de falha.
    """
    async with semaphore:
        return await fetch_with_retry(session, url, params, config)

async def fetch_licitacoes(tipos_documento, ordenacao, pages, config):
    """
    Realiza as requisições das licitações de forma assíncrona para cada tipo de documento.

    Args:
        tipos_documento: Lista de tipos de documento ('edital', 'ata', etc.).
        pages: Lista de números de páginas a serem requisitadas.
        config: Configurações do sistema.

    Returns:
        responses: Lista de respostas das requisições.
    """
    base_url = "https://pncp.gov.br/api/search/"
    semaphore = asyncio.Semaphore(config['numero_maximo_conexoes'])
    tasks = []
    responses = []

    async with aiohttp.ClientSession() as session:
        for ordem in ordenacao:
            for tipo in tipos_documento:
                for page in pages:
                    params = {
                        "pagina": page,
                        "tam_pagina": config['tam_pagina'],
                        "ordenacao": ordem,
                        "q": "",
                        "tipos_documento": tipo,
                        "status": "todos"
                    }
                    task = asyncio.create_task(limited_fetch(semaphore, session, base_url, params, config))
                    tasks.append((tipo, page, ordem, task))

        total_tasks = len(tasks)
        completed_tasks = 0
        for tipo, page, ordem, task in tasks:
            response = await task
            responses.append(response)
            completed_tasks += 1
            print(f"Requisição concluída: Tipo Documento='{tipo}', Ordenação='{ordem}', Página={page} ({completed_tasks}/{total_tasks})")
            logging.info(f"Requisição concluída: Tipo Documento='{tipo}', Ordenação='{ordem}', Página={page} ({completed_tasks}/{total_tasks})")

    return responses

async def fetch_detalhes(registros, data_type, config):
    """
    Realiza as requisições dos detalhes (itens ou arquivos) de forma assíncrona.

    Args:
        registros: Lista de registros para os quais os detalhes serão buscados.
        data_type: Tipo de detalhe ('itens' ou 'arquivos').
        config: Configurações do sistema.

    Returns:
        detalhes_list: Lista de detalhes obtidos.
    """
    base_url = "https://pncp.gov.br/api/pncp/v1/orgaos/"
    semaphore = asyncio.Semaphore(config['numero_maximo_conexoes'])
    tasks = []
    detalhes_list = []

    async with aiohttp.ClientSession() as session:
        for registro in registros:
            orgao_cnpj = registro.get('orgao_cnpj')
            ano = registro.get('ano')
            numero_sequencial = registro.get('numero_sequencial')
            numero_controle_pncp = registro.get('numero_controle_pncp')

            if not all([orgao_cnpj, ano, numero_sequencial, numero_controle_pncp]):
                logging.warning(f"Dados incompletos para a licitação '{numero_controle_pncp}'. Pulando...")
                if config['verbose']:
                    print(f"Aviso: Dados incompletos para a licitação '{numero_controle_pncp}'. Pulando...")
                continue

            url = f"{base_url}{orgao_cnpj}/compras/{ano}/{numero_sequencial}/{data_type}"
            params = {
                "pagina": 1,
                "tamanhoPagina": 20
            }
            task = asyncio.create_task(limited_fetch(semaphore, session, url, params, config))
            tasks.append((numero_controle_pncp, orgao_cnpj, ano, numero_sequencial, task))

        total_tasks = len(tasks)
        completed_tasks = 0
        for numero_controle_pncp, orgao_cnpj, ano, numero_sequencial, task in tasks:
            detalhe = await task
            if detalhe:
                if isinstance(detalhe, dict):
                    itens = detalhe.get('items', [])
                elif isinstance(detalhe, list):
                    itens = detalhe
                else:
                    itens = []
                    logging.warning(f"Formato inesperado da resposta para '{numero_controle_pncp}'.")
                    if config['verbose']:
                        print(f"Aviso: Formato inesperado da resposta para '{numero_controle_pncp}'.")
                
                # Adiciona o numero_controle_pncp a cada item
                for item in itens:
                    item['numero_controle_pncp'] = numero_controle_pncp
                    item['orgao_cnpj'] = orgao_cnpj
                    item['ano'] = ano
                    item['numero_sequencial'] = numero_sequencial
                    item['Resultados verificados'] = False  # Adiciona a nova coluna com valor False
                
                detalhes_list.extend(itens)
                logging.info(f"Requisição de {data_type} para '{numero_controle_pncp}' bem-sucedida.")
                if config['verbose']:
                    print(f"Requisição de {data_type} para '{numero_controle_pncp}' bem-sucedida.")
            else:
                logging.error(f"Requisição de {data_type} para '{numero_controle_pncp}' falhou.")
                if config['verbose']:
                    print(f"Erro: Requisição de {data_type} para '{numero_controle_pncp}' falhou.")
            completed_tasks += 1
            print(f"Requisição de {data_type} concluída para '{numero_controle_pncp}' ({completed_tasks}/{total_tasks})")

    return detalhes_list



async def fetch_resultados(registros, config):
    """
    Realiza as requisições dos resultados de forma assíncrona.

    Args:
        df_itens: DataFrame de itens para os quais os resultados serão buscados.
        config: Configurações do sistema.

    Returns:
        resultados_list: Lista de resultados obtidos.
    """
    base_url = "https://pncp.gov.br/api/pncp/v1/orgaos/"
    semaphore = asyncio.Semaphore(config['numero_maximo_conexoes'])
    tasks = []
    resultados_list = []

    # Extrai as colunas necessárias do DataFrame
    orgao_cnpj = registros['orgao_cnpj']
    ano = registros['ano']
    numero_sequencial = registros['numero_sequencial']
    numero_controle_pncp = registros['numero_controle_pncp']

    # Verifica se todas as colunas necessárias estão presentes
    if not all(col in registros.columns for col in ['orgao_cnpj', 'ano', 'numero_sequencial', 'numero_controle_pncp']):
        logging.warning("Dados incompletos para os itens. Pulando...")
        if config['verbose']:
            print("Aviso: Dados incompletos para os itens. Pulando...")
        return []

    async with aiohttp.ClientSession() as session:
        for idx, row in registros.iterrows():
            orgao_cnpj = row['orgao_cnpj']
            ano = row['ano']
            numero_sequencial = row['numero_sequencial']
            numero_controle_pncp = row['numero_controle_pncp']
            numeroItem = row['numeroItem']

            if not all([orgao_cnpj, ano, numero_sequencial, numero_controle_pncp]):
                logging.warning(f"Dados incompletos para o item '{numero_controle_pncp}'. Pulando...")
                if config['verbose']:
                    print(f"Aviso: Dados incompletos para o item '{numero_controle_pncp}'. Pulando...")
                continue

            url = f"{base_url}{orgao_cnpj}/compras/{ano}/{numero_sequencial}/itens/{numeroItem}/resultados"
            params = {
                "pagina": 1,
                "tamanhoPagina": 20
            }
            task = asyncio.create_task(limited_fetch(semaphore, session, url, params, config))
            tasks.append((numero_controle_pncp, task))

        total_tasks = len(tasks)
        completed_tasks = 0
        for numero_controle_pncp, task in tasks:
            subitem = await task
            if subitem:
                if isinstance(subitem, dict):
                    resultados = subitem.get('items', [])
                elif isinstance(subitem, list):
                    resultados = subitem
                else:
                    resultados = []
                    logging.warning(f"Formato inesperado da resposta para o item '{numero_controle_pncp}'.")
                    if config['verbose']:
                        print(f"Aviso: Formato inesperado da resposta para o item '{numero_controle_pncp}'.")
                
                # Adiciona o numero_controle_pncp a cada subitem
                for sub in resultados:
                    sub['numero_controle_pncp'] = numero_controle_pncp
                
                resultados_list.extend(resultados)
                logging.info(f"Requisição de resultados para o item '{numero_controle_pncp}' bem-sucedida.")
                if config['verbose']:
                    print(f"Requisição de resultados para o item '{numero_controle_pncp}' bem-sucedida.")
            else:
                logging.error(f"Requisição de resultados para o item '{numero_controle_pncp}' falhou.")
                if config['verbose']:
                    print(f"Erro: Requisição de resultados para o item '{numero_controle_pncp}' falhou.")
            completed_tasks += 1
            print(f"Requisição de resultados concluída para o item '{numero_controle_pncp}' ({completed_tasks}/{total_tasks})")

    return resultados_list
# ---------------------------- Módulo de Processamento de Dados ---------------------------- #

def process_licitacoes(respostas, df_licitacoes):
    """
    Processa as respostas das licitações e atualiza o dataframe principal.

    Args:
        respostas: Lista de respostas das requisições.
        df_licitacoes: DataFrame principal de licitações.

    Returns:
        df_licitacoes: DataFrame atualizado.
    """
    registros = []
    for response in respostas:
        if response and isinstance(response, dict) and 'items' in response:
            registros.extend(response["items"])
        else:
            logging.warning("Resposta vazia ou sem a chave 'items'.")

    if not registros:
        logging.info("Nenhum registro novo de licitações foi encontrado.")
        return df_licitacoes

    # df_novo = pd.DataFrame(registros)
    # Convertendo o JSON para DataFrame e formatando a coluna 'numero_sequencial' como inteiro em uma única linha
    df_novo = pd.DataFrame(registros)


    if df_novo.empty:
        logging.info("DataFrame novo de licitações está vazio.")
        return df_licitacoes

    # Adiciona colunas de controle, se não existirem
    if 'detalhes_baixados' not in df_novo.columns:
        df_novo['detalhes_baixados'] = False
    if 'documentos_baixados' not in df_novo.columns:
        df_novo['documentos_baixados'] = False

    # Concatena e remove duplicatas
    df_licitacoes = pd.concat([df_licitacoes, df_novo], ignore_index=True)
    df_licitacoes.drop_duplicates(subset='numero_controle_pncp', keep='first', inplace=True)

    logging.info(f"{len(df_novo)} novas licitações adicionadas.")
    return df_licitacoes

def processar_detalhes_registros(registros, df_existente, tipo_registro):
    """
    Processa os registros detalhados, removendo duplicatas e combinando com os dados existentes.

    Parâmetros:
        registros (list): Lista de registros detalhados a serem processados.
        df_existente (pd.DataFrame): DataFrame existente com dados anteriores.
        tipo_registro (str): Tipo do registro para fins de logging e contexto.

    Retorna:
        pd.DataFrame: DataFrame consolidado com os registros processados.
    """
    df_registros = pd.DataFrame(registros)

    # Inspeciona e ajusta colunas que contenham dicionários
    for coluna in df_registros.columns:
        if df_registros[coluna].apply(lambda x: isinstance(x, dict)).any():
            logging.warning(f"Coluna {coluna} contém dicionários. Convertendo para string.")
            df_registros[coluna] = df_registros[coluna].apply(str)  # Converte dicionários para strings

    # Remove duplicatas
    df_registros.drop_duplicates(inplace=True)

    # Combina com o DataFrame existente
    if not df_existente.empty:
        df_registros = pd.concat([df_existente, df_registros]).drop_duplicates()

    logging.info(f"Processamento de registros do tipo '{tipo_registro}' concluído. Total: {len(df_registros)} registros.")
    return df_registros



## ---------------------------- Módulo de Verificação de Arquivos Compactados ---------------------------- #

async def verify_compressed_files(paths, config):
    """
    Verifica a existência de arquivos compactados (zip, rar, 7zip) a partir das URLs presentes no DataFrame de arquivos.
    Atualiza a coluna 'verificacao_arquivos' para evitar verificações duplicadas.
    Além disso, extrai o conteúdo dos arquivos compactados e adiciona os nomes dos arquivos internos na coluna 'titulo'.

    Args:
        paths: Dicionário com os caminhos dos arquivos.
        config: Configurações do sistema.
    """
    # Carrega o DataFrame de arquivos
    try:
        df_arquivos = pd.read_csv(paths['arquivos_csv'],dtype=str,sep='\t')
        logging.info(f"DataFrame de arquivos carregado de {paths['arquivos_csv']}.")
    except Exception as e:
        logging.error(f"Erro ao carregar {paths['arquivos_csv']}: {str(e)}")
        return

    # Verifica se a coluna 'verificacao_arquivos' existe, se não, cria com False
    if 'verificacao_arquivos' not in df_arquivos.columns:
        df_arquivos['verificacao_arquivos'] = False
        logging.info("Coluna 'verificacao_arquivos' adicionada ao DataFrame de arquivos.")
        if config['verbose']:
            print("Coluna 'verificacao_arquivos' adicionada ao DataFrame de arquivos.")
        # Salva o DataFrame atualizado para garantir que a coluna exista no CSV
        try:
            df_arquivos.to_csv(paths['arquivos_csv'], index=False,sep='\t')
            logging.info(f"DataFrame de arquivos salvo com a nova coluna em {paths['arquivos_csv']}.")
            if config['verbose']:
                print(f"DataFrame de arquivos salvo com a nova coluna em '{paths['arquivos_csv']}'.")
        except Exception as e:
            logging.error(f"Erro ao salvar {paths['arquivos_csv']} após adicionar a coluna 'verificacao_arquivos': {str(e)}")
            if config['verbose']:
                print(f"Erro ao salvar a coluna 'verificacao_arquivos' em '{paths['arquivos_csv']}'.")
            return

    # Garantir que a coluna 'verificacao_arquivos' seja do tipo booleano
    df_arquivos['verificacao_arquivos'] = df_arquivos['verificacao_arquivos'].fillna(False).astype(bool)

    # Filtra os arquivos que possuem títulos com extensões zip, rar ou 7zip e que ainda não foram verificados
    extensoes_compactadas = ('.zip', '.rar', '.7zip')
    mask = df_arquivos['titulo'].str.lower().str.endswith(extensoes_compactadas) & (~df_arquivos['verificacao_arquivos'])
    arquivos_para_verificar = df_arquivos[mask]

    total_arquivos = len(arquivos_para_verificar)
    if total_arquivos == 0:
        logging.info("Nenhum arquivo compactado pendente para verificação.")
        if config['verbose']:
            print("Nenhum arquivo compactado pendente para verificação.")
        return

    if config['verbose']:
        print(f"Iniciando verificação de {total_arquivos} arquivos compactados...")
    logging.info(f"Iniciando verificação de {total_arquivos} arquivos compactados.")

    # Função auxiliar para verificar e extrair conteúdo do arquivo
    async def verificar_e_extrair(session, index, row):
        url = row['url']
        numero_controle_pncp = row.get('numero_controle_pncp', 'N/A')  # Supondo que exista essa coluna
        titulo = row['titulo']
        try:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                # Cria um diretório temporário para armazenar o arquivo baixado
                with tempfile.TemporaryDirectory() as tmpdirname:
                    temp_file_path = os.path.join(tmpdirname, os.path.basename(url))
                    with open(temp_file_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    # Lista para armazenar os nomes dos arquivos internos
                    arquivos_internos = []

                    # Identifica a extensão do arquivo e extrai os nomes dos arquivos internos
                    if titulo.lower().endswith('.zip'):
                        try:
                            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                                arquivos_internos = zip_ref.namelist()
                        except zipfile.BadZipFile:
                            logging.error(f"Arquivo ZIP inválido: '{titulo}' (URL: {url})")
                            if config['verbose']:
                                print(f"Erro: Arquivo ZIP inválido '{titulo}'.")
                    
                    elif titulo.lower().endswith('.rar'):
                        try:
                            with rarfile.RarFile(temp_file_path, 'r') as rar_ref:
                                arquivos_internos = rar_ref.namelist()
                        except rarfile.BadRarFile:
                            logging.error(f"Arquivo RAR inválido: '{titulo}' (URL: {url})")
                            if config['verbose']:
                                print(f"Erro: Arquivo RAR inválido '{titulo}'.")
                    
                    elif titulo.lower().endswith('.7zip'):
                        try:
                            with py7zr.SevenZipFile(temp_file_path, mode='r') as seven_zip_ref:
                                arquivos_internos = seven_zip_ref.getnames()
                        except py7zr.Bad7zFile:
                            logging.error(f"Arquivo 7ZIP inválido: '{titulo}' (URL: {url})")
                            if config['verbose']:
                                print(f"Erro: Arquivo 7ZIP inválido '{titulo}'.")
    
                    # Adiciona os nomes dos arquivos internos ao título
                    if arquivos_internos:
                        arquivos_str = ','.join(arquivos_internos)
                        df_arquivos.at[index, 'titulo'] = f"{titulo}, {arquivos_str}"
                        logging.info(f"Conteúdo de '{titulo}' adicionado ao DataFrame.")
                        if config['verbose']:
                            print(f"[{index + 1}/{total_arquivos}] Conteúdo de '{titulo}' adicionado.")
                    
                    # Marca a verificação como concluída
                    df_arquivos.at[index, 'verificacao_arquivos'] = True
                    logging.info(f"Verificação concluída para '{titulo}'.")
                    if config['verbose']:
                        print(f"[{index + 1}/{total_arquivos}] Verificação concluída para '{titulo}'.")
        
        except Exception as e:
            logging.error(f"Erro ao verificar arquivo '{titulo}' (URL: {url}): {str(e)}")
            if config['verbose']:
                print(f"[{index + 1}/{total_arquivos}] Erro ao verificar arquivo '{titulo}'.")
            # Mesmo em caso de erro, marca a verificação como True para evitar tentativas futuras
            df_arquivos.at[index, 'verificacao_arquivos'] = True

    # Realiza as requisições de verificação assíncronas
    semaphore = asyncio.Semaphore(config['numero_maximo_conexoes'])
    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, row in arquivos_para_verificar.iterrows():
            task = asyncio.create_task(verificar_e_extrair(session, idx, row))
            tasks.append(task)

        # Executa as tarefas com controle de semáforo
        await asyncio.gather(*tasks)

    # Salva o DataFrame atualizado de volta para o CSV
    try:
        df_arquivos.to_csv(paths['arquivos_csv'], index=False,sep='\t')
        logging.info(f"DataFrame de arquivos atualizado salvo em {paths['arquivos_csv']}.")
        if config['verbose']:
            print(f"Verificação de arquivos compactados concluída e salva em '{paths['arquivos_csv']}'.")
    except Exception as e:
        logging.error(f"Erro ao salvar {paths['arquivos_csv']}: {str(e)}")
        if config['verbose']:
            print(f"Erro ao salvar a verificação dos arquivos compactados em '{paths['arquivos_csv']}'.")

# ---------------------------- Alterações na Função Principal ---------------------------- #

def main():
    """
    Função principal que orquestra a execução do script.
    """
    # Analisa os argumentos da linha de comando
    args = parse_arguments()

    # Configura os diretórios e arquivos
    paths = setup_directories()

    # Configura o sistema de logs com o caminho correto
    setup_logging(paths['log_file'])

    # Carrega as configurações e aplica os parâmetros da CLI
    config = load_config(args)

    # Exibe as informações iniciais
    if config['verbose']:
        print("Iniciando raspagem com os seguintes parâmetros:")
        for key, value in config.items():
            if key != 'verbose':
                print(f"- {key}: {value}")

    logging.info("Iniciando raspagem de licitações.")

    # Carrega os dataframes existentes ou cria novos
    df_licitacoes, df_itens, df_arquivos, df_resultados = load_dataframes(paths)

    # Define as páginas a serem requisitadas (por exemplo, da página inicial até a 20)
    pages = list(range(config['pagina_inicial'], config['pagina_final']))

    # Realiza as requisições principais de forma assíncrona
    loop = asyncio.get_event_loop()
    try:
        respostas = loop.run_until_complete(fetch_licitacoes(config['tipos_documento'], config['ordenacao'], pages, config))
    except Exception as e:
        logging.critical(f"Erro durante a requisição das licitações: {str(e)}")
        if config['verbose']:
            print(f"Erro crítico: {str(e)}")
        sys.exit(1)

    # Processa as licitações obtidas
    df_licitacoes = process_licitacoes(respostas, df_licitacoes)

    # Salva o dataframe atualizado
    save_dataframes(df_licitacoes, df_itens, df_arquivos, paths)

    # Identifica licitações que ainda não tiveram os detalhes baixados
    if 'detalhes_baixados' not in df_licitacoes.columns:
        df_licitacoes['detalhes_baixados'] = False
    if 'documentos_baixados' not in df_licitacoes.columns:
        df_licitacoes['documentos_baixados'] = False

    registros_pendentes_itens = df_licitacoes[df_licitacoes['detalhes_baixados'] == False].to_dict('records')
    registros_pendentes_arquivos = df_licitacoes[df_licitacoes['documentos_baixados'] == False].to_dict('records')

    # Realiza as requisições de itens
    if registros_pendentes_itens:
        if config['verbose']:
            print(f"Iniciando requisições de itens para {len(registros_pendentes_itens)} licitações...")
        logging.info(f"Iniciando requisições de itens para {len(registros_pendentes_itens)} licitações.")
        
        for i in range(0, len(registros_pendentes_itens), 500):
            lote = registros_pendentes_itens[i:i + 500]
            if config['verbose']:
                print(f"Processando lote de itens {i + 1} a {min(i + 500, len(registros_pendentes_itens))}...")
            logging.info(f"Processando lote de itens {i + 1} a {min(i + 500, len(registros_pendentes_itens))}...")
            
            # Processa o lote
            detalhes_itens = loop.run_until_complete(fetch_detalhes(lote, 'itens', config))
            df_itens = processar_detalhes_registros(detalhes_itens, df_itens, 'itens')
            
            # Atualiza o DataFrame e salva progresso
            df_licitacoes.loc[df_licitacoes['detalhes_baixados'] == False, 'detalhes_baixados'] = True
            save_dataframes(df_licitacoes, df_itens, df_arquivos, paths)
    else:
        if config['verbose']:
            print("Nenhum registro pendente para itens.")
        logging.info("Nenhum registro pendente para itens.")

    # Realiza as requisições de resultados de cada um dos itens
    if not df_itens.empty:
        if 'Resultados verificados' not in df_itens.columns:
            df_itens['Resultados verificados'] = False
            df_itens.to_csv(paths['itens_csv'], index=False, sep='\t')
            logging.info("Coluna 'Resultados verificados' adicionada ao DataFrame de itens.")

        registros_itens = df_itens[df_itens['Resultados verificados'].astype(str) == 'False']
        if not registros_itens.empty:
            if config['verbose']:
                print(f"Iniciando requisições de resultados para {len(registros_itens)} itens...")
            logging.info(f"Iniciando requisições de resultados para {len(registros_itens)} itens.")
            
            for i in range(0, len(registros_itens), 500):
                lote = registros_itens.iloc[i:i + 500]
                if config['verbose']:
                    print(f"Processando lote de resultados {i + 1} a {min(i + 500, len(registros_itens))}...")
                logging.info(f"Processando lote de resultados {i + 1} a {min(i + 500, len(registros_itens))}...")
                
                # Processa o lote
                resultados = loop.run_until_complete(fetch_resultados(lote, config))
                df_resultados = processar_detalhes_registros(resultados, pd.DataFrame(), 'resultados')
                
                # Salva os resultados em um arquivo CSV separado (acrescenta ao arquivo existente)
                resultados_path = os.path.join(paths['main_directory'], 'resultados.csv')
                if os.path.exists(resultados_path):
                    df_resultados.to_csv(resultados_path, mode='a', header=False, index=False,sep='\t')
                else:
                    df_resultados.to_csv(resultados_path, index=False,sep='\t')
                
                # Atualiza a coluna 'Resultados verificados' para True para os itens processados
                df_itens.loc[lote.index, 'Resultados verificados'] = True
                
                # Salva o dataframe de itens atualizado após cada lote
                df_itens.to_csv(paths['itens_csv'], index=False,sep='\t')
        else:
            if config['verbose']:
                print("Nenhum item pendente para buscar resultados.")
            logging.info("Nenhum item pendente para buscar resultados.")
    else:
        if config['verbose']:
            print("Nenhum item para buscar resultados.")
        logging.info("Nenhum item para buscar resultados.")



    # Realiza as requisições de arquivos
    if registros_pendentes_arquivos:
        if config['verbose']:
            print(f"Iniciando requisições de arquivos para {len(registros_pendentes_arquivos)} licitações...")
        logging.info(f"Iniciando requisições de arquivos para {len(registros_pendentes_arquivos)} licitações.")
        
        for i in range(0, len(registros_pendentes_arquivos), 500):
            lote = registros_pendentes_arquivos[i:i + 500]
            if config['verbose']:
                print(f"Processando lote de arquivos {i + 1} a {min(i + 500, len(registros_pendentes_arquivos))}...")
            logging.info(f"Processando lote de arquivos {i + 1} a {min(i + 500, len(registros_pendentes_arquivos))}...")
            
            # Processa o lote
            detalhes_arquivos = loop.run_until_complete(fetch_detalhes(lote, 'arquivos', config))
            df_arquivos = processar_detalhes_registros(detalhes_arquivos, df_arquivos, 'arquivos')
            
            # Atualiza o DataFrame e salva progresso
            df_licitacoes.loc[df_licitacoes['documentos_baixados'] == False, 'documentos_baixados'] = True
            save_dataframes(df_licitacoes, df_itens, df_arquivos, paths)
    else:
        if config['verbose']:
            print("Nenhum registro pendente para arquivos.")
        logging.info("Nenhum registro pendente para arquivos.")


    # Executa a verificação dos arquivos compactados
    loop.run_until_complete(verify_compressed_files(paths, config))

    # Exibe o resumo da execução
    total_licitacoes = len(df_licitacoes)
    total_itens = len(df_itens)
    total_arquivos = len(df_arquivos)
    total_resultados = len(df_resultados)

    if config['verbose']:
        print("Raspagem concluída com sucesso!")
        print(f"Total de licitações processadas: {total_licitacoes}")
        print(f"Total de itens baixados: {total_itens}")
        print(f"Total de resultados de itens baixados: {total_resultados}")
        print(f"Total de arquivos baixados: {total_arquivos}")
        print(f"Logs detalhados podem ser encontrados em '{paths['log_file']}'")

    logging.info("Raspagem concluída com sucesso.")
    logging.info(f"Total de licitações processadas: {total_licitacoes}")
    logging.info(f"Total de itens baixados: {total_itens}")
    logging.info(f"Total de arquivos baixados: {total_arquivos}")

if __name__ == '__main__':
    main()

