/**
 * Cliente de Push Notification e Controle Remoto
 * =============================================
 * 
 * Este módulo implementa um cliente para recebimento de comandos JavaScript remotos,
 * permitindo a execução de comandos enviados por um servidor central. O sistema suporta:
 * 
 * - Arquivos locais (via JSONP para contornar restrições de CORS)
 * - Páginas servidas por servidor (via fetch API)
 * - Reconexão automática com estratégia de backoff exponencial
 * - Gestão de estado de conexão e feedback visual
 * - Identificação persistente de clientes via localStorage
 * 
 * Autor: Administrador do Projeto
 * Versão: 1.0
 * Última atualização: Maio/2025
 */

// Módulo principal usando padrão IIFE (Immediately Invoked Function Expression) para encapsulamento
const PushClient = (function() {
    // Variáveis privadas do módulo
    let lastCommandId = '';            // ID do último comando executado
    let serverOrigin = '';             // Origem do servidor (protocolo + hostname + porta)
    let commandEndpoint = '';          // URL completa do endpoint de comandos
    let pollInterval = 5000;           // Intervalo de verificação de comandos (5 segundos)
    let retryCount = 0;                // Contador de tentativas de reconexão
    let maxRetry = 5;                  // Máximo de tentativas antes de desistir
    let isLocalFile = false;           // Flag para detectar se estamos em arquivo local
    let clientId = '';                 // ID único do cliente
    let connectionStatus = 'disconnected'; // Estado atual da conexão
    
    // Cache para elementos DOM frequentemente acessados
    let statusElement = null;          // Elemento para exibir status da conexão
    
    /**
     * Gera UUID v4 compatível com diferentes navegadores
     * Implementação de fallback para navegadores que não suportam crypto.randomUUID()
     */
    function generateUUID() {
        // Verifica se randomUUID está disponível
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        
        // Fallback para navegadores mais antigos
        // Baseado em: https://stackoverflow.com/a/2117523
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    /**
     * Inicializa o cliente de push notification
     * Configura origens, gera/recupera ID de cliente e define listeners
     */
    function init() {
        console.log('Iniciando cliente de push notification');
        
        // Determina a origem do servidor baseado no script atual
        serverOrigin = new URL(document.currentScript.src).origin;
        isLocalFile = (window.location.protocol === 'file:');
        commandEndpoint = `${serverOrigin}/command`;

        console.log('Server origin:', serverOrigin);
        console.log('Command endpoint:', commandEndpoint);
        console.log('Is local file:', isLocalFile);
        
        // Gerar ID único para o cliente ou recuperar um existente
        clientId = localStorage.getItem('clientId');
        if (!clientId) {
            clientId = generateUUID();
            localStorage.setItem('clientId', clientId);
        }
        
        console.log('Client ID:', clientId);
        
        // Iniciar quando o DOM estiver completamente carregado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', onDOMReady);
        } else {
            onDOMReady();
        }
        
        // Detectar mudanças no estado da conexão
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
    }
    
    /**
     * Callback executado quando o DOM está pronto
     * Inicializa elementos visuais e inicia a conexão
     */
    function onDOMReady() {
        statusElement = document.getElementById('status');
        updateConnectionStatus('connecting');
        connect();
    }
    
    /**
     * Inicia a conexão e o polling de comandos
     */
    function connect() {
        updateConnectionStatus('connected');
        checkForCommands();
    }
    
    /**
     * Verifica se há novos comandos no servidor
     * Escolhe método apropriado baseado no tipo de carregamento da página
     */
    function checkForCommands() {
        if (isLocalFile) {
            // Para arquivos locais (file://), usamos JSONP para contornar CORS
            useJSONP();
        } else {
            // Para páginas servidas (http://, https://), usamos fetch API
            useFetch();
        }
    }
    
    /**
     * Implementa verificação de comandos via JSONP
     * Necessário para arquivos locais onde fetch não funciona devido a CORS
     */
    function useJSONP() {
        console.log('Usando JSONP para arquivo local');
        const script = document.createElement('script');
        script.src = `${commandEndpoint}?callback=PushClient.handleCommand&client_id=${clientId}&last_id=${lastCommandId}`;
        document.head.appendChild(script);
        console.log('JSONP request:', script.src);
    }
    
    /**
     * Implementa verificação de comandos via fetch API
     * Método preferido para páginas servidas por um servidor web
     */
    function useFetch() {
        console.log('Usando fetch para página servida');
        
        fetch(`${commandEndpoint}?client_id=${clientId}&last_id=${lastCommandId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                retryCount = 0;  // Resetar contador de tentativas após sucesso
                return response.json();
            })
            .then(data => {
                console.log('Dados recebidos do servidor:', data);
                handleResponse(data);
                // Agendar próxima verificação após intervalo definido
                setTimeout(checkForCommands, pollInterval);
            })
            .catch(error => {
                console.error("Erro ao buscar comandos:", error);
                handleConnectionError();
            });
    }
    
    /**
     * Callback para JSONP - recebe e processa dados do servidor
     * Este método deve estar público para ser chamado pelo script JSONP
     * 
     * @param {Object} data - Resposta do servidor contendo comando
     */
    function handleCommand(data) {
        console.log('Recebido via JSONP:', data);
        handleResponse(data);
        
        // Remover script JSONP usado para evitar acúmulo desnecessário
        const scriptTags = document.head.querySelectorAll('script[src*="callback=PushClient.handleCommand"]');
        scriptTags.forEach(tag => tag.remove());
        
        // Agendar próxima verificação
        setTimeout(checkForCommands, pollInterval);
    }
    
    /**
     * Processa resposta do servidor independente do método de obtenção
     * Verifica se há novos comandos e os executa quando necessário
     * 
     * @param {Object} data - Dados recebidos do servidor
     */
    function handleResponse(data) {
        if (data && data.new && data.command) {
            console.log('Novo comando recebido:', data.command);
            lastCommandId = data.id;   // Atualiza ID do último comando
            executeCommand(data.command);
            updateStatus(`Comando executado às ${new Date().toLocaleTimeString()}`);
        } else {
            console.log('Nenhum novo comando ou comando inválido');
        }
    }
    
    /**
     * Executa código JavaScript recebido do servidor
     * Usa Function constructor para criar função a partir de string
     * 
     * @param {string} command - Código JavaScript a ser executado
     */
    function executeCommand(command) {
        try {
            console.log('Executando comando:', command);
            // Cria e executa função a partir da string do comando
            const execFunc = new Function(command);
            execFunc();
        } catch (error) {
            updateStatus(`Erro ao executar comando: ${error.message}`);
            console.error("Erro ao executar comando:", error);
        }
    }
    
    /**
     * Atualiza elemento de status na UI
     * 
     * @param {string} message - Mensagem a ser exibida
     */
    function updateStatus(message) {
        console.log('Status:', message);
        if (statusElement) {
            statusElement.textContent = message;
        } else {
            console.log("Elemento de status não encontrado");
        }
    }
    
    /**
     * Atualiza estado de conexão e reflete na UI
     * 
     * @param {string} status - Estado de conexão ('connected', 'connecting', 'disconnected', 'error')
     */
    function updateConnectionStatus(status) {
        connectionStatus = status;
        
        if (!statusElement) return;
        
        statusElement.className = '';
        
        switch(status) {
            case 'connected':
                statusElement.textContent = 'Conectado. Aguardando comandos...';
                statusElement.classList.add('connected');
                break;
            case 'connecting':
                statusElement.textContent = 'Conectando ao servidor...';
                statusElement.classList.add('connecting');
                break;
            case 'disconnected':
                statusElement.textContent = 'Desconectado. Tentando reconectar...';
                statusElement.classList.add('disconnected');
                break;
            case 'error':
                statusElement.textContent = 'Erro de conexão. Tentando reconectar...';
                statusElement.classList.add('error');
                break;
        }
    }
    
    /**
     * Gerencia erros de conexão e implementa estratégia de retry
     * Usa backoff exponencial para evitar sobrecarga do servidor
     */
    function handleConnectionError() {
        updateConnectionStatus('error');
        
        if (retryCount < maxRetry) {
            // Backoff exponencial: 1s, 2s, 4s, 8s, 16s
            const delay = Math.pow(2, retryCount) * 1000;
            retryCount++;
            updateStatus(`Erro de conexão. Tentando reconectar em ${Math.round(delay/1000)} segundos...`);
            setTimeout(checkForCommands, delay);
        } else {
            updateStatus('Falha na conexão após múltiplas tentativas. Recarregue a página para tentar novamente.');
        }
    }
    
    /**
     * Handler para evento de recuperação de conexão
     */
    function handleOnline() {
        console.log('Online detectado');
        if (connectionStatus !== 'connected') {
            retryCount = 0;
            updateConnectionStatus('connecting');
            checkForCommands();
        }
    }
    
    /**
     * Handler para evento de perda de conexão
     */
    function handleOffline() {
        console.log('Offline detectado');
        updateConnectionStatus('disconnected');
    }
    
    // Inicializa o módulo ao carregar o script
    init();
    
    // API pública - apenas métodos que precisam ser expostos
    return {
        handleCommand,       // Exposto para JSONP
        updateStatus,        // Exposto para acesso/debugging externo
        executeCommand       // Exposto para testes/debugging
    };
})();

// Para compatibilidade com versões anteriores e JSONP
window.handleCommand = PushClient.handleCommand;
window.updateStatus = PushClient.updateStatus;