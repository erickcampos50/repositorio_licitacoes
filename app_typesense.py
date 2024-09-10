#%%
import os
from typesense import Client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json


#%%
# Configuração do cliente Typesense
client = Client({
    'nodes': [{
        'host': 'localhost',  # Endereço do Typesense
        'port': '8108',
        'protocol': 'http'
    }],
    'api_key': 'xyz',
    'connection_timeout_seconds': 2
})

#%%
# Definição do esquema da coleção
collection_schema = {
    "name": "catalog2",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "description", "type": "string"},
        {"name": "item_url", "type": "string"},
        {"name": "document_type", "type": "string"},
        {"name": "createdAt", "type": "string"},
        {"name": "orgao_nome", "type": "string"},
        {"name": "uf", "type": "string"},
        {"name": "modalidade_licitacao_nome", "type": "string"},
        {"name": "data_inicio_vigencia", "type": "string", "optional": True},
        {"name": "data_fim_vigencia", "type": "string", "optional": True},
        {"name": "cancelado", "type": "bool", "optional": True},
        {"name": "tem_resultado", "type": "bool", "optional": True}
    ]
}

# Criando a coleção, se ela não existir
try:
    client.collections.create(collection_schema)
except Exception as e:
    print(f"A coleção já existe ou ocorreu um erro: {e}")

# Função para processar e inserir o JSON na base de dados
def insert_documents_from_json(json_data):
    documents = []
    
    for item in json_data['items']:
        document = {
            "id": item['id'],
            "title": item['title'],
            "description": item['description'],
            "item_url": item['item_url'],
            "document_type": item['document_type'],
            "createdAt": item['createdAt'],
            "orgao_nome": item['orgao_nome'],
            "uf": item['uf'],
            "modalidade_licitacao_nome": item['modalidade_licitacao_nome'],
            "data_inicio_vigencia": item.get('data_inicio_vigencia'),
            "data_fim_vigencia": item.get('data_fim_vigencia'),
            "cancelado": item.get('cancelado', False),
            "tem_resultado": item.get('tem_resultado', False)
        }
        documents.append(document)
    
    # Inserindo os documentos na coleção
    try:
        result = client.collections['catalog2'].documents.import_(documents, {'action': 'upsert'})
        print(f"Documentos inseridos/atualizados: {result}")
    except Exception as e:
        print(f"Erro ao inserir documentos: {e}")

# Classe para monitorar novas adições de arquivos JSON
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return None
        elif event.src_path.endswith(".json"):
            print(f"Novo arquivo detectado: {event.src_path}")
            with open(event.src_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                insert_documents_from_json(json_data)

# Função para monitorar o diretório em busca de novos arquivos JSON
def monitor_directory(path_to_watch):
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()
    try:
        while True:
            pass  # Mantenha o processo em execução para monitoramento contínuo
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Defina o caminho do diretório a ser monitorado
path_to_watch = "pncp_dados_json"
#%%
# Inicia o monitoramento do diretório
monitor_directory(path_to_watch)

#%%
