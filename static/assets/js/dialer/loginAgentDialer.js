let selectedCampaign = null;
let isOnCooldown = false;
const COOLDOWN_TIME = 3000; // 3 segundos de cooldown

// Campaign selection functionality
document.querySelectorAll('.campaign-option').forEach(option => {
    option.addEventListener('click', function() {
        // Remove selected class from all options
        document.querySelectorAll('.campaign-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Add selected class to clicked option
        this.classList.add('selected');
        
        // Get campaign ID
        selectedCampaign = this.dataset.campaign;
        
        // Enable login button only if not on cooldown
        const loginBtn = document.getElementById('loginBtn');
        if (!isOnCooldown) {
            loginBtn.disabled = false;
        }
        
        // Add a subtle animation
        this.style.transform = 'scale(1.02)';
        setTimeout(() => {
            this.style.transform = '';
        }, 200);
    });
});

// Función para manejar el cooldown
function startCooldown() {
    isOnCooldown = true;
    const loginBtn = document.getElementById('loginBtn');
    
    let remainingTime = COOLDOWN_TIME / 1000; // Convertir a segundos
    
    const cooldownInterval = setInterval(() => {
        loginBtn.innerHTML = `<i class="fas fa-clock me-2"></i>Wait ${remainingTime}s`;
        loginBtn.disabled = true;
        remainingTime--;
        
        if (remainingTime < 0) {
            clearInterval(cooldownInterval);
            isOnCooldown = false;
            loginBtn.innerHTML = 'Continue to Campaign';
            
            // Solo habilitar si hay una campaña seleccionada
            if (selectedCampaign) {
                loginBtn.disabled = false;
            }
        }
    }, 1000);
}

// Función para enviar datos al backend
async function loginToCampaign(campaignId) {
    try {
        const response = await fetch('/api/dialer/agentDashboard/campaign/login/', {
            method: 'POST',
            body: JSON.stringify({
                campaign: campaignId,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error logging into campaign:', error);
        throw error;
    }
}

// Form submission
document.getElementById('campaignForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!selectedCampaign) {
        alert('Please select a campaign');
        return;
    }

    if (isOnCooldown) {
        alert('Please wait before trying again');
        return;
    }

    // Show loading state
    const loginBtn = document.getElementById('loginBtn');
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Connecting...';
    loginBtn.disabled = true;

    try {
        console.log('Sending request for campaign:', selectedCampaign);
        
        // Enviar fetch al backend y esperar respuesta
        const response = await loginToCampaign(selectedCampaign);
        
        console.log('Backend response:', response);
        
        // Mostrar mensaje de éxito
        loginBtn.innerHTML = '<i class="fas fa-check me-2"></i>Success!';
        
        // Esperar un momento para mostrar el éxito y luego redirigir
        setTimeout(() => {
            window.location.href = '/dialer/agentDashboard/';
        }, 1000);
        
    } catch (error) {
        console.error('Login failed:', error);
        
        // Mostrar error
        loginBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error';
        
        // Iniciar cooldown después del error
        setTimeout(() => {
            startCooldown();
        }, 1500);
        
        // Mostrar mensaje de error al usuario
        setTimeout(() => {
            alert('Login failed. Please try again.');
        }, 500);
    }
});

// Add some interactive effects
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to campaign options
    document.querySelectorAll('.campaign-option').forEach(option => {
        option.addEventListener('mouseenter', function() {
            if (!this.classList.contains('selected')) {
                this.style.background = 'rgba(30, 136, 229, 0.08)';
            }
        });
        
        option.addEventListener('mouseleave', function() {
            if (!this.classList.contains('selected')) {
                this.style.background = 'rgba(30, 136, 229, 0.05)';
            }
        });
    });
});