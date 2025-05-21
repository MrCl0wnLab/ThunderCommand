def js_format_try_catch(js_code):
    """
    Envolve o código JavaScript em um bloco try-catch para evitar erros de execução.
    "Trick" para evitar que erros de JavaScript interrompam a execução do restante do código.
    
    Args:
        js_code: Código JavaScript a ser executado
        
    Returns:
        Código JavaScript com tratamento de erro
    """
    if js_code:
        return f'try{{(function(){{{js_code}}}());}}catch(err){{}}'
    return ""

def format_datetime(dt):
    """
    Formata uma data/hora para exibição.
    
    Args:
        dt: Objeto datetime ou string ISO
        
    Returns:
        Data formatada como string
    """
    from datetime import datetime
    
    if isinstance(dt, str):
        # Converte string ISO para objeto datetime
        dt = datetime.fromisoformat(dt)
        
    
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def parse_user_agent(user_agent):
    """
    Extrai informações básicas do user agent.
    
    Args:
        user_agent: String do user agent
        
    Returns:
        Dicionário com browser e sistema operacional
    """
    browser = "Desconhecido"
    os_name = "Desconhecido"
    
    # Detectar sistema operacional
    if "Windows" in user_agent:
        os_name = "Windows"
        if "Windows NT 10.0" in user_agent:
            os_name = "Windows 10"
        elif "Windows NT 6.3" in user_agent:
            os_name = "Windows 8.1"
        elif "Windows NT 6.2" in user_agent:
            os_name = "Windows 8"
        elif "Windows NT 6.1" in user_agent:
            os_name = "Windows 7"
        elif "Windows NT 6.0" in user_agent:
            os_name = "Windows Vista"
        elif "Windows NT 5.1" in user_agent:
            os_name = "Windows XP"
    elif "Mac OS X" in user_agent:
        os_name = "macOS"
    elif "Android" in user_agent:
        os_name = "Android"
    elif "Linux" in user_agent:
        os_name = "Linux"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        os_name = "iOS"
    
    # Detectar navegador
    if "Firefox/" in user_agent:
        browser = "Firefox"
    elif "Chrome/" in user_agent and "Edge/" not in user_agent and "Edg/" not in user_agent:
        browser = "Chrome"
    elif "Safari/" in user_agent and "Chrome/" not in user_agent:
        browser = "Safari"
    elif "Edge/" in user_agent or "Edg/" in user_agent:
        browser = "Edge"
    elif "MSIE " in user_agent or "Trident/" in user_agent:
        browser = "Internet Explorer"
    elif "Opera" in user_agent or "OPR/" in user_agent:
        browser = "Opera"
    
    return {
        "browser": browser,
        "os": os_name
    }

def generate_client_id():
    """
    Gera um ID único para clientes.
    
    Returns:
        String UUID
    """
    import uuid
    return str(uuid.uuid4())