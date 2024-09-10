#%%
import os
import json
import csv

#%%
# Definir os diretórios de busca
dir_principal = "pncp_dados_json"
dir_itens = "pncp_dados_itens"
dir_arquivos = "pncp_dados_arquivos"
dir_unificados = "pncp_dados_unificados"
log_file = "log_unificacao.txt"
csv_file = "pncp_unificados.csv"

# Criar o diretório de arquivos unificados se ele não existir
if not os.path.exists(dir_unificados):
    os.makedirs(dir_unificados)

#%%
# Função para carregar JSON de um arquivo
def carregar_json(caminho_arquivo):
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Função para unificar os arquivos
def unificar_dados(arquivo_base, arquivo_itens, arquivo_arquivos):
    # Carregar os dados
    dados_base = carregar_json(arquivo_base)
    dados_itens = carregar_json(arquivo_itens)
    dados_arquivos = carregar_json(arquivo_arquivos)

    # Verificar se dados_arquivos é uma lista
    if isinstance(dados_arquivos, list) and len(dados_arquivos) > 0:
        dados_arquivos = dados_arquivos[0]  # Pega o primeiro item da lista
    else:
        dados_arquivos = {}

    # Unificar os dados seguindo a lógica definida
    dados_unificados = {
        "licitacao": {
            "id_pncp": dados_base.get("id", ""),
            "ano": dados_base.get("ano", ""),
            "numero_sequencial": dados_base.get("numero_sequencial", ""),
            "numero_controle_pncp": dados_base.get("numero_controle_pncp", ""),
            "orgao_superior": {
                "cnpj": dados_base.get("orgao_cnpj", ""),
                "nome": dados_base.get("orgao_nome", ""),
                "unidade": {
                    "codigo": dados_base.get("unidade_codigo", ""),
                    "nome": dados_base.get("unidade_nome", "")
                },
                "esfera": {
                    "id": dados_base.get("esfera_id", ""),
                    "nome": dados_base.get("esfera_nome", "")
                },
                "poder": {
                    "id": dados_base.get("poder_id", ""),
                    "nome": dados_base.get("poder_nome", "")
                },
                "municipio": {
                    "nome": dados_base.get("municipio_nome", ""),
                    "uf": dados_base.get("uf", "")
                }
            },
            "modalidade_licitacao": {
                "nome": dados_base.get("modalidade_licitacao_nome", "")
            },
            "datas": {
                "publicacao_pncp": dados_base.get("data_publicacao_pncp", ""),
                "inicio_vigencia": dados_base.get("data_inicio_vigencia", ""),
                "fim_vigencia": dados_base.get("data_fim_vigencia", "")
            },
            "cancelado": dados_base.get("cancelado", ""),
            "arquivos_publicados": {
                "titulo": dados_arquivos.get("titulo", ""),
                "uri": dados_arquivos.get("uri", ""),
                "arquivos": ", ".join(dados_arquivos.get("nome_real", []))
            },
            "tipo": {
                "id": dados_base.get("tipo_id", ""),
                "nome": dados_base.get("tipo_nome", "")
            },
            "item_url": f"https://pncp.gov.br/app/editais/{dados_base.get('orgao_cnpj', '')}/{dados_base.get('ano', '')}/{dados_base.get('numero_sequencial', '')}"
        },
        "itens": dados_itens
    }

    return dados_unificados

# Função para registrar log
def registrar_log(mensagem):
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(mensagem + '\n')

# Função para salvar os dados no CSV
def salvar_csv(dados_unificados, csv_writer):
    licitacao = dados_unificados["licitacao"]
    csv_writer.writerow([
        licitacao.get("id_pncp", ""),
        licitacao.get("ano", ""),
        licitacao.get("numero_sequencial", ""),
        licitacao.get("numero_controle_pncp", ""),
        licitacao["orgao_superior"].get("cnpj", ""),
        licitacao["orgao_superior"].get("nome", ""),
        licitacao["orgao_superior"]["unidade"].get("codigo", ""),
        licitacao["orgao_superior"]["unidade"].get("nome", ""),
        licitacao["orgao_superior"]["esfera"].get("nome", ""),
        licitacao["orgao_superior"]["poder"].get("nome", ""),
        licitacao["orgao_superior"]["municipio"].get("nome", ""),
        licitacao["orgao_superior"]["municipio"].get("uf", ""),
        licitacao["modalidade_licitacao"].get("nome", ""),
        licitacao["datas"].get("publicacao_pncp", ""),
        licitacao["datas"].get("inicio_vigencia", ""),
        licitacao["datas"].get("fim_vigencia", ""),
        licitacao.get("cancelado", ""),
        licitacao["arquivos_publicados"].get("titulo", ""),
        licitacao["arquivos_publicados"].get("uri", ""),
        licitacao["arquivos_publicados"].get("arquivos", ""),
        licitacao["tipo"].get("id", ""),
        licitacao["tipo"].get("nome", ""),
        licitacao.get("item_url", "")
    ])

# Função principal para buscar, unificar e salvar os arquivos
def processar_arquivos():
    # Inicializar o CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Escrever o cabeçalho do CSV
        csv_writer.writerow([
            "ID PNCP", "Ano", "Número Sequencial", "Número Controle PNCP",
            "CNPJ Órgão", "Nome Órgão", "Código Unidade", "Nome Unidade",
            "Esfera Nome", "Poder Nome", "Município Nome", "UF", "Modalidade",
            "Data Publicação PNCP", "Início Vigência", "Fim Vigência",
            "Cancelado", "Título Arquivo", "URI Arquivo", "Nomes Arquivos",
            "Tipo ID", "Tipo Nome", "Item URL"
        ])
        
        for arquivo in os.listdir(dir_principal):
            if arquivo.endswith(".json"):
                # Definir o caminho do arquivo principal
                caminho_arquivo_principal = os.path.join(dir_principal, arquivo)
                
                # Gerar o nome dos arquivos de itens e arquivos com base no nome do arquivo principal
                nome_base = arquivo.replace(".json", "")
                caminho_arquivo_itens = os.path.join(dir_itens, f"{nome_base}_itens.json")
                caminho_arquivo_arquivos = os.path.join(dir_arquivos, f"{nome_base}_arquivos.json")
                
                # Verificar se os arquivos de itens e arquivos existem e unificar
                dados_unificados = unificar_dados(caminho_arquivo_principal, caminho_arquivo_itens, caminho_arquivo_arquivos)
                
                # Definir o caminho de saída para o arquivo unificado
                caminho_saida = os.path.join(dir_unificados, f"{nome_base}_unificado.json")
                
                # Salvar o arquivo unificado em JSON
                with open(caminho_saida, 'w', encoding='utf-8') as f:
                    json.dump(dados_unificados, f, ensure_ascii=False, indent=4)
                
                # Salvar os dados no CSV
                salvar_csv(dados_unificados, csv_writer)
                
                # Verificar se algum arquivo não foi encontrado e registrar no log
                if not os.path.exists(caminho_arquivo_itens):
                    registrar_log(f"Arquivo de itens não encontrado para {nome_base}")
                if not os.path.exists(caminho_arquivo_arquivos):
                    registrar_log(f"Arquivo de documentos não encontrado para {nome_base}")
                
                print(f"Arquivo unificado salvo em: {caminho_saida}")
#%%
# Executar o script
if __name__ == "__main__":
    # Limpar o arquivo de log
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Log de unificação de arquivos\n")
    
    processar_arquivos()

# %%
