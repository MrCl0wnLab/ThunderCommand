# Guia de Desenvolvimento - Thunder Command

<h1 align="center">
  <img src="../static/img/logo.png"   width="200">
</h1>

## Introdução

Este guia é destinado a desenvolvedores que desejam contribuir ou modificar o Thunder Command. Complementa o `CLAUDE.md` fornecendo instruções práticas para setup, desenvolvimento e contribuição.

## Setup do Ambiente de Desenvolvimento

### Pré-requisitos
- **Python 3.8+** (testado com 3.13)
- **Node.js 16+** (para desenvolvimento frontend)
- **Git** para controle de versão
- **SQLite** (incluído no Python)

### Instalação Completa

```bash
# 1. Clone o repositório
git clone https://github.com/MrCl0wnLab/ThunderCommand.git
cd ThunderCommand

# 2. Configurar ambiente Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Instalar dependências frontend
npm install

# 5. Configurar variáveis de ambiente (opcional)
export SECRET_KEY="dev_secret_key"
export ADMIN_USERNAME="dev_admin"
export ADMIN_PASSWORD="dev_password"
export FLASK_ENV="development"
```

### Primeira Execução

```bash
# Servidor principal
python app.py

# Modo desenvolvimento com auto-reload
FLASK_ENV=development python app.py
```

Acesse: `http://localhost:5000/admin` (credenciais: `tandera`/`tandera`)

## Estrutura de Desenvolvimento

### Workflow Recomendado

1. **Development**: Use `python app.py` para desenvolvimento
2. **Frontend**: Use `npm run dev` para desenvolvimento com hot-reload  
3. **Testing**: Execute testes antes de commits
4. **Production**: Deploy simples com `python app.py`

### Organização de Código

#### Aplicação Principal (`app.py`)
- **Arquivo único** contendo toda a lógica da aplicação
- **Rotas organizadas** por funcionalidade
- **Autenticação integrada** 
- **Gerenciamento completo** de clientes e comandos
- **API REST** para comunicação com clientes

#### Core Modules (`core/`)
```
core/
├── database/                # Camada de persistência
│   ├── __init__.py
│   ├── connection.py        # Singleton de conexão
│   ├── client_repository.py # Repository pattern para clientes
│   └── command_repository.py# Repository pattern para comandos
└── utils/                   # Utilitários compartilhados
    ├── __init__.py
    ├── logger.py           # Sistema de logging multi-nível
    └── helpers.py          # Funções auxiliares
```

#### Frontend (`static/` + `templates/`)
```
static/
├── css/
│   ├── custom-dark-red.css  # Tema principal
│   └── components/          # Estilos por componente
├── js/
│   ├── app.js              # Script principal
│   ├── modules/            # Módulos organizados
│   │   ├── client-manager.js
│   │   ├── command-handler.js
│   │   └── dashboard-ui.js
│   └── vendor/             # Bibliotecas externas
└── img/                    # Assets de imagem

templates/
├── base.html               # Template base
├── admin_base.html         # Base administrativa
├── partials/               # Componentes HTMX
└── components/             # Componentes reutilizáveis
```

## Comandos de Desenvolvimento

### Python/Backend
```bash
# Executar com auto-reload
FLASK_ENV=development python app.py

# Limpar banco de dados
python clear_db.py
# ou
rm -f thunder_command.db

# Testes
pytest                      # Todos os testes
pytest tests/unit/          # Apenas testes unitários
pytest tests/integration/   # Apenas testes de integração
pytest -v --tb=short       # Verbose com traceback curto

# Testes específicos
pytest tests/unit/test_command_executor.py
pytest tests/integration/test_routes.py::test_admin_login
```

### Frontend/JavaScript
```bash
# Desenvolvimento
npm run dev                 # Modo desenvolvimento
npm start                  # Modo produção

# Qualidade de código
npm run lint               # ESLint
npm test                   # Testes JavaScript
eslint static/js/**/*.js   # Lint específico

# Build
npm run build              # Build otimizado
```

### Database
```bash
# Inspeção do banco
sqlite3 thunder_command.db
.tables
.schema clients
SELECT * FROM clients LIMIT 5;
SELECT * FROM commands WHERE type = 'html';

# Backup
cp thunder_command.db backup_$(date +%Y%m%d_%H%M%S).db

# Reset completo
rm -f thunder_command.db && python app.py
```

## Adicionando Novas Funcionalidades

### 1. Novo Tipo de Comando

#### Backend (`app.py`)
```python
# No app.py, encontrar a função de geração de comandos (~linha 280)
elif command_type == 'new_type':
    # Gerar JavaScript para o novo comando
    js_command = f"""
        // Implementação do novo comando
        console.log('Executing new command type: {content}');
        // Adicionar lógica específica aqui
    """
```

#### Frontend (Templates)
```html
<!-- templates/partials/form_command_table.html -->
<div class="tab-pane fade" id="new-type-tab" role="tabpanel">
    <div class="mb-3">
        <label for="new-type-content" class="form-label">Novo Comando:</label>
        <textarea class="form-control" id="new-type-content" rows="4" 
                  placeholder="Conteúdo do novo comando..."></textarea>
    </div>
</div>

<!-- Adicionar aba -->
<li class="nav-item" role="presentation">
    <button class="nav-link" id="new-type-tab" data-bs-toggle="tab" 
            data-bs-target="#new-type-tab" type="button">
        <i class="fas fa-new-icon"></i> Novo Comando
    </button>
</li>
```

#### Cliente (payload/cmd.js)
```javascript
// Em executeCommand(), adicionar novo case
case 'new_type':
    result = this.executeNewType(commandData);
    break;

// Implementar método
executeNewType(commandData) {
    try {
        // Lógica específica do cliente
        console.log('Executing new type:', commandData);
        return { success: true, result: 'New command executed' };
    } catch (error) {
        return { success: false, error: error.toString() };
    }
}
```

### 2. Nova Rota API

#### Adicionar Nova Rota
```python
# No app.py, adicionar nova rota
@app.route('/api/new-endpoint', methods=['GET', 'POST'])
def new_endpoint():
    """Nova funcionalidade"""
    if request.method == 'POST':
        data = request.get_json()
        # Processar dados
        return jsonify({'status': 'success', 'data': data})
    
    return jsonify({'status': 'ready'})

@app.route('/api/new-endpoint/<int:client_id>', methods=['DELETE'])
def delete_client_data(client_id):
    """Deletar dados específicos do cliente"""
    try:
        # Lógica de deleção usando os repositórios existentes
        client_repo.delete_client(client_id)
        return jsonify({'status': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 3. Novo Componente Frontend

#### Template Component
```html
<!-- templates/components/new_component.html -->
<div class="new-component-container">
    <div class="card">
        <div class="card-header">
            <h5 class="card-title">Nova Funcionalidade</h5>
        </div>
        <div class="card-body">
            <div id="new-component-content">
                <!-- Conteúdo dinâmico -->
            </div>
        </div>
    </div>
</div>
```

#### JavaScript Module
```javascript
// static/js/modules/new-component.js
class NewComponent {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
    }

    setupEventListeners() {
        // Event listeners específicos
    }

    async loadData() {
        try {
            const response = await fetch('/api/new/data');
            const data = await response.json();
            this.renderData(data);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    renderData(data) {
        // Renderizar dados no componente
    }
}

// Exportar para uso global
window.NewComponent = NewComponent;
```

## Debugging e Troubleshooting

### Logs de Desenvolvimento
```python
# Ativar logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs específicos por módulo
from core.utils.logger import app_logger, command_logger

app_logger.debug("Debug message")
command_logger.info("Command executed: %s", command_data)
```

### Debug do Cliente
```javascript
// No payload/cmd.js, habilitar debug
window.thunderDebug = true;

// Logs detalhados aparecerão no console
console.debug('Thunder Command Debug Mode Enabled');
```

### Problemas Comuns

#### 1. Comandos HTML Não Funcionam
**Sintoma**: JavaScript wrapper aparece na página
**Causa**: Cliente tratando JS como HTML
**Solução**: Verificar `executeCommand()` em `payload/cmd.js`

```javascript
// ❌ ERRO
case 'html':
    result = this.injectHTML(commandData.command);

// ✅ CORRETO
case 'html':
    result = await this.executeJavaScript(commandData.command);
```

#### 2. Cliente Não Conecta
**Diagnóstico**:
```bash
# Verificar se servidor está rodando
curl http://localhost:5000/
curl http://localhost:5000/command?client_id=test

# Verificar logs
tail -f logs/app.log
```

#### 3. Porta Ocupada
**Problema**: Porta 5000 já está em uso
**Solução**: 
```bash
# Verificar processos na porta 5000
lsof -i :5000
# Matar processo específico
pkill -f "python app.py"
```

## Testes

### Estrutura de Testes
```
tests/
├── unit/                   # Testes unitários
│   ├── test_command_executor.py
│   ├── test_client_repository.py
│   └── test_helpers.py
├── integration/            # Testes de integração
│   ├── test_routes.py
│   ├── test_client_flow.py
│   └── test_command_flow.py
└── fixtures/               # Dados de teste
    ├── sample_clients.json
    └── sample_commands.json
```

### Criando Novos Testes

#### Teste Unitário
```python
# tests/unit/test_new_feature.py
import pytest
from app.services.new_feature import NewFeatureService

class TestNewFeature:
    def setup_method(self):
        self.service = NewFeatureService()
    
    def test_new_functionality(self):
        # Arrange
        test_data = {'key': 'value'}
        
        # Act
        result = self.service.process(test_data)
        
        # Assert
        assert result['success'] is True
        assert 'processed' in result
    
    def test_error_handling(self):
        with pytest.raises(ValueError):
            self.service.process(None)
```

#### Teste de Integração
```python
# tests/integration/test_new_routes.py
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_new_endpoint(client):
    # Test GET
    response = client.get('/api/new-endpoint')
    assert response.status_code == 200
    
    # Test POST
    response = client.post('/api/new-endpoint', 
                          json={'test': 'data'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
```

### Executar Testes
```bash
# Todos os testes
pytest -v

# Com coverage
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/unit/test_new_feature.py::TestNewFeature::test_new_functionality

# Skip testes lentos
pytest -m "not slow"
```

## Contribuição

### Git Workflow
```bash
# 1. Criar branch para feature
git checkout -b feature/nova-funcionalidade

# 2. Fazer commits atômicos
git add .
git commit -m "feat: adicionar nova funcionalidade de comando"

# 3. Executar testes antes de push
pytest
npm test

# 4. Push para repositório
git push origin feature/nova-funcionalidade

# 5. Criar Pull Request
```

### Padrões de Commit
```
feat: nova funcionalidade
fix: correção de bug
docs: atualização de documentação
style: formatação de código
refactor: refatoração sem mudança de comportamento
test: adição ou correção de testes
chore: tarefas de manutenção
```

### Code Review Checklist
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Compatibilidade com versão legada
- [ ] Performance considerada
- [ ] Segurança verificada
- [ ] Logs apropriados

## Performance e Monitoramento

### Profiling
```python
# Profile de performance
import cProfile
cProfile.run('your_function()', 'profile_output.prof')

# Análise de memória
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Código a ser analisado
    pass
```

### Monitoramento de Produção
```python
# Métricas customizadas
from core.utils.logger import app_logger

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        app_logger.info(f"Function {func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

---

Este guia fornece uma base sólida para desenvolvimento no Thunder Command. Para informações mais técnicas sobre arquitetura e implementação, consulte `CLAUDE.md` e `docs/arquitetura.md`.