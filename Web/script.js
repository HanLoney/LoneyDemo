// 全局变量
let isVoiceEnabled = true;
let isTyping = false;
let currentAudio = null;
let isDevModeEnabled = true;
let isDevPanelVisible = false;
let debugStats = {
    totalConversations: 0,
    responseTimes: [],
    voiceSuccessCount: 0,
    voiceTotalCount: 0
};

// 当前AI情感状态
let currentAIEmotion = {
    primary_emotion: '中性',
    intensity: 0.5,
    stability: 0.7,
    recent_changes: '初始状态',
    emotions: {
        happy: 50,
        sad: 10,
        angry: 10,
        fear: 10,
        surprise: 10,
        disgust: 10,
        neutral: 0,
        excited: 0,
        calm: 0,
        confused: 0
    }
};

// 情感历史记录
let emotionHistory = [];
const MAX_HISTORY_LENGTH = 10;

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

// 开发者面板相关元素
const devModeToggle = document.getElementById('devModeToggle');
const devPanel = document.getElementById('devPanel');
const devPanelClose = document.getElementById('devPanelClose');
const debugTabs = document.querySelectorAll('.debug-tab');
const debugSections = document.querySelectorAll('.debug-section');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateCharCount();
    messageInput.focus();
    
    // 开发者模式默认启用
    addDebugLog('info', '开发者模式已默认启用，调试信息将持续记录', 'overview');
    
    // 初始化AI情感状态显示
    updateAIEmotionDisplay();
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
    
    // 开发者模式切换
    devModeToggle.addEventListener('click', toggleDevMode);
    
    // 开发者面板关闭
    devPanelClose.addEventListener('click', closeDevPanel);
    
    // 调试标签切换
    debugTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            switchDebugTab(this.dataset.tab);
        });
    });
    
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
    
    // 记录开始时间
    const startTime = Date.now();
    
    // 添加用户消息到界面
    addMessage(message, 'user');
    
    // 清空输入框
    messageInput.value = '';
    updateCharCount();
    
    // 显示打字指示器
    showTypingIndicator();
    
    // 开发者模式日志
    if (isDevModeEnabled) {
        addDebugLog('info', `用户发送消息: "${message}"`, 'overview');
    }
    
    try {
        // 发送到后端API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                voice_enabled: isVoiceEnabled,
                debug_mode: isDevModeEnabled
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 计算响应时间
        const responseTime = Date.now() - startTime;
        debugStats.responseTimes.push(responseTime);
        debugStats.totalConversations++;
        
        // 隐藏打字指示器
        hideTypingIndicator();
        
        if (data.success) {
            // 添加AI回复到界面
            addMessage(data.reply, 'ai', data.audio_id, data.has_audio);
            
            // 处理调试信息（无论是否开启开发者模式）
            if (data.debug_info) {
                const debug = data.debug_info;
                
                // 更新AI情感状态（始终执行）
                if (debug.emotion_info) {
                    updateAIEmotionFromAnalysis(debug.emotion_info);
                }
            }
            
            // 开发者模式日志
            if (isDevModeEnabled) {
                addDebugLog('success', `AI回复完成，耗时: ${responseTime}ms`, 'overview');
                
                // 记录调试信息
                if (data.debug_info) {
                    const debug = data.debug_info;
                    
                    // LLM调用信息
                    if (debug.llm_info) {
                        logLLMCall(debug.llm_info.prompt || message, data.reply, debug.llm_info.duration || 0);
                    }
                    
                    // 情感分析信息
                    if (debug.emotion_info) {
                        logEmotionAnalysis(debug.emotion_info);
                    }
                    
                    // 时间分析信息
                    if (debug.time_info) {
                        logTimeAnalysis(message, debug.time_info);
                    }
                    
                    // 语音合成信息
                    if (debug.voice_info) {
                        logVoiceSynthesis(data.reply, debug.voice_info.success, data.audio_id);
                    }
                }
                
                updateDebugStats();
            }
        } else {
            addMessage(data.reply || '呜呜，我好像出了一点小问题~ 稍后再试试吧', 'ai');
            if (isDevModeEnabled) {
                addDebugLog('error', `API调用失败: ${data.reply || '未知错误'}`, 'overview');
            }
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        hideTypingIndicator();
        addMessage('网络连接出现问题，请检查后端服务是否启动~', 'ai');
        
        if (isDevModeEnabled) {
            addDebugLog('error', `网络错误: ${error.message}`, 'overview');
        }
    }
}

// 添加消息到聊天界面
function addMessage(content, sender, audioId = null, hasAudio = false) {
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
        const voiceButton = (hasAudio && audioId) ? `
            <button class="play-voice-btn" onclick="playVoice('${audioId}', this)" title="播放语音">
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
function playVoice(audioId, button) {
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
    audioPlayer.src = `/api/audio/${audioId}`;
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

// 开发者面板功能函数
function toggleDevMode() {
    isDevPanelVisible = !isDevPanelVisible;
    
    if (isDevPanelVisible) {
        devModeToggle.classList.add('active');
        devPanel.style.display = 'flex';
        addDebugLog('info', '开发者面板已打开', 'overview');
        updateDebugStats();
    } else {
        devModeToggle.classList.remove('active');
        devPanel.style.display = 'none';
        addDebugLog('info', '开发者面板已关闭', 'overview');
    }
}

function closeDevPanel() {
    isDevPanelVisible = false;
    devModeToggle.classList.remove('active');
    devPanel.style.display = 'none';
}

function switchDebugTab(tabName) {
    // 移除所有活动状态
    debugTabs.forEach(tab => tab.classList.remove('active'));
    debugSections.forEach(section => section.classList.remove('active'));
    
    // 激活选中的标签和内容
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`debug-${tabName}`).classList.add('active');
}

function addDebugLog(type, message, category = 'overview') {
    if (!isDevModeEnabled) return;
    
    const timestamp = new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <div class="log-timestamp">[${timestamp}]</div>
        <div class="log-content">${escapeHtml(message)}</div>
    `;
    
    const logContainer = document.getElementById(`${category}Log`);
    if (logContainer) {
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

function updateDebugStats() {
    if (!isDevModeEnabled) return;
    
    // 更新总对话轮次
    document.getElementById('totalConversations').textContent = debugStats.totalConversations;
    
    // 计算平均响应时间
    const avgTime = debugStats.responseTimes.length > 0 
        ? Math.round(debugStats.responseTimes.reduce((a, b) => a + b, 0) / debugStats.responseTimes.length)
        : 0;
    document.getElementById('avgResponseTime').textContent = `${avgTime}ms`;
    
    // 计算语音合成成功率
    const successRate = debugStats.voiceTotalCount > 0 
        ? Math.round((debugStats.voiceSuccessCount / debugStats.voiceTotalCount) * 100)
        : 0;
    document.getElementById('voiceSuccessRate').textContent = `${successRate}%`;
}

function logLLMCall(prompt, response, duration) {
    if (!isDevModeEnabled) return;
    
    const message = `LLM调用完成
提示词长度: ${prompt.length} 字符
响应长度: ${response.length} 字符
耗时: ${duration}ms`;
    
    addDebugLog('success', message, 'llm');
}

function logEmotionAnalysis(emotionInfo) {
    if (!isDevModeEnabled || !emotionInfo) return;
    
    if (emotionInfo.success) {
        // 用户情感分析
        if (emotionInfo.user_emotion) {
            const userEmotion = emotionInfo.user_emotion;
            const userMessage = `👤 用户情感分析
文本: "${userEmotion.text.substring(0, 50)}${userEmotion.text.length > 50 ? '...' : ''}"
主要情感: ${userEmotion.primary_emotion}
置信度: ${(userEmotion.confidence * 100).toFixed(1)}%
情感分数: ${userEmotion.sentiment_score.toFixed(2)}
检测到的情感: ${Object.entries(userEmotion.detected_emotions).map(([k, v]) => `${k}(${(v * 100).toFixed(1)}%)`).join(', ')}
分析耗时: ${userEmotion.analysis_time.toFixed(2)}ms`;
            
            addDebugLog('info', userMessage, 'emotion');
        }
        
        // AI情感分析
        if (emotionInfo.ai_emotion) {
            const aiEmotion = emotionInfo.ai_emotion;
            const aiMessage = `🤖 AI情感分析
文本: "${aiEmotion.text.substring(0, 50)}${aiEmotion.text.length > 50 ? '...' : ''}"
主要情感: ${aiEmotion.primary_emotion}
置信度: ${(aiEmotion.confidence * 100).toFixed(1)}%
情感分数: ${aiEmotion.sentiment_score.toFixed(2)}
检测到的情感: ${Object.entries(aiEmotion.detected_emotions).map(([k, v]) => `${k}(${(v * 100).toFixed(1)}%)`).join(', ')}
分析耗时: ${aiEmotion.analysis_time.toFixed(2)}ms`;
            
            addDebugLog('info', aiMessage, 'emotion');
        }
        
        // 当前情感状态
        if (emotionInfo.current_state) {
            const currentState = emotionInfo.current_state;
            const stateMessage = `📊 当前情感状态
主要情感: ${currentState.primary_emotion}
强度: ${(currentState.intensity * 100).toFixed(1)}%
稳定性: ${(currentState.stability * 100).toFixed(1)}%
情感分布: ${Object.entries(currentState.emotions).map(([k, v]) => `${k}(${(v * 100).toFixed(1)}%)`).join(', ')}`;
            
            addDebugLog('info', stateMessage, 'emotion');
        }
        
        // 统计信息
        if (emotionInfo.statistics && Object.keys(emotionInfo.statistics).length > 0) {
            const statsMessage = `📈 情感统计
${Object.entries(emotionInfo.statistics).map(([k, v]) => `${k}: ${v}`).join('\n')}`;
            
            addDebugLog('info', statsMessage, 'emotion');
        }
        
        addDebugLog('success', `情感分析完成，总耗时: ${emotionInfo.duration}ms`, 'emotion');
        
        // 更新AI情感状态显示
        updateAIEmotionFromAnalysis(emotionInfo);
    } else {
        const errorMessage = `❌ 情感分析失败
错误信息: ${emotionInfo.error || '未知错误'}
用户文本: "${emotionInfo.user_emotion?.text || '未知'}"
AI回复: "${emotionInfo.ai_emotion?.text || '未知'}"`;
        
        addDebugLog('error', errorMessage, 'emotion');
    }
}

function logTimeAnalysis(text, timeInfo) {
    if (!isDevModeEnabled) return;
    
    const message = `时间分析结果
文本: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"
时间信息: ${JSON.stringify(timeInfo, null, 2)}`;
    
    addDebugLog('info', message, 'time');
}

function logVoiceSynthesis(text, success, audioId = null) {
    if (!isDevModeEnabled) return;
    
    debugStats.voiceTotalCount++;
    if (success) {
        debugStats.voiceSuccessCount++;
    }
    
    const message = `语音合成${success ? '成功' : '失败'}
文本: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"
${audioId ? `音频ID: ${audioId}` : ''}`;
    
    addDebugLog(success ? 'success' : 'error', message, 'voice');
    updateDebugStats();
}

// 更新AI情感状态显示
function updateAIEmotionDisplay() {
    // 更新当前情感
    const currentEmotionEl = document.getElementById('currentEmotion');
    if (currentEmotionEl) {
        currentEmotionEl.textContent = currentAIEmotion.primary_emotion;
    }
    
    // 更新强度
    const intensityEl = document.getElementById('emotionIntensity');
    if (intensityEl) {
        intensityEl.textContent = (currentAIEmotion.intensity * 100).toFixed(0) + '%';
    }
    
    // 更新稳定性
    const stabilityEl = document.getElementById('emotionStability');
    if (stabilityEl) {
        const stabilityText = currentAIEmotion.stability > 0.7 ? '稳定' : currentAIEmotion.stability > 0.4 ? '一般' : '不稳定';
        stabilityEl.textContent = stabilityText;
    }
    
    // 更新最近变化
    const changesEl = document.getElementById('recentChange');
    if (changesEl) {
        changesEl.textContent = currentAIEmotion.recent_changes;
    }
    
    // 更新情感分布图表
    Object.entries(currentAIEmotion.emotions).forEach(([emotion, percentage]) => {
        const fillEl = document.getElementById(`${emotion}Bar`);
        const percentEl = document.getElementById(`${emotion}Percent`);
        
        if (fillEl) {
            fillEl.style.width = percentage + '%';
        }
        
        if (percentEl) {
            percentEl.textContent = percentage + '%';
        }
    });
}

// 从情感分析结果更新AI情感状态
function updateAIEmotionFromAnalysis(emotionInfo) {
    if (!emotionInfo || !emotionInfo.success) return;
    
    // 记录之前的主要情感用于变化检测
    const previousEmotion = currentAIEmotion.primary_emotion;
    
    // 优先使用current_state数据（这是AI的实际情感状态）
    if (emotionInfo.current_state) {
        const currentState = emotionInfo.current_state;
        
        // 更新主要情感
        currentAIEmotion.primary_emotion = currentState.primary_emotion || '中性';
        
        // 更新强度
        currentAIEmotion.intensity = currentState.intensity || 0.5;
        
        // 更新稳定性
        currentAIEmotion.stability = currentState.stability || 0.7;
        
        // 更新情感分布
        if (currentState.emotions) {
            // 重置所有情感为0
            Object.keys(currentAIEmotion.emotions).forEach(emotion => {
                currentAIEmotion.emotions[emotion] = 0;
            });
            
            // 更新实际的情感分布
            Object.entries(currentState.emotions).forEach(([emotion, value]) => {
                if (currentAIEmotion.emotions.hasOwnProperty(emotion)) {
                    currentAIEmotion.emotions[emotion] = Math.round(value * 100);
                }
            });
        }
        
        // 检测情感变化
        const hasEmotionChanged = previousEmotion !== currentAIEmotion.primary_emotion;
        const hasIntensityChanged = Math.abs((emotionHistory.length > 0 ? emotionHistory[emotionHistory.length - 1].intensity : 0.5) - currentAIEmotion.intensity) > 0.1;
        
        if (hasEmotionChanged) {
            currentAIEmotion.recent_changes = `${previousEmotion} → ${currentAIEmotion.primary_emotion}`;
        } else if (hasIntensityChanged) {
            const intensityChange = currentAIEmotion.intensity > (emotionHistory.length > 0 ? emotionHistory[emotionHistory.length - 1].intensity : 0.5) ? '增强' : '减弱';
            currentAIEmotion.recent_changes = `${currentAIEmotion.primary_emotion}${intensityChange}`;
        } else if (emotionHistory.length === 0) {
            currentAIEmotion.recent_changes = '初始状态';
        } else {
            currentAIEmotion.recent_changes = '情感稳定';
        }
        
        // 添加到历史记录
        emotionHistory.push({
            primary_emotion: currentAIEmotion.primary_emotion,
            intensity: currentAIEmotion.intensity,
            timestamp: new Date().toISOString()
        });
        
        // 保持历史记录长度
        if (emotionHistory.length > MAX_HISTORY_LENGTH) {
            emotionHistory.shift();
        }
        
        // 更新显示
        updateAIEmotionDisplay();
    }
    // 如果没有current_state，尝试使用ai_emotion作为备选
    else if (emotionInfo.ai_emotion) {
        const aiEmotion = emotionInfo.ai_emotion;
        
        // 更新主要情感
        currentAIEmotion.primary_emotion = aiEmotion.primary_emotion || '中性';
        
        // 更新强度（基于置信度）
        currentAIEmotion.intensity = aiEmotion.confidence || 0.5;
        
        // 更新情感分布
        if (aiEmotion.detected_emotions) {
            // 重置所有情感为0
            Object.keys(currentAIEmotion.emotions).forEach(emotion => {
                currentAIEmotion.emotions[emotion] = 0;
            });
            
            Object.entries(aiEmotion.detected_emotions).forEach(([emotion, value]) => {
                if (currentAIEmotion.emotions.hasOwnProperty(emotion)) {
                    currentAIEmotion.emotions[emotion] = Math.round(value * 100);
                }
            });
        }
        
        // 检测情感变化
        const hasEmotionChanged = previousEmotion !== currentAIEmotion.primary_emotion;
        const hasIntensityChanged = Math.abs((emotionHistory.length > 0 ? emotionHistory[emotionHistory.length - 1].intensity : 0.5) - currentAIEmotion.intensity) > 0.1;
        
        if (hasEmotionChanged) {
            currentAIEmotion.recent_changes = `${previousEmotion} → ${currentAIEmotion.primary_emotion}`;
        } else if (hasIntensityChanged) {
            const intensityChange = currentAIEmotion.intensity > (emotionHistory.length > 0 ? emotionHistory[emotionHistory.length - 1].intensity : 0.5) ? '增强' : '减弱';
            currentAIEmotion.recent_changes = `${currentAIEmotion.primary_emotion}${intensityChange}`;
        } else if (emotionHistory.length === 0) {
            currentAIEmotion.recent_changes = '初始状态';
        } else {
            currentAIEmotion.recent_changes = '情感稳定';
        }
        
        // 添加到历史记录
        emotionHistory.push({
            primary_emotion: currentAIEmotion.primary_emotion,
            intensity: currentAIEmotion.intensity,
            timestamp: new Date().toISOString()
        });
        
        // 保持历史记录长度
        if (emotionHistory.length > MAX_HISTORY_LENGTH) {
            emotionHistory.shift();
        }
        
        // 计算稳定性（基于情感分布的方差）
        const emotionValues = Object.values(currentAIEmotion.emotions);
        const mean = emotionValues.reduce((a, b) => a + b, 0) / emotionValues.length;
        const variance = emotionValues.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / emotionValues.length;
        currentAIEmotion.stability = Math.max(0, Math.min(1, 1 - variance / 1000));
        
        // 更新显示
        updateAIEmotionDisplay();
    }
}