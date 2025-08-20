/**
 * ThunderCommand - Aplicativo Principal
 */
import { ClientManager } from './modules/client-manager.js';
import { CommandHandler } from './modules/command-handler.js';
import { DashboardUI } from './modules/dashboard-ui.js';

class ThunderCommandApp {
    constructor() {
        this.clientManager = new ClientManager(window.location.origin);
        this.commandHandler = new CommandHandler();
        this.ui = new DashboardUI();
    }
    
    /**
     * Inicializa o aplicativo
     */
    async init() {
        try {
            // Inicializar componentes
            this.ui.init();
            
            // Iniciar polling de clientes
            this.clientManager.startPolling();
            
            // Configurar event listeners
            this.setupEventListeners();
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
        }
    }
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Seleção de cliente
        document.addEventListener('client:select', (e) => {
            this.clientManager.selectClient(e.detail.clientId);
        });
        
        // Envio de comando
        document.addEventListener('command:send', async (e) => {
            try {
                const { clientId, type, content } = e.detail;
                
                // Enviar comando para o servidor
                const commandId = await this.clientManager.sendCommand(clientId, type, content);
                
                // Notificar usuário
                this.ui.showNotification('Comando enviado com sucesso', 'success');
                
                // Atualizar histórico
                document.dispatchEvent(new CustomEvent('command:executed', {
                    detail: {
                        command: {
                            id: commandId,
                            client_id: clientId,
                            type,
                            content
                        },
                        result: {
                            success: true,
                            message: 'Comando enviado para o servidor'
                        }
                    }
                }));
                
            } catch (error) {
                console.error('Failed to send command:', error);
                this.ui.showNotification(`Erro ao enviar comando: ${error.message}`, 'error');
            }
        });
    }
}

// Inicializar aplicação quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const app = new ThunderCommandApp();
    app.init();
});
