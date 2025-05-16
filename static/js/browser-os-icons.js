/**
 * Script para definir dinamicamente os ícones corretos do Font Awesome
 * para cada navegador e sistema operacional.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Aplicar ícones específicos para todos os elementos
    applyBrowserIcons();
    applyOSIcons();
});

/**
 * Aplica os ícones apropriados para cada navegador
 * Atualizado para Font Awesome 6
 */
function applyBrowserIcons() {
    const browserCells = document.querySelectorAll('.browser-cell');
    
    browserCells.forEach(cell => {
        const userAgent = cell.getAttribute('title') || '';
        const iconElement = cell.querySelector('i');
        
        if (!iconElement) return;
        
        // Remover classes existentes e configurar como Font Awesome 6 (fa-brands)
        iconElement.className = 'fa-brands me-1';
        
        // Adicionar a classe de ícone apropriada baseada no User-Agent
        if (userAgent.includes('Chrome') && !userAgent.includes('Edg') && !userAgent.includes('OPR')) {
            iconElement.classList.add('fa-chrome');
        } else if (userAgent.includes('Firefox')) {
            iconElement.classList.add('fa-firefox-browser');
        } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
            iconElement.classList.add('fa-safari');
        } else if (userAgent.includes('Edg') || userAgent.includes('Edge')) {
            iconElement.classList.add('fa-edge');
        } else if (userAgent.includes('OPR') || userAgent.includes('Opera')) {
            iconElement.classList.add('fa-opera');
        } else if (userAgent.includes('Trident') || userAgent.includes('MSIE')) {
            iconElement.classList.add('fa-internet-explorer');
        } else {
            // Ícone padrão para navegadores não identificados (usando fa-solid para globe)
            iconElement.className = 'fa-solid me-1';
            iconElement.classList.add('fa-globe');
        }
    });
}

/**
 * Aplica os ícones apropriados para cada sistema operacional
 * Atualizado para Font Awesome 6
 */
function applyOSIcons() {
    const osCells = document.querySelectorAll('.os-cell');
    
    osCells.forEach(cell => {
        const userAgent = cell.getAttribute('title') || '';
        const iconElement = cell.querySelector('i');
        
        if (!iconElement) return;
        
        // Determinar se o ícone deve ser brands ou solid
        let iconType = 'fa-brands';
        let iconName = '';
        
        // Adicionar a classe de ícone apropriada baseada no User-Agent
        if (userAgent.includes('Windows')) {
            iconName = 'fa-windows';
        } else if (userAgent.includes('Mac OS') || userAgent.includes('Macintosh')) {
            iconName = 'fa-apple';
        } else if (userAgent.includes('iPhone') || userAgent.includes('iPad') || userAgent.includes('iOS')) {
            iconName = 'fa-apple';
        } else if (userAgent.includes('Android')) {
            iconName = 'fa-android';
        } else if (userAgent.includes('Linux') || userAgent.includes('Ubuntu')) {
            iconName = 'fa-linux';
        } else {
            // Ícone padrão para SO não identificado (usando fa-solid)
            iconType = 'fa-solid';
            iconName = 'fa-desktop';
        }
        
        // Aplicar as classes
        iconElement.className = `${iconType} me-1 ${iconName}`;
    });
}

// Executar o script quando o DOM for atualizado dinamicamente (para tabelas que são carregadas via AJAX)
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            applyBrowserIcons();
            applyOSIcons();
        }
    });
});

// Iniciar a observação do conteúdo principal ou tabela de clientes
document.addEventListener('DOMContentLoaded', function() {
    const target = document.getElementById('clients-table') || document.getElementById('main-content');
    if (target) {
        observer.observe(target, { childList: true, subtree: true });
    }
    
    // Aplicar ícones assim que o DOM estiver pronto (para elementos já presentes)
    applyBrowserIcons();
    applyOSIcons();
});
