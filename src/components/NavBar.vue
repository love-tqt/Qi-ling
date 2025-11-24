<template>
  <nav class="nav-bar">
    <div class="nav-container">
      <div class="nav-left">
        <div class="logo">
          <div class="logo-icon">
            <span class="logo-text">AI</span>
          </div>
          <h1 class="logo-title">AI文物导览助手</h1>
        </div>
        <div class="nav-menu">
          <a href="#" class="nav-link active">首页</a>
          <a href="#" class="nav-link">文物识别</a>
          <a href="#" class="nav-link">知识库</a>
          <a href="#" class="nav-link">帮助中心</a>
        </div>
      </div>
      <div class="nav-right">
        <template v-if="isAuthenticated">
          <div class="user-info">
            <div class="user-avatar">
              <img src="@/assets/head.png" alt="用户头像" class="avatar-img">
            </div>
            <span class="username">{{ username }}</span>
          </div>
          
          <!-- 退出按钮 -->
          <button class="logout-btn" @click="handleLogout" title="退出登录">
            <span class="logout-icon">🚪</span>
          </button>
        </template>
        
        <template v-else>
          <button class="nav-btn login-btn" @click="$emit('show-login')">登录</button>
          <button class="nav-btn register-btn" @click="$emit('show-register')">注册</button>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavBar',
  props: {
    isAuthenticated: {
      type: Boolean,
      default: false
    },
    username: {
      type: String,
      default: ''
    }
  },
  data() {
    return {};
  },
  computed: {
    avatarInitial() {
      return this.username ? this.username.charAt(0).toUpperCase() : 'U';
    }
  },
  methods: {
    handleLogout() {
      // 清除所有相关本地存储
      localStorage.clear(); // 清除所有本地存储
      sessionStorage.clear(); // 清除所有会话存储
      
      // 清除cookie
      document.cookie.split(";").forEach(cookie => {
        const eqPos = cookie.indexOf("=");
        const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
      });
      
      // 触发全局登出事件
      window.dispatchEvent(new CustomEvent('auth-logout'));
      
      // 强制刷新页面以确保状态更新
      window.location.href = '/'; // 重定向到首页
    }
  }
}
</script>

<style scoped>
.nav-bar {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: #1e40af;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.logo-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  font-family: cursive;
}

.nav-menu {
  display: flex;
  gap: 24px;
}

.nav-link {
  color: #6b7280;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-link:hover,
.nav-link.active {
  color: #1e40af;
  background: #eff6ff;
}

.nav-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 20px;
  background: #f8fafc;
  transition: background-color 0.2s;
}

.user-info:hover {
  background: #e2e8f0;
}

.user-avatar {
  display: flex;
  align-items: center;
}

.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #d1d5db;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

/* 退出按钮 */
.logout-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background: #e5e7eb;
}

.logout-icon {
  font-size: 16px;
}

.nav-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.login-btn {
  background: #1e40af;
  color: white;
}

.login-btn:hover {
  background: #1d4ed8;
}

.register-btn {
  background: #1e40af;
  color: white;
}

.register-btn:hover {
  background: #1d4ed8;
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }
}
</style>