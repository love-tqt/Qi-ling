<template>
  <div class="card recognition-card">
    <h2 class="card-title">智能文物识别与问答</h2>
    
    <div class="recognition-content">
      <!-- 上传区域 -->
      <div class="upload-area">
        <el-upload
          ref="uploader"
          class="image-uploader"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          :action="uploadUrl"
          accept="image/*">
          <div class="upload-icon">
            <span class="icon-camera">📷</span>
          </div>
          <h3 class="upload-title">上传文物图片</h3>
          <p class="upload-desc">点击或拖拽图片到此处上传</p>
          <p class="upload-tips">支持 JPG、PNG、WEBP 格式，建议图片清晰度高于 1080p</p>
        </el-upload>
        <!-- 图片预览 -->
        <div v-if="uploadedImageUrl" class="image-preview">
          <img :src="uploadedImageUrl" alt="上传的图片" class="preview-image" />
          <button @click="clearImage" class="clear-image-btn">×</button>
        </div>
      </div>

      <div class="divider">
        <span class="divider-text">或</span>
      </div>

      <!-- 提问区域 -->
      <div class="question-area">
        <button class="voice-btn" @click="toggleVoiceRecording">
          <span class="voice-icon">🎤</span>
          <span>{{ isRecording ? '停止录音' : '语音提问' }}</span>
        </button>
        <div class="text-input-container">
          <el-input 
            v-model="questionText" 
            placeholder="输入您的问题，如：这是什么文物？它有什么历史背景？" 
            class="question-input"
            @keypress.enter="sendQuestion">
          </el-input>
          <el-button class="send-btn" @click="sendQuestion" type="primary" :disabled="isWaitingForReply">
            <i class="el-icon-send"></i> 发送
          </el-button>
        </div>
      </div>

      <!-- 等待回复提示 -->
      <div v-if="isWaitingForReply" class="waiting-indicator">
        <div class="loading-spinner"></div>
        <p class="waiting-text">正在等待AI回复...</p>
      </div>

      <!-- 快捷提问 -->
      <div class="quick-questions">
        <button v-for="(question, index) in quickQuestions" :key="index" 
                class="quick-question" @click="selectQuickQuestion(question)">
          {{ question }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { uploadAPI, voiceAPI, chatAPI } from '../services/api';

export default {
  name: 'RecognitionCard',
  data() {
    return {
      isRecording: false,
      questionText: '',
      uploadedImage: null, // 存储上传的图片文件对象
      uploadedImageUrl: null, // 存储图片的本地URL用于预览
      quickQuestions: [
        '这是什么文物？',
        '它的历史背景是？',
        '制作工艺如何？',
        '文化意义是什么？'
      ],
      uploadHeaders: {
        'X-User-ID': localStorage.getItem('user_id') || '',
        '__sid': localStorage.getItem('sessionId') || ''
      },
      uploadData: {
        fileid: this.generateFileId()
      },
      isWaitingForReply: false // 添加等待状态
    }
  },
  computed: {
    uploadUrl() {
      return 'http://localhost:8000/api/upload';
    }
  },
  methods: {
    // 生成文件ID
    generateFileId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // 上传前验证
    beforeUpload(file) {
      const isImage = file.type.startsWith('image/');
      const isLt10M = file.size / 1024 / 1024 < 10;
      
      if (!isImage) {
        this.$message.error('只能上传图片文件！');
        return false;
      }
      if (!isLt10M) {
        this.$message.error('图片大小不能超过 10MB!');
        return false;
      }
      
      // 更新文件ID
      this.uploadData.fileid = this.generateFileId();
      return true;
    },
    
    // 上传成功回调
    handleUploadSuccess(response, file, fileList) {
      console.log('上传成功：', response, file, fileList);
      
      if (response.status === 'success') {
        this.$emit('message', { 
          sender: 'ai', 
          content: response.ai_response 
        });
        
        // 保存图片URL到本地，供后续提问使用
        this.lastUploadedImageUrl = response.url;
      } else {
        this.$message.error(response.error || '上传失败');
      }
    },
    
    // 上传失败回调
    handleUploadError(error, file, fileList) {
      console.error('上传失败：', error, file, fileList);
      this.$message.error('图片上传失败，请重试');
    },
    
    // 文件选择变化处理
    handleFileChange(file, fileList) {
      console.log('文件选择变化:', file, fileList);
      // 检查是否已登录
      const userid = localStorage.getItem('userid');
      if (!userid) {
        // 未登录状态，显示登录提示
        window.dispatchEvent(new CustomEvent('auth-required', {
          detail: { message: '您还未登录，请先登录' }
        }));
        return false;
      }
      
      if (fileList.length > 0) {
        const selectedFile = fileList[0].raw;
        console.log('选择的文件:', selectedFile);
        if (selectedFile && selectedFile.type.startsWith('image/')) {
          // 先清除之前的图片状态
          this.clearImage();
          
          // 设置新的图片状态
          this.uploadedImage = selectedFile;
          // 创建本地URL用于预览
          this.uploadedImageUrl = URL.createObjectURL(selectedFile);
          console.log('设置新图片状态:', {
            uploadedImage: this.uploadedImage,
            uploadedImageUrl: this.uploadedImageUrl
          });
          this.$message.success('图片已选择，请在输入问题后点击发送');
        }
      }
    },
    
    // 清除已选图片
    clearImage() {
      console.log('清除图片前状态:', {
        uploadedImage: this.uploadedImage,
        uploadedImageUrl: this.uploadedImageUrl
      });
      
      // 1. 释放对象URL
      if (this.uploadedImageUrl) {
        URL.revokeObjectURL(this.uploadedImageUrl);
      }
      
      // 2. 重置所有图片相关状态
      this.uploadedImage = null;
      this.uploadedImageUrl = null;
      
      // 3. 强制清除el-upload组件的内部状态
      this.$nextTick(() => {
        const uploader = this.$refs.uploader;
        if (uploader && uploader.clearFiles) {
          uploader.clearFiles();
        }
      });
      
      console.log('清除图片后状态:', {
        uploadedImage: this.uploadedImage,
        uploadedImageUrl: this.uploadedImageUrl
      });
      
      // 4. 强制更新视图
      this.$forceUpdate();
    },
    
    // 上传进度回调
    handleUploadProgress(event, file, fileList) {
      console.log('上传进度：', event, file, fileList);
    },
    
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleDragOver(event) {
      event.currentTarget.classList.add('dragover');
    },
    handleDragLeave(event) {
      event.currentTarget.classList.remove('dragover');
    },
    handleDrop(event) {
      event.currentTarget.classList.remove('dragover');
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        this.handleFileUpload(files[0]);
      }
    },
    handleFileSelect(event) {
      if (event.target.files.length > 0) {
        this.handleFileUpload(event.target.files[0]);
      }
    },
    async handleFileUpload(file) {
      if (file.type.startsWith('image/')) {
        try {
          this.$emit('message', { sender: 'user', content: `已上传图片：${file.name}` });
          this.$emit('message', { sender: 'ai', content: '正在分析您上传的文物图片，请稍候...' });
          
          // 调用后端API上传文件并分析图片
          const result = await uploadAPI.uploadImage(file);
          
          if (result.status === 'success') {
            // 显示AI分析结果
            this.$emit('message', { 
              sender: 'ai', 
              content: result.ai_response 
            });
            
            // 保存图片URL到本地，供后续提问使用
            this.lastUploadedImageUrl = result.url;
            
            // 更新当前上传的图片状态
            this.uploadedImage = file;
            this.uploadedImageUrl = URL.createObjectURL(file);
          } else {
            throw new Error(result.error || '上传失败');
          }
        } catch (error) {
          console.error('文件上传失败:', error);
          this.$emit('message', { 
            sender: 'ai', 
            content: '抱歉，图片上传失败。请检查网络连接或稍后重试。' 
          });
        }
      } else {
        this.$emit('message', { 
          sender: 'ai', 
          content: '请上传图片文件（JPG、PNG、GIF等格式）' 
        });
      }
    },
    toggleVoiceRecording() {
      if (!this.isRecording) {
        this.startRecording();
      } else {
        this.stopRecording();
      }
    },
    async startRecording() {
      this.isRecording = true;
      
      try {
        // 模拟录音3秒
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 模拟语音识别结果
        const recognitionResult = await voiceAPI.recognizeSpeech(new File([], 'recording.wav'));
        
        if (recognitionResult.status === 'success') {
          const recognizedText = recognitionResult.text;
          this.$emit('message', { sender: 'user', content: recognizedText });
          
          // 发送识别到的文本到聊天API
          const chatResponse = await chatAPI.sendMessage(recognizedText);
          
          if (chatResponse.status === 'success') {
            this.$emit('message', { 
              sender: 'ai', 
              content: chatResponse.ai_response 
            });
          }
        }
      } catch (error) {
        console.error('语音识别失败:', error);
        this.$emit('message', { 
          sender: 'ai', 
          content: '语音识别失败，请重试或直接输入您的问题' 
        });
      } finally {
        this.stopRecording();
      }
    },
    stopRecording() {
      this.isRecording = false;
    },
    async sendQuestion() {
      // 检查是否已登录
      const userid = localStorage.getItem('userid');
      if (!userid) {
        // 未登录状态，显示登录提示
        window.dispatchEvent(new CustomEvent('auth-required', {
          detail: { message: '您还未登录，请先登录' }
        }));
        return;
      }
      
      const message = this.questionText.trim();
      if (!message) {
        console.log('⚠️ 消息为空，不发送请求');
        return;
      }
      
      try {
        // 设置等待状态
        this.isWaitingForReply = true;
        console.log('开始等待AI回复，isWaitingForReply:', this.isWaitingForReply);
        this.$emit('message', { sender: 'user', content: message });
        this.questionText = '';
        
        // 发送请求并等待响应
        const response = await chatAPI.sendMessage(message, this.uploadedImage);
        console.log('收到API响应:', response);
        
        // 验证响应数据 - API拦截器返回完整响应对象，使用 response.data.data.ai_response
        if (!response || !response.data || !response.data.success || !response.data.data || !response.data.data.ai_response) {
          console.error('无效的AI响应:', response);
          throw new Error('无效的AI响应');
        }
        
        // 添加AI响应
        this.$emit('message', { 
          sender: 'ai', 
          content: response.data.data.ai_response,
          timestamp: new Date().toISOString()
        });
        
        // 清除图片
        this.clearImage();
        
      } catch (error) {
        console.error('发送消息失败:', error);
        // 添加错误消息
        this.$emit('message', { 
          sender: 'ai', 
          content: `错误：${error.message || '发送消息失败'}`,
          timestamp: new Date().toISOString(),
          isError: true
        });
      } finally {
        this.isWaitingForReply = false;
        console.log('结束等待，isWaitingForReply:', this.isWaitingForReply);
        // 强制更新视图，确保等待状态立即更新
        this.$forceUpdate();
      }
    },
    selectQuickQuestion(question) {
      this.questionText = question;
      this.sendQuestion();
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

.recognition-card {
  margin-bottom: 24px;
}

.recognition-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-area {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.upload-area.dragover {
  border-color: #1d4ed8;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.upload-icon {
  width: 64px;
  height: 64px;
  background: #dbeafe;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 24px;
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.upload-desc {
  color: #6b7280;
  margin-bottom: 8px;
}

.upload-tips {
  color: #9ca3af;
  font-size: 12px;
}

.file-input {
  display: none;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

.divider-text {
  color: #6b7280;
  font-size: 12px;
}

.question-area {
  display: flex;
  gap: 12px;
  align-items: center;
}

.voice-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #059669;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.voice-btn:hover {
  background: #047857;
}

.voice-btn.recording {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.text-input-container {
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
}

.question-input {
  flex: 1;
}

.send-btn {
  height: 40px;
  white-space: nowrap;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-question {
  background: #f3f4f6;
  color: #6b7280;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.quick-question:hover {
  background: #e5e7eb;
  color: #374151;
}

/* 图片预览样式 */
.image-preview {
  position: relative;
  margin-top: 16px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
}

.clear-image-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.clear-image-btn:hover {
  background: #dc2626;
}

/* 等待回复指示器 */
.waiting-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.waiting-text {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

@media (max-width: 768px) {
  .question-area {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>