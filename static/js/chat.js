// Generate or retrieve a persistent user ID
let userId;
if (sessionStorage.getItem('userId')) {
    userId = sessionStorage.getItem('userId');
} else {
    userId = 'user-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('userId', userId);
}

// Add current_step variable to track chat state
let current_step = sessionStorage.getItem('current_step') || 'initial';

function sendMessage(message = '') {
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
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({ 
            message: message,
            user_id: userId 
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Check for error in response
        if (data.error) {
            throw new Error(data.error);
        }

        // Add bot message to chat
        addMessageToChat('bot', data.response);
        
        // Process response after a short delay to ensure message is displayed
        setTimeout(() => {
            const responseText = data.response.toLowerCase();
            
            // Always show question buttons in chat mode
            if (current_step === 'chat') {
                showButtons('question-buttons');
                document.getElementById('user-input').placeholder = '輸入您的問題...';
                return;
            }
            
            // Show question buttons after summary
            if (responseText.includes('關於麻醉的問題') && responseText.includes('資訊摘要')) {
                current_step = 'chat';
                sessionStorage.setItem('current_step', current_step);
                showButtons('question-buttons');
                document.getElementById('user-input').placeholder = '輸入您的問題...';
                return;
            }
            
            // Show sex buttons when asking about gender
            if (responseText.includes('性別是') || responseText.includes('男/女')) {
                showButtons('sex-buttons');
                return;
            }

            // Show CFS buttons when asking about independence
            if (responseText.includes('自行外出') && responseText.includes('是/否')) {
                showButtons('cfs-buttons');
                return;
            }

            // Show medical history buttons when asking about medical history
            if ((responseText.includes('病史') || responseText.includes('慢性病')) && 
                !responseText.includes('資訊摘要')) {
                showButtons('medical-history-buttons');
                document.getElementById('user-input').placeholder = '或直接輸入您的病史...';
                return;
            }

            // Show worry buttons when asking about concerns
            if (responseText.includes('擔心什麼') && !responseText.includes('資訊摘要')) {
                showButtons('worry-buttons');
                document.getElementById('user-input').placeholder = '或直接輸入您的擔憂...';
                return;
            }

            // Show text input by default
            showTextInput();
        }, 100);
    })
    .catch(error => {
        console.error('Error:', error);
        // Only show error message for actual errors, not for session resets
        if (!error.message.includes('session')) {
            addMessageToChat('bot', '抱歉，發生錯誤。請稍後再試。');
            showTextInput();
        }
    });
}

function selectQuestion(question) {
    // Ensure we're in chat mode
    current_step = 'chat';
    sessionStorage.setItem('current_step', current_step);
    
    // Hide buttons before sending message
    hideAllButtons();
    
    // Send the question
    sendMessage(question);
}

function hideAllButtons() {
    const buttonGroups = [
        'sex-buttons',
        'cfs-buttons',
        'medical-history-buttons',
        'worry-buttons',
        'question-buttons'
    ];
    
    buttonGroups.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'none';
        }
    });
}

function showButtons(buttonId) {
    // First hide everything
    hideAllButtons();
    hideTextInput();
    
    // Then show the specific button group
    const buttonGroup = document.getElementById(buttonId);
    if (buttonGroup) {
        buttonGroup.style.display = 'flex';
        // Scroll to bottom after showing buttons
        scrollToBottom();
    }
}

function showTextInput() {
    // First hide all buttons
    hideAllButtons();
    
    // Then show text input
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.style.display = 'block';
        userInput.focus();
        // Scroll to bottom after showing input
        scrollToBottom();
    }
}

function hideTextInput() {
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.style.display = 'none';
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function selectSex(sex) {
    sendMessage(sex);
}

function selectCFS(answer) {
    sendMessage(answer);
}

function selectMedicalHistory(history) {
    sendMessage(history);
}

function selectWorry(worry) {
    sendMessage(worry);
}

function startNewPatient() {
    // Reset current_step
    current_step = 'initial';
    sessionStorage.setItem('current_step', current_step);
    
    // Clear chat messages
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<div class="message bot-message">您好！我是您的麻醉諮詢助手。為了提供您最適合的建議，請讓我先了解一些基本資訊。</div>';
    
    // Hide all buttons
    hideAllButtons();
    
    // Reset session via API
    fetch('/reset_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Send initial message to start conversation
        sendMessage('');
    })
    .catch(error => {
        console.error('Error:', error);
        addMessageToChat('bot', '抱歉，系統發生錯誤。請重新整理頁面後再試。');
    });
}

// Add CSS for icon button and sidebar header
const style = document.createElement('style');
style.textContent = `
.sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.sidebar-header h3 {
    margin: 0;
}

.icon-button {
    background: none;
    border: none;
    padding: 5px;
    cursor: pointer;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.3s;
}

.icon-button:hover {
    background-color: rgba(0, 0, 0, 0.1);
}

.icon-button .emoji {
    font-size: 16px;
}`;

document.head.appendChild(style);

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

function addMessageToChat(role, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    // Format message with API response indicator
    if (role === 'bot' && message.includes('API回應：')) {
        const [apiResponse, ...otherParts] = message.split('\n\n');
        const responseContent = apiResponse.replace('API回應：\n', '');
        const questionPrompt = otherParts.join('\n\n');
        
        messageDiv.innerHTML = `
            <div class="api-header">API回應：</div>
            <div class="api-content">${responseContent}</div>
            <div class="question-prompt">${questionPrompt}</div>
        `;
    } else {
        messageDiv.innerHTML = message;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add CSS for API response formatting
const apiStyle = document.createElement('style');
apiStyle.textContent = `
    .api-response {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .api-header {
        color: #2c3e50;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .api-content {
        white-space: pre-wrap;
        color: #34495e;
    }
    .question-prompt {
        color: #7f8c8d;
        font-style: italic;
        margin-top: 10px;
    }
`;
document.head.appendChild(apiStyle);