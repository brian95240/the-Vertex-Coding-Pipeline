<template>
  <div class="dashboard-container">
    <h1>Dashboard</h1>
    
    <div class="stats-container">
      <div class="stat-card" v-for="(stat, index) in stats" :key="index">
        <div class="stat-icon" :class="stat.iconClass"></div>
        <div class="stat-content">
          <h3>{{ stat.title }}</h3>
          <p class="stat-value">{{ stat.value }}</p>
          <p class="stat-change" :class="stat.changeClass">{{ stat.change }}</p>
        </div>
      </div>
    </div>
    
    <div class="charts-container">
      <div class="chart-card">
        <h3>Task Execution</h3>
        <div class="chart-placeholder">
          <p>Task execution chart will be displayed here</p>
        </div>
      </div>
      
      <div class="chart-card">
        <h3>Resource Usage</h3>
        <div class="chart-placeholder">
          <p>Resource usage chart will be displayed here</p>
        </div>
      </div>
    </div>
    
    <div class="recent-activity">
      <h2>Recent Activity</h2>
      <div class="activity-list">
        <div class="activity-item" v-for="(activity, index) in recentActivities" :key="index">
          <div class="activity-icon" :class="activity.iconClass"></div>
          <div class="activity-content">
            <h4>{{ activity.title }}</h4>
            <p>{{ activity.description }}</p>
            <span class="activity-time">{{ activity.time }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardView',
  data() {
    return {
      stats: [
        {
          title: 'Active Tasks',
          value: '12',
          change: '+3 from yesterday',
          changeClass: 'positive',
          iconClass: 'tasks-icon'
        },
        {
          title: 'Completed Tasks',
          value: '87',
          change: '+15 from yesterday',
          changeClass: 'positive',
          iconClass: 'completed-icon'
        },
        {
          title: 'Active Providers',
          value: '5',
          change: 'No change',
          changeClass: 'neutral',
          iconClass: 'providers-icon'
        },
        {
          title: 'Resource Usage',
          value: '68%',
          change: '-5% from yesterday',
          changeClass: 'positive',
          iconClass: 'resource-icon'
        }
      ],
      recentActivities: [
        {
          title: 'Task Completed',
          description: 'Text summarization task completed successfully',
          time: '5 minutes ago',
          iconClass: 'completed-icon'
        },
        {
          title: 'New Batch Created',
          description: 'Batch "Image Processing" with 8 tasks created',
          time: '15 minutes ago',
          iconClass: 'batch-icon'
        },
        {
          title: 'Provider Added',
          description: 'New provider "Anthropic" added to the system',
          time: '1 hour ago',
          iconClass: 'providers-icon'
        },
        {
          title: 'System Optimization',
          description: 'Resource optimization completed, 15% improvement',
          time: '3 hours ago',
          iconClass: 'system-icon'
        }
      ]
    };
  },
  mounted() {
    // In a real implementation, we would fetch data from the API here
    // this.fetchDashboardData();
  },
  methods: {
    fetchDashboardData() {
      // Fetch dashboard data from API
    }
  }
};
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(74, 108, 247, 0.1);
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  margin: 0;
  font-size: 14px;
  color: var(--secondary-color);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin: 5px 0;
}

.stat-change {
  font-size: 12px;
  margin: 0;
}

.stat-change.positive {
  color: var(--success-color);
}

.stat-change.negative {
  color: var(--danger-color);
}

.stat-change.neutral {
  color: var(--secondary-color);
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.chart-card h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.chart-placeholder {
  height: 200px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--secondary-color);
}

.recent-activity {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.recent-activity h2 {
  margin-top: 0;
  margin-bottom: 15px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.activity-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.activity-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(74, 108, 247, 0.1);
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-content {
  flex: 1;
}

.activity-content h4 {
  margin: 0;
  font-size: 16px;
}

.activity-content p {
  margin: 5px 0;
  color: var(--secondary-color);
}

.activity-time {
  font-size: 12px;
  color: var(--secondary-color);
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
}
</style>
