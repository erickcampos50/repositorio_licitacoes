#%%
import os
import json
import requests
from io import BytesIO
from zipfile import ZipFile, BadZipFile
import datetime
import time

#%%
# Diretório onde os arquivos JSON individuais estão salvos (ajustado para o novo diretório de "atas")
INPUT_DIR = "pncp_atas_json"

# Diretório onde os resultados dos itens serão salvos (com "ata" no nome)
ITEMS_DIR_ATA = "pncp_atas_dados_itens"

# Diretório onde os resultados dos arquivos serão salvos (com "ata" no nome)
ARQUIVOS_DIR_ATA = "pncp_atas_dados_arquivos"

# Arquivo de log para rastrear quais arquivos JSON já foram processados (renomeado para especificidade com "ata")
LOG_FILE_ATA = "raspagem_atas_adicional_log.json"

# Tempo de espera entre requisições (em segundos) para evitar sobrecarga do servidor
DELAY = 2  

#%%
# Criar diretórios de saída se não existirem
for directory in [ITEMS_DIR_ATA, ARQUIVOS_DIR_ATA]:
    if not os.path.exists(directory):
        os.makedirs(directory)

#%%
# Funções para consultar itens e arquivos adicionais
def get_itens(orgao_cnpj, ano, numero_sequencial):
    url_itens = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_cnpj}/compras/{ano}/{numero_sequencial}/itens?pagina=1&tamanhoPagina=20"
    response = requests.get(url_itens)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao acessar itens para CNPJ {orgao_cnpj}, Ano {ano}, Nº Sequencial {numero_sequencial}: {response.status_code}")
        return None

def get_arquivos(orgao_cnpj, ano, numero_sequencial):
    url_arquivos = f"https://pncp.gov.br/api/pncp/v1/orgaos/{orgao_cnpj}/compras/{ano}/{numero_sequencial}/arquivos?pagina=1&tamanhoPagina=20"
    response = requests.get(url_arquivos)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao acessar arquivos para CNPJ {orgao_cnpj}, Ano {ano}, Nº Sequencial {numero_sequencial}: {response.status_code}")
        return None

# Função para obter o nome real do arquivo e sua extensão
def get_file_name_and_extension(url):
    response = requests.head(url, allow_redirects=True)
    if 'Content-Disposition' in response.headers:
        content_disposition = response.headers['Content-Disposition']
        # Trata casos onde 'filename=' pode estar no formato 'filename="nome.ext"'
        parts = content_disposition.split('filename=')
        if len(parts) > 1:
            filename = parts[1].strip('"')
        else:
            filename = url.split('/')[-1]
    else:
        # Fallback: use the URL path as filename
        filename = url.split('/')[-1]
    return filename

# Função para inspecionar o conteúdo de um arquivo ZIP e listar os nomes dos arquivos contidos
def inspect_zip_file(url, initial_chunk_size=512 * 1024):
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar o arquivo ZIP: {response.status_code}")
    content = BytesIO()
    chunk_size = initial_chunk_size

    # Continuar baixando até conseguirmos ler o conteúdo do ZIP
    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:  # Filtrar keep-alive chunks
            content.write(chunk)
            try:
                # Tentar abrir o arquivo zip com os bytes baixados até agora
                with ZipFile(BytesIO(content.getvalue())) as zip_file:
                    return zip_file.namelist()
            except BadZipFile:
                # Se der erro, significa que não baixamos bytes suficientes para ler o ZIP
                # Aumentar o tamanho do chunk para a próxima iteração
                chunk_size *= 2
                continue

    raise Exception("Não foi possível ler o conteúdo do arquivo ZIP.")

# Função para carregar o log
def load_log():
    if os.path.exists(LOG_FILE_ATA):
        with open(LOG_FILE_ATA, 'r', encoding='utf-8') as log_file:
            return json.load(log_file)
    else:
        return {}

# Função para atualizar o log
def update_log(log_data, item_id):
    log_data[item_id] = datetime.datetime.now().isoformat()
    with open(LOG_FILE_ATA, 'w', encoding='utf-8') as log_file:
        json.dump(log_data, log_file, ensure_ascii=False, indent=4)

# Função para processar os arquivos JSON
def process_json_files():
    log_data = load_log()

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(INPUT_DIR, filename)
            item_id = filename.replace(".json", "")
            
            # Verificar se o item já foi processado anteriormente
            if item_id in log_data:
                print(f"Item {item_id} já processado em {log_data[item_id]}. Pulando...")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            orgao_cnpj = data.get('orgao_cnpj')
            ano = data.get('ano')
            numero_sequencial = data.get('numero_sequencial')
            
            if orgao_cnpj and ano and numero_sequencial:
                # Consultando itens adicionais
                itens = get_itens(orgao_cnpj, ano, numero_sequencial)
                if itens:
                    itens_file_path = os.path.join(ITEMS_DIR_ATA, f"{item_id}_itens.json")
                    with open(itens_file_path, 'w', encoding='utf-8') as file:
                        json.dump(itens, file, ensure_ascii=False, indent=4)
                    print(f"Itens salvos para {filename}")
                
                # Consultando arquivos adicionais
                arquivos = get_arquivos(orgao_cnpj, ano, numero_sequencial)
                if arquivos:
                    for arquivo in arquivos:
                        url = arquivo.get('url')
                        if not url:
                            print(f"URL ausente para arquivo em {item_id}")
                            continue
                        filename_real = get_file_name_and_extension(url)
                        arquivo['nome_real'] = filename_real
                        arquivo['extensao_real'] = filename_real.split('.')[-1]
                        
                        # Se o arquivo for um ZIP, inspecionar o conteúdo
                        if arquivo['extensao_real'].lower() == 'zip':
                            try:
                                file_list = inspect_zip_file(url)
                                arquivo['conteudo_zip'] = file_list
                            except Exception as e:
                                print(f"Erro ao inspecionar ZIP {filename_real}: {str(e)}")
                    
                    arquivos_file_path = os.path.join(ARQUIVOS_DIR_ATA, f"{item_id}_arquivos.json")
                    with open(arquivos_file_path, 'w', encoding='utf-8') as file:
                        json.dump(arquivos, file, ensure_ascii=False, indent=4)
                    print(f"Arquivos salvos para {filename}")
                
                update_log(log_data, item_id)
                time.sleep(DELAY)
            else:
                print(f"Dados insuficientes para fazer consultas adicionais em {filename}")

#%%
if __name__ == "__main__":
    process_json_files()

# %%