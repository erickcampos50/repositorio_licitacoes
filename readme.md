## Crawler PNCP

### Visão Geral

O **Crawler PNCP** é uma ferramenta desenvolvida para facilitar a coleta de informações sobre compras públicas realizadas no Brasil. Utilizando a API oficial da [PNCP (Plataforma Nacional de Compras Públicas)](https://pncp.gov.br), o crawler busca, organiza e armazena dados relevantes em arquivos CSV, permitindo uma análise mais eficiente e estruturada das informações coletadas.

### Funcionalidades

- **Busca de Dados Automatizada:** Consulta automaticamente a API do PNCP para obter informações detalhadas sobre diversas compras públicas.
- **Organização de Dados:** Armazena os dados coletados em arquivos CSV organizados, facilitando a visualização e análise posterior.
- **Evita Duplicatas:** Verifica e impede a inserção de informações já existentes, garantindo que os dados sejam únicos e atualizados.
- **Coleta de Informações Adicionais:** Além dos dados principais, o crawler também coleta detalhes como itens e arquivos relacionados a cada compra.
- **Rapidez e Eficiência:** Utiliza múltiplas threads para acelerar o processo de coleta de dados, economizando tempo e recursos.
- **Registro de Atividades:** Gera logs detalhados das operações realizadas, auxiliando na identificação e resolução de possíveis problemas.
- **Cancelamento Seguro:** Permite interromper o processo de coleta a qualquer momento de forma segura, sem comprometer os dados já coletados.

### Como Usar

1. **Iniciar o Crawler:**
   
   - Execute o script `crawler_pncp.py`. Isso pode ser feito clicando duas vezes no arquivo ou executando-o através de um terminal ou prompt de comando.

2. **Escolher a Ordenação dos Dados:**
   
   - Ao iniciar, o crawler solicitará que você escolha como os dados serão organizados:
     ```
     Escolha o parâmetro de ordenação:
     1. Mais recentes primeiro
     2. Mais antigos primeiro
     3. Ordenados por relevância
     ```
   - Digite o número correspondente à opção desejada e pressione Enter.

3. **Monitorar o Processo:**
   
   - O crawler exibirá informações sobre o progresso no terminal, incluindo o número de itens processados, novos itens salvos e duplicatas encontradas.
   - **Para Cancelar o Processo:**
     - A qualquer momento, você pode digitar `q` e pressionar Enter para interromper a coleta de dados de forma segura.

4. **Finalização e Resultados:**
   
   - Ao concluir, o crawler apresentará um relatório resumido no terminal, detalhando estatísticas como tempo de execução, total de itens processados, novos itens salvos, duplicatas encontradas e erros ocorridos.
   - **Arquivos Gerados:**
     - **Logs:** Armazenados na pasta `Logs/`, com nomes como `crawler_log_YYYYMMDD_HHMMSS.log`.
     - **Dados CSV:** Armazenados na pasta `Dados_CSV/`, incluindo:
       - `pncp_data.csv`: Dados principais das compras.
       - `pncp_itens.csv`: Itens detalhados de cada compra.
       - `pncp_arquivos.csv`: Arquivos relacionados a cada compra.

### Entendendo os Resultados

- **Arquivos CSV:** São planilhas que podem ser abertas com programas como Microsoft Excel, Google Sheets ou qualquer editor de planilhas. Elas contêm informações estruturadas sobre as compras públicas, facilitando a análise e a geração de relatórios.
  
- **Logs:** Contêm um registro detalhado das operações realizadas pelo crawler, incluindo possíveis erros ou alertas. Esses logs são úteis para verificar o histórico de execução e identificar quaisquer problemas que possam ter ocorrido durante a coleta de dados.

### Dicas para Melhor Uso

- **Escolha de Ordenação:** Selecionar a opção de ordenação adequada pode ajudar a priorizar os dados mais relevantes para suas necessidades.
  
- **Monitoramento Regular:** Verifique periodicamente os arquivos CSV e os logs para garantir que os dados estão sendo coletados corretamente e para identificar qualquer comportamento inesperado.
  
- **Gerenciamento de Dados:** Mantenha os arquivos CSV organizados e faça backups regulares para evitar a perda de informações importantes.

### Tratamento de Erros

- **Requisições com Falha:**
  - O crawler tenta novamente até três vezes em caso de falhas nas requisições à API. Se todas as tentativas falharem, o erro será registrado no arquivo de log e o processo continuará com a próxima operação.
  
- **Verificação de Duplicatas:**
  - O sistema verifica automaticamente se os dados coletados já existem nos arquivos CSV para evitar duplicatas, garantindo que apenas informações novas sejam adicionadas.

### Sobre o Projeto

Este script serve para alimentar o repositório de informações de licitações, um projeto originalmente criado para o **GT de Obras do Forplad**. A ferramenta foi desenvolvida para facilitar a gestão e o acesso a dados de compras públicas, proporcionando maior transparência e eficiência no acompanhamento das licitações.

### Autor e Responsabilidades

O **Crawler PNCP** foi desenvolvido por **Erick C Campos**. Esta ferramenta é oferecida **sem garantias**, sendo fornecida "no estado em que se encontra" para uso conforme a necessidade do usuário. O desenvolvedor não se responsabiliza por quaisquer danos ou perdas decorrentes do uso desta ferramenta.

### Contato

Para dúvidas, sugestões ou suporte, entre em contato através do e-mail: [erick.campos@ufjf.br](mailto:erick.campos@ufjf.br).

