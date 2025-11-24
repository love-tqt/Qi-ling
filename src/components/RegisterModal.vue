<template>
  <div v-if="visible" class="modal-overlay" @click.self="closeModal">
    <div class="register-modal">
      <div class="modal-header">
        <h2>创建新账户 加入AI文物导览助手</h2>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <div class="input-group">
          <input 
            type="text" 
            v-model="username" 
            placeholder="用户名" 
            class="form-input"
          />
        </div>
        <div class="input-group">
          <input 
            type="email" 
            v-model="email" 
            placeholder="邮箱地址" 
            class="form-input"
          />
        </div>
        <div class="input-group">
          <input 
            type="password" 
            v-model="password" 
            placeholder="密码" 
            class="form-input"
          />
        </div>
        <div class="input-group">
          <input 
            type="password" 
            v-model="confirmPassword" 
            placeholder="确认密码" 
            class="form-input"
          />
        </div>
        <div class="agree-terms">
          <label>
            <input type="checkbox" v-model="agreeTerms" />
            <span>我已阅读并同意<a href="#">服务条款</a>和<a href="#">隐私政策</a></span>
          </label>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <button class="register-btn" @click="handleRegister" :disabled="isLoading || isSuccess">
          <span v-if="isLoading" class="loading-spinner"></span>
          <span v-else-if="isSuccess" class="success-check">✓</span>
          <span v-else>注册</span>
        </button>
        <p class="login-link">
          已有账户？<a href="#" @click.prevent="switchToLogin">立即登录</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { authAPI } from '../services/api';

export default {
  name: 'RegisterModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      agreeTerms: false,
      isLoading: false,
      isSuccess: false,
      errorMessage: ''
    }
  },
  methods: {
    closeModal() {
      this.$emit('close');
      this.resetForm();
    },
    resetForm() {
      this.username = '';
      this.email = '';
      this.password = '';
      this.confirmPassword = '';
      this.agreeTerms = false;
      this.errorMessage = '';
      this.isLoading = false;
    },
    async handleRegister() {
      if (!this.username || !this.email || !this.password || !this.confirmPassword) {
        this.errorMessage = '请填写所有必填字段';
        return;
      }
      
      if (this.password !== this.confirmPassword) {
        this.errorMessage = '两次输入的密码不一致';
        return;
      }
      
      if (!this.agreeTerms) {
        this.errorMessage = '请同意服务条款和隐私政策';
        return;
      }
      
      if (this.password.length < 6) {
        this.errorMessage = '密码长度至少6位';
        return;
      }
      
      if (!this.email.includes('@')) {
        this.errorMessage = '请输入有效的邮箱地址';
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';

      try {
        const userData = {
          username: this.username,
          email: this.email,
          password: this.password
        };

        const response = await authAPI.register(userData);
        
        if (response.data && response.data.success) {
          console.log('注册成功:', response);
          this.isSuccess = true;
          
          // 显示成功状态2秒后自动关闭
          setTimeout(() => {
            // 触发注册成功事件，自动切换到登录
            this.$emit('register-success', {
              username: this.username,
              email: this.email
            });
            
            this.closeModal();
          }, 2000);
        } else if (response.data && !response.data.success && response.data.message) {
          // 显示后端返回的具体错误信息
          this.errorMessage = response.data.message || '注册失败';
        } else {
          throw new Error('注册失败：未收到有效响应');
        }
      } catch (error) {
        console.error('注册失败:', error);
        this.errorMessage = error.message || '注册失败，请稍后重试';
      } finally {
        this.isLoading = false;
      }
    },
    switchToLogin() {
      this.$emit('switch-to-login');
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        document.body.style.overflow = 'hidden';
        this.resetForm();
      } else {
        document.body.style.overflow = '';
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.register-modal {
  width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.modal-header {
  background: #1e40af;
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 24px;
}

.input-group {
  margin-bottom: 16px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.agree-terms {
  margin-bottom: 20px;
}

.agree-terms label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  line-height: 1.4;
}

.agree-terms a {
  color: #1e40af;
  text-decoration: none;
}

.agree-terms a:hover {
  text-decoration: underline;
}

.agree-terms input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.error-message {
  color: #dc2626;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 16px;
  font-size: 14px;
}

.register-btn {
  width: 100%;
  padding: 12px;
  background: #1e40af;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.register-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.register-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

/* 加载动画 */
.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 成功对勾 */
.success-check {
  display: inline-block;
  font-weight: bold;
  font-size: 16px;
  color: #22c55e;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #6b7280;
}

.login-link a {
  color: #1e40af;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .register-modal {
    width: 90%;
    margin: 0 20px;
  }
  
  .modal-header h2 {
    font-size: 16px;
  }
}
</style>