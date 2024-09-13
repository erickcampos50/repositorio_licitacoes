import subprocess
import sys
import os
import logging
import threading
import queue

# Configuração do Logging
logging.basicConfig(
    filename='arquivos_principais/pipeline_log.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Função para ler e imprimir o fluxo de saída em tempo real
def stream_reader(pipe, script_name, log_queue):
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                line = line.rstrip()
                if line:
                    message = f"[{script_name}] {line}"
                    print(message)
                    log_queue.put(message)
    except Exception as e:
        error_message = f"[{script_name}] Erro ao ler o fluxo de saída: {e}"
        print(error_message)
        log_queue.put(error_message)

# Função para executar um script Python e capturar sua saída em tempo real
def executar_script(nome_script, log_queue):
    try:
        logging.info(f"Iniciando execução do script: {nome_script}")
        process = subprocess.Popen(
            [sys.executable, nome_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Linha por vez
        )

        # Threads para ler stdout e stderr
        stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, nome_script, log_queue))
        stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, f"{nome_script} [ERRO]", log_queue))

        stdout_thread.start()
        stderr_thread.start()

        # Esperar a conclusão do processo
        process.wait()

        # Aguardar as threads terminarem
        stdout_thread.join()
        stderr_thread.join()

        if process.returncode == 0:
            logging.info(f"Script {nome_script} executado com sucesso.")
        else:
            logging.error(f"Script {nome_script} terminou com código de erro {process.returncode}.")
            log_queue.put(f"[{nome_script}] Terminado com código de erro {process.returncode}.")
    except Exception as e:
        logging.error(f"Erro ao executar {nome_script}: {e}")
        log_queue.put(f"[{nome_script}] Erro ao executar: {e}")

# Função para executar a pipeline de atas
def run_atas_pipeline(log_queue):
    scripts = [
        'raspagem_pncp_atas.py',
        'raspagem_pncp_atas_itens-adicionais.py',
        'raspagem_unificacao_pncp_atas.py'
    ]
    for script in scripts:
        if os.path.exists(script):
            executar_script(script, log_queue)
        else:
            error_msg = f"[AtasPipeline] Script não encontrado: {script}"
            print(error_msg)
            logging.error(error_msg)
            log_queue.put(error_msg)

# Função para executar a pipeline de licitações
def run_pncp_pipeline(log_queue):
    scripts = [
        'raspagem_pncp.py',
        'raspagem_pncp_itens-adicionais.py',
        'raspagem_unificacao_pncp.py'
    ]
    for script in scripts:
        if os.path.exists(script):
            executar_script(script, log_queue)
        else:
            error_msg = f"[PncpPipeline] Script não encontrado: {script}"
            print(error_msg)
            logging.error(error_msg)
            log_queue.put(error_msg)

# Função para processar mensagens do log_queue e registrá-las no arquivo de log
def log_worker(log_queue):
    while True:
        message = log_queue.get()
        if message == "DONE":
            break
        logging.info(message)
        log_queue.task_done()

# Função principal do Pipeline
def main():
    # Criar uma fila para mensagens de log
    log_queue = queue.Queue()

    # Iniciar o thread do log_worker
    logging_thread = threading.Thread(target=log_worker, args=(log_queue,), daemon=True)
    logging_thread.start()

    # Criar threads para ambas as pipelines
    thread_atas = threading.Thread(target=run_atas_pipeline, name='AtasPipeline', args=(log_queue,))
    thread_pncp = threading.Thread(target=run_pncp_pipeline, name='PncpPipeline', args=(log_queue,))

    # Iniciar as threads
    thread_atas.start()
    thread_pncp.start()

    # Aguardar a conclusão de ambas as threads
    thread_atas.join()
    thread_pncp.join()

    # Enviar sinal para encerrar o log_worker
    log_queue.put("DONE")
    logging_thread.join()

    print("Todas as pipelines foram executadas. Verifique 'arquivos_principais/pipeline_log.log' para mais detalhes.")
    logging.info("Todas as pipelines foram executadas.")

if __name__ == "__main__":
    main()
