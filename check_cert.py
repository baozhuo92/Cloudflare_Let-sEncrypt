from cryptography import x509
from cryptography.hazmat.backends import default_backend

# 读取证书文件
with open('cert.pem', 'rb') as f:
    cert_data = f.read()

# 解析证书
cert = x509.load_pem_x509_certificate(cert_data, default_backend())

# 获取主题信息
subject = cert.subject
print(f"证书主题: {subject}")

# 获取SAN扩展
try:
    san_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    san_names = san_ext.value
    print("\n证书包含的域名:")
    for name in san_names:
        if isinstance(name, x509.DNSName):
            print(f"  - {name.value}")
except x509.ExtensionNotFound:
    print("未找到SAN扩展")

# 检查是否为通配符证书
has_wildcard = False
for name in san_names:
    if isinstance(name, x509.DNSName) and name.value.startswith('*.'):
        has_wildcard = True
        break

if has_wildcard:
    print("\n✅ 这是一个通配符域名证书")
else:
    print("\n❌ 这不是通配符域名证书")