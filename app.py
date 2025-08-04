from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from database import init_db, get_user_by_id
from routes.auth import auth_bp
from routes.main import main_bp
from routes.email import email_bp

# 创建Flask应用
app = Flask(__name__)

# 加载配置
try:
    from config import Config
    app.config.from_object(Config)
except ImportError:
    # 如果没有config.py文件，使用默认配置
    app.secret_key = 'your-secret-key-change-this-in-production'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # 需要配置
    app.config['MAIL_PASSWORD'] = 'your-app-password'     # 需要配置
    app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# 初始化扩展
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/auth/login'
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'error'

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(email_bp)

# 初始化数据库
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)