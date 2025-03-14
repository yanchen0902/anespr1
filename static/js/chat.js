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

    // Hide all buttons before sending message
    hideAllButtons();

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
                document.getElementById('user-input').placeholder = '請輸入您的病史...';
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
    // Hide all buttons before sending question
    hideAllButtons();
    
    // Ensure we're in chat mode
    current_step = 'chat';
    sessionStorage.setItem('current_step', current_step);
    
    // Send the question
    sendMessage(question);
    
    // Show question buttons after a short delay
    setTimeout(() => {
        showButtons('question-buttons');
    }, 200);
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
            element.classList.remove('visible');
        }
    });
    
    // Show text input area by default
    const textInputArea = document.querySelector('.text-input-area');
    if (textInputArea) {
        textInputArea.style.display = 'flex';
    }
}

function showButtons(buttonId) {
    // First hide everything
    hideAllButtons();
    
    // Then show the specific button group
    const buttonGroup = document.getElementById(buttonId);
    if (buttonGroup) {
        buttonGroup.style.display = 'flex';
        buttonGroup.classList.add('visible');
        // Scroll to bottom after showing buttons
        scrollToBottom();
    }
}

function showTextInput() {
    // First hide all buttons
    hideAllButtons();
    
    // Then show text input
    const textInputArea = document.querySelector('.text-input-area');
    const userInput = document.getElementById('user-input');
    if (textInputArea && userInput) {
        textInputArea.style.display = 'flex';
        userInput.style.display = 'block';
        userInput.focus();
        // Scroll to bottom after showing input
        scrollToBottom();
    }
}

function hideTextInput() {
    const textInputArea = document.querySelector('.text-input-area');
    if (textInputArea) {
        textInputArea.style.display = 'none';
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
    // Clear session storage
    sessionStorage.clear();
    
    // Generate new user ID
    userId = 'user-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('userId', userId);
    
    // Reset current step
    current_step = 'initial';
    sessionStorage.setItem('current_step', current_step);
    
    // Clear chat messages
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.innerHTML = '<div class="message bot-message">您好！我是您的麻醉諮詢助手。\n為了提供您最適合的建議，請讓我先了解一些基本資訊。\n我們會謹慎保護您的個人資料，請放心告訴我。</div>';
    }
    
    // Hide all buttons
    hideAllButtons();
    
    // Show text input
    showTextInput();
    
    // Reset input placeholder
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.placeholder = '請在此輸入您的回答...';
    }
    
    // Send empty message to start new conversation
    sendMessage();
}

// Add CSS for icon button and sidebar header
const style = document.createElement('style');
style.textContent = `
.sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-bottom: 1px solid #ddd;
}

.icon-button {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 5px;
    border-radius: 50%;
    transition: background-color 0.3s;
}

.icon-button:hover {
    background-color: #f0f0f0;
}

.emoji {
    font-style: normal;
}
`;
document.head.appendChild(style);

function goToSelfPay() {
    // Save current chat state
    sessionStorage.setItem('current_step', current_step);
    
    // Redirect to self-pay page with user_id parameter
    window.location.href = '/self_pay?user_id=' + userId;
}

// When page loads, send empty message to get initial greeting
window.onload = function() {
    // Send empty message to get initial greeting if this is a new session
    if (current_step === 'initial') {
        sendMessage();
    }
};

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
    
    // Format API responses
    if (role === 'bot' && message.includes('API Response')) {
        messageDiv.classList.add('api-response');
    }
    
    // Convert markdown links to HTML
    message = message.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Convert newlines to <br> tags
    message = message.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = message;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
}

// Add CSS for API response formatting
const apiStyle = document.createElement('style');
apiStyle.textContent = `
    .api-response {
        background-color: #f8f9fa;
        border-left: 4px solid #17a2b8;
        padding: 10px;
        margin: 10px 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    
    .api-response code {
        background-color: #e9ecef;
        padding: 2px 4px;
        border-radius: 4px;
    }
`;
document.head.appendChild(apiStyle);