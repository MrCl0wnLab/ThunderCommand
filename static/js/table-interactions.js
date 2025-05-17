/**
 * Funcionalidades interativas para tabelas no painel Thunder Command
 * Implementa:
 * - Seleção de linhas com destaque visual usando o tema neon
 * - Ordenação interativa das colunas
 * - Efeitos visuais para botões de ação
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializa os handlers de tabela
    initTableRowSelection();
    initTableSorting();
    initTableHoverEffects();
});

/**
 * Inicializa a funcionalidade de seleção de linhas nas tabelas
 */
function initTableRowSelection() {
    // Aplicar para todas as tabelas com a classe .table-hover
    document.querySelectorAll('.table-hover').forEach(table => {
        table.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (!row || row.tagName !== 'TR' || row.parentNode.tagName === 'THEAD') return;
            
            // Ignora cliques em botões e links dentro das linhas
            if (e.target.closest('button') || e.target.closest('a')) {
                return;
            }
            
            // Verifica se a linha clicada não é uma linha de cabeçalho
            if (!row.closest('thead')) {
                // Toggle classe 'selected' e 'client-selected' na linha
                const wasSelected = row.classList.contains('selected');
                
                // Remove seleção de todas as linhas de todas as tabelas
                document.querySelectorAll('tr.selected, tr.client-selected, tr.tandera-row-highlight, tr.tandera-client-highlight').forEach(tr => {
                    tr.classList.remove('selected', 'client-selected', 'tandera-row-highlight', 'tandera-client-highlight');
                    
                    // Remover efeitos de estilo inline
                    tr.style.boxShadow = '';
                    
                    // Limpar estilos inline dos códigos de cliente
                    const codeElement = tr.querySelector('.client-id code');
                    if (codeElement) {
                        codeElement.style.color = '';
                        codeElement.style.fontWeight = '';
                    }
                });
                
                // Se a linha não estava selecionada, seleciona-a
                if (!wasSelected) {
                    // Preservar classes de formatação originais
                    let classList = Array.from(row.classList)
                        .filter(cls => !['selected', 'client-selected', 'tandera-row-highlight', 'tandera-client-highlight'].includes(cls));
                    
                    // Remover classes de seleção anteriores
                    row.className = classList.join(' ');
                    
                    // Adicionar classes de seleção sem perder formatações originais
                    row.classList.add('selected', 'tandera-row-highlight');
                    
                    // Verifica se é um cliente e aplica efeitos específicos
                    if (row.hasAttribute('data-client-id')) {
                        // Destaque para cliente selecionado
                        const clientId = row.getAttribute('data-client-id');
                        
                        // Destacar todas as instâncias deste cliente em outras tabelas
                        document.querySelectorAll(`tr[data-client-id="${clientId}"]`).forEach(clientRow => {
                            if (clientRow !== row) { // Não duplicar no elemento atual
                                // Adicionar classes de seleção preservando as originais
                                clientRow.classList.add('client-selected', 'tandera-client-highlight');
                                
                                // Destacar apenas o código do cliente sem afetar o layout da linha
                                const codeElement = clientRow.querySelector('.client-id code');
                                if (codeElement) {
                                    codeElement.style.color = 'var(--accent-color, #00ffb8)';
                                    codeElement.style.fontWeight = 'bold';
                                }
                            }
                        });
                        
                        // Chama a função targetClient para atualizar o dropdown no painel de comandos
                        if (typeof window.targetClient === 'function') {
                            window.targetClient(clientId);
                        }
                    }
                    
                    // Dispara evento customizado que outras partes da aplicação podem ouvir
                    const rowData = collectRowData(row);
                    const event = new CustomEvent('tableRowSelected', {
                        detail: { row, rowData, tableId: table.id }
                    });
                    document.dispatchEvent(event);
                }
            }
        });
    });
}

/**
 * Coleta dados de uma linha da tabela
 */
function collectRowData(row) {
    const data = {};
    // Coleta dados dos atributos data-* para facilitar o acesso aos dados da linha
    Object.keys(row.dataset).forEach(key => {
        data[key] = row.dataset[key];
    });
    
    // Coleta o texto visível de cada célula (para tabelas simples)
    const cells = Array.from(row.cells);
    cells.forEach((cell, index) => {
        // Busca código de cliente em cells que contêm elementos <code>
        const codeElement = cell.querySelector('code');
        if (codeElement) {
            data[`cell${index}Code`] = codeElement.textContent;
        }
        data[`cell${index}`] = cell.textContent.trim();
    });
    
    return data;
}

/**
 * Inicializa a funcionalidade de ordenação para tabelas
 */
function initTableSorting() {
    document.querySelectorAll('.table-sortable thead th').forEach(th => {
        th.addEventListener('click', function() {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const index = Array.from(th.parentNode.children).indexOf(th);
            const direction = th.classList.contains('sort-asc') ? -1 : 1;
            
            // Limpa classes de ordenação em todos os cabeçalhos
            table.querySelectorAll('thead th').forEach(header => {
                header.classList.remove('sort-asc', 'sort-desc');
            });
            
            // Define classe de ordenação neste cabeçalho
            th.classList.add(direction > 0 ? 'sort-asc' : 'sort-desc');
            
            // Ordena as linhas
            rows.sort((a, b) => {
                const aValue = a.cells[index].textContent.trim();
                const bValue = b.cells[index].textContent.trim();
                
                // Tenta ordenação numérica se os valores parecerem números
                if (!isNaN(aValue) && !isNaN(bValue)) {
                    return direction * (parseFloat(aValue) - parseFloat(bValue));
                }
                
                // Ordenação de data se os valores parecerem datas
                if (aValue.match(/^(\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2})/) && 
                    bValue.match(/^(\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2})/)) {
                    return direction * (new Date(aValue) - new Date(bValue));
                }
                
                // Ordenação de texto para outros casos
                return direction * aValue.localeCompare(bValue);
            });
            
            // Reinsere linhas ordenadas
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

/**
 * Inicializa efeitos de hover para os botões de ação nas tabelas
 */
function initTableHoverEffects() {
    document.querySelectorAll('.table .action-btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
        
        // Efeito de pressionar
        btn.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(1px)';
        });
        
        btn.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-2px)';
        });
    });
}

/**
 * Adiciona uma linha destacada a uma tabela com efeito de aparecimento
 * @param {string} tableId - ID da tabela
 * @param {object} data - Dados para as células
 * @param {string} highlightClass - Classe para destacar (opcional)
 */
function addHighlightedRow(tableId, data, highlightClass = 'table-flash') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const row = document.createElement('tr');
    
    // Adiciona classe de destaque
    row.classList.add(highlightClass);
    
    // Cria células com os dados
    Object.values(data).forEach(cellText => {
        const cell = document.createElement('td');
        cell.innerHTML = cellText; // Permite HTML se necessário
        row.appendChild(cell);
    });
    
    // Insere a linha no topo da tabela
    if (tbody.firstChild) {
        tbody.insertBefore(row, tbody.firstChild);
    } else {
        tbody.appendChild(row);
    }
    
    // Aplica efeito de aparecimento
    setTimeout(() => {
        row.classList.remove(highlightClass);
        
        // Após a animação, adiciona classe normal
        setTimeout(() => {
            row.classList.add('table-primary');
        }, 300);
    }, 1500);
}

/**
 * Destaca um cliente que teve atividade recente
 * @param {string} clientId - ID do cliente com atividade recente
 */
function highlightClientActivity(clientId) {
    // Encontra todas as linhas que representam este cliente
    document.querySelectorAll(`tr[data-client-id="${clientId}"]`).forEach(row => {
        // Remove qualquer classe de atividade anterior
        row.classList.remove('recent-activity');
        
        // Trigger reflow para reiniciar a animação
        void row.offsetWidth;
        
        // Adiciona a classe de atividade recente
        row.classList.add('recent-activity');
        
        // Aplica efeito neon no ID do cliente
        const codeElement = row.querySelector('.client-id code');
        if (codeElement) {
            codeElement.style.color = 'var(--accent-color)';
            codeElement.style.textShadow = '0 0 5px rgba(0, 255, 184, 0.5)';
            
            // Remove o efeito após a animação
            setTimeout(() => {
                codeElement.style.color = '';
                codeElement.style.textShadow = '';
            }, 3000);
        }
    });
}

// Exporta funções para uso global
window.TableUtils = {
    addHighlightedRow,
    initTableRowSelection,
    initTableSorting,
    initTableHoverEffects,
    highlightClientActivity
};
