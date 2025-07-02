/*
 * Copyright (C) 2025 StarsX Studio
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */
/**
 * @param {string} message
 * @param {string} [type]
 */
function showAlert(message, type) {
    const existingAlert = document.querySelector('.custom-alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    const alertContainer = document.getElementById('alertContainer');
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert custom-alert alert-dismissible fade show';
    
    switch (type) {
        case 'error':
            alertDiv.classList.add('alert-error');
            break;
        case 'warn':
            alertDiv.classList.add('alert-warn');
            break;
        case 'info':
            alertDiv.classList.add('alert-info');
            break;
        default:
            alertDiv.classList.add('alert-default');
            break;
    }

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alertDiv);
    setTimeout(() => {
        alertDiv.classList.add('show');
    }, 10);
    const delay = type === 'error' ? 8000 : 5000;
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                alertDiv.remove();
            }, 300);
        }
    }, delay);
}
window.showAlert = showAlert;
// 用法：
// showAlert("这是一条普通消息");
// showAlert("这是一条错误消息", "error");
// showAlert("这是一条警告消息", "warn");
// showAlert("这是一条信息消息", "info");