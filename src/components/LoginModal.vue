<template>
  <div v-if="visible" class="modal-overlay" @click.self="closeModal">
    <div class="login-modal">
      <div class="modal-header">
        <h2>欢迎回来 登录您的AI文物导览助手账户</h2>
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
            type="password" 
            v-model="password" 
            placeholder="密码" 
            class="form-input"
          />
        </div>
        <div class="remember-me">
          <label>
            <input type="checkbox" v-model="rememberMe" />
            <span>记住我</span>
          </label>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <button class="login-btn" @click="handleLogin" :disabled="isLoading || isSuccess">
          <span v-if="isLoading" class="loading-spinner"></span>
          <span v-else-if="isSuccess" class="success-check">✓</span>
          <span v-else>登录</span>
        </button>
        <p class="register-link">
          还没有账户？<a href="#" @click.prevent="switchToRegister">立即注册</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { authAPI } from '../services/api';

export default {
  name: 'LoginModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      username: '',
      password: '',
      rememberMe: false,
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
      this.password = '';
      this.rememberMe = false;
      this.errorMessage = '';
      this.isLoading = false;
      this.isSuccess = false;
    },
    async handleLogin() {
      if (!this.username || !this.password) {
        this.errorMessage = '请输入用户名和密码';
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';

      try {
        const credentials = {
          username: this.username,
          password: this.password
        };
        const response = await authAPI.login(credentials);
        
        if (response.data && response.data.success) {
          // 保存用户信息和过期时间
          const { userid, expires_at } = response.data.data;
          localStorage.setItem('userid', userid);
          localStorage.setItem('expires_at', expires_at);
          console.log('登录成功，用户信息已保存');
          
          this.isSuccess = true;
          
          // 显示成功状态1秒后自动关闭
          setTimeout(() => {
            // 触发登录成功事件
            this.$emit('login-success', {
              username: response.data.data.userid,
              userid: response.data.data.userid
            });
            
            this.closeModal();
            // 重新加载页面
            window.location.reload();
          }, 1000);
        } else if (response.data && !response.data.success && response.data.message) {
          // 显示后端返回的错误信息
          this.errorMessage = response.data.message || '登录失败';
        } else {
          throw new Error('登录失败：未收到有效响应');
        }
      } catch (error) {
        console.error('登录失败:', error);
        this.errorMessage = error.message || '登录失败，请检查用户名和密码';
      } finally {
        this.isLoading = false;
      }
    },
    switchToRegister() {
      this.$emit('switch-to-register');
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        // 模态框显示时，阻止背景滚动
        document.body.style.overflow = 'hidden';
        this.resetForm();
      } else {
        // 模态框隐藏时，恢复背景滚动
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

.login-modal {
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

.remember-me {
  margin-bottom: 20px;
}

.remember-me label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
}

.remember-me input[type="checkbox"] {
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

.login-btn {
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

.login-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.login-btn:disabled {
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

.register-link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #6b7280;
}

.register-link a {
  color: #1e40af;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .login-modal {
    width: 90%;
    margin: 0 20px;
  }
  
  .modal-header h2 {
    font-size: 16px;
  }
}
</style>