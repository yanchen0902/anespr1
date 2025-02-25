// Generate a unique user ID
const userId = 'user-' + Date.now();

// Add current_step variable to track chat state
let current_step = 'initial';

function sendMessage(message) {
    if (!message && message !== '') return;
    
    // Clear input if it exists
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.value = '';
    }
    
    // Don't add empty initial message to chat
    if (message) {
        addMessageToChat('user', message);
    }

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: message,
            user_id: userId 
        })
    })
    .then(response => response.json())
    .then(data => {
        // Add bot message to chat
        addMessageToChat('bot', data.response);
        
        // Hide all buttons first
        hideAllButtons();
        
        const response = data.response.toLowerCase();

        // If this is an API response (after initial flow), only show question buttons
        if (current_step === 'chat' || response.includes('api response')) {
            showButtons('question-buttons');
            document.getElementById('user-input').placeholder = '輸入您的問題...';
            return;
        }
        
        // Below are only for initial flow
        // Show sex buttons when asking about gender
        if (response.includes('性別是') || (response.includes('男') && response.includes('女'))) {
            showButtons('sex-buttons');
        }

        // Show CFS buttons when asking about independence
        if (response.includes('自行外出') && response.includes('是/否')) {
            showButtons('cfs-buttons');
        }

        // Show medical history buttons when asking about medical history
        if ((response.includes('慢性病史') || response.includes('病史')) && 
            !response.includes('資訊摘要')) {
            showButtons('medical-history-buttons');
            document.getElementById('user-input').placeholder = '或直接輸入您的病史...';
        }

        // Show worry buttons when asking about concerns
        if (response.includes('最擔心什麼') && !response.includes('資訊摘要')) {
            showButtons('worry-buttons');
            document.getElementById('user-input').placeholder = '或直接輸入您的擔憂...';
        }

        // Show question buttons after summary
        if (response.includes('關於麻醉的問題') && response.includes('資訊摘要')) {
            showButtons('question-buttons');
            document.getElementById('user-input').placeholder = '輸入您的問題...';
            current_step = 'chat';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessageToChat('bot', '抱歉，發生錯誤。請稍後再試。');
    });
}

function hideAllButtons() {
    document.getElementById('sex-buttons').style.display = 'none';
    document.getElementById('cfs-buttons').style.display = 'none';
    document.getElementById('medical-history-buttons').style.display = 'none';
    document.getElementById('worry-buttons').style.display = 'none';
    document.getElementById('question-buttons').style.display = 'none';
}

function showButtons(buttonId) {
    document.getElementById(buttonId).style.display = 'flex';
    setTimeout(scrollToBottom, 100); // Scroll after buttons render
}

function addMessageToChat(role, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.innerHTML = message;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function selectSex(sex) {
    sendMessage(sex);
    document.getElementById('sex-buttons').style.display = 'none';
}

function selectCFS(answer) {
    sendMessage(answer);
    document.getElementById('cfs-buttons').style.display = 'none';
}

function selectMedicalHistory(history) {
    sendMessage(history);
    document.getElementById('medical-history-buttons').style.display = 'none';
}

function selectWorry(worry) {
    sendMessage(worry);
    document.getElementById('worry-buttons').style.display = 'none';
}

function selectQuestion(question) {
    sendMessage(question);
}

// Function to handle self-pay transition
function goToSelfPay() {
    // Store user ID in session storage
    sessionStorage.setItem('user_id', userId);
    
    // Redirect to self-pay form
    window.location.href = '/self_pay?user_id=' + userId;
}

// When page loads, send empty message to get initial greeting
window.onload = function() {
    hideAllButtons();
    sendMessage('');
}

// Add enter key handler for input
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const message = this.value.trim();
        if (message) {
            sendMessage(message);
        }
    }
});