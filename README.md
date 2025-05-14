# Olho de Tandera: Sistema de Controle Remoto para Páginas Web

Este projeto implementa um sistema de comunicação unidirecional de servidor para cliente, permitindo que um administrador execute comandos JavaScript remotamente em páginas web em tempo real, sem necessidade de atualização da página.

## Funcionalidades

O sistema permite que um administrador:

- **Execute código JavaScript** em tempo real em páginas cliente
- **Inserir conteúdo HTML** diretamente no corpo das páginas
- **Manipule elementos específicos** por ID (adicionar, substituir, inserir conteúdo)
- **Controle a visibilidade** de elementos nas páginas cliente
- **Modifique o cabeçalho da página** (adicionar CSS, JavaScript, meta tags)
- **Envie comandos** para todos os clientes ou para um cliente específico
- **Monitore** os clientes conectados e o histórico de comandos

## Arquitetura do Sistema

O sistema funciona através de polling, onde cada cliente verifica periodicamente se há novos comandos a serem executados:

```
+-------------+        +-------------+        +----------------+
| Painel Admin| -----> | Servidor    | <----- | Páginas Cliente|
| (admin.html)| envia  | (Flask)     | polling| (JavaScript)   |
+-------------+ comando+-------------+ comando+----------------+
```

## Estrutura do Projeto

```
projeto_push/
├── app.py                  # Servidor Flask e lógica de backend
├── favicon.ico             # Ícone do site
├── requirements.txt        # Dependências do projeto
├── static/
│   ├── favicon.ico         # Ícone do site para o servidor estático
│   ├── css/
│   │   └── style.css       # Estilos CSS para interfaces
│   └── js/
│       ├── cmd.js          # Cliente JavaScript de notificações push
│       └── old_cmd.js      # Versão anterior (para referência)
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
- Use sempre credenciais seguras para o painel administrativo
- Considere implementar validação avançada para os comandos
- Não use em ambientes públicos sem medidas de segurança adicionais

## Funcionamento Técnico

### Backend (Flask)

- O servidor armazena comandos em memória para cada cliente
- Implementa autenticação básica para o painel administrativo
- Fornece APIs para envio e recuperação de comandos
- Suporta JSONP para casos de uso em arquivos locais

### Frontend (JavaScript)

- O cliente verifica periodicamente novos comandos (polling a cada 5 segundos)
- Executa comandos usando construtor `Function` para avaliar JavaScript
- Implementa reconexão automática com backoff exponencial
- Suporta arquivos locais através de JSONP

## Casos de Uso

- Coleta informacional de dados em tempo real
- Modificação de pagina em tempo real
- Notificações em tempo real para usuários
- Correção de bugs em páginas em produção sem necessidade de redeploy
- Testes A/B dinâmicos
- Adaptação da interface baseada em eventos do servidor
- Mensagens de manutenção temporárias

## Desenvolvimento

### Estrutura do código

- **app.py**: Backend Flask com endpoints e lógica principal
- **cmd.js**: Cliente JavaScript que busca e executa comandos
- **admin.html**: Interface do painel administrativo