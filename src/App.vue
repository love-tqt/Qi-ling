<template>
  <div id="app">
    <!-- 导航栏 -->
    <NavBar 
      :isAuthenticated="isAuthenticated"
      :username="currentUser?.username || ''"
      @show-login="showLoginModal = true" 
      @show-register="showRegisterModal = true" 
    />
    
    <!-- 主要内容区域 -->
    <main class="main-content">
      <div class="content-container">
        <div class="main-section">
          <!-- 智能识别区域 -->
          <RecognitionCard @message="addMessage" />
          
          <!-- 对话记录 -->
          <ChatCard :messages="chatMessages" />
        </div>

        <!-- 侧边栏 -->
        <aside class="sidebar">
          <!-- 热门文物分类 -->
          <SidebarCard 
            title="热门文物分类"
            type="categories"
            :categories="categories"
          />
          
          <!-- 使用提示 -->
          <SidebarCard 
            title="使用提示"
            type="tips"
            :tips="usageTips"
          />
          
          <!-- 最新识别 -->
          <SidebarCard 
            title="最新识别"
            type="recent"
            :recentItems="recentIdentifications"
          />
        </aside>
      </div>
    </main>

    <!-- 页脚 -->
    <AppFooter />

    <!-- 登录模态框 -->
    <LoginModal 
      :visible="showLoginModal" 
      @close="showLoginModal = false"
      @switch-to-register="handleSwitchToRegister"
      @login-success="handleLoginSuccess"
    />

    <!-- 注册模态框 -->
    <RegisterModal 
      :visible="showRegisterModal" 
      @close="showRegisterModal = false"
      @switch-to-login="handleSwitchToLogin"
      @register-success="handleRegisterSuccess"
    />
  </div>
</template>

<script>
import NavBar from './components/NavBar.vue'
import RecognitionCard from './components/RecognitionCard.vue'
import ChatCard from './components/ChatCard.vue'
import SidebarCard from './components/SidebarCard.vue'
import AppFooter from './components/Footer.vue'
import LoginModal from './components/LoginModal.vue'
import RegisterModal from './components/RegisterModal.vue'

export default {
  name: 'App',
  components: {
    NavBar,
    RecognitionCard,
    ChatCard,
    SidebarCard,
    AppFooter,
    LoginModal,
    RegisterModal
  },
  data() {
    return {
      showLoginModal: false,
      showRegisterModal: false,
      isAuthenticated: false,
      currentUser: null,
      chatMessages: [
        {
          sender: 'ai',
          content: '您好！我是 AI 文物导览助手，可以帮您识别和了解各类器具文物。请上传文物图片或直接提问，我会为您提供专业的解答.'
        }
      ],
      categories: [
        { name: '青铜器', description: '商周礼器、兵器' },
        { name: '陶瓷器', description: '瓷器、陶器' },
        { name: '玉器', description: '玉佩、玉璧' },
        { name: '漆器', description: '漆盒、漆盘' }
      ],
      usageTips: [
        { 
          title: '拍摄建议', 
          description: '保持光线充足，尽量正面拍摄，避免反光和阴影' 
        },
        { 
          title: '提问技巧', 
          description: '可以询问文物的名称、年代、用途、制作工艺等' 
        },
        { 
          title: '连续对话', 
          description: '支持多轮对话，可以追问更多细节信息，支持根据用户最近的5条消息进行对话生成回答。' 
        }
      ],
      recentIdentifications: [
        { name: '商代青铜鼎', description: '祭祀礼器，象征权力' },
        { name: '宋代青瓷瓶', description: '精美瓷器，釉色温润' },
        { name: '汉代玉璧', description: '礼制用器，寓意天圆' }
      ]
    }
  },
  methods: {
    addMessage(message) {
      this.chatMessages.push(message);
    },
    handleSwitchToRegister() {
      this.showLoginModal = false;
      this.showRegisterModal = true;
    },
    handleSwitchToLogin() {
      this.showRegisterModal = false;
      this.showLoginModal = true;
    },
    handleLoginSuccess(userData) {
      console.log('用户登录成功:', userData);
      this.isAuthenticated = true;
      this.currentUser = {
        id: userData.userId,
        username: userData.username
      };
      
      // 登录成功后关闭登录模态框
      this.showLoginModal = false;
      
      // 移除全局点击监听器，避免继续拦截操作
      document.removeEventListener('click', this.globalClickHandler);
      
      this.$emit('message', { 
        sender: 'ai', 
        content: `欢迎回来，${userData.username}！您已成功登录。` 
      });
    },
    handleRegisterSuccess(userData) {
      console.log('用户注册成功:', userData);
      // 注册成功后自动切换到登录界面
      this.showRegisterModal = false;
      this.showLoginModal = true;
      
      this.$emit('message', { 
        sender: 'ai', 
        content: `注册成功！请使用您的账户登录。` 
      });
    },
    checkAuthStatus() {
      const userid = localStorage.getItem('userid');
      const expiresAt = localStorage.getItem('expires_at');
      
      // 检查登录状态和过期时间
      if (userid && expiresAt) {
        const now = new Date();
        const expires = new Date(expiresAt);
        this.isAuthenticated = now < expires;
        
        if (this.isAuthenticated) {
          this.currentUser = {
            id: userid,
            username: userid // 使用userid作为用户名，可以从API获取详细信息
          };
        } else {
          // 清除过期的登录信息
          localStorage.removeItem('userid');
          localStorage.removeItem('expires_at');
        }
      } else {
        this.isAuthenticated = false;
      }
    },
    handleAuthRequired() {
      console.log('需要重新认证');
      this.isAuthenticated = false;
      this.currentUser = null;
      this.showLoginModal = true;
    },
    handleLogout() {
      console.log('用户登出');
      this.isAuthenticated = false;
      this.currentUser = null;
      
      this.$emit('message', { 
        sender: 'ai', 
        content: '您已成功退出登录。' 
      });
    },
    
    // 全局认证检查
    setupGlobalAuthCheck() {
      // 检查当前是否已登录
      const userid = localStorage.getItem('userid');
      const expiresAt = localStorage.getItem('expires_at');
      
      if (!userid || !expiresAt) {
        this.showLoginModal = true;
        return;
      }
      
      // 检查过期时间
      const now = new Date();
      const expires = new Date(expiresAt);
      if (now >= expires) {
        localStorage.removeItem('userid');
        localStorage.removeItem('expires_at');
        this.showLoginModal = true;
        return;
      }
      
      // 添加全局点击事件监听
      document.addEventListener('click', this.globalClickHandler);
    },
    
    // 全局点击处理器
    globalClickHandler(event) {
      // 检查是否已登录
      const userid = localStorage.getItem('userid');
      const expiresAt = localStorage.getItem('expires_at');
      
      if (!userid || !expiresAt) {
        // 阻止默认行为
        event.preventDefault();
        event.stopPropagation();
        
        // 检查点击的是否是登录/注册相关元素
        const target = event.target;
        const isAuthElement = target.closest('.login-btn, .register-btn, .auth-modal, [data-auth-ignore]');
        
        if (!isAuthElement) {
          // 显示登录框
          this.showLoginModal = true;
          // 显示提示信息
          window.dispatchEvent(new CustomEvent('auth-required', {
            detail: { message: '您还未登录，请先登录' }
          }));
        }
      } else {
        // 检查是否过期
        const now = new Date();
        const expires = new Date(expiresAt);
        if (now >= expires) {
          localStorage.removeItem('userid');
          localStorage.removeItem('expires_at');
          event.preventDefault();
          event.stopPropagation();
          this.showLoginModal = true;
          window.dispatchEvent(new CustomEvent('auth-required', {
            detail: { message: '登录已过期，请重新登录' }
          }));
        }
      }
    }
  },
  mounted() {
    // 初始化检查认证状态
    this.setupGlobalAuthCheck();
    
    // 监听全局认证事件
    window.addEventListener('auth-required', this.handleAuthRequired);
    window.addEventListener('auth-logout', this.handleLogout);
    
    // 检查认证状态
    this.checkAuthStatus();
  },
  beforeUnmount() {
    // 移除事件监听
    window.removeEventListener('auth-required', this.handleAuthRequired);
    window.removeEventListener('auth-logout', this.handleLogout);
  }
}
</script>

<style>
/* 基础样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background-color: #f8fafc;
  color: #333333;
  line-height: 1.6;
}

/* 主要内容区域 */
.main-content {
  padding: 32px 0;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  align-items: start;
}

.main-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>