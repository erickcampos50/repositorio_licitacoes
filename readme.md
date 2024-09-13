# Pipeline de Raspagem e Unificação de Dados das Atas e Licitações (PNCP)

Este projeto consiste em uma **pipeline** completa para raspagem, processamento e unificação de dados provenientes de duas plataformas distintas: **Atas** e **Licitações (PNCP)**. A pipeline é projetada para ser executada de forma eficiente e robusta, garantindo que os dados sejam coletados e unificados corretamente, mesmo em caso de falhas em partes específicas do processo.

## Índice

1. [Visão Geral](#visão-geral)
2. [Lógica do Projeto](#lógica-do-projeto)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Benefícios](#benefícios)
5. [Como Usar](#como-usar)
    - [Execução da Pipeline](#execução-da-pipeline)
    - [Monitoramento da Execução](#monitoramento-da-execução)
6. [Interfaces de Acesso aos Dados](#interfaces-de-acesso-aos-dados)
7. [Logs](#logs)
8. [Resolução de Problemas](#resolução-de-problemas)
9. [Considerações Finais](#considerações-finais)
10. [Licença](#licença)

---

## Visão Geral

Esta pipeline é composta por duas etapas principais:

1. **Raspagem de Dados:**
    - **Principal:** Raspagem dos dados principais das plataformas de Atas e Licitações.
    - **Secundária:** Raspagem de dados adicionais que dependem dos dados principais já coletados.

2. **Unificação de Dados:**
    - Unificação dos dados coletados das plataformas de Atas e Licitações em formatos consolidados (JSON, CSV, JSONL e Markdown).

O processo é gerenciado por um **script mestre** que orquestra a execução independente das duas pipelines (Atas e Licitações), permitindo que falhas em uma não afetem a outra.

## Lógica do Projeto

A pipeline segue uma sequência estruturada para garantir a integridade e a eficiência na coleta e processamento dos dados:

1. **Raspagem Principal:**
    - **Atas:** O script `raspagem_atas.py` coleta os dados principais das atas e os salva em arquivos JSON no diretório `pncp_atas_json/`.
    - **Licitações:** O script `raspagem_pncp.py` coleta os dados principais das licitações e os salva em arquivos JSON no diretório `pncp_dados_json/`.

2. **Raspagem Secundária:**
    - **Itens Adicionais das Atas:** O script `raspagem_pncp_atas_itens-adicionais.py` coleta informações adicionais relacionadas aos itens das atas e os salva em `pncp_dados_itens/`.
    - **Itens Adicionais das Licitações:** O script `raspagem_pncp_itens-adicionais.py` coleta informações adicionais relacionadas aos itens das licitações e os salva em `pncp_dados_arquivos/`.
    - **Nota:** Esses scripts já possuem atrasos internos para respeitar os limites da API utilizada.

3. **Unificação dos Dados:**
    - **Atas:** O script `unificacao_pncp_atas.py` consolida os dados principais e adicionais das atas em formatos JSON, CSV, JSONL e Markdown, salvando-os nos diretórios apropriados.
    - **Licitações:** O script `unificacao_pncp.py` consolida os dados principais e adicionais das licitações em formatos JSON, CSV, JSONL e Markdown, salvando-os nos diretórios apropriados.

4. **Orquestração da Pipeline:**
    - O script mestre `run_pipeline.py` gerencia a execução das pipelines de **Atas** e **Licitações** de forma independente e paralela, garantindo que cada etapa seja concluída antes de prosseguir para a próxima.

## Estrutura do Projeto

```
├── arquivos_principais/
│   ├── log_unificacao.txt
│   ├── pipeline_log.log
│   ├── pncp_unificados.csv
│   ├── pncp_unificados.jsonl
│   ├── pncp_unificados_parte_1.md
│   ├── pncp_unificados_parte_2.md
│   └── ... (até parte_10.md)
├── pncp_dados_json/
│   ├── <id_pncp>.json
│   └── ... (outros arquivos JSON das licitações principais)
├── pncp_dados_itens/
│   ├── <id_pncp>_itens.json
│   └── ... (outros arquivos JSON de itens adicionais das licitações)
├── pncp_dados_arquivos/
│   ├── <id_pncp>_arquivos.json
│   └── ... (outros arquivos JSON de arquivos adicionais das licitações)
├── pncp_atas_json/
│   ├── <id_pncp>.json
│   └── ... (outros arquivos JSON das atas)
├── pncp_dados_unificados/
│   ├── <id_pncp>_unificado.json
│   └── ... (outros arquivos JSON unificados)
├── raspagem_pncp_itens-adicionais.py
├── raspagem_pncp_atas_itens-adicionais.py
├── raspagem_pncp.py
├── raspagem_atas.py
├── unificacao_pncp.py
├── unificacao_pncp_atas.py
├── run_pipeline.py
└── README.md
```

### Descrição das Pastas

- **arquivos_principais/**: Contém os arquivos gerados após a unificação dos dados, incluindo logs, CSV, JSONL e arquivos Markdown.
- **pncp_dados_json/**: Armazena os arquivos JSON principais das licitações.
- **pncp_dados_itens/**: Armazena os arquivos JSON de itens adicionais das licitações.
- **pncp_dados_arquivos/**: Armazena os arquivos JSON de arquivos adicionais das licitações.
- **pncp_atas_json/**: Contém os arquivos JSON principais das atas.
- **pncp_dados_unificados/**: Armazena os arquivos JSON unificados das licitações e atas.

## Benefícios

- **Acesso Completo aos Dados do PNCP:** Fornece uma maneira estruturada e eficiente de coletar todos os dados disponíveis nas plataformas de Atas e Licitações, garantindo que nenhuma informação importante seja omitida.
  
- **Facilidade de Análise:** Ao unificar os dados em formatos como CSV e JSONL, facilita a análise e o processamento posterior, permitindo o uso em ferramentas de BI, data science e outros sistemas de análise de dados.
  
- **Robustez e Resiliência:** As pipelines independentes garantem que falhas em uma parte do processo não afetem a outra, aumentando a confiabilidade do sistema como um todo.
  
- **Monitoramento em Tempo Real:** Com a execução paralela das pipelines e o monitoramento das saídas no terminal, é possível acompanhar o progresso e identificar rapidamente quaisquer problemas.
  
- **Automatização Completa:** Reduz a necessidade de intervenções manuais, economizando tempo e minimizando erros humanos.
  
- **Interfaces de Acesso e Visualização:** Disponibiliza interfaces gráficas para acesso facilitado e visualização dos dados raspados, adaptando-se às diferentes necessidades dos usuários.

## Interfaces de Acesso aos Dados

Além da pipeline de raspagem e unificação, este projeto oferece **interfaces gráficas** para facilitar o acesso e a visualização dos dados coletados:

1. ### [Interface Streamlit](https://repositorio-nacional-licitacoes.streamlit.app/)
   
   - **Descrição:** Uma interface gráfica desenvolvida com **Streamlit** que permite realizar buscas diretas na **API do PNCP**.
   - **Funcionalidades:**
     - Pesquisa rápida e eficiente de licitações.
     - Visualização detalhada dos resultados das buscas.
   - **Benefícios:**
     - **Foco Exclusivo em Licitações:** Ideal para usuários que precisam acessar rapidamente informações sobre licitações sem a necessidade de consultar dados das atas.
     - **Interação Intuitiva:** Interface amigável que facilita a navegação e a obtenção de dados específicos.
   - **Quando Usar:**
     - Quando se deseja realizar consultas rápidas e específicas diretamente na API do PNCP.
     - Para usuários que não necessitam integrar ou visualizar dados das atas.

2. ### [Interface Looker Studio](https://lookerstudio.google.com/u/0/reporting/5413c554-7852-46d4-84cf-edd7cdecb2e8/page/wWYBE)
   
   - **Descrição:** Uma interface desenvolvida com **Looker Studio** que permite visualizar os dados raspados das licitações e atas de forma integrada e interativa.
   - **Funcionalidades:**
     - Dashboards interativos para análise de dados.
     - Visualizações gráficas e relatórios detalhados.
   - **Benefícios:**
     - **Visualização Integrada:** Permite visualizar e analisar dados tanto de licitações quanto de atas em uma única plataforma.
     - **Ferramentas de BI Avançadas:** Oferece recursos avançados de Business Intelligence para análises profundas e customizadas.
   - **Quando Usar:**
     - Para usuários que precisam de análises detalhadas e integradas dos dados de licitações e atas.
     - Quando há a necessidade de gerar relatórios complexos e dashboards interativos para tomada de decisão.

**Escolha a interface que melhor atende às suas necessidades:**

- **Streamlit:** Para consultas rápidas e específicas nas licitações, com uma interface simples e direta.
- **Looker Studio:** Para análises integradas e visualizações avançadas dos dados coletados, incluindo licitações e atas.

## Como Usar

### Execução da Pipeline

A pipeline completa é orquestrada pelo script `run_pipeline.py`, que executa as pipelines de **Atas** e **Licitações** de forma independente e paralela.

1. **Verifique os Diretórios de Entrada:**

    - **Atas:**
        - `pncp_atas_json/`: Contém os arquivos JSON principais das atas.
        - `pncp_dados_itens/`: Contém os arquivos JSON de itens adicionais das licitações.
        - `pncp_dados_arquivos/`: Contém os arquivos JSON de arquivos adicionais das licitações.

    - **Licitações:**
        - `pncp_dados_json/`: Contém os arquivos JSON principais das licitações.
        - `pncp_dados_itens/`: Contém os arquivos JSON de itens adicionais das licitações.
        - `pncp_dados_arquivos/`: Contém os arquivos JSON de arquivos adicionais das licitações.

    **Certifique-se de que esses diretórios contêm os arquivos necessários antes de executar a pipeline.**

2. **Execute o Script Mestre:**

    No terminal, navegue até o diretório do projeto e execute:

    ```bash
    python run_pipeline.py
    ```

    **O que acontece:**

    - **Pipelines Paralelas:** As pipelines de **Atas** e **Licitações** são executadas simultaneamente em threads separadas.
    - **Logs em Tempo Real:** As saídas dos scripts são exibidas em tempo real no terminal, com prefixos indicando a origem das mensagens.
    - **Logs Detalhados:** Todas as mensagens de execução são registradas no arquivo `pipeline_log.log` para referência futura.

### Monitoramento da Execução

Durante a execução, você poderá acompanhar o progresso diretamente no terminal com mensagens semelhantes a:

```
[raspagem_atas.py] Iniciando raspagem das atas...
[raspagem_pncp.py] Iniciando raspagem das licitações...
[raspagem_atas.py] Raspagem das atas concluída com sucesso.
[raspagem_pncp.py] Raspagem das licitações concluída com sucesso.
[raspagem_pncp_atas_itens-adicionais.py] Iniciando raspagem de itens adicionais das atas...
[raspagem_pncp_itens-adicionais.py] Iniciando raspagem de itens adicionais das licitações...
[raspagem_pncp_atas_itens-adicionais.py] Raspagem de itens adicionais das atas concluída com sucesso.
[raspagem_pncp_itens-adicionais.py] Raspagem de itens adicionais das licitações concluída com sucesso.
[unificacao_pncp_atas.py] Iniciando unificação dos dados das atas...
[unificacao_pncp.py] Iniciando unificação dos dados das licitações...
[unificacao_pncp_atas.py] Unificação dos dados das atas concluída com sucesso.
[unificacao_pncp.py] Unificação dos dados das licitações concluída com sucesso.
Todas as pipelines foram executadas. Verifique 'pipeline_log.log' para mais detalhes.
```

## Interfaces de Acesso aos Dados

Além da pipeline de raspagem e unificação, este projeto oferece **interfaces gráficas** para facilitar o acesso e a visualização dos dados coletados:

1. ### [Interface Streamlit](https://repositorio-nacional-licitacoes.streamlit.app/)
   
   - **Descrição:** Uma interface gráfica desenvolvida com **Streamlit** que permite realizar buscas diretas na **API do PNCP**.
   - **Funcionalidades:**
     - Pesquisa rápida e eficiente de licitações.
     - Visualização detalhada dos resultados das buscas.
   - **Benefícios:**
     - **Foco Exclusivo em Licitações:** Ideal para usuários que precisam acessar rapidamente informações sobre licitações sem a necessidade de consultar dados das atas.
     - **Interação Intuitiva:** Interface amigável que facilita a navegação e a obtenção de dados específicos.
   - **Quando Usar:**
     - Quando se deseja realizar consultas rápidas e específicas diretamente na API do PNCP.
     - Para usuários que não necessitam integrar ou visualizar dados das atas.

2. ### [Interface Looker Studio](https://lookerstudio.google.com/u/0/reporting/5413c554-7852-46d4-84cf-edd7cdecb2e8/page/wWYBE)
   
   - **Descrição:** Uma interface desenvolvida com **Looker Studio** que permite visualizar os dados raspados das licitações e atas de forma integrada e interativa.
   - **Funcionalidades:**
     - Dashboards interativos para análise de dados.
     - Visualizações gráficas e relatórios detalhados.
   - **Benefícios:**
     - **Visualização Integrada:** Permite visualizar e analisar dados tanto de licitações quanto de atas em uma única plataforma.
     - **Ferramentas de BI Avançadas:** Oferece recursos avançados de Business Intelligence para análises profundas e customizadas.
   - **Quando Usar:**
     - Para usuários que precisam de análises detalhadas e integradas dos dados de licitações e atas.
     - Quando há a necessidade de gerar relatórios complexos e dashboards interativos para tomada de decisão.

**Escolha a interface que melhor atende às suas necessidades:**

- **Streamlit:** Para consultas rápidas e específicas nas licitações, com uma interface simples e direta.
- **Looker Studio:** Para análises integradas e visualizações avançadas dos dados coletados, incluindo licitações e atas.

## Logs

- **`pipeline_log.log`**
  
    - **Descrição:** Arquivo de log que armazena todas as mensagens de execução, incluindo informações de progresso e erros.
    - **Localização:** Diretório principal do projeto (`arquivos_principais/`).
    - **Uso:** Consulte este arquivo para detalhes sobre a execução da pipeline, especialmente para identificar e solucionar problemas.

## Resolução de Problemas

### Problema 1: Script Não Encontrado

**Mensagem de Erro no Terminal:**

```
[AtasPipeline] Script não encontrado: raspagem_atas.py
```

**Solução:**

- Verifique se o arquivo `raspagem_atas.py` está presente no diretório raiz do projeto.
- Certifique-se de que o nome do arquivo está correto e que não há erros de digitação.

### Problema 2: Erro Durante a Execução de um Script

**Mensagem de Erro no Terminal:**

```
[raspagem_pncp.py] Erro ao executar: Mensagem de erro detalhada
```

**Solução:**

- Consulte o arquivo `pipeline_log.log` para obter detalhes sobre o erro.
- Verifique o script `raspagem_pncp.py` para identificar e corrigir o problema.
- Assegure-se de que todas as dependências necessárias estão instaladas e atualizadas.

### Problema 3: Falha na Unificação dos Dados

**Mensagem de Erro no Terminal:**

```
[unificacao_pncp.py] Erro ao executar: Mensagem de erro detalhada
```

**Solução:**

- Verifique se os arquivos JSON de entrada estão presentes e corretamente formatados.
- Consulte `pipeline_log.log` para detalhes específicos sobre a falha.
- Assegure-se de que os diretórios de saída possuem permissões de escrita adequadas.

### Problema 4: Saída de Dados Incompleta ou Incorreta

**Solução:**

- Verifique se todos os scripts de raspagem foram executados com sucesso (mensagens de "executado com sucesso" no terminal).
- Consulte `pipeline_log.log` para identificar possíveis erros ou avisos durante a raspagem e unificação.
- Valide manualmente alguns arquivos de saída (JSON, CSV, Markdown) para garantir a integridade dos dados.

## Considerações Finais

- **Manutenção e Extensibilidade:**
    - Adicione novos scripts à pipeline conforme necessário, ajustando o `run_pipeline.py` para incluir os novos scripts nas pipelines apropriadas.
    - Mantenha o arquivo `requirements.txt` atualizado com todas as dependências necessárias.

- **Segurança:**
    - Assegure-se de que os dados coletados e processados estão sendo armazenados de forma segura.
    - Evite expor informações sensíveis nos logs ou nos arquivos de saída.

- **Performance:**
    - A raspagem secundária já possui mecanismos internos para respeitar os limites da API. Não adicione delays adicionais no script mestre para evitar atrasos desnecessários.

- **Ambiente Virtual:**
    - Utilize ambientes virtuais para isolar as dependências dos seus scripts, facilitando a reprodução e manutenção do ambiente de desenvolvimento.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

**Desenvolvido por [Erick C. Campos](https://github.com/seu-usuario)**

Se você tiver alguma dúvida, sugestão ou encontrar problemas, sinta-se à vontade para enviar um email para erickcampos50@gmail.com