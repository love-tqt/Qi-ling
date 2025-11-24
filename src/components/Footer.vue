<template>
  <footer class="footer">
    <div class="footer-container">
      <div class="footer-main">
        <div class="footer-brand">
          <div class="footer-logo">
            <div class="logo-icon small">
              <span class="logo-text">AI</span>
            </div>
            <h3 class="footer-title">AI文物导览助手</h3>
          </div>
          <p class="footer-desc">基于文心大模型的智能文物识别与问答平台，为您提供专业的文物知识服务。</p>
          <div class="social-links">
            <div class="social-icon">💬</div>
            <div class="social-icon">📱</div>
            <div class="social-icon">🐧</div>
          </div>
        </div>
        <div class="footer-links">
          <div class="link-group">
            <h4 class="link-title">产品功能</h4>
            <ul class="link-list">
              <li>智能文物识别</li>
              <li>多模态问答</li>
              <li>知识库检索</li>
              <li>语音交互</li>
            </ul>
          </div>
          <div class="link-group">
            <h4 class="link-title">帮助支持</h4>
            <ul class="link-list">
              <li>使用指南</li>
              <li>常见问题</li>
              <li>联系客服</li>
              <li>意见反馈</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2024 AI文物导览助手. 保留所有权利. | 基于文心大模型技术驱动</p>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'AppFooter'
}
</script>

<style scoped>
.footer {
  background: white;
  border-top: 1px solid #e5e7eb;
  margin-top: 48px;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 20px;
}

.footer-main {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 32px;
  margin-bottom: 24px;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon.small {
  width: 32px;
  height: 32px;
  background: #1e40af;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.footer-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  font-family: cursive;
}

.footer-desc {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
}

.social-links {
  display: flex;
  gap: 12px;
}

.social-icon {
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.footer-links {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.link-group h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.link-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.link-list li {
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
}

.link-list li:hover {
  color: #1e40af;
}

.footer-bottom {
  border-top: 1px solid #e5e7eb;
  padding-top: 24px;
  text-align: center;
}

.footer-bottom p {
  font-size: 12px;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .footer-main {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .footer-links {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
</style>
