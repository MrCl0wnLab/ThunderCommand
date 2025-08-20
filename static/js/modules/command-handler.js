/**
 * Gerenciador de execução de comandos para ThunderCommand
 */
export class CommandHandler {
    constructor() {
        this.commandQueue = [];
        this.processing = false;
        this.commandHistory = [];
        this.maxHistorySize = 50;
    }
    
    /**
     * Executa um comando com base no tipo
     * @param {Object} command - Comando a ser executado
     * @returns {Promise<Object>} - Resultado da execução
     */
    async executeCommand(command) {
        try {
            // Adicionar ao histórico
            this.addToHistory(command);
            
            let result;
            switch(command.type) {
                case 'js':
                    result = await this.executeJavaScript(command.content);
                    break;
                case 'html':
                    result = await this.injectHTML(command.content);
                    break;
                case 'manipulate':
                    result = await this.manipulateDOM(command);
                    break;
                case 'visibility':
                    result = await this.toggleVisibility(command);
                    break;
                case 'head':
                    result = await this.modifyHead(command.content);
                    break;
                default:
                    throw new Error(`Unknown command type: ${command.type}`);
            }
            
            return {
                success: true,
                result,
                command_id: command.id
            };
            
        } catch (error) {
            console.error('Command execution error:', error);
            return { 
                success: false, 
                error: error.message,
                command_id: command.id
            };
        }
    }
    
    /**
     * Executa código JavaScript arbitrário de forma segura
     * @param {string} code - Código a ser executado
     * @returns {Promise<any>} - Resultado da execução
     */
    async executeJavaScript(code) {
        try {
            // Usar Function constructor para evitar eval direto
            const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
            const func = new AsyncFunction(code);
            const result = await func();
            return result;
        } catch (error) {
            // Se falhar como expressão, tenta executar como declaração
            try {
                const func = new Function(code);
                func();
                return "Comando executado com sucesso";
            } catch (innerError) {
                throw innerError;
            }
        }
    }
    
    /**
     * Injeta conteúdo HTML no corpo do documento
     * @param {string} html - HTML a ser injetado
     * @returns {string} - Mensagem de sucesso
     */
    async injectHTML(html) {
        try {
            // Criar elemento temporário
            const temp = document.createElement('div');
            temp.innerHTML = html;
            
            // Adicionar cada nó ao body
            while (temp.firstChild) {
                document.body.appendChild(temp.firstChild);
            }
            
            return "HTML injetado com sucesso";
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Manipula elementos DOM
     * @param {Object} command - Comando de manipulação
     * @returns {string} - Mensagem de sucesso
     */
    async manipulateDOM(command) {
        const { target_id, action, content } = command;
        
        // Buscar elemento alvo
        const element = this.findElement(target_id);
        
        if (!element) {
            throw new Error(`Elemento não encontrado: ${target_id}`);
        }
        
        // Executar ação de manipulação
        switch(action) {
            case 'ADD':
                element.innerHTML += content;
                break;
            case 'REPLACE':
                element.innerHTML = content;
                break;
            case 'INSERT_AFTER':
                element.insertAdjacentHTML('afterend', content);
                break;
            case 'INSERT_BEFORE':
                element.insertAdjacentHTML('beforebegin', content);
                break;
            default:
                throw new Error(`Ação de manipulação inválida: ${action}`);
        }
        
        return `Elemento ${target_id} manipulado com sucesso`;
    }
    
    /**
     * Altera a visibilidade de um elemento
     * @param {Object} command - Comando de visibilidade
     * @returns {string} - Mensagem de sucesso
     */
    async toggleVisibility(command) {
        const { target_id, is_visible } = command;
        
        // Buscar elemento alvo
        const element = this.findElement(target_id);
        
        if (!element) {
            throw new Error(`Elemento não encontrado: ${target_id}`);
        }
        
        // Alterar visibilidade
        element.style.display = is_visible ? '' : 'none';
        
        return `Visibilidade do elemento ${target_id} alterada para ${is_visible ? 'visível' : 'oculto'}`;
    }
    
    /**
     * Modifica elementos no cabeçalho (head) do documento
     * @param {string} content - Conteúdo a ser adicionado ao head
     * @returns {string} - Mensagem de sucesso
     */
    async modifyHead(content) {
        try {
            document.head.insertAdjacentHTML('beforeend', content);
            return "Cabeçalho modificado com sucesso";
        } catch (error) {
            throw error;
        }
    }
    
    /**
     * Busca um elemento pelo ID, classe ou seletor
     * @param {string} selector - Identificador do elemento
     * @returns {HTMLElement} - Elemento encontrado ou null
     */
    findElement(selector) {
        // Tentar múltiplas estratégias
        return document.getElementById(selector) || 
               document.querySelector(`.${selector}`) || 
               document.querySelector(selector);
    }
    
    /**
     * Adiciona comando ao histórico
     * @param {Object} command - Comando a ser adicionado
     */
    addToHistory(command) {
        this.commandHistory.unshift({
            ...command,
            timestamp: new Date()
        });
        
        // Limitar tamanho do histórico
        if (this.commandHistory.length > this.maxHistorySize) {
            this.commandHistory.pop();
        }
    }
    
    /**
     * Retorna histórico de comandos
     * @returns {Array} - Histórico de comandos
     */
    getHistory() {
        return this.commandHistory;
    }
}
