# 📑 Documentação Thunder Command v2.2+

<h1 align="center">
  <img src="../static/img/logo.png"   width="200">
</h1>

## 📚 Índice da Documentação

### 👤 **Para Usuários**

#### 📖 **[Guia do Painel de Controle](./Introdução-Painel-de-Controle.md)**
> **Atualizado v2.0.1** - Guia completo do painel administrativo, incluindo a **correção crítica do bug de injeção HTML**. Explica como controlar remotamente páginas web em tempo real, integração via script `cmd.js`, e as cinco funcionalidades principais: execução de JavaScript, injeção de HTML (corrigida), manipulação DOM, controle de visibilidade e modificação do head. Inclui exemplos práticos, sistema de logs (100 comandos) e solução de problemas atualizados.

### 🛠️ **Para Desenvolvedores**

#### 🏗️ **[Arquitetura do Sistema](./arquitetura.md)**
> Documentação técnica completa da **arquitetura simplificada v2.2**. Explica o sistema unificado (`app.py`), fluxo de comunicação HTTP polling, sistema de repositórios SQLite, estrutura HTMX + Bootstrap, e configuração simplificada. Essencial para entender o design interno do sistema.

#### 💻 **[Guia de Desenvolvimento](./desenvolvimento.md)**
> Manual prático para desenvolvedores contribuindo com o projeto. Inclui setup do ambiente, estrutura de código simplificada, comandos de desenvolvimento (Python + npm), padrões para adicionar novas funcionalidades, debugging, testes (pytest), Git workflow, e monitoramento de performance. Complementa o `CLAUDE.md` com instruções hands-on.

### 📋 **Documentação Complementar**

#### 📝 **[CLAUDE.md](../CLAUDE.md)**
> Guia técnico para instâncias futuras do Claude Code trabalhando neste repositório. Contém comandos essenciais, arquitetura de alto nível, bug fixes críticos, e padrões de implementação.

#### 📄 **[README Principal](../README.md)**
> Documentação geral do projeto com instalação, funcionalidades, changelog v2.0.1, e casos de uso.

---

## 🆕 **Novidades v2.2.0**

### 🔥 **Simplificação Arquitetural**
- **Arquitetura unificada**: Consolidação completa em `app.py` único
- **Remoção da complexidade**: Eliminados `run.py`, diretório `app/`, diretório `config/`
- **Deploy simplificado**: Apenas `python app.py` para todos os ambientes
- **Manutenção facilitada**: Código mais direto e fácil de compreender
- **Funcionalidades preservadas**: Todas as features mantidas intactas

### ✅ **Histórico - v2.1.0: Limpeza WebSocket/Socket.IO**
- **Remoção total**: Eliminados todos os vestígios de Socket.IO/WebSocket do código
- **Endpoints removidos**: `/socket.io/` routes completamente removidos
- **Database cleanup**: Tabela `socket_clients` removida do schema
- **Interface 100% polling**: CSS, JavaScript e templates atualizados
- **Logging simplificado**: `websocket.log` e funções relacionadas removidas

### ✅ **Correção Crítica v2.0.1 - Injeção HTML**
- **Problema**: Comandos "Inject HTML" mostravam código JavaScript visível
- **Solução**: Cliente agora executa JavaScript corretamente para comandos HTML
- **Impacto**: Interface mais limpa e funcionamento adequado

### 🏗️ **Arquitetura Simplificada**
- **Deploy unificado**: Sistema principal (`app.py`) único
- **Frontend modular**: npm + webpack + HTMX + Bootstrap 5.3.0
- **Testes**: Framework pytest implementado
- **HTTP Polling**: Exclusivo, sistema puramente polling

---

## 🎯 **Por Onde Começar**

### **Sou usuário novo**
1. 📖 Leia o **[Guia do Painel de Controle](./Introdução-Painel-de-Controle.md)**
2. 📄 Consulte o **[README principal](../README.md)** para instalação

### **Quero desenvolver/contribuir**
1. 🏗️ Entenda a **[Arquitetura do Sistema](./arquitetura.md)**
2. 💻 Siga o **[Guia de Desenvolvimento](./desenvolvimento.md)**
3. 📝 Consulte **[CLAUDE.md](../CLAUDE.md)** para contexto técnico

### **Tenho problemas**
1. 📖 Seção "Solução de Problemas" no **[Guia do Painel](./Introdução-Painel-de-Controle.md)**
2. 🏗️ "Troubleshooting Arquitetural" em **[Arquitetura](./arquitetura.md)**
3. 💻 "Debugging e Troubleshooting" no **[Guia de Desenvolvimento](./desenvolvimento.md)**

---

## 🔍 **Busca Rápida**

| Procurando por... | Documento | Seção |
|-------------------|-----------|-------|
| Como usar comando HTML | [Painel de Controle](./Introdução-Painel-de-Controle.md) | 2.2. HTML |
| Correção bug HTML | [Painel de Controle](./Introdução-Painel-de-Controle.md) | Solução de Problemas |
| Execução do servidor | [Arquitetura](./arquitetura.md) | Execução do Servidor |
| Adicionar novo comando | [Desenvolvimento](./desenvolvimento.md) | 1. Novo Tipo de Comando |
| Comandos npm/pytest | [Desenvolvimento](./desenvolvimento.md) | Comandos de Desenvolvimento |
| Estrutura de pastas | [Arquitetura](./arquitetura.md) | Componentes Principais |
| Como contribuir | [Desenvolvimento](./desenvolvimento.md) | Contribuição |

---

**⚠️ Nota de Segurança**: Este é um sistema de execução remota de JavaScript para fins educacionais e pesquisa de segurança. Use apenas em ambientes controlados.
