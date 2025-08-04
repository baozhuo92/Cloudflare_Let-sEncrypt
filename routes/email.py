from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import get_user_email_logs, get_email_log_detail

email_bp = Blueprint('email', __name__)

@email_bp.route('/email-logs')
@login_required
def email_logs():
    """邮件发送记录页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取用户的邮件记录
    logs = get_user_email_logs(current_user.id, limit=per_page * page)
    
    # 简单分页处理
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    page_logs = logs[start_index:end_index]
    
    has_next = len(logs) > end_index
    has_prev = page > 1
    
    return render_template('email_logs.html', 
                         logs=page_logs,
                         page=page,
                         has_next=has_next,
                         has_prev=has_prev)

@email_bp.route('/email-logs/<int:log_id>')
@login_required
def email_log_detail(log_id):
    """邮件记录详情页面"""
    log_detail = get_email_log_detail(log_id, current_user.id)
    
    if not log_detail:
        flash('邮件记录不存在或无权访问。', 'error')
        return redirect(url_for('email.email_logs'))
    
    return render_template('email_log_detail.html', log=log_detail)

@email_bp.route('/api/email-stats')
@login_required
def email_stats():
    """获取邮件统计信息"""
    logs = get_user_email_logs(current_user.id, limit=1000)
    
    total = len(logs)
    sent = len([log for log in logs if log['status'] == 'sent'])
    failed = len([log for log in logs if log['status'] == 'failed'])
    pending = len([log for log in logs if log['status'] == 'pending'])
    
    return jsonify({
        'total': total,
        'sent': sent,
        'failed': failed,
        'pending': pending,
        'success_rate': round((sent / total * 100) if total > 0 else 0, 2)
    })