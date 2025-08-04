import sqlite3
import hashlib
import secrets
from datetime import datetime
from flask_login import UserMixin
from flask_mail import Message
from flask import url_for, current_app

class User(UserMixin):
    def __init__(self, id, email, password_hash, is_verified=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.is_verified = is_verified

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建邮件日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            email_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 检查certificates表是否存在user_id列
    cursor.execute("PRAGMA table_info(certificates)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'user_id' not in columns:
        # 如果不存在user_id列，先创建新表
        cursor.execute('''
            CREATE TABLE certificates_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                cf_email TEXT NOT NULL,
                status TEXT NOT NULL,
                private_key TEXT,
                certificate TEXT,
                ca_certificate TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 如果旧表存在数据，需要迁移（这里假设没有旧数据或创建默认用户）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificates'")
        if cursor.fetchone():
            # 删除旧表
            cursor.execute('DROP TABLE certificates')
        
        # 重命名新表
        cursor.execute('ALTER TABLE certificates_new RENAME TO certificates')
    else:
        # 如果已存在user_id列，确保表结构正确
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                cf_email TEXT NOT NULL,
                status TEXT NOT NULL,
                private_key TEXT,
                certificate TEXT,
                ca_certificate TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    
    conn.commit()
    conn.close()

def create_user(email, password):
    """创建新用户"""
    from werkzeug.security import generate_password_hash
    
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        # 检查邮箱是否已存在
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return {'success': False, 'message': '该邮箱已被注册。'}
        
        # 生成密码哈希和验证令牌
        password_hash = generate_password_hash(password)
        verification_token = secrets.token_urlsafe(32)
        
        # 插入用户
        cursor.execute('''
            INSERT INTO users (email, password_hash, verification_token)
            VALUES (?, ?, ?)
        ''', (email, password_hash, verification_token))
        
        conn.commit()
        
        # 发送验证邮件
        send_verification_email(email, verification_token)
        
        return {'success': True, 'message': '注册成功，请检查邮箱验证。'}
        
    except Exception as e:
        return {'success': False, 'message': f'注册失败: {str(e)}'}
    finally:
        conn.close()

def verify_user(email, password):
    """验证用户登录"""
    from werkzeug.security import check_password_hash
    
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, password_hash, is_verified
            FROM users WHERE email = ?
        ''', (email,))
        
        user_data = cursor.fetchone()
        if user_data:
            # 确保password_hash是字符串类型
            password_hash = user_data[2]
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')
            
            if check_password_hash(password_hash, password):
                return User(user_data[0], user_data[1], password_hash, user_data[3])
        
        return None
        
    finally:
        conn.close()

def get_user_by_id(user_id):
    """根据ID获取用户"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, password_hash, is_verified
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        if user_data:
            # 确保password_hash是字符串类型
            password_hash = user_data[2]
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')
            
            return User(user_data[0], user_data[1], password_hash, user_data[3])
        
        return None
        
    finally:
        conn.close()

def verify_email_token(token):
    """验证邮箱令牌"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users SET is_verified = TRUE, verification_token = NULL
            WHERE verification_token = ?
        ''', (token,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True
        
        return False
        
    finally:
        conn.close()

def send_verification_email(email, token):
    """发送验证邮件"""
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    subject = 'SSL证书管理系统 - 邮箱验证'
    content = f'''
    <h2>欢迎注册SSL证书管理系统！</h2>
    <p>请点击下面的链接验证您的邮箱地址：</p>
    <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
    <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
    <p>{verification_url}</p>
    <p>此链接24小时内有效。</p>
    '''
    
    # 获取用户ID（如果存在）
    user_id = None
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user_data = cursor.fetchone()
        if user_data:
            user_id = user_data[0]
    finally:
        conn.close()
    
    # 发送邮件并记录
    send_email_with_log(user_id, email, subject, content, 'verification')

def send_email_with_log(user_id, recipient_email, subject, content, email_type='general'):
    """发送邮件并记录到数据库，包含重试机制"""
    import time
    import socket
    
    # 先记录邮件到数据库
    email_log_id = log_email(user_id, recipient_email, subject, content, email_type, 'pending')
    
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            from app import mail  # 延迟导入避免循环依赖
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                html=content
            )
            
            # 设置超时时间
            with mail.connect() as conn:
                conn.send(msg)
            
            # 更新邮件状态为成功
            update_email_status(email_log_id, 'sent')
            print(f"邮件发送成功: {recipient_email}")
            return
            
        except socket.timeout:
            error_msg = f"邮件发送超时 (尝试 {attempt + 1}/{max_retries})"
            print(error_msg)
            if attempt == max_retries - 1:
                update_email_status(email_log_id, 'failed', f"发送失败: {error_msg}")
            else:
                time.sleep(retry_delay)
                
        except socket.error as e:
            error_msg = f"网络连接错误: {str(e)} (尝试 {attempt + 1}/{max_retries})"
            print(error_msg)
            if attempt == max_retries - 1:
                update_email_status(email_log_id, 'failed', f"发送失败: {error_msg}")
            else:
                time.sleep(retry_delay)
                
        except Exception as e:
            error_msg = f"邮件发送失败: {str(e)} (尝试 {attempt + 1}/{max_retries})"
            print(error_msg)
            
            # 对于认证错误等不需要重试的错误，直接失败
            if 'authentication' in str(e).lower() or 'login' in str(e).lower():
                update_email_status(email_log_id, 'failed', f"认证失败: {str(e)}")
                return
                
            if attempt == max_retries - 1:
                update_email_status(email_log_id, 'failed', f"发送失败: {error_msg}")
            else:
                time.sleep(retry_delay)

def log_email(user_id, recipient_email, subject, content, email_type, status, error_message=None):
    """记录邮件到数据库"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO email_logs (user_id, recipient_email, subject, content, email_type, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, recipient_email, subject, content, email_type, status, error_message))
        
        email_log_id = cursor.lastrowid
        conn.commit()
        return email_log_id
        
    finally:
        conn.close()

def update_email_status(email_log_id, status, error_message=None):
    """更新邮件发送状态"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE email_logs 
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', (status, error_message, email_log_id))
        
        conn.commit()
        
    finally:
        conn.close()

def get_user_email_logs(user_id, limit=50):
    """获取用户的邮件发送记录"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, recipient_email, subject, email_type, status, sent_at, error_message
            FROM email_logs 
            WHERE user_id = ? OR user_id IS NULL
            ORDER BY sent_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'recipient_email': row[1],
                'subject': row[2],
                'email_type': row[3],
                'status': row[4],
                'sent_at': row[5],
                'error_message': row[6]
            })
        
        return logs
        
    finally:
        conn.close()

def get_email_log_detail(log_id, user_id):
    """获取邮件记录详情"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, recipient_email, subject, content, email_type, status, sent_at, error_message
            FROM email_logs 
            WHERE id = ? AND (user_id = ? OR user_id IS NULL)
        ''', (log_id, user_id))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'recipient_email': row[1],
                'subject': row[2],
                'content': row[3],
                'email_type': row[4],
                'status': row[5],
                'sent_at': row[6],
                'error_message': row[7]
            }
        
        return None
        
    finally:
        conn.close()

def save_certificate_record(user_id, domain, email, cf_email, status, private_key=None, certificate=None, ca_certificate=None, error_message=None):
    """保存证书记录"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO certificates (user_id, domain, email, cf_email, status, private_key, certificate, ca_certificate, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, domain, email, cf_email, status, private_key, certificate, ca_certificate, error_message))
        
        cert_id = cursor.lastrowid
        conn.commit()
        return cert_id
        
    finally:
        conn.close()

def get_user_certificates(user_id):
    """获取用户的证书记录"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, domain, email, cf_email, status, created_at, error_message
            FROM certificates 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        certificates = []
        for row in cursor.fetchall():
            certificates.append({
                'id': row[0],
                'domain': row[1],
                'email': row[2],
                'cf_email': row[3],
                'status': row[4],
                'created_at': row[5],
                'error_message': row[6]
            })
        
        return certificates
        
    finally:
        conn.close()

def get_certificate_by_id(cert_id, user_id):
    """根据ID获取证书详情（仅限用户自己的证书）"""
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, domain, email, cf_email, status, private_key, certificate, ca_certificate, created_at, error_message
            FROM certificates 
            WHERE id = ? AND user_id = ?
        ''', (cert_id, user_id))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'domain': row[1],
                'email': row[2],
                'cf_email': row[3],
                'status': row[4],
                'private_key': row[5],
                'certificate': row[6],
                'ca_certificate': row[7],
                'created_at': row[8],
                'error_message': row[9]
            }
        
        return None
        
    finally:
        conn.close()