<template>
  <div class="card chat-card">
    <div class="user-info-header">
      <div class="user-avatar">
        <img src="@/assets/head.png" alt="用户头像" class="avatar-img">
      </div>
      <h3 class="card-title">对话记录</h3>
    </div>
    <div class="chat-container" ref="chatContainer">
      <!-- 显示最近5条消息 -->
      <div v-if="latestMessages.length > 0">
        <div v-for="(message, index) in latestMessages" :key="'latest-'+index" 
             :class="['message', message.sender]">
          <div v-if="message.sender === 'ai'" class="message-header">
            <div class="ai-avatar">
              <span class="ai-icon">🤖</span>
            </div>
            <span class="sender-name">AI 助手</span>
          </div>
          <div v-else class="message-header">
            <div class="user-avatar-small">
              <img src="@/assets/head.png" alt="用户头像" class="avatar-img-small">
            </div>
          </div>
          <!-- 显示结构化消息（包含文本和/或图片） -->
          <template v-if="message.content">
            <!-- 文本内容 -->
            <p v-if="message.content.text" class="message-content">
              {{ message.content.text }}
            </p>
            <!-- 图片内容 -->
            <img 
              v-if="message.content.image_path" 
              :src="message.content.image_path" 
              class="message-image" 
              alt="上传的图片"
              @error="handleImageError">
          </template>
        </div>
      </div>
      
      <!-- 显示当前对话消息 -->
      <div v-for="(message, index) in messages" :key="'current-'+index" 
           :class="['message', message.sender]">
        <div v-if="message.sender === 'ai'" class="message-header">
          <div class="ai-avatar">
            <span class="ai-icon">🤖</span>
          </div>
          <span class="sender-name">AI 助手</span>
        </div>
        <div v-else class="message-header">
          <div class="user-avatar-small">
            <img src="@/assets/head.png" alt="用户头像" class="avatar-img-small">
          </div>
        </div>
        <p class="message-content">{{ message.content }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { chatAPI } from '../services/api';

export default {
  name: 'ChatCard',
  props: {
    messages: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      latestMessages: [],
      isLoading: false
    }
  },
  watch: {
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      },
      deep: true
    }
  },
  async mounted() {
    this.scrollToBottom();
    await this.loadLatestMessages();
  },
  methods: {
    isValidMessageContent(content) {
      if (!content) return false;
      if (typeof content === 'object') {
        return content.text || content.image_path;
      }
      if (typeof content === 'string') {
        try {
          const fixedContent = content.replace(/'/g, '"');
          const parsed = JSON.parse(fixedContent);
          return parsed.text || parsed.image_path;
        } catch (e) {
          return content.trim().length > 0;
        }
      }
      return false;
    },
    getMessageText(content) {
      if (!content) return '';
      if (typeof content === 'object') return content.text || '';
      if (typeof content === 'string') {
        try {
          const fixedContent = content.replace(/'/g, '"');
          const parsed = JSON.parse(fixedContent);
          return parsed.text || '';
        } catch (e) {
          return content;
        }
      }
      return '';
    },
    getMessageImagePath(content) {
      if (!content) return '';
      if (typeof content === 'object') return content.image_path || '';
      if (typeof content === 'string') {
        try {
          const fixedContent = content.replace(/'/g, '"');
          const parsed = JSON.parse(fixedContent);
          return parsed.image_path || '';
        } catch (e) {
          return '';
        }
      }
      return '';
    },
    scrollToBottom() {
      const container = this.$refs.chatContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
  async loadLatestMessages() {
      try {
        this.isLoading = true;
        const response = await chatAPI.getLatestMessages();
        console.log('API完整响应:', response); // 打印完整响应对象
        
        // 确保正确处理响应数据（使用response.data.history）
        if (response && response.data && Array.isArray(response.data.history)) {
          // 按时间戳升序排序（从旧到新）
          const sortedHistory = [...response.data.history].sort((a, b) => {
            const timeA = new Date(a.timestamp).getTime();
            const timeB = new Date(b.timestamp).getTime();
            return timeA - timeB;
          });
          
          this.latestMessages = sortedHistory.map(msg => {
            console.log('原始消息:', msg); // 打印完整消息对象
            
            // 处理消息内容
            let content = msg.content;
            let text = '';
            let imagePath = '';
            
            // 如果内容是JSON字符串（单引号或双引号）
            if (typeof content === 'string' && content.trim().startsWith('{')) {
              try {
                // 处理单引号JSON
                const fixedContent = content.replace(/'/g, '"');
                const parsed = JSON.parse(fixedContent);
                text = parsed.text || '';
                imagePath = parsed.image_path || '';
              } catch (e) {
                console.error('解析消息内容失败:', e);
                text = content; // 作为纯文本显示
              }
            } else if (typeof content === 'object') {
              // 如果已经是对象，直接使用
              text = content.text || '';
              imagePath = content.image_path || '';
            } else {
              // 纯文本消息
              text = content;
            }
            
            // 构造消息对象
            return {
              sender: msg.role === 'assistant' ? 'ai' : 'user',
              content: {
                text: text,
                image_path: imagePath
              },
              timestamp: msg.timestamp
            };
          });
        }
      } catch (error) {
        console.error('加载最新消息失败:', error);
      } finally {
        this.isLoading = false;
      }
    },
    
    // 图片加载错误处理
    handleImageError(event) {
      console.error('图片加载失败:', event);
      // 可以在这里添加默认图片或错误处理逻辑
      if (event.target) {
        event.target.style.display = 'none';
      }
    }
  }
}
</script>

<style scoped>
.card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 20px;
}

.chat-card {
  min-height: 400px;
}

.chat-container {
  max-height: 400px;
  min-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  margin-bottom: 12px;
}

.message.user {
  align-items: flex-end;
  margin-left: auto;
}

.message.ai {
  align-items: flex-start;
  margin-right: auto;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.message.user .message-header {
  flex-direction: row-reverse;
  justify-content: flex-end;
}

.message.ai .message-header {
  justify-content: flex-start;
}

.message-content {
  max-width: 100%;
  padding: 10px 14px;
  border-radius: 18px;
  word-break: break-word;
  line-height: 1.4;
}

.message.user .message-content {
  background: linear-gradient(135deg, #4A8EF1 0%, #3a7bd5 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  margin-left: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message.ai .message-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 18px 18px 18px 4px;
  margin-right: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 头像样式 */
.ai-avatar, .user-avatar-small {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 8px;
}

.ai-avatar {
  background: #1e40af;
  color: white;
}

.user-avatar-small img, .user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 确保用户消息头像在右侧 */
.message.user .message-header {
  flex-direction: row-reverse;
  margin-left: auto;
}

/* 确保AI消息头像在左侧 */
.message.ai .message-header {
  margin-right: auto;
}

.message.user .message-content {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
}

.message.ai .message-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px 16px 16px 4px;
  padding: 16px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.ai-avatar {
  width: 24px;
  height: 24px;
  background: #1e40af;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
}

.user-avatar-small {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img-small {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sender-name {
  font-size: 12px;
  color: #6b7280;
}

.message-content, .message-text {
  font-size: 14px;
  line-height: 1.5;
  padding: 12px;
  word-break: break-word;
}

.message-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  margin: 8px 12px;
  object-fit: contain;
  display: block;
}

/* 基础消息样式 */
.message-content {
  padding: 10px 14px;
  border-radius: 18px;
  max-width: 75%;
  word-break: break-word;
  line-height: 1.4;
}

/* 用户消息样式 - 蓝色气泡 */
.message.user .message-content {
  background: linear-gradient(135deg, #4A8EF1 0%, #3a7bd5 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  margin-left: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* AI消息样式 - 白色气泡 */
.message.ai .message-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 18px 18px 18px 4px;
  margin-right: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 统一历史消息和最新消息样式 */
.latestMessages .message-content,
.messages .message-content {
  font-size: 15px;
}

/* 消息间距 */
.message {
  margin-bottom: 12px;
}

/* 消息容器样式 */
.chat-container {
  padding: 10px;
}

/* 移除冗余的历史消息类 */
.history-message {
  display: none; /* 暂时隐藏，因为我们统一使用latestMessages */
}
</style>