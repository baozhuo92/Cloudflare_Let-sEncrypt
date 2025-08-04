# SSL证书管理系统配置文件
# 请根据您的实际情况修改以下配置

import os

class Config:
    # Flask应用密钥 - 请在生产环境中更改为随机字符串
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # 邮件服务器配置
    # 163邮箱配置 - 使用SSL连接更稳定
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.163.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)  # 使用SSL端口
    MAIL_USE_TLS = False  # 使用SSL而不是TLS
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@163.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-authorization-code'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'your-email@163.com'
    
    # 其他邮件服务器配置示例：
    
    # QQ邮箱配置
    # MAIL_SERVER = 'smtp.qq.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = 'your-email@qq.com'
    # MAIL_PASSWORD = 'your-authorization-code'  # QQ邮箱授权码

    
    # Outlook/Hotmail配置
    # MAIL_SERVER = 'smtp-mail.outlook.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = 'your-email@outlook.com'
    # MAIL_PASSWORD = 'your-password'

# 邮件配置说明：
# 
# 1. Gmail配置：
#    - 需要开启两步验证
#    - 生成应用专用密码：https://myaccount.google.com/apppasswords
#    - 使用应用专用密码作为MAIL_PASSWORD
# 
# 2. QQ邮箱配置：
#    - 登录QQ邮箱 -> 设置 -> 账户
#    - 开启SMTP服务，获取授权码
#    - 使用授权码作为MAIL_PASSWORD
# 
# 3. 163邮箱配置：
#    - 登录163邮箱 -> 设置 -> POP3/SMTP/IMAP
#    - 开启SMTP服务，获取授权码
#    - 使用授权码作为MAIL_PASSWORD
# 
# 4. 环境变量配置（推荐）：
#    可以通过设置环境变量来配置邮件服务器，这样更安全：
#    
#    Windows:
#    set MAIL_USERNAME=your-email@gmail.com
#    set MAIL_PASSWORD=your-app-password
#    
#    Linux/Mac:
#    export MAIL_USERNAME=your-email@gmail.com
#    export MAIL_PASSWORD=your-app-password