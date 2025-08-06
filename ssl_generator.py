import requests
import time
import json
from acme import client, messages
from acme.challenges import DNS01
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from josepy import JWKRSA
import OpenSSL
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SSLCertificateGenerator:
    def __init__(self, cf_email, cf_api_key):
        self.cf_email = cf_email
        self.cf_api_key = cf_api_key
        self.acme_directory_url = 'https://acme-v02.api.letsencrypt.org/directory'
        
    def get_zone_id(self, domain):
        """获取域名的Zone ID"""
        # 提取根域名
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            root_domain = '.'.join(domain_parts[-2:])
        else:
            root_domain = domain
            
        headers = {
            'X-Auth-Email': self.cf_email,
            'X-Auth-Key': self.cf_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://api.cloudflare.com/client/v4/zones?name={root_domain}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['result']:
                return data['result'][0]['id']
        
        raise Exception(f"无法获取域名 {root_domain} 的Zone ID")
    
    def add_dns_record(self, zone_id, name, content):
        """添加DNS记录"""
        headers = {
            'X-Auth-Email': self.cf_email,
            'X-Auth-Key': self.cf_api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            'type': 'TXT',
            'name': name,
            'content': content,
            'ttl': 120
        }
        
        response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                return result['result']['id']
        
        raise Exception(f"添加DNS记录失败: {response.text}")
    
    def delete_dns_record(self, zone_id, record_id):
        """删除DNS记录"""
        headers = {
            'X-Auth-Email': self.cf_email,
            'X-Auth-Key': self.cf_api_key
        }
        
        response = requests.delete(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}',
            headers=headers,
            timeout=30
        )
        
        return response.status_code == 200
    
    def generate_private_key(self):
        """生成私钥"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        return private_key
    
    def generate_csr(self, private_key, domain):
        """生成证书签名请求"""
        # 方案1：CN直接使用原域名，避免域名不匹配问题
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, domain)
        ])
        
        # 构建SAN列表
        san_list = [x509.DNSName(domain)]
        
        # 如果是通配符域名，同时添加根域名
        if domain.startswith("*."):
            base_domain = domain.lstrip("*.")
            san_list.append(x509.DNSName(base_domain))
        
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            subject
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False
        ).sign(private_key, hashes.SHA256())
        
        return csr
    
    def generate_certificate(self, domain, email):
        """生成SSL证书的主要方法"""
        try:
            print(f"开始为域名 {domain} 生成证书...")
            
            # 生成账户私钥
            account_key = self.generate_private_key()
            jwk = JWKRSA(key=account_key)
            
            # 创建带有超时配置的ACME客户端
            # 配置网络客户端，确保能获取完整证书链
            net = client.ClientNetwork(
                jwk, 
                user_agent='ssl-cert-generator/1.0', 
                timeout=120,
                verify_ssl=True  # 确保SSL验证
            )
            
            # 获取ACME目录并创建客户端
            directory = client.ClientV2.get_directory(self.acme_directory_url, net)
            acme_client = client.ClientV2(directory, net=net)
            
            print(f"ACME客户端初始化成功，目录URL: {self.acme_directory_url}")
            
            # 注册账户
            new_account = messages.NewRegistration.from_data(
                email=email,
                terms_of_service_agreed=True
            )
            account = acme_client.new_account(new_account)
            print("ACME账户注册成功")
            
            # 生成证书私钥和CSR
            cert_private_key = self.generate_private_key()
            csr = self.generate_csr(cert_private_key, domain)
            
            # 将CSR转换为PEM格式
            csr_pem = csr.public_bytes(serialization.Encoding.PEM)
            
            # 创建订单
            order = acme_client.new_order(csr_pem)
            print("创建证书订单成功")
            
            # 处理挑战
            dns_records_to_cleanup = []  # 存储需要清理的DNS记录
            
            try:
                for authorization in order.authorizations:
                    domain_name = authorization.body.identifier.value
                    print(f"处理域名 {domain_name} 的验证...")
                    
                    # 找到DNS挑战
                    dns_challenge = None
                    for challenge in authorization.body.challenges:
                        if isinstance(challenge.chall, DNS01):
                            dns_challenge = challenge
                            break
                    
                    if not dns_challenge:
                        raise Exception("未找到DNS挑战")
                    
                    # 获取挑战响应
                    response, validation = dns_challenge.response_and_validation(jwk)
                    
                    # 添加DNS记录
                    zone_id = self.get_zone_id(domain_name)
                    record_name = f"_acme-challenge.{domain_name}"
                    record_id = self.add_dns_record(zone_id, record_name, validation)
                    print(f"DNS记录添加成功: {record_name}")
                    
                    # 保存记录信息用于后续清理
                    dns_records_to_cleanup.append({
                        'zone_id': zone_id,
                        'record_id': record_id,
                        'domain_name': domain_name
                    })
                
                # 等待所有DNS记录传播
                print("等待DNS记录传播...")
                time.sleep(30)
                
                # 响应所有挑战
                for authorization in order.authorizations:
                    domain_name = authorization.body.identifier.value
                    
                    # 找到DNS挑战
                    dns_challenge = None
                    for challenge in authorization.body.challenges:
                        if isinstance(challenge.chall, DNS01):
                            dns_challenge = challenge
                            break
                    
                    if dns_challenge:
                        response, _ = dns_challenge.response_and_validation(jwk)
                        acme_client.answer_challenge(dns_challenge, response)
                        print(f"域名 {domain_name} 挑战响应成功")
                
                # 等待所有验证完成
                print("等待验证完成...")
                time.sleep(30)
                
            finally:
                # 清理所有DNS记录
                for record_info in dns_records_to_cleanup:
                    try:
                        self.delete_dns_record(record_info['zone_id'], record_info['record_id'])
                        print(f"DNS记录清理完成: _acme-challenge.{record_info['domain_name']}")
                    except Exception as cleanup_error:
                        print(f"清理DNS记录失败: {cleanup_error}")
            
            # 完成订单并获取证书
            print("完成订单并获取证书...")
            try:
                # 使用poll_and_finalize方法完成订单
                finalized_order = acme_client.poll_and_finalize(order)
                
                # 获取完整证书链
                fullchain_pem = finalized_order.fullchain_pem
                if not fullchain_pem:
                    raise Exception("无法获取证书链")
                
                # 验证证书链内容
                cert_count = fullchain_pem.count('-----BEGIN CERTIFICATE-----')
                print(f"获取到证书链，包含 {cert_count} 个证书")
                
                if cert_count < 2:
                    print("警告: 证书链可能不完整，只包含服务器证书")
                    print("这可能导致 'unable to get local issuer certificate' 错误")
                else:
                    print(f"✓ 证书链完整，包含服务器证书和 {cert_count-1} 个中间/根证书")
                
            except Exception as e:
                raise Exception(f"证书获取失败: {str(e)}")
            
            print("证书生成成功！")
            
            # 转换私钥为PEM格式
            private_key_pem = cert_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            return {
                'success': True,
                'private_key': private_key_pem,
                'certificate': fullchain_pem
            }
            
        except Exception as e:
            error_msg = f"证书生成失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg
            }