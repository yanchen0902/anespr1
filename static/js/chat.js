// 生成唯一的用戶ID
const userId = 'user-' + Date.now();

function sendMessage(message = null) {
    if (!message.trim()) return;
    
    const userInput = document.getElementById('user-input');
    userInput.value = '';
    
    addMessageToChat('user', message);

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message, user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        addMessageToChat('bot', data.response);
        
        // Show sex buttons only when specifically asking for sex/gender
        if (data.response.toLowerCase().includes('性別')) {
            document.getElementById('sex-buttons').style.display = 'flex';
        } else {
            document.getElementById('sex-buttons').style.display = 'none';
        }

        // Show CFS buttons when asking about independence
        if (data.response.includes('您是否能夠自行外出')) {
            document.getElementById('cfs-buttons').style.display = 'flex';
        } else {
            document.getElementById('cfs-buttons').style.display = 'none';
        }

        // Show worry buttons when asking about concerns
        if (data.response.includes('您最擔心什麼') || 
            data.response.includes('有什麼擔心的地方')) {
            document.getElementById('worry-buttons').style.display = 'flex';
        } else {
            document.getElementById('worry-buttons').style.display = 'none';
        }

        // Show question buttons when appropriate
        if (data.response.includes('您可以問我關於麻醉的問題') && 
            !data.response.includes('可以點擊下方綠色按鈕')) {
            document.getElementById('question-buttons').style.display = 'flex';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessageToChat('bot', '抱歉，發生錯誤。請稍後再試。');
    });
}

function handleChatCompletion(response) {
    if (response.includes("諮詢結束")) {
        // Add a small delay before transition
        setTimeout(() => {
            const message = document.createElement('div');
            message.className = 'message bot-message';
            message.innerHTML = '感謝您的諮詢！現在為您導向自費項目選擇頁面...';
            document.getElementById('chat-messages').appendChild(message);
            
            // Scroll to the bottom
            message.scrollIntoView({ behavior: 'smooth' });
            
            // Redirect after showing message
            setTimeout(() => {
                window.location.href = '/self_pay';
            }, 2000);
        }, 1000);
    }
}

function selectSex(sex) {
    sendMessage(sex);
    document.getElementById('sex-buttons').style.display = 'none';
}

function selectCFS(answer) {
    sendMessage(answer);
    document.getElementById('cfs-buttons').style.display = 'none';
}

function selectWorry(worry) {
    sendMessage(worry);
    document.getElementById('worry-buttons').style.display = 'none';
}

function selectQuestion(question) {
    sendMessage(question);
}

function addMessageToChat(role, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    // Handle line breaks and format message
    if (typeof message === 'string') {
        const formattedMessage = message.replace(/\n/g, '<br>');
        messageDiv.innerHTML = formattedMessage;
    } else {
        messageDiv.innerHTML = message;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Show self-pay button after collecting basic information
    if (message.includes('可以點擊下方綠色按鈕進入自費項目選擇')) {
        document.getElementById('self-pay-button').style.display = 'flex';
        // Hide question buttons when showing self-pay button
        document.getElementById('question-buttons').style.display = 'none';
    }
}

// 當頁面載入時自動發送一個空消息來觸發首次問候語
window.onload = function() {
    sendMessage('');
};

document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});