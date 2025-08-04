// SSL证书管理系统 - 通用JavaScript
// 动态背景效果和交互功能

// 创建浮动圆圈
function createFloatingCircles() {
    const circlesContainer = document.createElement('div');
    circlesContainer.className = 'floating-circles';
    document.body.appendChild(circlesContainer);
    
    // 创建多个随机浮动圆圈
    for (let i = 0; i < 5; i++) {
        const circle = document.createElement('div');
        circle.className = 'floating-circle';
        
        // 随机大小和位置
        const size = Math.random() * 100 + 50;
        const startX = Math.random() * window.innerWidth;
        const startY = Math.random() * window.innerHeight;
        const duration = Math.random() * 10 + 15; // 15-25秒
        const delay = Math.random() * 5; // 0-5秒延迟
        
        circle.style.cssText = `
            position: fixed;
            width: ${size}px;
            height: ${size}px;
            left: ${startX}px;
            top: ${startY}px;
            background: linear-gradient(45deg, 
                rgba(168, 230, 207, 0.3), 
                rgba(116, 185, 255, 0.3), 
                rgba(129, 236, 236, 0.3)
            );
            border-radius: 50%;
            pointer-events: none;
            z-index: -1;
            animation: floatRandom ${duration}s ease-in-out infinite;
            animation-delay: ${delay}s;
            filter: blur(1px);
        `;
        
        circlesContainer.appendChild(circle);
    }
}

// 添加CSS动画关键帧
function addFloatingAnimations() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes floatRandom {
            0%, 100% {
                transform: translate(0px, 0px) rotate(0deg) scale(1);
                opacity: 0.6;
            }
            25% {
                transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(90deg) scale(1.1);
                opacity: 0.8;
            }
            50% {
                transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(180deg) scale(0.9);
                opacity: 0.4;
            }
            75% {
                transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(270deg) scale(1.05);
                opacity: 0.7;
            }
        }
        
        .floating-circle {
            transition: all 0.3s ease;
        }
        
        .floating-circle:hover {
            transform: scale(1.2) !important;
            opacity: 0.9 !important;
        }
    `;
    document.head.appendChild(style);
}

// 复制到剪贴板功能
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.style.background = 'rgba(168, 230, 207, 0.9)';
        
        setTimeout(function() {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }).catch(function(err) {
        console.error('复制失败: ', err);
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        const originalText = button.textContent;
        button.textContent = '已复制!';
        setTimeout(function() {
            button.textContent = originalText;
        }, 2000);
    });
}

// 表单验证增强
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // 实时验证
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            // 输入时清除错误状态
            input.addEventListener('input', function() {
                this.classList.remove('error');
                const errorMsg = this.parentNode.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            });
        });
        
        // 表单提交验证
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // 滚动到第一个错误字段
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
}

// 字段验证函数
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const required = field.hasAttribute('required');
    
    // 清除之前的错误
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 必填验证
    if (required && !value) {
        showFieldError(field, '此字段为必填项');
        return false;
    }
    
    // 邮箱验证
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, '请输入有效的邮箱地址');
            return false;
        }
    }
    
    // 密码验证
    if (type === 'password' && value) {
        if (value.length < 6) {
            showFieldError(field, '密码长度至少6位');
            return false;
        }
    }
    
    // 域名验证
    if (field.name === 'domain' && value) {
        // 支持通配符域名（*.example.com）和普通域名（example.com）
        const domainRegex = /^(\*\.)?[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
        if (!domainRegex.test(value)) {
            showFieldError(field, '请输入有效的域名，例如：example.com 或 *.example.com');
            return false;
        }
    }
    
    return true;
}

// 显示字段错误
function showFieldError(field, message) {
    field.classList.add('error');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: rgba(255, 183, 197, 0.9);
        font-size: 0.9em;
        margin-top: 5px;
        padding: 5px 10px;
        background: rgba(255, 183, 197, 0.2);
        border-radius: 5px;
        border: 1px solid rgba(255, 183, 197, 0.3);
    `;
    
    field.parentNode.appendChild(errorDiv);
}

// 添加错误样式
function addErrorStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .form-group input.error,
        .form-group textarea.error,
        .form-group select.error {
            border-color: rgba(255, 183, 197, 0.8) !important;
            background: rgba(255, 183, 197, 0.1) !important;
            box-shadow: 0 0 0 3px rgba(255, 183, 197, 0.2) !important;
        }
    `;
    document.head.appendChild(style);
}

// 平滑滚动
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 加载动画
function showLoading(element) {
    const loading = element.querySelector('.loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

function hideLoading(element) {
    const loading = element.querySelector('.loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// 通知系统
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    // 根据类型设置颜色
    if (type === 'success') {
        notification.style.background = 'rgba(168, 230, 207, 0.8)';
    } else if (type === 'error') {
        notification.style.background = 'rgba(255, 183, 197, 0.8)';
    } else if (type === 'warning') {
        notification.style.background = 'rgba(255, 235, 59, 0.8)';
        notification.style.color = 'rgba(139, 69, 19, 0.9)';
    }
    
    document.body.appendChild(notification);
    
    // 动画显示
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
    
    // 点击关闭
    notification.addEventListener('click', () => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    });
}

// 初始化所有功能
function initCommonFeatures() {
    // 创建浮动背景
    addFloatingAnimations();
    createFloatingCircles();
    
    // 增强表单
    addErrorStyles();
    enhanceFormValidation();
    
    // 平滑滚动
    initSmoothScroll();
    
    // 为所有复制按钮添加功能
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('copy-btn')) {
            const targetId = e.target.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                copyToClipboard(targetElement.textContent, e.target);
            }
        }
    });
    
    // 响应式导航
    const navbar = document.querySelector('.navbar');
    if (navbar && window.innerWidth <= 768) {
        navbar.classList.add('mobile');
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommonFeatures);
} else {
    initCommonFeatures();
}

// 窗口大小改变时重新调整
window.addEventListener('resize', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.innerWidth <= 768) {
            navbar.classList.add('mobile');
        } else {
            navbar.classList.remove('mobile');
        }
    }
});

// 导出常用函数供其他脚本使用
window.SSLApp = {
    copyToClipboard,
    showNotification,
    showLoading,
    hideLoading,
    validateField
};