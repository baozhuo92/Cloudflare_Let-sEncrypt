from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import get_user_certificates, get_certificate_by_id, save_certificate_record
from ssl_generator import SSLCertificateGenerator
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/history')
@login_required
def history():
    certificates = get_user_certificates(current_user.id)
    return render_template('history.html', certificates=certificates)

@main_bp.route('/certificate/<int:cert_id>')
@login_required
def certificate_detail(cert_id):
    certificate = get_certificate_by_id(cert_id, current_user.id)
    if not certificate:
        return "证书不存在或您没有权限查看", 404
    return render_template('certificate_detail.html', certificate=certificate)

@main_bp.route('/generate', methods=['POST'])
@login_required
def generate_certificate():
    try:
        data = request.get_json()
        domain = data.get('domain')
        email = data.get('email')
        cf_email = data.get('cf_email')
        cf_api_key = data.get('cf_api_key')
        
        if not all([domain, email, cf_email, cf_api_key]):
            return jsonify({
                'success': False,
                'message': '请填写所有必需字段'
            })
        
        # 生成证书
        generator = SSLCertificateGenerator(cf_email, cf_api_key)
        result = generator.generate_certificate(domain, email)
        
        if result['success']:
            # 保存到数据库
            cert_id = save_certificate_record(
                user_id=current_user.id,
                domain=domain,
                email=email,
                cf_email=cf_email,
                status='success',
                private_key=result['private_key'],
                certificate=result['certificate'],
                ca_certificate=result.get('ca_certificate', '')
            )
            
            return jsonify({
                'success': True,
                'message': '证书生成成功！',
                'certificate_id': cert_id,
                'private_key': result['private_key'],
                'certificate': result['certificate'],
                'ca_certificate': result.get('ca_certificate', '')
            })
        else:
            # 保存失败记录
            save_certificate_record(
                user_id=current_user.id,
                domain=domain,
                email=email,
                cf_email=cf_email,
                status='failed',
                error_message=result['message']
            )
            
            return jsonify({
                'success': False,
                'message': result['message']
            })
            
    except Exception as e:
        error_msg = f"生成证书时发生错误: {str(e)}"
        print(f"Error: {error_msg}")
        print(traceback.format_exc())
        
        # 保存错误记录
        try:
            save_certificate_record(
                user_id=current_user.id,
                domain=data.get('domain', ''),
                email=data.get('email', ''),
                cf_email=data.get('cf_email', ''),
                status='failed',
                error_message=error_msg
            )
        except:
            pass
        
        return jsonify({
            'success': False,
            'message': error_msg
        })