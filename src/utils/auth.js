/**
 * 认证工具类
 */
export class AuthUtil {
  // 存储登录信息
  static setLoginInfo(response) {
    const { userid, expires_at } = response.data;
    localStorage.setItem('userid', userid);
    localStorage.setItem('expires_at', expires_at);
  }

  // 检查登录状态
  static isLoggedIn() {
    const userid = localStorage.getItem('userid');
    const expiresAt = localStorage.getItem('expires_at');
    
    if (!userid || !expiresAt) return false;
    
    const now = new Date();
    const expires = new Date(expiresAt);
    return now < expires;
  }

  // 清除登录信息
  static clearLoginInfo() {
    localStorage.removeItem('userid');
    localStorage.removeItem('expires_at');
  }

  // 获取请求头
  static getAuthHeaders() {
    if (!this.isLoggedIn()) {
      this.clearLoginInfo();
      window.location.href = '/login'; // 跳转到登录页
      return {};
    }
    
    return {
      'X-User-ID': localStorage.getItem('userid')
    };
  }
}

// 请求拦截器
export const requestInterceptor = {
  request: (config) => {
    const headers = AuthUtil.getAuthHeaders();
    return {
      ...config,
      headers: {
        ...config.headers,
        ...headers
      }
    };
  },
  response: (response) => {
    return response;
  },
  error: (error) => {
    if (error.response?.status === 401) {
      AuthUtil.clearLoginInfo();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
};