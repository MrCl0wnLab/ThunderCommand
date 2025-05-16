/**
 * table-fixes-consolidated.js
 * Arquivo consolidado com todas as correções de tabela
 * Combina as funcionalidades de:
 * - table-selection-fix.js
 * - final-table-fix.js
 * 
 * Data: 16 de maio de 2025
 */

(function() {
  // Executar assim que o DOM estiver pronto
  document.addEventListener('DOMContentLoaded', function() {
    console.log("Inicializando correções de tabela unificadas...");
    
    // Inicializar as correções com um pequeno delay para garantir
    // que outros scripts já foram carregados
    setTimeout(initTableFixes, 300);
  });

  /**
   * Inicializa todas as correções de tabela
   */
  function initTableFixes() {
    // Corrigir estrutura de células da tabela
    enforceTableCellStructure();
    
    // Aplicar observador para correções dinâmicas
    setupTableObserver();
  }
  
  /**
   * Configura observador para monitorar alterações nas tabelas
   */
  function setupTableObserver() {
    const tables = document.querySelectorAll('table');
    if (!tables.length) return;
    
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        // Verificar se houve alterações nas classes dos elementos
        if (mutation.type === 'attributes' && 
            mutation.attributeName === 'class' && 
            mutation.target.tagName === 'TR') {
          fixRowSelection(mutation.target);
        }
      });
    });
    
    // Observar todas as tabelas para mudanças
    tables.forEach(table => {
      observer.observe(table, { 
        attributes: true,
        subtree: true,
        attributeFilter: ['class']
      });
    });
    
    // Também corrigir linhas existentes
    fixAllTableRows();
  }
  
  /**
   * Garante a estrutura correta para células de tabela
   */
  function enforceTableCellStructure() {
    // Código da função enforceTableCellStructure de table-selection-fix.js
    const tables = document.querySelectorAll('table');
    if (!tables.length) return;
    
    tables.forEach(table => {
      const rows = table.querySelectorAll('tr');
      rows.forEach(row => {
        const cells = row.querySelectorAll('td, th');
        cells.forEach(cell => {
          // Garantir que o estilo de exibição é preservado
          if (!cell.hasAttribute('data-display-fixed')) {
            cell.setAttribute('data-original-display', getComputedStyle(cell).display);
            cell.setAttribute('data-display-fixed', 'true');
          }
        });
      });
    });
  }
  
  /**
   * Corrige a seleção de uma linha específica
   */
  function fixRowSelection(row) {
    // Código combinado de funções de table-selection-fix.js e final-table-fix.js
    if (!row || row.tagName !== 'TR') return;
    
    const isSelected = row.classList.contains('selected') || 
                        row.classList.contains('active') || 
                        row.hasAttribute('aria-selected');
                        
    const cells = row.querySelectorAll('td, th');
    
    if (isSelected) {
      // Configurações para linha selecionada
      row.style.backgroundColor = 'var(--dark-card)';
      row.style.boxShadow = 'var(--accent-shadow)';
      row.style.color = 'var(--accent-color)';
      
      cells.forEach(cell => {
        const originalDisplay = cell.getAttribute('data-original-display') || 'table-cell';
        cell.style.display = originalDisplay;
        cell.style.color = 'var(--text-table)';
      });
    } else {
      // Restaurar para estilo normal
      row.style.backgroundColor = '';
      row.style.boxShadow = '';
      row.style.color = '';
      
      cells.forEach(cell => {
        const originalDisplay = cell.getAttribute('data-original-display') || 'table-cell';
        cell.style.display = originalDisplay;
        cell.style.color = '';
      });
    }
  }
  
  /**
   * Corrige todas as linhas da tabela
   */
  function fixAllTableRows() {
    const rows = document.querySelectorAll('table tr');
    rows.forEach(row => fixRowSelection(row));
  }
})();
