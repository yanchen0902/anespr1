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

// Function to manage the main option buttons container visibility after interaction
function hideOptionButtonsAfterInteraction() {
    const optionsWrapper = document.getElementById('option-buttons-container');
    if (!optionsWrapper) return;
    
    if (window.innerWidth <= 576) { // On mobile - hide the container
        optionsWrapper.style.display = 'none';
    } else { // On desktop - ensure the container is visible
        optionsWrapper.style.display = 'flex';
    }
}

// Add variables to store multiple selections
let selectedWorries = [];
let selectedMedicalHistory = [];

function resetButtonStates() {
    // Reset all button colors
    const allButtons = document.querySelectorAll('.option-button');
    allButtons.forEach(btn => {
        btn.style.backgroundColor = '';
        btn.style.color = '';
    });
    
    // Reset selection arrays
    selectedWorries = [];
    selectedMedicalHistory = [];
    
    // Remove any send selection buttons
    const sendButtons = document.querySelectorAll('.send-selections-button');
    sendButtons.forEach(btn => btn.remove());
}

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

    // Hide all individual button groups
    hideAllButtons();

    // Hide the main option buttons container on mobile
    hideOptionButtonsAfterInteraction();

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

            // Show operation buttons when asking about operation
            if (responseText.includes('什麼手術') && !responseText.includes('資訊摘要')) {
                showButtons('operation-buttons');
                document.getElementById('user-input').placeholder = '請選擇或輸入手術類型...';
                return;
            }

            // Show fracture options when asking about fracture location
            if (responseText.includes('骨折位置') && !responseText.includes('資訊摘要')) {
                showButtons('fracture-options');
                document.getElementById('user-input').placeholder = '請選擇骨折位置...';
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
        'operation-buttons',
        'fracture-options',
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
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
}

function selectSex(sex) {
    sendMessage(sex);
}

function selectCFS(answer) {
    sendMessage(answer);
}

function selectMedicalHistory(history) {
    const button = event.currentTarget;
    if (history === '沒有') {
        // If "沒有" is selected, clear all other selections
        selectedMedicalHistory = ['沒有'];
        // Reset all button styles except the current one
        const buttons = document.querySelectorAll('#medical-history-buttons .option-button');
        buttons.forEach(btn => {
            btn.style.backgroundColor = '';
            btn.style.color = '';
        });
        button.style.backgroundColor = '#007bff';
        button.style.color = 'white';
        // Send immediately when "沒有" is selected
        sendMessage('沒有');
    } else {
        // Remove "沒有" if it exists when selecting other conditions
        const index = selectedMedicalHistory.indexOf('沒有');
        if (index > -1) {
            selectedMedicalHistory.splice(index, 1);
            // Reset "沒有" button style
            const noHistoryBtn = document.querySelector('#medical-history-buttons .option-button:first-child');
            if (noHistoryBtn) {
                noHistoryBtn.style.backgroundColor = '';
                noHistoryBtn.style.color = '';
            }
        }
        
        // Toggle selection
        const index2 = selectedMedicalHistory.indexOf(history);
        if (index2 > -1) {
            selectedMedicalHistory.splice(index2, 1);
            button.style.backgroundColor = '';
            button.style.color = '';
        } else {
            selectedMedicalHistory.push(history);
            button.style.backgroundColor = '#007bff';
            button.style.color = 'white';
        }
    }
    
    // Add send button if not exists
    addSendButtonIfNeeded('medical-history-buttons', selectedMedicalHistory);
}

function selectWorry(worry) {
    const button = event.currentTarget;
    if (worry === '沒有特別擔心') {
        // If "沒有特別擔心" is selected, clear all other selections
        selectedWorries = ['沒有特別擔心'];
        // Reset all button styles except the current one
        const buttons = document.querySelectorAll('#worry-buttons .option-button');
        buttons.forEach(btn => {
            btn.style.backgroundColor = '';
            btn.style.color = '';
        });
        button.style.backgroundColor = '#007bff';
        button.style.color = 'white';
        // Send immediately when "沒有特別擔心" is selected
        sendMessage('沒有特別擔心');
    } else {
        // Remove "沒有特別擔心" if it exists when selecting other worries
        const index = selectedWorries.indexOf('沒有特別擔心');
        if (index > -1) {
            selectedWorries.splice(index, 1);
            // Reset "沒有特別擔心" button style
            const noWorryBtn = document.querySelector('#worry-buttons .option-button:last-child');
            if (noWorryBtn) {
                noWorryBtn.style.backgroundColor = '';
                noWorryBtn.style.color = '';
            }
        }
        
        // Toggle selection
        const index2 = selectedWorries.indexOf(worry);
        if (index2 > -1) {
            selectedWorries.splice(index2, 1);
            button.style.backgroundColor = '';
            button.style.color = '';
        } else {
            selectedWorries.push(worry);
            button.style.backgroundColor = '#007bff';
            button.style.color = 'white';
        }
    }
    
    // Add send button if not exists
    addSendButtonIfNeeded('worry-buttons', selectedWorries);
}

function selectFractureLocation(location) {
    // Hide fracture options
    document.getElementById('fracture-options').style.display = 'none';
    
    // Send the selected fracture location
    sendMessage(location);
}

function addSendButtonIfNeeded(containerId, selectedItems) {
    const container = document.getElementById(containerId);
    let sendButton = container.querySelector('.send-selections-button');
    
    if (selectedItems.length > 0 && !sendButton) {
        sendButton = document.createElement('button');
        sendButton.className = 'send-selections-button option-button';
        sendButton.innerHTML = '<span class="emoji">✉️</span> 送出選擇';
        sendButton.onclick = () => {
            let message = selectedItems.join('、');
            
            // Check for additional text input for medical history
            if (containerId === 'medical-history-buttons') {
                const userInputField = document.getElementById('user-input');
                if (userInputField && userInputField.value.trim()) {
                    // Add text input to the message if it exists
                    message += '、' + userInputField.value.trim();
                    userInputField.value = ''; // Clear the input field
                }
                selectedMedicalHistory = [];
            } else {
                selectedWorries = [];
            }
            
            // Send message and remove send button
            sendMessage(message);
            sendButton.remove();
        };
        container.appendChild(sendButton);
    } else if (selectedItems.length === 0 && sendButton) {
        sendButton.remove();
    }
}

function selectOperation(operation) {
    sendMessage(operation);
}

function handleSendButton() {
    const userInputField = document.getElementById('user-input');
    const userInputValue = userInputField ? userInputField.value.trim() : '';
    
    // Check if we're in medical history selection mode and have selections
    if (document.getElementById('medical-history-buttons').style.display === 'flex' && selectedMedicalHistory.length > 0) {
        let message = selectedMedicalHistory.join('、');
        
        // Add text input to the message if it exists
        if (userInputValue) {
            message += '、' + userInputValue;
            userInputField.value = ''; // Clear the input field
        }
        
        // Send message and reset selections
        sendMessage(message);
        selectedMedicalHistory = [];
        resetButtonStates();
        return;
    }
    
    // Check if we're in worries selection mode and have selections
    if (document.getElementById('worry-buttons').style.display === 'flex' && selectedWorries.length > 0) {
        let message = selectedWorries.join('、');
        
        // Add text input to the message if it exists
        if (userInputValue) {
            message += '、' + userInputValue;
            userInputField.value = ''; // Clear the input field
        }
        
        // Send message and reset selections
        sendMessage(message);
        selectedWorries = [];
        resetButtonStates();
        return;
    }
    
    // Default behavior - just send the text input
    sendMessage(userInputValue);
}

function startNewPatient() {
    // Reload the page to the root.
    // This will trigger the '/' route on the backend, which should call session.clear(),
    // ensuring a full server-side and client-side reset.
    // The backend's @app.before_request will then set up a fresh session state.
    window.location.href = '/';
}

function showWorryButtons() {
    document.getElementById('operation-buttons').style.display = 'none';
    document.getElementById('fracture-options').style.display = 'none';
    document.getElementById('worry-buttons').style.display = 'block';
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
    // Reset all button states
    resetButtonStates();
    
    // Add a small delay to ensure session sync has completed
    setTimeout(() => {
        // Get the freshest current_step from sessionStorage
        const freshCurrentStep = sessionStorage.getItem('current_step') || 'initial';
        console.log('window.onload: current_step from sessionStorage =', freshCurrentStep);
        
        // Send empty message to get initial greeting if this is a new session
        if (freshCurrentStep === 'initial') {
            console.log('Starting new conversation with initial greeting');
            sendMessage();
        }
    }, 100); // Small delay to ensure session sync completes first
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
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    // Check if message contains HTML tags (from backend markdown conversion)
    const hasHTMLTags = /<[^>]+>/.test(message);

    if (hasHTMLTags) {
        // Message is already HTML formatted - use it directly without converting \n to <br>
        messageDiv.innerHTML = message;
    } else {
        // Plain text message - convert newlines to <br> for proper display
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    }

    // Add touch event for message actions (if needed)
    messageDiv.addEventListener('touchstart', function(e) {
        // Prevent text selection on long press
        e.preventDefault();
    }, { passive: false });

    chatMessages.appendChild(messageDiv);
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

// Add touch event listeners for better touch feedback
document.addEventListener('DOMContentLoaded', function() {
    // Add touch feedback for all buttons
    const buttons = document.querySelectorAll('button, .button, .option-button');
    buttons.forEach(button => {
        // Add touch feedback class on touch start
        button.addEventListener('touchstart', function() {
            this.classList.add('touch-feedback');
        }, { passive: true });
        
        // Remove touch feedback after a short delay
        button.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-feedback');
            }, 150);
        }, { passive: true });
        
        // Remove touch feedback if touch moves away
        button.addEventListener('touchmove', function(e) {
            const touch = e.touches[0];
            const rect = this.getBoundingClientRect();
            if (touch.clientX < rect.left || touch.clientX > rect.right || 
                touch.clientY < rect.top || touch.clientY > rect.bottom) {
                this.classList.remove('touch-feedback');
            }
        }, { passive: true });
    });
    
    // Prevent zoom on double-tap
    let lastTouchTime = 0;
    document.addEventListener('touchend', function(event) {
        const currentTime = new Date().getTime();
        if (currentTime - lastTouchTime < 300) {
            event.preventDefault();
        }
        lastTouchTime = currentTime;
    }, { passive: false });
    
    // Improve scrolling in chat messages
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.addEventListener('touchstart', function() {
            this.style.overflowY = 'auto';
            this.style.webkitOverflowScrolling = 'touch';
        }, { passive: true });
    }
    
    // Fix for iOS viewport height issue
    function updateViewportHeight() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    // Update on load and orientation change
    updateViewportHeight();
    window.addEventListener('resize', updateViewportHeight);
    window.addEventListener('orientationchange', updateViewportHeight);
});

// Add CSS for touch feedback
const touchFeedbackStyle = document.createElement('style');
touchFeedbackStyle.textContent = `
    .touch-feedback {
        opacity: 0.7;
        transform: scale(0.98);
        transition: opacity 0.1s, transform 0.1s;
    }
    
    /* Prevent text selection on tap */
    button, .button, .option-button {
        -webkit-tap-highlight-color: rgba(0,0,0,0.1);
        -webkit-touch-callout: none;
        user-select: none;
    }
    
    /* Smooth scrolling */
    #chat-messages {
        -webkit-overflow-scrolling: touch;
        scroll-behavior: smooth;
    }
`;
document.head.appendChild(touchFeedbackStyle);