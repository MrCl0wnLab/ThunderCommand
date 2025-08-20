/**
 * Gerenciador de clientes para o ThunderCommand
 */
export class ClientManager {
    constructor(apiUrl) {
        this.apiUrl = apiUrl || window.location.origin;
        this.clients = [];
        this.selectedClientId = null;
        this.pollingInterval = null;
        this.refreshRate = 5000; // ms
    }

    /**
     * Inicia o polling para atualização de clientes
     */
    startPolling() {
        this.fetchClients();
        this.pollingInterval = setInterval(() => this.fetchClients(), this.refreshRate);
    }

    /**
     * Para o polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Busca clientes ativos no servidor
     */
    async fetchClients() {
        try {
            const response = await fetch(`${this.apiUrl}/admin/clients`);
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && Array.isArray(data.clients)) {
                this.updateClients(data.clients);
            }
        } catch (error) {
            console.error('Failed to fetch clients:', error);
        }
    }

    /**
     * Atualiza a lista de clientes e dispara evento
     */
    updateClients(newClients) {
        // Verificar se houve mudanças
        const clientsChanged = JSON.stringify(this.clients) !== JSON.stringify(newClients);
        
        if (clientsChanged) {
            this.clients = newClients;
            
            // Disparar evento de atualização
            const event = new CustomEvent('clients:updated', {
                detail: { clients: this.clients }
            });
            
            document.dispatchEvent(event);
        }
    }

    /**
     * Define o cliente selecionado
     */
    selectClient(clientId) {
        this.selectedClientId = clientId;
        
        // Disparar evento de seleção
        const event = new CustomEvent('client:selected', {
            detail: { 
                clientId,
                client: this.getClientById(clientId)
            }
        });
        
        document.dispatchEvent(event);
    }

    /**
     * Obtém cliente por ID
     */
    getClientById(clientId) {
        return this.clients.find(client => client.id === clientId) || null;
    }

    /**
     * Envia comando para um cliente
     */
    async sendCommand(clientId, commandType, content) {
        try {
            const response = await fetch(`${this.apiUrl}/admin/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId,
                    type: commandType,
                    content
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            return data.command_id;
            
        } catch (error) {
            console.error('Failed to send command:', error);
            throw error;
        }
    }
}
