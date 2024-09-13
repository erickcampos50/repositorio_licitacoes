#%%
import os
import json
import csv
import math
import datetime

#%%
# Definir os diretórios de busca ajustados para "atas"
dir_principal = "pncp_atas_json"
dir_itens = "pncp_atas_dados_itens"
dir_arquivos = "pncp_atas_dados_arquivos"
dir_unificados = "pncp_atas_dados_unificados"
dir_arquivos_principais = "arquivos_principais"

# Definir os nomes dos arquivos
log_file = os.path.join(dir_arquivos_principais, "log_atas_unificacao.txt")
csv_file = os.path.join(dir_arquivos_principais, "pncp_atas_unificados.csv")
jsonl_file = os.path.join(dir_arquivos_principais, "pncp_atas_unificados.jsonl")
markdown_file = os.path.join(dir_arquivos_principais, "pncp_atas_unificados.md")

#%%
# Criar os diretórios de arquivos unificados e principais se não existirem
for directory in [dir_unificados, dir_arquivos_principais]:
    if not os.path.exists(directory):
        os.makedirs(directory)

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
    # Concatenar 'nome_real' com 'conteudo_zip' para formar 'nomes_arquivos_unificados'
    nomes_arquivos = dados_arquivos.get("nome_real", "")
    conteudo_zip = dados_arquivos.get("conteudo_zip", [])
    if conteudo_zip:
        nomes_arquivos += ", " + ", ".join(conteudo_zip)

    dados_unificados = {
        "licitacao": {
            "id_pncp": dados_base.get("id", ""),
            "ano": dados_base.get("ano", ""),
            "descricao": dados_base.get("description", ""),
            "titulo": dados_base.get("title", ""),
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
            "modalidade_licitacao": dados_base.get("modalidade_licitacao_nome", ""),
            "data_publicacao_pncp": dados_base.get("data_publicacao_pncp", ""),
            "data_atualizacao_pncp": dados_base.get("data_atualizacao_pncp", ""),
            "data_assinatura": dados_base.get("data_assinatura", ""),
            "data_inicio_vigencia": dados_base.get("data_inicio_vigencia", ""),
            "data_fim_vigencia": dados_base.get("data_fim_vigencia", ""),
            "cancelado": dados_base.get("cancelado", False),
            "arquivos_publicados": {
                "titulo": dados_arquivos.get("titulo", ""),
                "uri": dados_arquivos.get("uri", ""),
                "nomes_arquivos_unificados": nomes_arquivos
            },
            "tipo": {
                "id": dados_base.get("tipo_id", ""),
                "nome": dados_base.get("tipo_nome", "")
            },
            "item_url": f"https://pncp.gov.br{dados_base.get('item_url', '')}"
        },
        "itens": dados_itens
    }

    return dados_unificados

# Função para registrar log
def registrar_log(mensagem):
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(mensagem + '\n')

# Função para salvar os dados no CSV, incluindo os itens da licitação
def salvar_csv(dados_unificados, csv_writer):
    licitacao = dados_unificados["licitacao"]
    itens = dados_unificados.get("itens", [])

    if not isinstance(itens, list):  # Caso seja um dicionário
        itens = [itens]

    for item in itens:
        csv_writer.writerow([
            licitacao.get("titulo", ""),
            licitacao.get("ano", ""),
            licitacao.get("descricao", ""),
            licitacao["orgao_superior"].get("cnpj", ""),
            licitacao["orgao_superior"].get("nome", ""),
            licitacao["orgao_superior"]["unidade"].get("codigo", ""),
            licitacao["orgao_superior"]["unidade"].get("nome", ""),
            licitacao["orgao_superior"]["esfera"].get("nome", ""),
            licitacao["orgao_superior"]["poder"].get("nome", ""),
            licitacao["orgao_superior"]["municipio"].get("nome", ""),
            licitacao["orgao_superior"]["municipio"].get("uf", ""),
            licitacao.get("modalidade_licitacao", ""),
            licitacao.get("data_publicacao_pncp", ""),
            licitacao.get("data_atualizacao_pncp", ""),
            licitacao.get("data_assinatura", ""),
            licitacao.get("data_inicio_vigencia", ""),
            licitacao.get("data_fim_vigencia", ""),
            licitacao.get("cancelado", False),
            licitacao["arquivos_publicados"].get("titulo", ""),
            licitacao["arquivos_publicados"].get("uri", ""),
            licitacao["arquivos_publicados"].get("nomes_arquivos_unificados", ""),
            licitacao["arquivos_publicados"].get("extensao_real", ""),  # Se precisar manter, caso contrário remova
            licitacao["tipo"].get("id", ""),
            licitacao["tipo"].get("nome", ""),
            licitacao.get("item_url", ""),
            item.get("descricao", ""),
            item.get("materialOuServicoNome", ""),
            item.get("valorUnitarioEstimado", ""),
            item.get("quantidade", "")
            
        ])

# Função para gerar arquivo Markdown a partir do CSV, dividido em partes iguais
def gerar_markdown(partes):
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        total_linhas = len(reader)
        linhas_por_parte = math.ceil(total_linhas / partes)

        for parte in range(partes):
            parte_inicio = parte * linhas_por_parte
            parte_fim = min((parte + 1) * linhas_por_parte, total_linhas)
            markdown_file_parte = os.path.join(dir_arquivos_principais, f"pncp_unificados_parte_{parte + 1}.md")

            with open(markdown_file_parte, 'w', encoding='utf-8') as mdfile:
                for row in reader[parte_inicio:parte_fim]:
                    mdfile.write(f"# Licitação {row['Título']} - {row['Nome Órgão']}\n\n")
                    mdfile.write(f"**Licitação:** {row['Título']}\n")
                    mdfile.write(f"**Ano:** {row['Ano']}\n")
                    mdfile.write(f"**Objeto da licitação:** {row['Descrição']}\n")
                    mdfile.write(f"**CNPJ do Órgão:** {row['CNPJ Órgão']}\n")
                    mdfile.write(f"**Nome do Órgão:** {row['Nome Órgão']}\n")
                    mdfile.write(f"**Código da Unidade:** {row['Código Unidade']}\n")
                    mdfile.write(f"**Nome da Unidade:** {row['Nome Unidade']}\n")
                    mdfile.write(f"**Esfera:** {row['Esfera Nome']}\n")
                    mdfile.write(f"**Poder:** {row['Poder Nome']}\n")
                    mdfile.write(f"**Município:** {row['Município Nome']} - {row['UF']}\n")
                    mdfile.write(f"**Modalidade de Licitação:** {row['Modalidade']}\n")
                    mdfile.write(f"**Data de Publicação PNCP:** {row['Data da Publicação no PNCP']}\n")
                    mdfile.write(f"**Data de Atualização PNCP:** {row['Data da Atualização PNCP']}\n")
                    mdfile.write(f"**Data de Assinatura:** {row['Data de Assinatura']}\n")
                    mdfile.write(f"**Início da Vigência:** {row['Data de Início Vigência']}\n")
                    mdfile.write(f"**Fim da Vigência:** {row['Data de Fim Vigência']}\n")
                    mdfile.write(f"**Cancelado:** {row['Cancelado']}\n")
                    mdfile.write(f"**Título do Arquivo:** {row['Título Arquivo']}\n")
                    mdfile.write(f"**URI do Arquivo:** {row['URI Arquivo']}\n")
                    mdfile.write(f"**Nomes dos Arquivos:** {row['Nomes Arquivos']}\n")
                    mdfile.write(f"**Tipo ID:** {row['Tipo ID']}\n")
                    mdfile.write(f"**Tipo Nome:** {row['Tipo Nome']}\n")
                    mdfile.write(f"**Item URL:** {row['Item URL']}\n\n")
                    mdfile.write(f"## Itens da Licitação\n")
                    mdfile.write(f"**Descrição do Item:** {row['Item Descrição']}\n")
                    mdfile.write(f"**Material ou Serviço:** {row['Material ou Serviço Nome']}\n")
                    mdfile.write(f"**Valor Unitário Estimado:** {row['Valor Unitário Estimado']}\n")
                    mdfile.write(f"**Quantidade:** {row['Quantidade']}\n")
                    mdfile.write("\n---\n\n")
        
            print(f"Arquivo Markdown parte {parte + 1} gerado: {markdown_file_parte}")

# Função principal para buscar, unificar e salvar os arquivos
def processar_arquivos():
    # Inicializar o CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Escrever o cabeçalho do CSV (removemos "Conteúdo ZIP" e ajustamos "Nomes Arquivos")
        csv_writer.writerow([
            "Título", "Ano", "Descrição",
            "CNPJ Órgão", "Nome Órgão", "Código Unidade", "Nome Unidade",
            "Esfera Nome", "Poder Nome", "Município Nome", "UF", "Modalidade",
            "Data da Publicação no PNCP", "Data da Atualização PNCP", "Data de Assinatura",
            "Data de Início Vigência", "Data de Fim Vigência", "Cancelado",
            "Título Arquivo", "URI Arquivo", "Nomes Arquivos", "Extensão Real",
            "Tipo ID", "Tipo Nome", "Item URL",
            "Item Descrição", "Material ou Serviço Nome", "Valor Unitário Estimado", "Quantidade"
            
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

# Função para converter os arquivos unificados em um único arquivo JSONL
def converter_para_jsonl():
    with open(jsonl_file, 'w', encoding='utf-8') as jsonl_out:
        for arquivo in os.listdir(dir_unificados):
            if arquivo.endswith(".json"):
                caminho_arquivo_unificado = os.path.join(dir_unificados, arquivo)
                dados_unificados = carregar_json(caminho_arquivo_unificado)
                # Gravar cada objeto JSON como uma linha no arquivo JSONL
                jsonl_out.write(json.dumps(dados_unificados, ensure_ascii=False) + '\n')
    print(f"Arquivo JSONL criado: {jsonl_file}")

#%%
# Executar o script
if __name__ == "__main__":
    # Limpar o arquivo de log
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("Log de unificação de arquivos\n")
    
    processar_arquivos()
    converter_para_jsonl()
    
    # Número de partes do markdown fornecido pelo usuário
    partes = 10
    gerar_markdown(partes)

# %%
