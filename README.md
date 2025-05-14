# Olho de Tandera: Sistema de Controle Remoto para Páginas Web

Este projeto implementa um sistema de comunicação bidirecional entre servidor e cliente, permitindo que um administrador execute comandos JavaScript remotamente em páginas web em tempo real, sem necessidade de atualização da página.

## Funcionalidades

O sistema permite que um administrador:

- **Comunique em tempo real via WebSockets** com clientes conectados
- **Execute código JavaScript** em tempo real em páginas cliente
- **Inserir conteúdo HTML** diretamente no corpo das páginas
- **Manipule elementos específicos** por ID (adicionar, substituir, inserir conteúdo)
- **Controle a visibilidade** de elementos nas páginas cliente
- **Modifique o cabeçalho da página** (adicionar CSS, JavaScript, meta tags)
- **Envie comandos** para todos os clientes ou para um cliente específico
- **Monitore** os clientes conectados e o histórico de comandos

## Arquitetura do Sistema

O sistema funciona primariamente com WebSockets, com fallback para polling:

```
+-------------+        +-------------+        +----------------+
| Painel Admin| <----> | Servidor    | <----> | Páginas Cliente|
| (admin.html)| WebSkt | (Flask      | WebSkt | (JavaScript)   |
+-------------+ ou HTTP| SocketIO)   | ou HTTP+----------------+
```

## Estrutura do Projeto

```
Olho-de-Tandera/
├── app.py                  # Servidor Flask, Socket.IO e lógica de backend
├── requirements.txt        # Dependências do projeto
├── static/
│   ├── favicon.ico         # Ícone do site para o servidor estático
│   ├── css/
│   │   ├── style.css       # Estilos CSS para interfaces
│   │   └── admin-panel.css # Estilos específicos para o painel admin
│   └── js/
│       ├── cmd.js          # Cliente JavaScript com WebSockets e fallback
│       ├── cmd.js.bak      # Backup da versão anterior
│       └── socket.io.min.js # Biblioteca cliente de Socket.IO
└── templates/
    ├── admin.html          # Painel de administração para enviar comandos
    ├── login.html          # Página de autenticação para o painel admin
    └── server_to_client.html # Página cliente que recebe comandos
```

## Instalação e Configuração

### Pré-requisitos

- Python 3.6+
- pip (gerenciador de pacotes do Python)

### Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

4. Execute o servidor Flask:

```bash
python app.py
```

5. Acesse as páginas no navegador:
   - Cliente: http://localhost:5000/
   - Administração: http://localhost:5000/admin (credenciais padrão: tandera/tandera)

## Como Usar

### Painel de Administração

O painel de administração oferece várias opções para enviar comandos:

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

### Clientes Conectados

- O painel exibe todos os clientes ativos
- O ícone ⚡ indica conexões via WebSockets
- Cada cliente possui um ID único persistente (armazenado no localStorage do navegador)
- Clientes inativos por mais de 30 minutos são marcados como offline
- Comandos podem ser direcionados a clientes específicos ou para todos

### Histórico de Logs

- O sistema mantém o histórico dos últimos 100 comandos enviados
- Para cada comando, são registrados: data/hora, tipo, conteúdo e cliente-alvo

## Integrando em Outros Projetos

Para integrar o sistema em páginas existentes, basta incluir o script cliente:

```html
<!-- Adicionar antes do fechamento do </body> -->
<div id="status"></div>
<script src="http://seu-servidor:5000/js/cmd.js"></script>
```

## Segurança

**Atenção**: Este sistema foi projetado para ambientes controlados e possui aspectos que devem ser considerados:

- O sistema permite a execução de código JavaScript arbitrário
- Em produção, sempre use HTTPS para evitar interceptação de comandos
- Configure o sistema para verificar a origem das requisições (CORS)
- Configure permissões para conexões Socket.IO
- Use sempre credenciais seguras para o painel administrativo
- Considere implementar validação avançada para os comandos
- Não use em ambientes públicos sem medidas de segurança adicionais

## Funcionamento Técnico

### Backend (Flask + Socket.IO)

- Comunicação em tempo real via WebSockets usando Socket.IO
- Fallback automático para HTTP polling quando WebSockets não disponível
- O servidor armazena comandos em memória para cada cliente
- Fornece APIs para envio e recuperação de comandos

### Frontend (JavaScript)

- Tenta estabelecer conexão WebSocket como método preferencial
- Implementa fallback automático para polling HTTP
- Suporta arquivos locais através de JSONP
- Implementa reconexão automática com backoff exponencial

## Casos de Uso

- Coleta informacional de dados em tempo real
- Modificação de páginas em tempo real
- Notificações em tempo real para usuários
- Correção de bugs em páginas em produção sem necessidade de redeploy
- Testes A/B dinâmicos
- Adaptação da interface baseada em eventos do servidor
- Mensagens de manutenção temporárias
- Chat e sistemas interativos em tempo real

## Desenvolvimento

### Estrutura do código

- **app.py**: Backend Flask com endpoints e lógica principal
- **cmd.js**: Cliente JavaScript que busca e executa comandos
- **admin.html**: Interface do painel administrativo