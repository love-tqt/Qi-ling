<template>
  <div class="card sidebar-card">
    <h3 class="card-title">{{ title }}</h3>
    <div v-if="type === 'categories'" class="category-grid">
      <div v-for="(category, index) in categories" :key="index" class="category-card">
        <div class="category-image">
          <span class="placeholder-image">🖼️</span>
        </div>
        <h4 class="category-name">{{ category.name }}</h4>
        <p class="category-desc">{{ category.description }}</p>
      </div>
    </div>
    
    <div v-else-if="type === 'tips'" class="tips-list">
      <div v-for="(tip, index) in tips" :key="index" class="tip-item">
        <div class="tip-icon">
          <span class="tip-bullet">💡</span>
        </div>
        <div class="tip-content">
          <h4 class="tip-title">{{ tip.title }}</h4>
          <p class="tip-desc">{{ tip.description }}</p>
        </div>
      </div>
    </div>
    
    <div v-else-if="type === 'recent'" class="recent-items">
      <div v-for="(item, index) in recentItems" :key="index" class="recent-item">
        <div class="item-image">
          <span class="placeholder-image">🖼️</span>
        </div>
        <div class="item-info">
          <h4 class="item-name">{{ item.name }}</h4>
          <p class="item-desc">{{ item.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SidebarCard',
  props: {
    title: {
      type: String,
      required: true
    },
    type: {
      type: String,
      required: true,
      validator: value => ['categories', 'tips', 'recent'].includes(value)
    },
    categories: {
      type: Array,
      default: () => []
    },
    tips: {
      type: Array,
      default: () => []
    },
    recentItems: {
      type: Array,
      default: () => []
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

.sidebar-card {
  margin-bottom: 0;
}

.category-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.category-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-image {
  width: 100%;
  height: 80px;
  background: #e5e7eb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  font-size: 24px;
}

.category-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.category-desc {
  font-size: 12px;
  color: #6b7280;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tip-icon {
  width: 24px;
  height: 24px;
  background: #eff6ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tip-bullet {
  font-size: 12px;
}

.tip-content {
  flex: 1;
}

.tip-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.tip-desc {
  font-size: 12px;
  color: 6b7280;
  line-height: 1.4;
}

.recent-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.item-image {
  width: 48px;
  height: 48px;
  background: #e5e7eb;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.item-desc {
  font-size: 12px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .category-grid {
    grid-template-columns: 1fr;
  }
}
</style>