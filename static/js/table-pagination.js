/**
 * Sistema de paginação para tabelas grandes no Olho de Tandera
 * 
 * Este script implementa:
 * - Paginação automática baseada em quantidade de linhas
 * - Busca e filtro nas tabelas
 * - Controles de tamanho de página
 * - Navegação entre páginas com efeito visual
 * 
 * Compatível com o tema escuro neon do painel
 */

class TablePagination {
    /**
     * Inicializa a paginação para uma tabela
     * @param {string} tableId - ID da tabela
     * @param {object} options - Opções de configuração
     */
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        
        if (!this.table) {
            console.error(`Tabela com ID ${tableId} não encontrada.`);
            return;
        }
        
        this.options = {
            rowsPerPage: options.rowsPerPage || 10,
            pageControlsId: options.pageControlsId || `${tableId}-pagination`,
            searchInputId: options.searchInputId || `${tableId}-search`,
            pageSizeSelectId: options.pageSizeSelectId || `${tableId}-pagesize`,
            ...options
        };
        
        this.currentPage = 1;
        this.totalRows = 0;
        this.totalPages = 0;
        this.filteredRows = [];
        
        this._init();
    }
    
    /**
     * Inicializa o sistema de paginação
     */
    _init() {
        // Armazena todas as linhas originais da tabela
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        this.allRows = Array.from(tbody.querySelectorAll('tr'));
        this.totalRows = this.allRows.length;
        this.filteredRows = [...this.allRows];
        
        // Criar controles de paginação se não existirem
        this._createControls();
        
        // Aplicar paginação inicial
        this._updatePagination();
        
        // Adicionar event listeners
        this._addEventListeners();
    }
    
    /**
     * Cria os controles de paginação necessários
     */
    _createControls() {
        // Verifica se os controles já existem ou cria novos
        let paginationContainer = document.getElementById(this.options.pageControlsId);
        
        if (!paginationContainer) {
            paginationContainer = document.createElement('div');
            paginationContainer.id = this.options.pageControlsId;
            paginationContainer.className = 'pagination-container mt-3';
            
            const searchContainer = document.createElement('div');
            searchContainer.className = 'search-container mb-3';
            
            // Input de busca
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.id = this.options.searchInputId;
            searchInput.className = 'form-control form-control-sm table-search';
            searchInput.placeholder = 'Buscar na tabela...';
            
            searchContainer.appendChild(searchInput);
            
            // Container para paginação e seletor de tamanho
            const controlsRow = document.createElement('div');
            controlsRow.className = 'd-flex justify-content-between align-items-center';
            
            // Select para tamanho da página
            const pageSizeContainer = document.createElement('div');
            pageSizeContainer.className = 'page-size-container';
            
            const pageSizeLabel = document.createElement('label');
            pageSizeLabel.className = 'me-2 text-muted small';
            pageSizeLabel.textContent = 'Itens por página:';
            
            const pageSizeSelect = document.createElement('select');
            pageSizeSelect.id = this.options.pageSizeSelectId;
            pageSizeSelect.className = 'form-select form-select-sm d-inline-block w-auto';
            
            [5, 10, 25, 50, 100].forEach(size => {
                const option = document.createElement('option');
                option.value = size;
                option.textContent = size;
                if (size === this.options.rowsPerPage) {
                    option.selected = true;
                }
                pageSizeSelect.appendChild(option);
            });
            
            pageSizeContainer.appendChild(pageSizeLabel);
            pageSizeContainer.appendChild(pageSizeSelect);
            
            // Container para os botões de paginação
            const paginationNav = document.createElement('nav');
            paginationNav.setAttribute('aria-label', 'Navegação de páginas');
            
            const paginationUl = document.createElement('ul');
            paginationUl.className = 'pagination pagination-sm mb-0';
            paginationNav.appendChild(paginationUl);
            
            controlsRow.appendChild(pageSizeContainer);
            controlsRow.appendChild(paginationNav);
            
            paginationContainer.appendChild(searchContainer);
            paginationContainer.appendChild(controlsRow);
            
            // Adiciona após a tabela
            this.table.parentNode.insertBefore(paginationContainer, this.table.nextSibling);
        }
        
        this.paginationContainer = paginationContainer;
    }
    
    /**
     * Adiciona listeners para os eventos de controle
     */
    _addEventListeners() {
        // Evento para busca
        const searchInput = document.getElementById(this.options.searchInputId);
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this._filterTable(searchInput.value);
            });
        }
        
        // Evento para mudar tamanho da página
        const pageSizeSelect = document.getElementById(this.options.pageSizeSelectId);
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', () => {
                this.options.rowsPerPage = parseInt(pageSizeSelect.value);
                this.currentPage = 1; // Volta para a primeira página
                this._updatePagination();
            });
        }
    }
    
    /**
     * Filtra a tabela com base no termo de busca
     * @param {string} term - Termo de busca
     */
    _filterTable(term) {
        term = term.toLowerCase().trim();
        
        if (!term) {
            this.filteredRows = [...this.allRows];
        } else {
            this.filteredRows = this.allRows.filter(row => {
                const text = row.textContent.toLowerCase();
                return text.includes(term);
            });
        }
        
        this.currentPage = 1; // Volta para a primeira página
        this._updatePagination();
    }
    
    /**
     * Atualiza a paginação e exibe a página atual
     */
    _updatePagination() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        // Limpa a tabela
        tbody.innerHTML = '';
        
        // Calcula páginas
        this.totalPages = Math.ceil(this.filteredRows.length / this.options.rowsPerPage);
        
        // Ajusta página atual se necessário
        if (this.currentPage > this.totalPages) {
            this.currentPage = this.totalPages || 1;
        }
        
        // Calcula índices das linhas a mostrar
        const startIdx = (this.currentPage - 1) * this.options.rowsPerPage;
        const endIdx = Math.min(startIdx + this.options.rowsPerPage, this.filteredRows.length);
        
        // Exibe as linhas da página atual
        for (let i = startIdx; i < endIdx; i++) {
            tbody.appendChild(this.filteredRows[i].cloneNode(true));
        }
        
        // Atualiza controles de paginação
        this._updatePaginationControls();
        
        // Re-aplica efeitos interativos
        if (window.TableUtils) {
            window.TableUtils.initTableRowSelection();
            window.TableUtils.initTableHoverEffects();
        }
    }
    
    /**
     * Atualiza os controles de paginação (botões de página)
     */
    _updatePaginationControls() {
        const paginationNav = this.paginationContainer.querySelector('nav ul');
        if (!paginationNav) return;
        
        paginationNav.innerHTML = '';
        
        // Adiciona informação do total de registros
        const infoEl = document.createElement('li');
        infoEl.className = 'page-item disabled me-3';
        const infoA = document.createElement('span');
        infoA.className = 'page-link border-0';
        infoA.innerHTML = `<small>${this.filteredRows.length} registros</small>`;
        infoEl.appendChild(infoA);
        paginationNav.appendChild(infoEl);
        
        // Se não houver páginas suficientes
        if (this.totalPages <= 1) {
            return;
        }
        
        // Botão Anterior
        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${this.currentPage === 1 ? 'disabled' : ''}`;
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.setAttribute('aria-label', 'Anterior');
        prevLink.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevItem.appendChild(prevLink);
        
        if (this.currentPage > 1) {
            prevLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage--;
                this._updatePagination();
            });
        }
        
        paginationNav.appendChild(prevItem);
        
        // Determina quais números de página mostrar
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(this.totalPages, startPage + 4);
        
        // Ajusta para sempre mostrar 5 páginas quando possível
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // Adiciona link para primeira página se necessário
        if (startPage > 1) {
            const firstItem = document.createElement('li');
            firstItem.className = 'page-item';
            const firstLink = document.createElement('a');
            firstLink.className = 'page-link';
            firstLink.href = '#';
            firstLink.textContent = '1';
            firstItem.appendChild(firstLink);
            
            firstLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = 1;
                this._updatePagination();
            });
            
            paginationNav.appendChild(firstItem);
            
            // Adiciona elipse se há um salto
            if (startPage > 2) {
                const ellipsisItem = document.createElement('li');
                ellipsisItem.className = 'page-item disabled';
                const ellipsisLink = document.createElement('span');
                ellipsisLink.className = 'page-link';
                ellipsisLink.innerHTML = '&hellip;';
                ellipsisItem.appendChild(ellipsisLink);
                paginationNav.appendChild(ellipsisItem);
            }
        }
        
        // Números de página
        for (let i = startPage; i <= endPage; i++) {
            const numItem = document.createElement('li');
            numItem.className = `page-item ${i === this.currentPage ? 'active' : ''}`;
            const numLink = document.createElement('a');
            numLink.className = 'page-link';
            numLink.href = '#';
            numLink.textContent = i;
            numItem.appendChild(numLink);
            
            if (i !== this.currentPage) {
                numLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.currentPage = i;
                    this._updatePagination();
                });
            }
            
            paginationNav.appendChild(numItem);
        }
        
        // Adiciona link para última página se necessário
        if (endPage < this.totalPages) {
            // Adiciona elipse se há um salto
            if (endPage < this.totalPages - 1) {
                const ellipsisItem = document.createElement('li');
                ellipsisItem.className = 'page-item disabled';
                const ellipsisLink = document.createElement('span');
                ellipsisLink.className = 'page-link';
                ellipsisLink.innerHTML = '&hellip;';
                ellipsisItem.appendChild(ellipsisLink);
                paginationNav.appendChild(ellipsisItem);
            }
            
            const lastItem = document.createElement('li');
            lastItem.className = 'page-item';
            const lastLink = document.createElement('a');
            lastLink.className = 'page-link';
            lastLink.href = '#';
            lastLink.textContent = this.totalPages;
            lastItem.appendChild(lastLink);
            
            lastLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = this.totalPages;
                this._updatePagination();
            });
            
            paginationNav.appendChild(lastItem);
        }
        
        // Botão Próximo
        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}`;
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.setAttribute('aria-label', 'Próximo');
        nextLink.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextItem.appendChild(nextLink);
        
        if (this.currentPage < this.totalPages) {
            nextLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage++;
                this._updatePagination();
            });
        }
        
        paginationNav.appendChild(nextItem);
    }
    
    /**
     * Atualiza a tabela com novos dados
     * @param {Array} data - Novos dados para a tabela
     */
    updateData(data) {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        // Limpa a tabela atual
        tbody.innerHTML = '';
        
        // Atualiza com os novos dados
        this.allRows = data.map(rowData => {
            const row = document.createElement('tr');
            row.innerHTML = rowData;
            return row;
        });
        
        this.filteredRows = [...this.allRows];
        this.totalRows = this.allRows.length;
        this.currentPage = 1;
        
        // Re-aplica paginação
        this._updatePagination();
    }
    
    /**
     * Adiciona novas linhas à tabela
     * @param {Array} data - Novas linhas
     */
    addRows(data) {
        const newRows = data.map(rowData => {
            const row = document.createElement('tr');
            row.innerHTML = rowData;
            return row;
        });
        
        // Adiciona ao array de linhas
        this.allRows = [...newRows, ...this.allRows];
        
        // Atualiza filtradas se não houver filtragem ativa
        const searchInput = document.getElementById(this.options.searchInputId);
        if (!searchInput || !searchInput.value.trim()) {
            this.filteredRows = [...this.allRows];
        } else {
            // Re-aplica o filtro atual
            this._filterTable(searchInput.value);
        }
        
        this.totalRows = this.allRows.length;
        
        // Re-aplica paginação
        this._updatePagination();
    }
}

// Inicializa automaticamente tabelas com classe .table-paginate
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.table-paginate').forEach(table => {
        if (table.id) {
            new TablePagination(table.id, {
                rowsPerPage: table.dataset.pageSize ? parseInt(table.dataset.pageSize) : 10
            });
        }
    });
});
