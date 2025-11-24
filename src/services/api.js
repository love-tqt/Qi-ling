// API基础配置
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000  // 将超时时间从10秒增加到30秒
  // 移除了固定的 Content-Type 设置，让axios自动处理
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 排除认证相关的API端点
    const authEndpoints = ['/auth/login', '/auth/register', '/health'];
    const isAuthRequest = authEndpoints.some(endpoint => config.url.includes(endpoint));
    
    if (isAuthRequest) {
      return config; // 不拦截认证请求
    }

    // 获取用户ID和过期时间
    const userid = localStorage.getItem('userid');
    const expiresAt = localStorage.getItem('expires_at');

    // 检查登录状态
    if (!userid || !expiresAt) {
      window.dispatchEvent(new CustomEvent('auth-required', {
        detail: { message: '您还未登录，请先登录' }
      }));
      return Promise.reject(new Error('未登录，请先登录'));
    }

    // 检查是否过期
    const now = new Date();
    const expires = new Date(expiresAt);
    if (now >= expires) {
      localStorage.removeItem('userid');
      localStorage.removeItem('expires_at');
      window.dispatchEvent(new CustomEvent('auth-required', {
        detail: { message: '登录已过期，请重新登录' }
      }));
      return Promise.reject(new Error('登录已过期，请重新登录'));
    }

    // 添加用户ID到请求头
    config.headers['X-User-ID'] = userid;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 保留完整的响应结构，不提取data
    return response;
  },
  (error) => {
    // 检查是否需要重新认证
    if (error.response?.status === 401) {
      // 清除本地存储
      localStorage.removeItem('userid');
      localStorage.removeItem('expires_at');
      
      // 触发全局登出事件并显示登录框
      window.dispatchEvent(new CustomEvent('auth-required', {
        detail: { message: '认证已过期，请重新登录' }
      }));
      
      return Promise.reject(new Error('认证已过期，请重新登录'));
    }
    
    if (error.response?.status) {
      return Promise.reject(new Error(`HTTP error! status: ${error.response.status}`));
    }
    
    return Promise.reject(error);
  }
);

// 通用请求函数
async function request(endpoint, options = {}) {
  try {
    const response = await apiClient({
      url: endpoint,
      ...options
    });
    
    return response;
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
}

  // 聊天相关API
  export const chatAPI = {
    // 发送消息（支持文本和图片文件，支持上下文对话）
    sendMessage: async (message, imageFile = null) => {
      const formData = new FormData();
      formData.append('message', message);
      
      if (imageFile) {
        formData.append('image', imageFile);
      }
      
      return request('/chat/send', {
        method: 'POST',
        data: formData
        // 不需要手动设置Content-Type，让浏览器自动设置为multipart/form-data
      });
    },

    // 获取聊天历史
    getChatHistory: async () => {
      return request('/chat/history');
    },
    
    // 获取最近5条消息
    getLatestMessages: async () => {
      return request('/chat/latest');
    }
  };

// 文件上传相关API
export const uploadAPI = {
  // 上传图片文件
  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return request('/upload', {
      method: 'POST',
      data: formData
    });
  }
};

// 语音相关API
export const voiceAPI = {
  // 语音识别
  recognizeSpeech: async (audioFile) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    
    return request('/voice/recognize', {
      method: 'POST',
      data: formData
    });
  },

  // 语音合成
  synthesizeSpeech: async (text) => {
    return request('/voice/synthesize', {
      method: 'POST',
      data: { text }
    });
  }
};

// 认证相关API
export const authAPI = {
  // 用户注册
  register: async (userData) => {
    return request('/auth/register', {
      method: 'POST',
      data: userData
    });
  },
  // 用户登录
  login: async (credentials) => {
    return request('/auth/login', {
      method: 'POST',
      data: credentials
    });
  },
  // 获取用户信息
  getUserInfo: async (userId) => {
    return request(`/auth/user/${userId}`);
  }
};

// 配置相关API
export const configAPI = {
  // 获取配置
  getConfig: async () => {
    return request('/config');
  }
};

// 健康检查
export const healthAPI = {
  check: async () => {
    return request('/health');
  }
};

export default {
  chat: chatAPI,
  upload: uploadAPI,
  voice: voiceAPI,
  auth: authAPI,
  config: configAPI,
  health: healthAPI
};