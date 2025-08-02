from flask import Flask, render_template, request, jsonify
import requests
from acme import client
from acme import messages
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import josepy
import time
import tempfile
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            email TEXT NOT NULL,
            cloudflare_email TEXT NOT NULL,
            status TEXT NOT NULL,
            private_key TEXT,
            certificate TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 保存证书记录到数据库
def save_certificate_record(domain, email, cloudflare_email, status, private_key=None, certificate=None, error_message=None):
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO certificates (domain, email, cloudflare_email, status, private_key, certificate, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (domain, email, cloudflare_email, status, private_key, certificate, error_message))
    conn.commit()
    conn.close()

# 获取所有证书记录
def get_all_certificates():
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, domain, email, cloudflare_email, status, created_at, error_message
        FROM certificates
        ORDER BY created_at DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

# 根据ID获取证书详情
def get_certificate_by_id(cert_id):
    conn = sqlite3.connect('ssl_certificates.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, domain, email, cloudflare_email, status, private_key, certificate, error_message, created_at
        FROM certificates
        WHERE id = ?
    ''', (cert_id,))
    record = cursor.fetchone()
    conn.close()
    return record

# 初始化数据库
init_db()

class SSLCertificateGenerator:
    def __init__(self, domain, email, cloudflare_email, cloudflare_api_key):
        self.domain = domain
        self.base_domain = domain.lstrip('*.')
        self.email = email
        self.cloudflare_email = cloudflare_email
        self.cloudflare_api_key = cloudflare_api_key
        self.acme_directory_url = "https://acme-v02.api.letsencrypt.org/directory"
        self.cloudflare_api_base = "https://api.cloudflare.com/client/v4"
        
    def get_cloudflare_zone_id(self):
        """获取Cloudflare的Zone ID"""
        headers = {
            "X-Auth-Email": self.cloudflare_email,
            "X-Auth-Key": self.cloudflare_api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{self.cloudflare_api_base}/zones?name={self.base_domain}",
            headers=headers
        )
        result = response.json()
        if not result.get('success') or not result.get('result'):
            raise Exception(f"获取Zone ID失败: {result.get('errors', '未知错误')}")
        return result["result"][0]["id"]

    def add_dns_record(self, zone_id, name, content):
        """添加DNS记录到Cloudflare"""
        headers = {
            "X-Auth-Email": self.cloudflare_email,
            "X-Auth-Key": self.cloudflare_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "type": "TXT",
            "name": name,
            "content": content,
            "ttl": 120
        }
        response = requests.post(
            f"{self.cloudflare_api_base}/zones/{zone_id}/dns_records",
            headers=headers,
            json=data
        )
        result = response.json()
        if not result.get('success'):
            raise Exception(f"添加DNS记录失败: {result.get('errors', '未知错误')}")
        return result["result"]["id"]

    def delete_dns_record(self, zone_id, record_id):
        """删除Cloudflare DNS记录"""
        headers = {
            "X-Auth-Email": self.cloudflare_email,
            "X-Auth-Key": self.cloudflare_api_key,
            "Content-Type": "application/json"
        }
        requests.delete(
            f"{self.cloudflare_api_base}/zones/{zone_id}/dns_records/{record_id}",
            headers=headers
        )

    def generate_private_key(self):
        """生成私钥"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key

    def create_csr(self, private_key, domain):
        """创建CSR"""
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, domain.lstrip("*."))
        ])
        
        # 添加SAN扩展以支持通配符域名
        san_list = [x509.DNSName(domain)]
        if domain.startswith("*."):
            # 如果是通配符域名，同时添加根域名
            base_domain = domain.lstrip("*.")
            san_list.append(x509.DNSName(base_domain))
        
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            subject
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).sign(private_key, hashes.SHA256(), backend=default_backend())
        
        return csr

    def generate_certificate(self):
        """生成SSL证书"""
        try:
            # 生成账户密钥
            account_key = self.generate_private_key()
            
            # 生成域名私钥
            domain_key = self.generate_private_key()
            
            # 创建ACME客户端
            net = client.ClientNetwork(josepy.JWKRSA(key=account_key))
            directory = messages.Directory.from_json(requests.get(self.acme_directory_url).json())
            acme_client = client.ClientV2(directory, net=net)
            
            # 注册账户
            registration = acme_client.new_account(
                messages.NewRegistration.from_data(email=self.email, terms_of_service_agreed=True)
            )
            
            # 创建CSR
            csr = self.create_csr(domain_key, self.domain)
            
            # 申请证书
            order = acme_client.new_order(csr.public_bytes(serialization.Encoding.PEM))
            
            # 获取Cloudflare Zone ID
            zone_id = self.get_cloudflare_zone_id()
            dns_records = []
            
            # 添加DNS验证记录
            for auth in order.authorizations:
                challenge = [c for c in auth.body.challenges if c.typ == "dns-01"][0]
                token = challenge.validation(net.key)
                record_name = "_acme-challenge"
                record_id = self.add_dns_record(zone_id, record_name, token)
                dns_records.append(record_id)
            
            # 等待DNS生效
            time.sleep(30)
            
            # 完成验证
            for auth in order.authorizations:
                challenge = [c for c in auth.body.challenges if c.typ == "dns-01"][0]
                acme_client.answer_challenge(challenge, challenge.response(net.key))
            
            # 获取证书
            certificate = acme_client.poll_and_finalize(order)
            
            # 清理DNS记录
            for record_id in dns_records:
                self.delete_dns_record(zone_id, record_id)
            
            # 返回私钥和证书
            private_key_pem = domain_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            certificate_pem = certificate.fullchain_pem
            
            return {
                'success': True,
                'private_key': private_key_pem,
                'certificate': certificate_pem
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    certificates = get_all_certificates()
    return render_template('history.html', certificates=certificates)

@app.route('/certificate/<int:cert_id>')
def certificate_detail(cert_id):
    certificate = get_certificate_by_id(cert_id)
    if not certificate:
        return "证书记录未找到", 404
    return render_template('certificate_detail.html', certificate=certificate)

@app.route('/generate', methods=['POST'])
def generate_certificate():
    data = request.json
    
    domain = data.get('domain')
    email = data.get('email')
    cloudflare_email = data.get('cloudflare_email')
    cloudflare_api_key = data.get('cloudflare_api_key')
    
    if not all([domain, email, cloudflare_email, cloudflare_api_key]):
        return jsonify({'success': False, 'error': '请填写所有必需字段'})
    
    generator = SSLCertificateGenerator(domain, email, cloudflare_email, cloudflare_api_key)
    result = generator.generate_certificate()
    
    # 保存记录到数据库
    if result['success']:
        save_certificate_record(
            domain=domain,
            email=email,
            cloudflare_email=cloudflare_email,
            status='成功',
            private_key=result['private_key'],
            certificate=result['certificate']
        )
    else:
        save_certificate_record(
            domain=domain,
            email=email,
            cloudflare_email=cloudflare_email,
            status='失败',
            error_message=result['error']
        )
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)