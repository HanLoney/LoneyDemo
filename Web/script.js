// 全局变量
let isVoiceEnabled = true;
let isTyping = false;
let currentAudio = null;

// DOM元素
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const voiceToggle = document.getElementById('voiceToggle');
const emojiBtn = document.getElementById('emojiBtn');
const emojiPanel = document.getElementById('emojiPanel');
const typingIndicator = document.getElementById('typingIndicator');
const charCount = document.getElementById('charCount');
const loadingOverlay = document.getElementById('loadingOverlay');
const audioPlayer = document.getElementById('audioPlayer');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateCharCount();
    messageInput.focus();
});

// 事件监听器初始化
function initializeEventListeners() {
    // 发送按钮点击
    sendBtn.addEventListener('click', sendMessage);
    
    // 输入框回车发送
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 输入框字符计数
    messageInput.addEventListener('input', updateCharCount);
    
    // 语音开关
    voiceToggle.addEventListener('click', toggleVoice);
    
    // 表情按钮
    emojiBtn.addEventListener('click', toggleEmojiPanel);
    
    // 表情选择
    document.querySelectorAll('.emoji').forEach(emoji => {
        emoji.addEventListener('click', function() {
            insertEmoji(this.dataset.emoji);
        });
    });
    
    // 点击其他地方关闭表情面板
    document.addEventListener('click', function(e) {
        if (!emojiPanel.contains(e.target) && !emojiBtn.contains(e.target)) {
            emojiPanel.style.display = 'none';
        }
    });
    
    // 音频播放结束事件
    audioPlayer.addEventListener('ended', function() {
        document.querySelectorAll('.play-voice-btn.playing').forEach(btn => {
            btn.classList.remove('playing');
            btn.innerHTML = '<i class="fas fa-play"></i>';
        });
    });
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;
    
    // 添加用户消息到界面
    addMessage(message, 'user');
    
    // 清空输入框
    messageInput.value = '';
    updateCharCount();
    
    // 显示打字指示器
    showTypingIndicator();
    
    try {
        // 发送到后端API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                voice_enabled: isVoiceEnabled
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 隐藏打字指示器
        hideTypingIndicator();
        
        if (data.success) {
            // 添加AI回复到界面
            addMessage(data.reply, 'ai', data.audio_file);
        } else {
            addMessage('呜呜，我好像出了一点小问题~ 稍后再试试吧', 'ai');
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        hideTypingIndicator();
        addMessage('网络连接出现问题，请检查后端服务是否启动~', 'ai');
    }
}

// 添加消息到聊天界面
function addMessage(content, sender, audioFile = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const currentTime = new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-bubble">
                    <p>${escapeHtml(content)}</p>
                    <div class="message-time">${currentTime}</div>
                </div>
            </div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
    } else {
        const voiceButton = audioFile ? `
            <button class="play-voice-btn" onclick="playVoice('${audioFile}', this)" title="播放语音">
                <i class="fas fa-play"></i>
            </button>
        ` : '';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-heart"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>${escapeHtml(content)}</p>
                    <div class="message-time">${currentTime}</div>
                </div>
                ${voiceButton}
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 播放语音
function playVoice(audioFile, button) {
    // 停止当前播放的音频
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
    
    // 重置所有播放按钮状态
    document.querySelectorAll('.play-voice-btn.playing').forEach(btn => {
        btn.classList.remove('playing');
        btn.innerHTML = '<i class="fas fa-play"></i>';
    });
    
    // 设置新的音频
    audioPlayer.src = `/api/audio/${audioFile}`;
    currentAudio = audioPlayer;
    
    // 更新按钮状态
    button.classList.add('playing');
    button.innerHTML = '<i class="fas fa-pause"></i>';
    
    // 播放音频
    audioPlayer.play().catch(error => {
        console.error('音频播放失败:', error);
        button.classList.remove('playing');
        button.innerHTML = '<i class="fas fa-play"></i>';
        showNotification('音频播放失败，请检查文件是否存在');
    });
}

// 显示打字指示器
function showTypingIndicator() {
    isTyping = true;
    typingIndicator.style.display = 'inline-flex';
    sendBtn.disabled = true;
    scrollToBottom();
}

// 隐藏打字指示器
function hideTypingIndicator() {
    isTyping = false;
    typingIndicator.style.display = 'none';
    sendBtn.disabled = false;
}

// 切换语音功能
function toggleVoice() {
    isVoiceEnabled = !isVoiceEnabled;
    voiceToggle.classList.toggle('active', isVoiceEnabled);
    
    if (isVoiceEnabled) {
        voiceToggle.innerHTML = '<i class="fas fa-volume-up"></i>';
        showNotification('语音功能已开启 🔊');
    } else {
        voiceToggle.innerHTML = '<i class="fas fa-volume-mute"></i>';
        showNotification('语音功能已关闭 🔇');
    }
}

// 切换表情面板
function toggleEmojiPanel() {
    const isVisible = emojiPanel.style.display === 'block';
    emojiPanel.style.display = isVisible ? 'none' : 'block';
}

// 插入表情
function insertEmoji(emoji) {
    const cursorPos = messageInput.selectionStart;
    const textBefore = messageInput.value.substring(0, cursorPos);
    const textAfter = messageInput.value.substring(messageInput.selectionEnd);
    
    messageInput.value = textBefore + emoji + textAfter;
    messageInput.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
    messageInput.focus();
    
    updateCharCount();
    emojiPanel.style.display = 'none';
}

// 更新字符计数
function updateCharCount() {
    const count = messageInput.value.length;
    charCount.textContent = `${count}/500`;
    
    if (count > 450) {
        charCount.style.color = '#ff6b6b';
    } else {
        charCount.style.color = '#666';
    }
    
    sendBtn.disabled = count === 0 || count > 500 || isTyping;
}

// 滚动到底部
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示通知
function showNotification(message) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #ff9a9e, #fecfef);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        z-index: 3000;
        animation: slideInRight 0.3s ease;
        font-size: 14px;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// 错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
    showNotification('页面出现错误，请刷新重试');
});

// 网络状态检测
window.addEventListener('online', function() {
    showNotification('网络连接已恢复 🌐');
});

window.addEventListener('offline', function() {
    showNotification('网络连接已断开 📡');
});