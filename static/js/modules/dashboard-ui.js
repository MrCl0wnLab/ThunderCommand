/**
 * UI do dashboard para ThunderCommand
 */
export class DashboardUI {
    constructor() {
        // Elementos de UI
        this.clientTableBody = document.getElementById('clients-table-body');
        this.clientCards = document.getElementById('client-cards');
        this.selectedClientInfo = document.getElementById('selected-client-info');
        this.commandForm = document.getElementById('command-form');
        this.commandTypeSelect = document.getElementById('command-type');
        this.commandContentArea = document.getElementById('command-content');
        this.commandHistoryList = document.getElementById('command-history');
        
        // Estatísticas
        this.totalClientsCounter = document.getElementById('total-clients');
        this.activeClientsCounter = document.getElementById('active-clients');
        this.commandsCounter = document.getElementById('total-commands');
    }
    
    /**
     * Inicializa a UI e registra event listeners
     */
    init() {
        this.setupEventListeners();
        this.setupCommandForm();
    }
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Atualização de clientes
        document.addEventListener('clients:updated', (event) => {
            this.updateClientTable(event.detail.clients);
            this.updateClientCards(event.detail.clients);
            this.updateStatistics(event.detail.clients);
        });
        
        // Seleção de cliente
        document.addEventListener('client:selected', (event) => {
            this.updateSelectedClient(event.detail.client);
        });
        
        // Histórico de comandos
        document.addEventListener('command:executed', (event) => {
            this.updateCommandHistory(event.detail.command, event.detail.result);
        });
    }
    
    /**
     * Configura o formulário de comandos
     */
    setupCommandForm() {
        if (!this.commandForm) return;
        
        this.commandForm.addEventListener('submit', (event) => {
            event.preventDefault();
            
            const clientId = document.querySelector('.client-card.selected')?.dataset.clientId;
            if (!clientId) {
                this.showNotification('Selecione um cliente primeiro', 'error');
                return;
            }
            
            const commandType = this.commandTypeSelect.value;
            const commandContent = this.commandContentArea.value;
            
            if (!commandContent.trim()) {
                this.showNotification('O conteúdo do comando não pode estar vazio', 'error');
                return;
            }
            
            // Disparar evento para enviar comando
            const commandEvent = new CustomEvent('command:send', {
                detail: {
                    clientId,
                    type: commandType,
                    content: commandContent
                }
            });
            
            document.dispatchEvent(commandEvent);
            
            // Limpar formulário
            this.commandContentArea.value = '';
        });
        
        // Atualizar área de código conforme tipo de comando
        this.commandTypeSelect.addEventListener('change', () => {
            const commandType = this.commandTypeSelect.value;
            this.updateCommandInputPlaceholder(commandType);
        });
    }
    
    /**
     * Atualiza placeholder da área de código baseado no tipo de comando
     */
    updateCommandInputPlaceholder(commandType) {
        const placeholders = {
            'js': 'console.log("Olá Mundo!");',
            'html': '<div class="custom-element">Conteúdo HTML</div>',
            'manipulate': 'Selecione esta opção e use os controles de manipulação',
            'visibility': 'Selecione esta opção e use os controles de visibilidade',
            'head': '<script>console.log("Script no cabeçalho");</script>'
        };
        
        this.commandContentArea.placeholder = placeholders[commandType] || '';
    }
    
    /**
     * Atualiza tabela de clientes
     */
    updateClientTable(clients) {
        if (!this.clientTableBody) return;
        
        // Limpar tabela
        this.clientTableBody.innerHTML = '';
        
        if (clients.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">Nenhum cliente conectado</td>';
            this.clientTableBody.appendChild(row);
            return;
        }
        
        // Adicionar cada cliente
        clients.forEach(client => {
            const row = document.createElement('tr');
            row.dataset.clientId = client.id;
            row.classList.add('client-row');
            
            // Formatar data
            const lastSeen = new Date(client.last_seen);
            const timeAgo = this.getTimeAgo(lastSeen);
            
            // Extrair informações do navegador
            const browserInfo = this.parseBrowserInfo(client.user_agent);
            
            row.innerHTML = `
                <td>${client.id.substring(0, 8)}...</td>
                <td>
                    <span class="browser-icon ${browserInfo.icon}"></span>
                    ${browserInfo.browser} ${browserInfo.version}
                </td>
                <td>${client.ip_address}</td>
                <td>${timeAgo}</td>
                <td>
                    <button class="btn btn-sm btn-primary select-client">Selecionar</button>
                </td>
            `;
            
            // Adicionar evento ao botão
            row.querySelector('.select-client').addEventListener('click', () => {
                // Disparar evento de seleção de cliente
                const event = new CustomEvent('client:select', {
                    detail: { clientId: client.id }
                });
                document.dispatchEvent(event);
                
                // Atualizar visuais
                document.querySelectorAll('.client-row').forEach(r => {
                    r.classList.remove('selected');
                });
                row.classList.add('selected');
            });
            
            this.clientTableBody.appendChild(row);
        });
    }
    
    /**
     * Atualiza cards de clientes
     */
    updateClientCards(clients) {
        if (!this.clientCards) return;
        
        // Limpar cards
        this.clientCards.innerHTML = '';
        
        if (clients.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.classList.add('col-12', 'text-center', 'p-4');
            emptyMessage.textContent = 'Nenhum cliente conectado';
            this.clientCards.appendChild(emptyMessage);
            return;
        }
        
        // Adicionar cada cliente
        clients.forEach(client => {
            const card = document.createElement('div');
            card.classList.add('col-md-4', 'mb-3');
            
            // Extrair informações do navegador
            const browserInfo = this.parseBrowserInfo(client.user_agent);
            
            // Formatar data
            const lastSeen = new Date(client.last_seen);
            const timeAgo = this.getTimeAgo(lastSeen);
            
            card.innerHTML = `
                <div class="card client-card" data-client-id="${client.id}">
                    <div class="card-header">
                        <span class="browser-icon ${browserInfo.icon}"></span>
                        ${browserInfo.browser} ${browserInfo.version}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">ID: ${client.id.substring(0, 8)}...</h5>
                        <p class="card-text">IP: ${client.ip_address}</p>
                        <p class="card-text">Visto: ${timeAgo}</p>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-sm btn-primary select-client-card">Selecionar</button>
                    </div>
                </div>
            `;
            
            // Adicionar evento ao botão
            card.querySelector('.select-client-card').addEventListener('click', () => {
                // Disparar evento de seleção de cliente
                const event = new CustomEvent('client:select', {
                    detail: { clientId: client.id }
                });
                document.dispatchEvent(event);
                
                // Atualizar visuais
                document.querySelectorAll('.client-card').forEach(c => {
                    c.classList.remove('selected');
                });
                card.querySelector('.client-card').classList.add('selected');
            });
            
            this.clientCards.appendChild(card);
        });
    }
    
    /**
     * Atualiza informações do cliente selecionado
     */
    updateSelectedClient(client) {
        if (!this.selectedClientInfo || !client) return;
        
        // Extrair informações do navegador
        const browserInfo = this.parseBrowserInfo(client.user_agent);
        
        // Formatar data
        const lastSeen = new Date(client.last_seen);
        const formattedDate = lastSeen.toLocaleString();
        
        this.selectedClientInfo.innerHTML = `
            <div class="alert alert-info">
                <h4>Cliente Selecionado</h4>
                <p><strong>ID:</strong> ${client.id}</p>
                <p><strong>Navegador:</strong> ${browserInfo.browser} ${browserInfo.version}</p>
                <p><strong>Sistema:</strong> ${browserInfo.os}</p>
                <p><strong>IP:</strong> ${client.ip_address}</p>
                <p><strong>Última Atividade:</strong> ${formattedDate}</p>
            </div>
        `;
    }
    
    /**
     * Atualiza histórico de comandos
     */
    updateCommandHistory(command, result) {
        if (!this.commandHistoryList) return;
        
        const item = document.createElement('li');
        item.classList.add('list-group-item', result.success ? 'list-group-item-success' : 'list-group-item-danger');
        
        const timestamp = new Date().toLocaleTimeString();
        
        item.innerHTML = `
            <div>
                <strong>${timestamp} - ${command.type.toUpperCase()}</strong>
                <span class="badge ${result.success ? 'bg-success' : 'bg-danger'} float-end">
                    ${result.success ? 'Sucesso' : 'Erro'}
                </span>
            </div>
            <div class="mt-2">
                <small class="text-muted">Cliente: ${command.client_id.substring(0, 8)}...</small>
            </div>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-secondary show-details">Ver Detalhes</button>
            </div>
            <div class="command-details mt-2" style="display: none;">
                <div class="card">
                    <div class="card-header">Comando</div>
                    <div class="card-body">
                        <pre>${this.escapeHtml(command.content)}</pre>
                    </div>
                </div>
                <div class="card mt-2">
                    <div class="card-header">Resultado</div>
                    <div class="card-body">
                        <pre>${this.escapeHtml(JSON.stringify(result, null, 2))}</pre>
                    </div>
                </div>
            </div>
        `;
        
        // Adicionar evento para mostrar/esconder detalhes
        item.querySelector('.show-details').addEventListener('click', (e) => {
            const details = item.querySelector('.command-details');
            if (details.style.display === 'none') {
                details.style.display = 'block';
                e.target.textContent = 'Esconder Detalhes';
            } else {
                details.style.display = 'none';
                e.target.textContent = 'Ver Detalhes';
            }
        });
        
        // Adicionar ao topo da lista
        if (this.commandHistoryList.firstChild) {
            this.commandHistoryList.insertBefore(item, this.commandHistoryList.firstChild);
        } else {
            this.commandHistoryList.appendChild(item);
        }
        
        // Limitar tamanho da lista
        if (this.commandHistoryList.children.length > 50) {
            this.commandHistoryList.removeChild(this.commandHistoryList.lastChild);
        }
    }
    
    /**
     * Atualiza estatísticas do dashboard
     */
    updateStatistics(clients) {
        if (this.totalClientsCounter) {
            this.totalClientsCounter.textContent = clients.length;
        }
        
        if (this.activeClientsCounter) {
            // Clientes ativos nas últimas 5 minutos
            const fiveMinutesAgo = new Date();
            fiveMinutesAgo.setMinutes(fiveMinutesAgo.getMinutes() - 5);
            
            const activeCount = clients.filter(client => {
                return new Date(client.last_seen) >= fiveMinutesAgo;
            }).length;
            
            this.activeClientsCounter.textContent = activeCount;
        }
    }
    
    /**
     * Exibe notificação na interface
     */
    showNotification(message, type = 'info') {
        // Criar elemento de notificação
        const notification = document.createElement('div');
        notification.classList.add('alert', `alert-${type}`, 'notification');
        notification.textContent = message;
        
        // Adicionar ao corpo
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remover após timeout
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
    
    /**
     * Extrai informações do navegador a partir do user agent
     */
    parseBrowserInfo(userAgent) {
        // Implementação simplificada
        let browser = 'Unknown';
        let version = '';
        let os = 'Unknown';
        let icon = 'browser-default';
        
        // Detecção de navegador
        if (userAgent.includes('Firefox')) {
            browser = 'Firefox';
            icon = 'browser-firefox';
        } else if (userAgent.includes('Chrome')) {
            browser = 'Chrome';
            icon = 'browser-chrome';
        } else if (userAgent.includes('Safari')) {
            browser = 'Safari';
            icon = 'browser-safari';
        } else if (userAgent.includes('Edge')) {
            browser = 'Edge';
            icon = 'browser-edge';
        } else if (userAgent.includes('MSIE') || userAgent.includes('Trident/')) {
            browser = 'Internet Explorer';
            icon = 'browser-ie';
        }
        
        // Detecção de sistema operacional
        if (userAgent.includes('Windows')) {
            os = 'Windows';
        } else if (userAgent.includes('Mac OS')) {
            os = 'macOS';
        } else if (userAgent.includes('Linux')) {
            os = 'Linux';
        } else if (userAgent.includes('Android')) {
            os = 'Android';
        } else if (userAgent.includes('iOS')) {
            os = 'iOS';
        }
        
        return { browser, version, os, icon };
    }
    
    /**
     * Calcula tempo relativo
     */
    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        
        if (diffSec < 60) return 'agora mesmo';
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)} minutos atrás`;
        if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} horas atrás`;
        return `${Math.floor(diffSec / 86400)} dias atrás`;
    }
    
    /**
     * Escapa HTML para exibição segura
     */
    escapeHtml(text) {
        if (typeof text !== 'string') {
            text = JSON.stringify(text);
        }
        
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}
