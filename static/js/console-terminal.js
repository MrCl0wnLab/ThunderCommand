/**
 * Thunder Command - Console Terminal
 * Script para gerenciar o terminal de logs no estilo de console Linux
 */

/**
 * Escapa caracteres especiais HTML para evitar XSS
 * @param {string} text - O texto a ser escapado
 * @returns {string} - O texto escapado
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Exibe uma notificação toast estilizada
 * @param {string} message - A mensagem a ser exibida
 * @param {string} type - O tipo de toast (success, error, warning, info)
 * @param {number} duration - A duração em milissegundos
 */
function showNeonToast(message, type = 'info', duration = 3000) {
    // Remover toasts existentes que já tenham desaparecido
    const oldToasts = document.querySelectorAll('.neon-toast[data-disposed="true"]');
    oldToasts.forEach(toast => toast.remove());
    
    // Criar o elemento toast
    const toast = document.createElement('div');
    toast.className = `neon-toast neon-toast-${type}`;
    toast.setAttribute('data-disposed', 'false');
    
    // Ícone baseado no tipo
    let icon;
    switch(type) {
        case 'success': icon = 'fa-check-circle'; break;
        case 'error': icon = 'fa-exclamation-circle'; break;
        case 'warning': icon = 'fa-exclamation-triangle'; break;
        default: icon = 'fa-info-circle'; break;
    }
    
    // Definir o conteúdo
    toast.innerHTML = `
        <div class="neon-toast-content">
            <i class="fas ${icon} neon-toast-icon"></i>
            <span class="neon-toast-message">${escapeHtml(message)}</span>
        </div>
        <div class="neon-toast-progress"></div>
    `;
    
    // Adicionar ao corpo do documento
    document.body.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => {
        toast.classList.add('neon-toast-visible');
    }, 10);
    
    // Animar progresso
    const progress = toast.querySelector('.neon-toast-progress');
    progress.style.transition = `width ${duration}ms linear`;
    setTimeout(() => {
        progress.style.width = '0%';
    }, 10);
    
    // Remover após a duração
    setTimeout(() => {
        toast.classList.remove('neon-toast-visible');
        toast.setAttribute('data-disposed', 'true');
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, duration);
    
    // Retornar o elemento toast caso o chamador queira fazer algo com ele
    return toast;
}

// Funções apenas para o histórico de logs (Terminal Interativo foi removido)

/**
 * Alterna o modo de tela cheia para o console de histórico
 */
function toggleFullscreen() {
    const consoleContainer = document.querySelector('.console-container');
    
    if (consoleContainer.classList.contains('fullscreen')) {
        // Sair do modo de tela cheia
        consoleContainer.classList.remove('fullscreen');
        consoleContainer.style.position = '';
        consoleContainer.style.top = '';
        consoleContainer.style.left = '';
        consoleContainer.style.width = '';
        consoleContainer.style.height = '';
        consoleContainer.style.zIndex = '';
        
        // Mostrar novamente o seletor de clientes
        const clientSelector = document.querySelector('.card.mt-4');
        if (clientSelector) clientSelector.style.display = '';
        
        showNeonToast('Modo tela normal', 'info', 1000);
    } else {
        // Entrar no modo de tela cheia
        consoleContainer.classList.add('fullscreen');
        consoleContainer.style.position = 'fixed';
        consoleContainer.style.top = '10px';
        consoleContainer.style.left = '10px';
        consoleContainer.style.width = 'calc(100% - 20px)';
        consoleContainer.style.height = 'calc(100% - 20px)';
        consoleContainer.style.zIndex = '9999';
        
        // Ocultar o seletor de clientes quando em tela cheia
        const clientSelector = document.querySelector('.card.mt-4');
        if (clientSelector) clientSelector.style.display = 'none';
        
        showNeonToast('Modo tela cheia ativado', 'info', 1000);
    }
    
    // Ajustar a altura do contêiner de saída
    const consoleBody = document.querySelector('.console-body');
    if (consoleContainer.classList.contains('fullscreen')) {
        consoleBody.style.maxHeight = 'calc(100% - 60px)';
    } else {
        consoleBody.style.maxHeight = '500px';
    }
}

/**
 * Atualiza a lista de clientes disponíveis para o console
 */
function refreshClientsForConsole() {
    fetch('/admin/clients')
        .then(response => response.json())
        .then(data => {
            const dropdown = document.getElementById('console-target-client');
            
            // Manter opção padrão
            const defaultOption = dropdown.options[0];
            dropdown.innerHTML = '';
            dropdown.appendChild(defaultOption);
            
            // Adicionar clientes online
            if (data.clients && data.clients.length > 0) {
                // Filtrar apenas clientes ativos
                const onlineClients = data.clients.filter(client => client.active);
                
                // All clients use polling - no sorting needed
                
                // Adicionar ao dropdown
                onlineClients.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.id;
                    
                    const connection = '🔄'; // All clients use polling
                    option.textContent = `Cliente: ${client.id.substring(0, 8)}... ${connection}`;
                    
                    dropdown.appendChild(option);
                });
                
                showNeonToast(`${onlineClients.length} clientes disponíveis`, 'success', 2000);
            } else {
                showNeonToast('Nenhum cliente online encontrado', 'warning', 2000);
            }
        })
        .catch(error => {
            console.error('Erro ao atualizar lista de clientes para console:', error);
            showNeonToast('Erro ao carregar clientes', 'error', 2000);
        });
}

/**
 * Executa um comando diretamente
 * @param {string} command - Comando a ser executado
 */
function copyToConsole(command) {
    // Obter o cliente alvo
    const clientId = document.getElementById('console-target-client').value;
    
    // Enviar comando ao servidor
    fetch('/admin/set_command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            type: 'js',
            client_id: clientId,
            content: command
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNeonToast(`Comando executado com sucesso (ID: ${data.command.id.substring(0, 8)})`, 'success', 2000);
            // Atualizar o histórico de comandos
            refreshLogs();
        } else {
            throw new Error(data.error || "Erro não especificado");
        }
    })
    .catch(error => {
        showNeonToast(`Erro ao executar comando: ${error.message}`, 'error', 3000);
    });
}

/**
 * Copia um texto para a área de transferência
 * @param {string} text - Texto a ser copiado
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showNeonToast('Comando copiado para a área de transferência', 'success', 1500);
        })
        .catch(err => {
            console.error('Erro ao copiar texto: ', err);
            showNeonToast('Erro ao copiar comando', 'error', 1500);
        });
}

/**
 * Atualiza a exibição de logs na aba de histórico
 */
function refreshLogs() {
    const logsList = document.getElementById('logs-list');
    logsList.innerHTML = '<p class="text-center p-4"><i class="fas fa-circle-notch fa-spin me-2"></i> Carregando logs...</p>';
    
    fetch('/admin/logs')
        .then(response => response.json())
        .then(data => {
            if (data.logs && data.logs.length > 0) {
                // Ordenar logs do mais recente para o mais antigo
                data.logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                
                const logsHtml = data.logs.map((log, index) => {
                    // Formatação da data e hora
                    const date = new Date(log.timestamp);
                    const timeStr = date.toTimeString().split(' ')[0];
                    const dateStr = date.toLocaleDateString();
                    
                    // Ícone com base no tipo de comando
                    let typeIcon;
                    switch(log.type) {
                        case 'js': typeIcon = 'fa-code'; break;
                        case 'html': typeIcon = 'fa-file-code'; break;
                        case 'manipulate': typeIcon = 'fa-edit'; break;
                        case 'visibility': typeIcon = 'fa-eye-slash'; break;
                        case 'head': typeIcon = 'fa-heading'; break;
                        default: typeIcon = 'fa-terminal'; break;
                    }
                    
                    // Gerar conteúdo da aba de comando
                    const commandContent = `
                        <div class="command-display">
                            <pre class="command-code"><code>${escapeHtml(log.command)}</code></pre>
                            <div class="command-actions mt-2">
                                <button class="console-button primary" onclick="copyToConsole('${escapeHtml(log.command.replace(/'/g, "\\'"))}')">
                                    <i class="fas fa-play me-1"></i> Executar
                                </button>
                                <button class="console-button" onclick="copyToClipboard('${escapeHtml(log.command.replace(/'/g, "\\'"))}')">
                                    <i class="fas fa-copy me-1"></i> Copiar
                                </button>
                            </div>
                        </div>
                    `;
                    
                    // Gerar conteúdo da aba de resultado
                    let resultContent;
                    if (log.has_results && log.results && log.results.length > 0) {
                        const resultsHtml = log.results.map(result => {
                            const resultDate = result.timestamp ? new Date(result.timestamp) : null;
                            const resultTimeStr = resultDate ? resultDate.toTimeString().split(' ')[0] : 'N/A';
                            
                            return `
                                <div class="result-item ${result.success ? 'success' : 'error'}">
                                    <div class="result-header">
                                        <span class="result-status">
                                            <i class="fas ${result.success ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
                                            ${result.success ? 'Sucesso' : 'Erro'}
                                        </span>
                                        <span class="result-time">
                                            <i class="fas fa-clock me-1"></i>${resultTimeStr}
                                        </span>
                                        ${result.execution_time ? `<span class="execution-time"><i class="fas fa-stopwatch me-1"></i>${result.execution_time}ms</span>` : ''}
                                    </div>
                                    <div class="result-content">
                                        <code class="${result.success ? 'result-success' : 'result-error'}">
                                            ${escapeHtml(result.result || (result.success ? 'undefined' : 'Erro desconhecido'))}
                                        </code>
                                    </div>
                                </div>
                            `;
                        }).join('');
                        
                        resultContent = `
                            <div class="results-display">
                                <div class="results-summary">
                                    <span class="total-results">${log.total_results} execução(ões)</span>
                                    ${log.success_count > 0 ? `<span class="success-count"><i class="fas fa-check"></i> ${log.success_count}</span>` : ''}
                                    ${log.error_count > 0 ? `<span class="error-count"><i class="fas fa-times"></i> ${log.error_count}</span>` : ''}
                                </div>
                                <div class="results-list">
                                    ${resultsHtml}
                                </div>
                            </div>
                        `;
                    } else {
                        resultContent = `
                            <div class="no-result">
                                <div class="no-result-content">
                                    <i class="fas fa-hourglass-half text-muted me-2"></i>
                                    <span class="text-muted">Aguardando resultado da execução...</span>
                                </div>
                                <small class="text-muted">
                                    O resultado aparecerá aqui quando o comando for executado no cliente.
                                </small>
                            </div>
                        `;
                    }
                    
                    // Determinar status do resultado para a badge
                    let resultBadge = '';
                    if (log.overall_status === 'success') {
                        resultBadge = '<span class="result-status-badge success"><i class="fas fa-check"></i></span>';
                    } else if (log.overall_status === 'error') {
                        resultBadge = '<span class="result-status-badge error"><i class="fas fa-times"></i></span>';
                    } else if (log.overall_status === 'pending') {
                        resultBadge = '<span class="result-status-badge pending"><i class="fas fa-clock"></i></span>';
                    } else {
                        resultBadge = '<span class="result-status-badge no-response"><i class="fas fa-minus"></i></span>';
                    }
                    
                    return `
                    <div class="console-history-entry">
                        <div class="console-history-header">
                            <div class="console-history-timestamp">
                                <i class="fas fa-calendar-alt me-1"></i> ${dateStr}
                                <i class="fas fa-clock ms-3 me-1"></i> ${timeStr}
                                <span class="console-history-type ${log.type}">
                                    <i class="fas ${typeIcon} me-1"></i>${log.type}
                                </span>
                            </div>
                            <div class="console-history-client">
                                <i class="fas fa-user me-1"></i> Cliente: ${log.client_id}
                            </div>
                        </div>
                        
                        <div class="log-entry-tabs" id="log-${index}">
                            <div class="simple-tabs-nav">
                                <button class="simple-tab-btn active" data-tab="command" onclick="switchTab('log-${index}', 'command')">
                                    <i class="fas fa-code me-1"></i>Comando
                                </button>
                                <button class="simple-tab-btn" data-tab="result" onclick="switchTab('log-${index}', 'result')">
                                    <i class="fas fa-play-circle me-1"></i>Resultado
                                    ${resultBadge}
                                    ${log.total_results > 1 ? `<span class="result-count-badge">${log.total_results}</span>` : ''}
                                </button>
                            </div>
                            
                            <div class="simple-tabs-content">
                                <div class="simple-tab-panel active" data-panel="command">
                                    ${commandContent}
                                </div>
                                <div class="simple-tab-panel" data-panel="result">
                                    ${resultContent}
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('');
                
                logsList.innerHTML = logsHtml;
            } else {
                logsList.innerHTML = `
                    <div class="console-output p-4 text-center"><i class="fas fa-info-circle me-2"></i><span>Nenhum histórico de comando encontrado.</span></div>
                `;
            }
        })
        .catch(error => {
            logsList.innerHTML = `
                <div class="console-output error p-4">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <span>Erro ao carregar logs: ${escapeHtml(error.message || 'Erro desconhecido')}</span>
                </div>
            `;
        });
}

/**
 * Alterna entre abas em um sistema de abas específico
 * @param {string} containerId - ID do contêiner das abas
 * @param {string} tabName - Nome da aba a ser ativada
 */
function switchTab(containerId, tabName) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Remove active class from all tab buttons
    const tabButtons = container.querySelectorAll('.simple-tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Remove active class from all tab panels
    const tabPanels = container.querySelectorAll('.simple-tab-panel');
    tabPanels.forEach(panel => panel.classList.remove('active'));
    
    // Activate the selected tab button
    const selectedButton = container.querySelector(`[data-tab="${tabName}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Activate the selected tab panel
    const selectedPanel = container.querySelector(`[data-panel="${tabName}"]`);
    if (selectedPanel) {
        selectedPanel.classList.add('active');
    }
}

// Inicialização do histórico de logs quando a página é acessada
document.addEventListener('DOMContentLoaded', function() {
    // Se já estivermos na página de logs, inicializar
    if (document.getElementById('logs-page').classList.contains('active')) {
        refreshClientsForConsole();
    }
});
