from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
import re
from database import create_user, verify_user, verify_email_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = verify_user(email, password)
        if user:
            if user.is_verified:
                login_user(user)
                flash('登录成功！', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('请先验证您的邮箱地址。', 'error')
        else:
            flash('邮箱或密码错误。', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 验证邮箱格式
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('请输入有效的邮箱地址。', 'error')
            return render_template('register.html')
        
        # 验证密码长度
        if len(password) < 6:
            flash('密码长度至少为6位。', 'error')
            return render_template('register.html')
        
        # 验证密码确认
        if password != confirm_password:
            flash('两次输入的密码不一致。', 'error')
            return render_template('register.html')
        
        # 创建用户
        result = create_user(email, password)
        if result['success']:
            flash('注册成功！请检查您的邮箱并点击验证链接。', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('register.html')

@auth_bp.route('/verify/<token>')
def verify_email(token):
    if verify_email_token(token):
        flash('邮箱验证成功！您现在可以登录了。', 'success')
    else:
        flash('验证链接无效或已过期。', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录。', 'success')
    return redirect(url_for('auth.login'))