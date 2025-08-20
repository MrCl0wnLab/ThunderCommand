# Arquitetura Thunder Command v2.2

<h1 align="center">
  <img src="../static/img/logo.png"   width="200">
</h1>

## Visão Geral da Arquitetura

O Thunder Command v2.2 implementa uma **arquitetura simplificada** focada em facilidade de uso e manutenção, consolidando toda a funcionalidade em um único arquivo principal.

## Execução do Servidor

### Servidor Principal (`app.py`)
- **Arquivo único** com todas as rotas e lógica de negócio
- **Deploy simples** para qualquer ambiente
- **Fácil manutenção** e compreensão
- **Ideal para**: Todos os casos de uso, desenvolvimento e produção

```bash
python app.py
# ou modo desenvolvimento
FLASK_ENV=development python app.py
```

## Componentes Principais

### Backend - Flask + SQLite

#### Camada de Dados
- **SQLite Database**: `thunder_command.db` (auto-criado)
- **Repository Pattern**: Abstração de acesso aos dados
  - `ClientRepository`: Gerenciamento de clientes conectados
  - `CommandRepository`: Histórico e rastreamento de comandos
- **Tabelas principais**:
  - `clients`: Informações e estatísticas de clientes
  - `commands`: Histórico de comandos executados
  - `command_results`: Resultados e métricas de execução

#### Camada de Negócio
```
core/
├── database/
│   ├── connection.py         # Singleton de conexão
│   ├── client_repository.py  # CRUD de clientes
│   └── command_repository.py # CRUD de comandos
└── utils/
    ├── logger.py            # Sistema multi-nível de logs
    └── helpers.py           # Utilitários auxiliares
```

#### Aplicação Principal (`app.py`)
- **Arquivo único** contendo todas as rotas e lógica
- **Sistema de autenticação** integrado
- **Gerenciamento de clientes** e comandos
- **API REST** completa para comunicação
- **Templates** e recursos estáticos organizados

### Frontend - Dashboard Administrativo

#### Tecnologias
- **Bootstrap 5.3.0**: Framework CSS responsivo
- **HTMX**: Atualizações parciais sem JavaScript complexo
- **Chart.js 4.3.0**: Visualização de dados em tempo real
- **Webpack 5.88.0**: Build system moderno

#### Estrutura
```
templates/
├── base.html               # Template base
├── admin_base.html         # Base administrativa
├── admin-dashboard.html    # Dashboard principal
├── partials/               # Componentes HTMX
│   ├── card_stats.html     # Cards de estatísticas
│   ├── clients_table.html  # Tabela de clientes
│   └── form_command_table.html # Interface de comandos
└── components/             # Componentes reutilizáveis
    ├── buttons.html
    ├── command_forms.html
    └── notifications.html
```

### Cliente - Polling Inteligente

#### Características
- **HTTP Polling exclusivo**: Sem dependências WebSocket
- **Estratégias de execução inteligentes**: Detecção automática de tipos de comando
- **Tolerância a falhas**: Sistema de retry e reconexão automática
- **JSONP Support**: Compatibilidade com arquivos locais

#### Arquivos
```
payload/
├── cmd.js                  # Cliente atual (HTTP polling)
└── cmd.js.new             # Versão atualizada
```

## Fluxo de Comunicação

### 1. Inicialização do Cliente
```mermaid
sequenceDiagram
    participant Browser as Navegador
    participant Server as Servidor Flask
    participant DB as SQLite

    Browser->>Server: GET /<id>/<file>.js
    Server->>Browser: Script cmd.js
    Browser->>Browser: Gerar ID único (localStorage)
    Browser->>Server: Registrar cliente
    Server->>DB: Salvar cliente
    Browser->>Browser: Iniciar polling
```

### 2. Execução de Comandos
```mermaid
sequenceDiagram
    participant Admin as Admin Panel
    participant Server as Servidor
    participant DB as SQLite
    participant Client as Cliente Browser

    Admin->>Server: POST /admin/set_command
    Server->>Server: Gerar JavaScript
    Server->>Server: Aplicar js_format_try_catch()
    Server->>DB: Salvar comando
    Server->>Admin: Confirmação

    Client->>Server: GET /command (polling)
    Server->>Client: Comando JavaScript
    Client->>Client: Executar JavaScript
    Client->>Server: POST /command/result
    Server->>DB: Salvar resultado
```

### 3. Processamento de Comandos HTML (Correção v2.0.1)

**Problema Original:**
```javascript
// Cliente tratava JavaScript como HTML
case 'html':
    result = this.injectHTML(commandData.command); // ❌ ERRO
```

**Correção Aplicada:**
```javascript
// Cliente executa JavaScript que injeta HTML
case 'html':
    result = await this.executeJavaScript(commandData.command); // ✅ CORRETO
```

## Sistema de Logging

### Níveis de Log
- **app_logger**: Logs gerais da aplicação
- **command_logger**: Logs específicos de comandos
- **auth_logger**: Logs de autenticação

### Estrutura
```
logs/
├── app.log              # Logs gerais
├── command.log          # Execução de comandos
└── auth.log            # Eventos de autenticação
```

**Nota**: O arquivo `websocket.log` foi removido na v2.1 com a eliminação completa do suporte WebSocket/Socket.IO.

## Configuração

### Variáveis de Ambiente
```bash
# Configurações opcionais via ambiente
export SECRET_KEY="sua_chave_secreta"
export ADMIN_USERNAME="seu_usuario"
export ADMIN_PASSWORD="sua_senha"
export FLASK_ENV="development"  # ou "production"
```

### Configuração no Código
- **Credenciais padrão**: `tandera`/`tandera`
- **Debug mode**: Ativado automaticamente com `FLASK_ENV=development`
- **Polling interval**: 5 segundos (configurável no código)

## Sistema de Build Frontend

### Desenvolvimento
```bash
npm install              # Instalar dependências
npm run dev             # Modo desenvolvimento (python app.py)
npm run lint            # Verificar código
npm test                # Executar testes
```

### Produção
```bash
npm start               # Executar servidor (python app.py)
```

## Segurança e Autenticação

### Autenticação
- **Session-based**: Gerenciamento via Flask sessions
- **Credenciais padrão**: `tandera`/`tandera` (configurável via ENV)
- **Middleware**: Decorator `@login_required`

### Variáveis de Ambiente
```bash
SECRET_KEY="sua_chave_secreta"
ADMIN_USERNAME="seu_usuario"
ADMIN_PASSWORD="sua_senha"
HOST="0.0.0.0"
PORT="5000"
```

## Monitoramento e Métricas

### Captura de Resultados
- **Toggle configurável**: Habilitação/desabilitação global
- **Métricas detalhadas**: Tempo de execução, tipo de resultado
- **Contadores**: Comandos recebidos, bem-sucedidos, falhados

### Limpeza Automática
- **Clientes inativos**: Remoção após 30 minutos (configurável)
- **Logs rotacionais**: Limite de 1000 comandos (configurável)
- **Cache híbrido**: Memória + persistência para performance

## Extensibilidade

### Adicionando Novos Tipos de Comando
1. **Server-side**: Atualizar `app.py` (função de geração de comandos)
2. **Client-side**: Modificar `payload/cmd.js` (método `executeCommand`)
3. **UI**: Adicionar em `templates/partials/form_command_table.html`
4. **Testes**: Criar em `tests/unit/` e `tests/integration/`

### Novas Rotas
```python
# Adicionar diretamente no app.py
@app.route('/nova-rota')
def nova_funcionalidade():
    return jsonify({'status': 'success'})
```

## Performance e Otimização

### Cache Strategy
- **Clientes ativos**: Cache em memória para polling rápido
- **Comandos**: Persistência SQLite + cache temporário
- **Resultados**: Armazenamento opcional configurável

### Polling Optimization
- **Intervalos inteligentes**: Ajuste automático baseado na atividade
- **Retry logic**: Backoff exponencial para reconexões
- **Batch processing**: Múltiplos clientes processados eficientemente

## Troubleshooting Arquitetural

### Problemas Comuns
1. **Port binding**: Verifique se porta 5000 está disponível
2. **Database locks**: SQLite não suporta escritas concorrentes extremas
3. **Memory leaks**: Monitore crescimento de cache de clientes
4. **Template errors**: Verifique se todos os templates estão no diretório `templates/`

### Debugging
```bash
# Logs detalhados
FLASK_ENV=development python app.py

# Database inspection
sqlite3 thunder_command.db
.tables
SELECT * FROM clients;
```

---

Esta arquitetura simplificada oferece facilidade de uso, manutenibilidade e clareza, permitindo que o Thunder Command seja facilmente compreendido e modificado por desenvolvedores de qualquer nível.