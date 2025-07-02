/*
 * Copyright (C) 2025 StarsX Studio
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */
document.addEventListener('DOMContentLoaded', function() {
  updatePage();
  setInterval(updatePage, 5 * 60 * 1000);
  const refreshBtn = document.getElementById('refresh-history');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', fetchHistoryData);
  }
});
function updatePage() {
  const loadingSpinner = document.getElementById('loading-spinner');
  const lastUpdated = document.getElementById('last-updated');
  loadingSpinner.style.display = 'inline-block';
  lastUpdated.textContent = '最后更新: 加载中...';
  fetch('/api/status')
    .then(response => {
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return response.text().then(text => {
          throw new Error(`无效的响应: ${text.slice(0, 100)}...`);
        });
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success') {
        const now = new Date();
        lastUpdated.textContent = 
          `最后更新: ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
        updateServiceCards(data.data);
        fetchHistoryData();
      } else {
        throw new Error(data.message || 'API返回未知错误');
      }
    })
    .catch(error => {
      console.error('获取状态失败:', error);
      lastUpdated.textContent = 
        `最后更新: 错误 - ${error.message}`;
    })
    .finally(() => {
      loadingSpinner.style.display = 'none';
    });
}
function updateServiceCards(services) {
  const container = document.getElementById('services-container');
  if (!container) return;
  
  container.innerHTML = '';
  Object.entries(services).forEach(([service, data]) => {
    const card = document.createElement('div');
    card.className = 'col-md-4 mb-4';
    let icon = 'fa-globe';
    if (service === 'mysql') icon = 'fa-database';
    if (service === 'minecraft') icon = 'fa-server';
    let statusClass = 'status-offline';
    let statusText = '离线';
    if (data.status) {
      statusClass = 'status-online';
      statusText = '在线';
    } else if (data.details && (data.details.includes('警告') || data.details.includes('部分'))) {
      statusClass = 'status-warning';
      statusText = '警告';
    }
    let timestamp;
    try {
      timestamp = new Date(data.timestamp || new Date());
    } catch (e) {
      timestamp = new Date();
    }
    const timeStr = `${timestamp.toLocaleDateString()} ${timestamp.toLocaleTimeString()}`;
    card.innerHTML = `
      <div class="card service-card glass-effect">
        <div class="card-body text-center p-4">
          <div class="service-icon">
            <i class="fas ${icon}"></i>
          </div>
          <h4 class="mb-3">${service.charAt(0).toUpperCase() + service.slice(1)}</h4>
          <span class="status-badge ${statusClass} mb-3">${statusText}</span>
          <p class="mb-2"><i class="fas fa-clock me-2"></i>最后检测: ${timeStr}</p>
          <p class="mb-0">${data.details || '无详情信息'}</p>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}
function fetchHistoryData() {
  const chartContainer = document.getElementById('history-chart');
  if (!chartContainer) return;
  chartContainer.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary "></div><p>加载历史数据中...</p></div>';
  fetch('/api/history')
    .then(response => {
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return response.text().then(text => {
          throw new Error(`无效的响应: ${text.slice(0, 100)}...`);
        });
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      renderHistoryChart(data);
    })
    .catch(error => {
      console.error('获取历史数据失败:', error);
      chartContainer.innerHTML = `<div class="alert alert-danger">加载历史数据失败: ${error.message}</div>`;
    });
}
function renderHistoryChart(historyData = {}) {
  const chartContainer = document.getElementById('history-chart');
  if (!chartContainer) return;
  chartContainer.innerHTML = '';
  if (!historyData || Object.keys(historyData).length === 0) {
    chartContainer.innerHTML = '<div class="alert alert-info">没有可用的历史数据</div>';
    return;
  }
  const chartWrapper = document.createElement('div');
  chartWrapper.className = 'chart-wrapper';
  chartWrapper.style.display = 'flex';
  chartWrapper.style.alignItems = 'flex-end';
  chartWrapper.style.height = '100%';
  chartWrapper.style.overflowX = 'auto';
  chartWrapper.style.padding = '0 10px';
  const allDates = new Set();
  const services = ['mysql', 'minecraft', 'web'];
  services.forEach(service => {
    if (historyData[service]) {
      historyData[service].forEach(entry => {
        if (entry && entry.date) {
          allDates.add(entry.date);
        }
      });
    }
  });
  if (allDates.size === 0) {
    chartContainer.innerHTML = '<div class="alert alert-info">没有可用的日期数据</div>';
    return;
  }
  const sortedDates = Array.from(allDates).sort();
  sortedDates.forEach(date => {
    let dateObj;
    try {
      dateObj = new Date(date);
    } catch (e) {
      dateObj = new Date();
    }
    const dayColumn = document.createElement('div');
    dayColumn.className = 'day-column';
    dayColumn.style.display = 'flex';
    dayColumn.style.flexDirection = 'column';
    dayColumn.style.alignItems = 'center';
    dayColumn.style.margin = '0 8px';
    dayColumn.style.height = '100%';
    dayColumn.style.minWidth = '30px';
    let totalUptime = 0;
    let count = 0;
    
    services.forEach(service => {
      if (historyData[service]) {
        const serviceEntry = historyData[service].find(e => e && e.date === date);
        if (serviceEntry && serviceEntry.uptime !== undefined) {
          totalUptime += Number(serviceEntry.uptime);
          count++;
        }
      }
    });
    
    const avgUptime = count > 0 ? totalUptime / count : 0;
    const heightPercent = Math.max(1, avgUptime);
    const dayBar = document.createElement('div');
    dayBar.className = 'day-bar';
    dayBar.style.width = '24px';
    dayBar.style.position = 'relative';
    dayBar.dataset.targetHeight = `${heightPercent}%`;
    const dayPercent = document.createElement('div');
    dayPercent.className = 'day-percent';
    dayPercent.textContent = `${Math.round(avgUptime)}%`;
    dayPercent.style.position = 'absolute';
    dayPercent.style.top = '-25px';
    dayPercent.style.left = '50%';
    dayPercent.style.transform = 'translateX(-50%)';
    dayPercent.style.fontSize = '0.75rem';
    dayPercent.style.background = 'rgba(0, 0, 0, 0.6)';
    dayPercent.style.padding = '2px 6px';
    dayPercent.style.borderRadius = '4px';
    dayPercent.style.opacity = '0';
    dayPercent.style.transition = 'opacity 0.3s';
    dayPercent.style.zIndex = '10';
    dayBar.appendChild(dayPercent);
    dayBar.addEventListener('mouseenter', function() {
      dayPercent.style.opacity = '1';
    });
    dayBar.addEventListener('mouseleave', function() {
      dayPercent.style.opacity = '0';
    });
    const dayLabel = document.createElement('div');
    dayLabel.className = 'day-label';
    dayLabel.textContent = dateObj.getDate();
    dayLabel.style.marginTop = '8px';
    dayLabel.style.fontSize = '0.7rem';
    dayLabel.style.color = '#aaaaaa';
    
    dayColumn.appendChild(dayBar);
    dayColumn.appendChild(dayLabel);
    chartWrapper.appendChild(dayColumn);
  });
  
  chartContainer.appendChild(chartWrapper);
  animateChartBars();
}
function animateChartBars() {
  const dayBars = document.querySelectorAll('.day-bar');
  if (!dayBars.length) return;
  if (typeof gsap === 'undefined') {
    dayBars.forEach(bar => {
      const targetHeight = bar.dataset.targetHeight || '0%';
      bar.style.height = targetHeight;
      bar.style.background = 'linear-gradient(to top, #00ffff, #b300ff)';
      bar.style.borderRadius = '4px 4px 0 0';
    });
    return;
  }
  gsap.set(dayBars, {
    height: 0,
    background: 'linear-gradient(to top,rgb(0, 255, 115), rgb(0, 255, 115))',
    borderRadius: '4px 4px 0 0'
  });
  const tl = gsap.timeline();
  dayBars.forEach(bar => {
    const targetHeight = bar.dataset.targetHeight || '0%';
    tl.to(bar, {
      height: targetHeight,
      duration: 1.5,
      ease: "power3.out"
    }, '<0.03');
  });
  tl.eventCallback("onComplete", () => {
    dayBars.forEach(bar => {
      const targetHeight = bar.dataset.targetHeight || '0%';
      bar.style.height = targetHeight;
    });
  });
}