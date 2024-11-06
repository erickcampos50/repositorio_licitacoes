# Manual do Sistema de Raspagem de Licitações do PNCP

---

## Sumário
1. [Introdução](#introdução)
2. [Descrição dos Módulos](#descrição-dos-módulos)
    - [Módulo de Configuração](#módulo-de-configuração)
    - [Módulo de Interface de Linha de Comando (CLI)](#módulo-de-interface-de-linha-de-comando-cli)
    - [Módulo de Logs](#módulo-de-logs)
    - [Módulo de Diretórios e Arquivos](#módulo-de-diretórios-e-arquivos)
    - [Módulo de Armazenamento](#módulo-de-armazenamento)
    - [Módulo de Requisições](#módulo-de-requisições)
    - [Módulo de Processamento de Dados](#módulo-de-processamento-de-dados)
    - [Módulo de Verificação de Arquivos Compactados](#módulo-de-verificação-de-arquivos-compactados)
    - [Módulo Principal (Main)](#módulo-principal-main)
3. [Uso da Interface de Linha de Comando (CLI)](#uso-da-interface-de-linha-de-comando-cli)
    - [Principais Parâmetros da CLI](#principais-parâmetros-da-cli)
    - [Exemplos de Uso da CLI](#exemplos-de-uso-da-cli)
4. [Fluxo Geral do Sistema](#fluxo-geral-do-sistema)
5. [Diagrama do Sistema](#diagrama-do-sistema)
6. [Considerações Finais](#considerações-finais)

---

## 1. Introdução

Este documento fornece uma visão detalhada do **Sistema de Raspagem de Licitações do PNCP** desenvolvido em Python. O sistema é projetado para coletar e processar dados de licitações públicas a partir da API do **Portal Nacional de Contratações Públicas (PNCP)**. Dada a grande quantidade de dados (aproximadamente 10 mil registros de licitações, itens e arquivos), o sistema é modularizado para garantir eficiência, escalabilidade e facilidade de manutenção.

O sistema inclui uma **Interface de Linha de Comando (CLI)** que permite aos usuários configurar parâmetros de execução, monitorar o progresso em tempo real e obter relatórios detalhados sobre o processo de raspagem.

---

## 2. Descrição dos Módulos

O sistema é composto por vários módulos, cada um responsável por uma parte específica do processo de raspagem. A seguir, são descritos cada um desses módulos e como eles interagem entre si.

### Módulo de Configuração

**Objetivo:** Centralizar e carregar as configurações do sistema. Essas configurações definem os parâmetros básicos das requisições à API, como URLs, tamanho das páginas, critérios de ordenação e controle de taxa para requisições simultâneas.

**Funções Principais:**
- **`load_config(args)`**: Carrega as configurações do arquivo `config.ini` e aplica os parâmetros fornecidos via CLI.

**Interação com Outros Módulos:**
- Fornece as configurações carregadas para os módulos de Requisições, Processamento de Dados e Verificação de Arquivos Compactados.

### Módulo de Interface de Linha de Comando (CLI)

**Objetivo:** Facilitar a configuração dos parâmetros de execução do sistema diretamente pelo usuário através da linha de comando.

**Funções Principais:**
- **`parse_arguments()`**: Define e analisa os argumentos fornecidos via CLI, permitindo ao usuário customizar o comportamento do script.

**Interação com Outros Módulos:**
- Fornece os parâmetros analisados para o Módulo de Configuração, que os integra às configurações do sistema.

### Módulo de Logs

**Objetivo:** Gerenciar o registro detalhado das ações e erros que ocorrem durante a execução do sistema.

**Funções Principais:**
- **`setup_logging(log_file)`**: Configura o sistema de logs para registrar eventos e erros em um arquivo log (`raspagem_pncp.log`) e, opcionalmente, no console.

**Interação com Outros Módulos:**
- É utilizado por todos os módulos para registrar eventos e erros, garantindo rastreabilidade e diagnóstico de problemas.

### Módulo de Diretórios e Arquivos

**Objetivo:** Garantir que os diretórios e arquivos necessários para a operação do sistema existam e estejam corretamente configurados.

**Funções Principais:**
- **`setup_directories()`**: Verifica a existência dos diretórios e arquivos necessários (`raspagem/licitacoes.csv`, `raspagem/itens.csv`, `raspagem/arquivos.csv`, `raspagem/raspagem_pncp.log`) e os cria se não existirem.

**Interação com Outros Módulos:**
- Fornece os caminhos dos arquivos para os módulos de Armazenamento, Requisições e Verificação de Arquivos Compactados.

### Módulo de Armazenamento

**Objetivo:** Armazenar os dataframes em arquivos CSV para persistência dos dados e garantir que o sistema possa retomar o processo a partir de onde parou em execuções anteriores.

**Funções Principais:**
- **`load_dataframes(paths)`**: Carrega os dataframes existentes a partir dos arquivos CSV ou cria novos dataframes vazios se os arquivos não existirem.
- **`save_dataframes(df_licitacoes, df_itens, df_arquivos, paths)`**: Salva os dataframes atualizados em arquivos CSV, evitando duplicidades.

**Interação com Outros Módulos:**
- Recebe dataframes do Módulo de Processamento de Dados e fornece dataframes para o Módulo de Verificação de Arquivos Compactados.
- Utiliza o Módulo de Logs para registrar eventos de armazenamento.

### Módulo de Requisições

**Objetivo:** Realizar as requisições assíncronas à API do PNCP e controlar a taxa de requisições simultâneas.

**Funções Principais:**
- **`fetch_with_retry(session, url, params, config, tentativa=1)`**: Realiza uma requisição HTTP com retentativas e backoff exponencial em caso de falhas.
- **`limited_fetch(semaphore, session, url, params, config)`**: Controla o número máximo de conexões simultâneas utilizando um semáforo.
- **`fetch_licitacoes(tipos_documento, ordenacao, pages, config)`**: Realiza as requisições das licitações de forma assíncrona para cada tipo de documento.
- **`fetch_detalhes(registros, data_type, config)`**: Realiza as requisições dos detalhes (itens ou arquivos) de forma assíncrona para cada registro de licitação.

**Interação com Outros Módulos:**
- Recebe configurações do Módulo de Configuração.
- Fornece dados JSON para o Módulo de Processamento de Dados.
- Utiliza o Módulo de Logs para registrar eventos de requisição.

### Módulo de Processamento de Dados

**Objetivo:** Estruturar e processar os dados recebidos das requisições, transformando-os em dataframes do `pandas` para armazenamento e análise.

**Funções Principais:**
- **`process_licitacoes(respostas, df_licitacoes)`**: Processa as respostas das licitações e atualiza o dataframe principal `df_licitacoes`.
- **`process_detalhes(detalhes_list, df_detalhes, data_type)`**: Processa os detalhes (itens ou arquivos) e atualiza os dataframes correspondentes (`df_itens` ou `df_arquivos`).

**Interação com Outros Módulos:**
- Recebe dados JSON do Módulo de Requisições.
- Fornece dados processados para o Módulo de Armazenamento.
- Utiliza o Módulo de Logs para registrar eventos de processamento.

### Módulo de Verificação de Arquivos Compactados

**Objetivo:** Realizar uma verificação adicional para inspecionar o conteúdo dos arquivos compactados (`.zip`, `.rar`, `.7zip`) listados nas licitações.

**Funções Principais:**
- **`verify_compressed_files(paths, config)`**: Verifica arquivos compactados, extrai seus conteúdos e atualiza o DataFrame `df_arquivos`.
    - **`verificar_e_extrair(session, index, row)`**: Função auxiliar para baixar e extrair arquivos compactados usando as bibliotecas `zipfile`, `rarfile` e `py7zr`.

**Interação com Outros Módulos:**
- Recebe configurações do Módulo de Configuração.
- Recebe dataframes do Módulo de Armazenamento.
- Atualiza o DataFrame `df_arquivos` e utiliza o Módulo de Logs para registrar eventos de verificação.

### Módulo Principal (Main)

**Objetivo:** Orquestrar o fluxo de execução entre os módulos, garantindo que o processo siga corretamente do início ao fim.

**Funções Principais:**
- **`main()`**: Coordena a execução dos módulos, gerencia o fluxo de dados entre eles e controla o processo de raspagem.

**Fluxo de Execução:**
1. **Configurações Iniciais:** Carrega os parâmetros do sistema e configura os diretórios e arquivos.
2. **Carregamento dos Dataframes:** Verifica a existência dos arquivos CSV e carrega dados previamente salvos, garantindo a continuidade do processo.
3. **Requisições e Processamento de Dados:** Executa requisições à API, processa os dados e os armazena nos dataframes.
4. **Verificação de Arquivos Compactados:** Inicia a verificação de arquivos compactados, caso necessário, para cada licitação.
5. **Salvamento e Logging:** Salva os dados processados periodicamente e registra os eventos no log.
6. **Relatório Final:** No final da execução, exibe um resumo com o número total de registros processados, itens baixados e arquivos verificados, tanto no console quanto no log.

---

## 3. Uso da Interface de Linha de Comando (CLI)

A **Interface de Linha de Comando (CLI)** do sistema permite ao usuário configurar os parâmetros de execução diretamente no momento de inicialização, fornecendo flexibilidade para customizar o comportamento do programa. A seguir, são detalhados os principais parâmetros disponíveis na CLI e exemplos de como utilizá-los.

### Principais Parâmetros da CLI

1. **`--pagina-inicial`**
   - **Descrição:** Define a página inicial para começar a raspagem.
   - **Exemplo:** `--pagina-inicial 5` (começa a raspagem a partir da página 5).
   - **Padrão:** 1 (primeira página).

2. **`--tam-pagina`**
   - **Descrição:** Define o tamanho da página, ou seja, quantos registros são baixados por requisição.
   - **Exemplo:** `--tam-pagina 100` (baixa 100 registros por requisição).
   - **Padrão:** 500.

3. **`--ordenacao`**
   - **Descrição:** Define o critério de ordenação dos registros retornados. Pode receber múltiplos critérios separados por vírgula.
   - **Exemplo:** `--ordenacao data_publicacao_pncp,-data,relevancia` (ordena os resultados pela data de publicação no PNCP, data descendente e relevância).
   - **Padrão:** `data,-data,relevancia`.

4. **`--tipos-documento`**
   - **Descrição:** Define os tipos de documentos que devem ser baixados. As opções incluem `edital`, `ata` ou ambos.
   - **Exemplo:** `--tipos-documento edital ata` (baixará documentos dos tipos edital e ata).
   - **Padrão:** `edital,ata`.

5. **`--max-conexoes`**
   - **Descrição:** Define o número máximo de conexões simultâneas ao fazer requisições à API.
   - **Exemplo:** `--max-conexoes 5` (limita o número de conexões a 5).
   - **Padrão:** 10.

6. **`--tentativas-maximas`**
   - **Descrição:** Define o número máximo de tentativas em caso de falha em uma requisição.
   - **Exemplo:** `--tentativas-maximas 3` (tenta cada requisição até 3 vezes em caso de falha).
   - **Padrão:** 5.

7. **`--verbose`**
   - **Descrição:** Ativa o modo verboso, apresentando informações detalhadas sobre o andamento do processo.
   - **Exemplo:** `--verbose` (ativa a exibição de mensagens detalhadas no console).
   - **Padrão:** Modo silencioso (sem `--verbose`).

8. **`--help`**
   - **Descrição:** Exibe a ajuda e informações sobre todos os parâmetros disponíveis.
   - **Exemplo:** `--help`.

### Exemplos de Uso da CLI

1. **Execução com Configurações Padrão**
    ```bash
    python raspagem.py
    ```
    - **Descrição:** Inicia o processo de raspagem com as configurações padrão: página inicial 1, tamanho de página 500, ordenação por `data,-data,relevancia`, tipos de documento `edital,ata`, máximo de 10 conexões, até 5 tentativas em caso de falha e modo silencioso.

2. **Execução Definindo Página Inicial e Tamanho da Página**
    ```bash
    python raspagem.py --pagina-inicial 10 --tam-pagina 100
    ```
    - **Descrição:** Inicia a raspagem a partir da página 10, com 100 registros baixados por requisição.

3. **Execução com Ordenação e Tipos de Documentos Específicos**
    ```bash
    python raspagem.py --ordenacao data_publicacao_pncp --tipos-documento edital
    ```
    - **Descrição:** Ordena os registros por `data_publicacao_pncp` e baixa apenas documentos do tipo `edital`.

4. **Execução Limitando o Número de Conexões e Ativando o Modo Verboso**
    ```bash
    python raspagem.py --max-conexoes 5 --verbose
    ```
    - **Descrição:** Limita o número de conexões simultâneas a 5 e exibe mensagens detalhadas sobre o progresso.

5. **Execução com Todas as Configurações Personalizadas**
    ```bash
    python raspagem.py --pagina-inicial 3 --tam-pagina 200 --ordenacao data_publicacao_pncp,-data --tipos-documento edital ata --max-conexoes 8 --tentativas-maximas 4 --verbose
    ```
    - **Descrição:** Configura uma raspagem começando na página 3, com 200 registros por página, ordena por `data_publicacao_pncp` e `-data`, baixa documentos dos tipos `edital` e `ata`, limita conexões simultâneas a 8, permite até 4 tentativas por requisição e exibe mensagens detalhadas.

---

## 4. Fluxo Geral do Sistema

O fluxo de execução do **Sistema de Raspagem de Licitações do PNCP** é organizado para garantir eficiência, controle e robustez durante a coleta e processamento dos dados. A seguir, é apresentado o fluxo geral do sistema:

1. **Inicialização:**
   - O sistema é iniciado através do módulo principal (`main`).
   - As configurações são carregadas e os diretórios necessários são configurados.
   - O sistema de logs é configurado para registrar eventos e erros.

2. **Carregamento dos Dataframes:**
   - Os dataframes existentes (`df_licitacoes`, `df_itens`, `df_arquivos`) são carregados a partir dos arquivos CSV.
   - Caso os arquivos CSV não existam, novos dataframes vazios são criados.

3. **Requisições à API:**
   - As requisições à API do PNCP são realizadas de forma assíncrona utilizando `asyncio` e `aiohttp`.
   - O controle de conexões simultâneas é mantido conforme o parâmetro `--max-conexoes`.
   - Em caso de falhas nas requisições, o sistema tenta novamente com backoff exponencial até o número máximo de tentativas definido.

4. **Processamento de Dados:**
   - Os dados JSON recebidos das requisições são processados e organizados nos dataframes correspondentes.
   - São mantidas colunas de controle (`detalhes_baixados` e `documentos_baixados`) para monitorar o status de cada licitação.

5. **Armazenamento dos Dados:**
   - Os dataframes atualizados são salvos em arquivos CSV para persistência dos dados.
   - O sistema garante que não haja duplicidades nos registros salvos.

6. **Verificação de Arquivos Compactados:**
   - O sistema identifica arquivos compactados (`.zip`, `.rar`, `.7zip`) que ainda não foram verificados.
   - Para cada arquivo, o sistema realiza o download e inspeciona seu conteúdo, listando os arquivos internos.
   - Os nomes dos arquivos internos são adicionados ao título do arquivo no DataFrame `df_arquivos`.
   - A coluna `verificacao_arquivos` é atualizada para `True` após a verificação.

7. **Registro de Eventos e Erros:**
   - Todas as ações, sucessos e erros são registrados no arquivo de log configurado.
   - Mensagens detalhadas são exibidas no console se o modo verboso estiver ativado.

8. **Relatório Final:**
   - Ao final da execução, o sistema exibe e registra um resumo com o número total de licitações processadas, itens baixados e arquivos compactados verificados.
   - Indica também a localização dos logs detalhados para referência futura.

Este fluxo garante que o sistema execute a raspagem de forma organizada, eficiente e resiliente a falhas, permitindo uma coleta de dados robusta e confiável.

---

## 5. Diagrama do Sistema

A seguir, apresenta-se um diagrama detalhado da arquitetura do sistema utilizando a linguagem **Mermaid**, que ilustra os módulos, suas funções principais, métodos importantes e os relacionamentos entre eles.

```mermaid
graph TD
    A[Módulo Principal (Main)]
    B[Módulo de Configuração]
    C[Módulo de Interface de Linha de Comando (CLI)]
    D[Módulo de Logs]
    E[Módulo de Diretórios e Arquivos]
    F[Módulo de Armazenamento]
    G[Módulo de Requisições]
    H[Módulo de Processamento de Dados]
    I[Módulo de Verificação de Arquivos Compactados]
    
    %% Relacionamentos entre Módulos
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    
    %% Detalhes dos Módulos
    B --> |Carrega Configurações| B1[Função load_config]
    C --> |Analisa Argumentos CLI| C1[Função parse_arguments]
    D --> |Configura Logs| D1[Função setup_logging]
    E --> |Configura Diretórios e Arquivos| E1[Função setup_directories]
    F --> |Carrega/Sava Dataframes| F1[Funções load_dataframes e save_dataframes]
    G --> |Realiza Requisições Assíncronas| G1[Funções fetch_licitacoes e fetch_detalhes]
    H --> |Processa Dados JSON| H1[Funções process_licitacoes e process_detalhes]
    I --> |Verifica Arquivos Compactados| I1[Função verify_compressed_files]
    I1 --> |Verifica e Extrai| I2[Função auxiliar verificar_e_extrair]
    
    %% Relações Adicionais
    B -->|Fornece Configurações| G
    B -->|Fornece Configurações| H
    B -->|Fornece Configurações| I
    
    E -->|Fornece Caminhos| F
    E -->|Fornece Caminhos| I
    
    G -->|Fornece Dados JSON| H
    H -->|Atualiza Dataframes| F
    I -->|Atualiza Dataframes| F
    
    D -->|Registra Eventos e Erros| A
    D -->|Registra Eventos e Erros| B
    D -->|Registra Eventos e Erros| C
    D -->|Registra Eventos e Erros| E
    D -->|Registra Eventos e Erros| F
    D -->|Registra Eventos e Erros| G
    D -->|Registra Eventos e Erros| H
    D -->|Registra Eventos e Erros| I
    
    %% Métodos Importantes
    G1 --> |Implementa Retentativas| G1a[Função fetch_with_retry]
    G1 --> |Controla Conexões| G1b[Função limited_fetch]
    I1 --> |Usa zipfile, rarfile, py7zr| I1a[Bibliotecas de Extração]
```

### Explicação do Diagrama

1. **Módulo Principal (Main):**
   - **Funções Principais:**
     - Coordena a execução de todos os outros módulos.
     - Garante que o fluxo de dados entre os módulos ocorra corretamente.
   - **Métodos Importantes:**
     - **`main`**: Função central que inicia e gerencia todo o processo de raspagem.

2. **Módulo de Configuração:**
   - **Funções Principais:**
     - **`load_config`**: Carrega as configurações do sistema a partir do arquivo `config.ini` e aplica os parâmetros da CLI.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

3. **Módulo de Interface de Linha de Comando (CLI):**
   - **Funções Principais:**
     - **`parse_arguments`**: Define e analisa os argumentos fornecidos via CLI, permitindo ao usuário customizar o comportamento do script.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

4. **Módulo de Logs:**
   - **Funções Principais:**
     - **`setup_logging`**: Configura o sistema de logs para registrar eventos e erros.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

5. **Módulo de Diretórios e Arquivos:**
   - **Funções Principais:**
     - **`setup_directories`**: Verifica a existência dos diretórios e arquivos necessários (`raspagem/licitacoes.csv`, `raspagem/itens.csv`, `raspagem/arquivos.csv`, `raspagem/raspagem_pncp.log`) e os cria se não existirem.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

6. **Módulo de Armazenamento:**
   - **Funções Principais:**
     - **`load_dataframes`**: Carrega os dataframes existentes a partir dos arquivos CSV ou cria novos dataframes vazios se os arquivos não existirem.
     - **`save_dataframes`**: Salva os dataframes atualizados em arquivos CSV, evitando duplicidades.
   - **Métodos Importantes:**
     - **`Verificação de Registros`**: Garante que não haja duplicidades nos registros salvos.

7. **Módulo de Requisições:**
   - **Funções Principais:**
     - **`fetch_with_retry`**: Realiza uma requisição HTTP com retentativas e backoff exponencial em caso de falhas.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas utilizando um semáforo.
     - **`fetch_licitacoes`**: Realiza as requisições das licitações de forma assíncrona para cada tipo de documento.
     - **`fetch_detalhes`**: Realiza as requisições dos detalhes (itens ou arquivos) de forma assíncrona para cada registro de licitação.
   - **Métodos Importantes:**
     - **`Backoff Strategy`**: Estratégia de aumento progressivo do tempo de espera entre tentativas em caso de falhas nas requisições.
     - **`fetch_with_retry`**: Implementa retentativas com backoff exponencial.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas.

8. **Módulo de Processamento de Dados:**
   - **Funções Principais:**
     - **`process_licitacoes`**: Processa as respostas das licitações e atualiza o dataframe principal `df_licitacoes`.
     - **`process_detalhes`**: Processa os detalhes (itens ou arquivos) e atualiza os dataframes correspondentes (`df_itens` ou `df_arquivos`).
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

9. **Módulo de Verificação de Arquivos Compactados:**
   - **Funções Principais:**
     - **`verify_compressed_files`**: Verifica arquivos compactados, extrai seus conteúdos e atualiza o DataFrame `df_arquivos`.
     - **`verificar_e_extrair`**: Função auxiliar para baixar e extrair arquivos compactados usando as bibliotecas `zipfile`, `rarfile` e `py7zr`.
   - **Métodos Importantes:**
     - **`Bibliotecas de Extração`**: Utiliza `zipfile`, `rarfile` e `py7zr` para manipular diferentes formatos de arquivos compactados.

---

## 6. Considerações Finais

O **Sistema de Raspagem de Licitações do PNCP** é uma ferramenta robusta e eficiente para coletar e processar grandes volumes de dados de licitações públicas. Sua estrutura modularizada facilita a manutenção, escalabilidade e flexibilidade, permitindo ajustes conforme as necessidades específicas do usuário.

Através da **Interface de Linha de Comando (CLI)**, os usuários têm controle total sobre os parâmetros de execução, garantindo que o sistema possa ser adaptado para diferentes cenários e requisitos de coleta de dados.

O **diagrama em Mermaid** fornece uma visão clara da arquitetura do sistema, destacando as interações entre os módulos e os métodos importantes que cada um deles possui. Isso facilita a compreensão do fluxo de dados e do funcionamento interno do sistema.

Para garantir o correto funcionamento do sistema, é essencial que todas as dependências estejam instaladas e que o ambiente de execução esteja configurado adequadamente, especialmente para o manuseio de arquivos compactados que exigem ferramentas específicas como `unrar`.

Em caso de dúvidas ou necessidade de suporte adicional, recomenda-se consultar os logs detalhados gerados pelo sistema, que fornecem informações valiosas sobre o progresso e possíveis erros durante a execução do processo de raspagem.

---

# Anexos

## Diagrama do Sistema (Mermaid)

```mermaid
graph TD
    A[Módulo Principal (Main)]
    B[Módulo de Configuração]
    C[Módulo de Interface de Linha de Comando (CLI)]
    D[Módulo de Logs]
    E[Módulo de Diretórios e Arquivos]
    F[Módulo de Armazenamento]
    G[Módulo de Requisições]
    H[Módulo de Processamento de Dados]
    I[Módulo de Verificação de Arquivos Compactados]
    
    %% Relacionamentos entre Módulos
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    
    %% Detalhes dos Módulos
    B --> |Carrega Configurações| B1[Função load_config]
    C --> |Analisa Argumentos CLI| C1[Função parse_arguments]
    D --> |Configura Logs| D1[Função setup_logging]
    E --> |Configura Diretórios e Arquivos| E1[Função setup_directories]
    F --> |Carrega/Sava Dataframes| F1[Funções load_dataframes e save_dataframes]
    G --> |Realiza Requisições Assíncronas| G1[Funções fetch_licitacoes e fetch_detalhes]
    H --> |Processa Dados JSON| H1[Funções process_licitacoes e process_detalhes]
    I --> |Verifica Arquivos Compactados| I1[Função verify_compressed_files]
    I1 --> |Verifica e Extrai| I2[Função auxiliar verificar_e_extrair]
    
    %% Relações Adicionais
    B -->|Fornece Configurações| G
    B -->|Fornece Configurações| H
    B -->|Fornece Configurações| I
    
    E -->|Fornece Caminhos| F
    E -->|Fornece Caminhos| I
    
    G -->|Fornece Dados JSON| H
    H -->|Atualiza Dataframes| F
    I -->|Atualiza Dataframes| F
    
    D -->|Registra Eventos e Erros| A
    D -->|Registra Eventos e Erros| B
    D -->|Registra Eventos e Erros| C
    D -->|Registra Eventos e Erros| E
    D -->|Registra Eventos e Erros| F
    D -->|Registra Eventos e Erros| G
    D -->|Registra Eventos e Erros| H
    D -->|Registra Eventos e Erros| I
    
    %% Métodos Importantes
    G1 --> |Implementa Retentativas| G1a[Função fetch_with_retry]
    G1 --> |Controla Conexões| G1b[Função limited_fetch]
    I1 --> |Usa zipfile, rarfile, py7zr| I1a[Bibliotecas de Extração]
```

### Explicação do Diagrama

1. **Módulo Principal (Main):**
   - **Funções Principais:**
     - Coordena a execução de todos os outros módulos.
     - Garante que o fluxo de dados entre os módulos ocorra corretamente.
   - **Métodos Importantes:**
     - **`main`**: Função central que inicia e gerencia todo o processo de raspagem.

2. **Módulo de Configuração:**
   - **Funções Principais:**
     - **`load_config`**: Carrega as configurações do sistema a partir do arquivo `config.ini` e aplica os parâmetros da CLI.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

3. **Módulo de Interface de Linha de Comando (CLI):**
   - **Funções Principais:**
     - **`parse_arguments`**: Define e analisa os argumentos fornecidos via CLI, permitindo ao usuário customizar o comportamento do script.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

4. **Módulo de Logs:**
   - **Funções Principais:**
     - **`setup_logging`**: Configura o sistema de logs para registrar eventos e erros.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

5. **Módulo de Diretórios e Arquivos:**
   - **Funções Principais:**
     - **`setup_directories`**: Verifica a existência dos diretórios e arquivos necessários (`raspagem/licitacoes.csv`, `raspagem/itens.csv`, `raspagem/arquivos.csv`, `raspagem/raspagem_pncp.log`) e os cria se não existirem.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

6. **Módulo de Armazenamento:**
   - **Funções Principais:**
     - **`load_dataframes`**: Carrega os dataframes existentes a partir dos arquivos CSV ou cria novos dataframes vazios se os arquivos não existirem.
     - **`save_dataframes`**: Salva os dataframes atualizados em arquivos CSV, evitando duplicidades.
   - **Métodos Importantes:**
     - **`Verificação de Registros`**: Garante que não haja duplicidades nos registros salvos.

7. **Módulo de Requisições:**
   - **Funções Principais:**
     - **`fetch_with_retry`**: Realiza uma requisição HTTP com retentativas e backoff exponencial em caso de falhas.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas utilizando um semáforo.
     - **`fetch_licitacoes`**: Realiza as requisições das licitações de forma assíncrona para cada tipo de documento.
     - **`fetch_detalhes`**: Realiza as requisições dos detalhes (itens ou arquivos) de forma assíncrona para cada registro de licitação.
   - **Métodos Importantes:**
     - **`Backoff Strategy`**: Estratégia de aumento progressivo do tempo de espera entre tentativas em caso de falhas nas requisições.
     - **`fetch_with_retry`**: Implementa retentativas com backoff exponencial.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas.

8. **Módulo de Processamento de Dados:**
   - **Funções Principais:**
     - **`process_licitacoes`**: Processa as respostas das licitações e atualiza o dataframe principal `df_licitacoes`.
     - **`process_detalhes`**: Processa os detalhes (itens ou arquivos) e atualiza os dataframes correspondentes (`df_itens` ou `df_arquivos`).
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

9. **Módulo de Verificação de Arquivos Compactados:**
   - **Funções Principais:**
     - **`verify_compressed_files`**: Verifica arquivos compactados, extrai seus conteúdos e atualiza o DataFrame `df_arquivos`.
     - **`verificar_e_extrair`**: Função auxiliar para baixar e extrair arquivos compactados usando as bibliotecas `zipfile`, `rarfile` e `py7zr`.
   - **Métodos Importantes:**
     - **`Bibliotecas de Extração`**: Utiliza `zipfile`, `rarfile` e `py7zr` para manipular diferentes formatos de arquivos compactados.

---

## 7. Considerações Finais

O **Sistema de Raspagem de Licitações do PNCP** é uma ferramenta robusta e eficiente para coletar e processar grandes volumes de dados de licitações públicas. Sua estrutura modularizada facilita a manutenção, escalabilidade e flexibilidade, permitindo ajustes conforme as necessidades específicas do usuário.

Através da **Interface de Linha de Comando (CLI)**, os usuários têm controle total sobre os parâmetros de execução, garantindo que o sistema possa ser adaptado para diferentes cenários e requisitos de coleta de dados.

O **diagrama em Mermaid** fornece uma visão clara da arquitetura do sistema, destacando as interações entre os módulos e os métodos importantes que cada um deles possui. Isso facilita a compreensão do fluxo de dados e do funcionamento interno do sistema.

Para garantir o correto funcionamento do sistema, é essencial que todas as dependências estejam instaladas e que o ambiente de execução esteja configurado adequadamente, especialmente para o manuseio de arquivos compactados que exigem ferramentas específicas como `unrar`.

Em caso de dúvidas ou necessidade de suporte adicional, recomenda-se consultar os logs detalhados gerados pelo sistema, que fornecem informações valiosas sobre o progresso e possíveis erros durante a execução do processo de raspagem.

---

# Anexos

## Diagrama do Sistema (Mermaid)

```mermaid
graph TD
    A[Módulo Principal (Main)]
    B[Módulo de Configuração]
    C[Módulo de Interface de Linha de Comando (CLI)]
    D[Módulo de Logs]
    E[Módulo de Diretórios e Arquivos]
    F[Módulo de Armazenamento]
    G[Módulo de Requisições]
    H[Módulo de Processamento de Dados]
    I[Módulo de Verificação de Arquivos Compactados]
    
    %% Relacionamentos entre Módulos
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    A --> I
    
    %% Detalhes dos Módulos
    B --> |Carrega Configurações| B1[Função load_config]
    C --> |Analisa Argumentos CLI| C1[Função parse_arguments]
    D --> |Configura Logs| D1[Função setup_logging]
    E --> |Configura Diretórios e Arquivos| E1[Função setup_directories]
    F --> |Carrega/Sava Dataframes| F1[Funções load_dataframes e save_dataframes]
    G --> |Realiza Requisições Assíncronas| G1[Funções fetch_licitacoes e fetch_detalhes]
    H --> |Processa Dados JSON| H1[Funções process_licitacoes e process_detalhes]
    I --> |Verifica Arquivos Compactados| I1[Função verify_compressed_files]
    I1 --> |Verifica e Extrai| I2[Função auxiliar verificar_e_extrair]
    
    %% Relações Adicionais
    B -->|Fornece Configurações| G
    B -->|Fornece Configurações| H
    B -->|Fornece Configurações| I
    
    E -->|Fornece Caminhos| F
    E -->|Fornece Caminhos| I
    
    G -->|Fornece Dados JSON| H
    H -->|Atualiza Dataframes| F
    I -->|Atualiza Dataframes| F
    
    D -->|Registra Eventos e Erros| A
    D -->|Registra Eventos e Erros| B
    D -->|Registra Eventos e Erros| C
    D -->|Registra Eventos e Erros| E
    D -->|Registra Eventos e Erros| F
    D -->|Registra Eventos e Erros| G
    D -->|Registra Eventos e Erros| H
    D -->|Registra Eventos e Erros| I
    
    %% Métodos Importantes
    G1 --> |Implementa Retentativas| G1a[Função fetch_with_retry]
    G1 --> |Controla Conexões| G1b[Função limited_fetch]
    I1 --> |Usa zipfile, rarfile, py7zr| I1a[Bibliotecas de Extração]
```

### Explicação do Diagrama

1. **Módulo Principal (Main):**
   - **Funções Principais:**
     - Coordena a execução de todos os outros módulos.
     - Garante que o fluxo de dados entre os módulos ocorra corretamente.
   - **Métodos Importantes:**
     - **`main`**: Função central que inicia e gerencia todo o processo de raspagem.

2. **Módulo de Configuração:**
   - **Funções Principais:**
     - **`load_config`**: Carrega as configurações do sistema a partir do arquivo `config.ini` e aplica os parâmetros da CLI.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

3. **Módulo de Interface de Linha de Comando (CLI):**
   - **Funções Principais:**
     - **`parse_arguments`**: Define e analisa os argumentos fornecidos via CLI, permitindo ao usuário customizar o comportamento do script.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

4. **Módulo de Logs:**
   - **Funções Principais:**
     - **`setup_logging`**: Configura o sistema de logs para registrar eventos e erros.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

5. **Módulo de Diretórios e Arquivos:**
   - **Funções Principais:**
     - **`setup_directories`**: Verifica a existência dos diretórios e arquivos necessários (`raspagem/licitacoes.csv`, `raspagem/itens.csv`, `raspagem/arquivos.csv`, `raspagem/raspagem_pncp.log`) e os cria se não existirem.
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

6. **Módulo de Armazenamento:**
   - **Funções Principais:**
     - **`load_dataframes`**: Carrega os dataframes existentes a partir dos arquivos CSV ou cria novos dataframes vazios se os arquivos não existirem.
     - **`save_dataframes`**: Salva os dataframes atualizados em arquivos CSV, evitando duplicidades.
   - **Métodos Importantes:**
     - **`Verificação de Registros`**: Garante que não haja duplicidades nos registros salvos.

7. **Módulo de Requisições:**
   - **Funções Principais:**
     - **`fetch_with_retry`**: Realiza uma requisição HTTP com retentativas e backoff exponencial em caso de falhas.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas utilizando um semáforo.
     - **`fetch_licitacoes`**: Realiza as requisições das licitações de forma assíncrona para cada tipo de documento.
     - **`fetch_detalhes`**: Realiza as requisições dos detalhes (itens ou arquivos) de forma assíncrona para cada registro de licitação.
   - **Métodos Importantes:**
     - **`Backoff Strategy`**: Estratégia de aumento progressivo do tempo de espera entre tentativas em caso de falhas nas requisições.
     - **`fetch_with_retry`**: Implementa retentativas com backoff exponencial.
     - **`limited_fetch`**: Controla o número máximo de conexões simultâneas.

8. **Módulo de Processamento de Dados:**
   - **Funções Principais:**
     - **`process_licitacoes`**: Processa as respostas das licitações e atualiza o dataframe principal `df_licitacoes`.
     - **`process_detalhes`**: Processa os detalhes (itens ou arquivos) e atualiza os dataframes correspondentes (`df_itens` ou `df_arquivos`).
   - **Métodos Importantes:**
     - Nenhum método adicional além das funções mencionadas.

9. **Módulo de Verificação de Arquivos Compactados:**
   - **Funções Principais:**
     - **`verify_compressed_files`**: Verifica arquivos compactados, extrai seus conteúdos e atualiza o DataFrame `df_arquivos`.
     - **`verificar_e_extrair`**: Função auxiliar para baixar e extrair arquivos compactados usando as bibliotecas `zipfile`, `rarfile` e `py7zr`.
   - **Métodos Importantes:**
     - **`Bibliotecas de Extração`**: Utiliza `zipfile`, `rarfile` e `py7zr` para manipular diferentes formatos de arquivos compactados.

Este diagrama e as descrições dos módulos oferecem uma visão abrangente do funcionamento e da estrutura do sistema de raspagem. O usuário pode usar a CLI para customizar o processo, e cada módulo desempenha uma função específica para garantir a execução eficiente e modular do sistema.

---

# Resumo

Este manual detalha a estrutura, funcionamento e uso do **Sistema de Raspagem de Licitações do PNCP**. A modularização do sistema, combinada com uma **Interface de Linha de Comando (CLI)** flexível e um robusto sistema de logs, assegura uma coleta de dados eficiente, escalável e fácil de manter. O diagrama em **Mermaid** complementa o entendimento da arquitetura do sistema, destacando as interações entre os módulos e os métodos críticos que garantem o funcionamento adequado do processo de raspagem.

Para garantir o correto funcionamento do sistema, assegure-se de que todas as dependências estão instaladas e que o ambiente de execução está devidamente configurado, especialmente para o manuseio de arquivos compactados que requerem ferramentas específicas como `unrar`.

Em caso de dúvidas ou necessidade de suporte adicional, consulte os logs detalhados gerados pelo sistema, que fornecem informações valiosas sobre o progresso e possíveis erros durante a execução do processo de raspagem.