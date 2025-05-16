/**
 * Função para analisar o User-Agent e extrair informações do navegador e sistema operacional
 * Esta função detecta os principais navegadores e sistemas operacionais
 */
function parseUserAgent(userAgent) {
    if (!userAgent) return { browser: 'Desconhecido', os: 'Desconhecido' };
    
    // Objeto para armazenar o resultado
    const result = {
        browser: 'Desconhecido',
        os: 'Desconhecido'
    };
    
    // Identificar o sistema operacional
    if (/Windows NT 10.0/.test(userAgent)) {
        result.os = 'Windows 10';
    } else if (/Windows NT 6.3/.test(userAgent)) {
        result.os = 'Windows 8.1';
    } else if (/Windows NT 6.2/.test(userAgent)) {
        result.os = 'Windows 8';
    } else if (/Windows NT 6.1/.test(userAgent)) {
        result.os = 'Windows 7';
    } else if (/Windows NT 6.0/.test(userAgent)) {
        result.os = 'Windows Vista';
    } else if (/Windows NT 5.1/.test(userAgent)) {
        result.os = 'Windows XP';
    } else if (/Windows/.test(userAgent)) {
        result.os = 'Windows';
    } else if (/Android/.test(userAgent)) {
        const match = userAgent.match(/Android\s([0-9.]+)/);
        result.os = match ? `Android ${match[1]}` : 'Android';
    } else if (/iPhone|iPad|iPod/.test(userAgent)) {
        const match = userAgent.match(/OS\s([0-9_]+)/);
        const version = match ? match[1].replace(/_/g, '.') : '';
        result.os = version ? `iOS ${version}` : 'iOS';
    } else if (/Mac OS X/.test(userAgent)) {
        const match = userAgent.match(/Mac OS X\s([0-9_.]+)/);
        const version = match ? match[1].replace(/_/g, '.') : '';
        result.os = version ? `macOS ${version}` : 'macOS';
    } else if (/Linux/.test(userAgent)) {
        if (/Ubuntu/.test(userAgent)) {
            result.os = 'Ubuntu';
        } else {
            result.os = 'Linux';
        }
    } else if (/CrOS/.test(userAgent)) {
        result.os = 'Chrome OS';
    }
    
    // Identificar o navegador
    if (/Chrome\//.test(userAgent) && !/Chromium\//.test(userAgent) && !/Edge\/|Edg\//.test(userAgent)) {
        const match = userAgent.match(/Chrome\/([0-9.]+)/);
        const version = match ? match[1].split('.')[0] : '';
        result.browser = version ? `Chrome ${version}` : 'Chrome';
    } else if (/Firefox\//.test(userAgent)) {
        const match = userAgent.match(/Firefox\/([0-9.]+)/);
        const version = match ? match[1].split('.')[0] : '';
        result.browser = version ? `Firefox ${version}` : 'Firefox';
    } else if (/Safari\//.test(userAgent) && !/Chrome\//.test(userAgent)) {
        const match = userAgent.match(/Version\/([0-9.]+)/);
        const version = match ? match[1].split('.')[0] : '';
        result.browser = version ? `Safari ${version}` : 'Safari';
    } else if (/MSIE|Trident\//.test(userAgent)) {
        if (/MSIE\s([0-9.]+)/.test(userAgent)) {
            const match = userAgent.match(/MSIE\s([0-9.]+)/);
            const version = match ? match[1].split('.')[0] : '';
            result.browser = `Internet Explorer ${version}`;
        } else {
            result.browser = 'Internet Explorer';
        }
    } else if (/Edge\/|Edg\//.test(userAgent)) {
        const match = userAgent.match(/Edge\/([0-9.]+)|Edg\/([0-9.]+)/);
        const version = match ? (match[1] || match[2]).split('.')[0] : '';
        result.browser = version ? `Edge ${version}` : 'Edge';
    } else if (/Opera|OPR\//.test(userAgent)) {
        const match = userAgent.match(/OPR\/([0-9.]+)/);
        const version = match ? match[1].split('.')[0] : '';
        result.browser = version ? `Opera ${version}` : 'Opera';
    } else if (/Chromium\//.test(userAgent)) {
        const match = userAgent.match(/Chromium\/([0-9.]+)/);
        const version = match ? match[1].split('.')[0] : '';
        result.browser = version ? `Chromium ${version}` : 'Chromium';
    } else if (/Brave\//.test(userAgent)) {
        result.browser = 'Brave';
    } else if (/Mobile/.test(userAgent)) {
        result.browser = 'Navegador Mobile';
    }
    
    return result;
}

/**
 * Função para alternar a visibilidade dos detalhes do User-Agent na interface
 * Usada no painel de administração para mostrar ou ocultar detalhes técnicos
 */
function toggleUserAgent() {
    const details = document.getElementById('user-agent-details');
    const toggleLink = document.getElementById('show-user-agent');
    
    if (details.classList.contains('d-none')) {
        details.classList.remove('d-none');
        toggleLink.textContent = 'Ocultar User-Agent';
    } else {
        details.classList.add('d-none');
        toggleLink.textContent = 'Ver User-Agent completo';
    }
}

// Auto-teste para verificar se as funções funcionam corretamente
(function() {
    console.log('🔍 User-Agent Parser carregado com sucesso');
    
    // Auto-teste com o User-Agent do navegador atual
    console.log('Debug - User-Agent atual:', parseUserAgent(navigator.userAgent));
})();
