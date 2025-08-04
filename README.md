# SSL证书管理系统

这是一个基于Flask的SSL证书管理系统，支持通过Let's Encrypt自动申请SSL证书，并提供用户登录和证书记录管理功能。

## 功能特性

- 🔐 **邮箱登录系统**：用户通过邮箱注册和登录
- 📧 **邮箱验证**：注册时需要验证邮箱地址
- 🔒 **用户隔离**：每个用户只能查看自己的证书记录
- 🎫 **SSL证书申请**：通过Let's Encrypt自动申请SSL证书
- ☁️ **Cloudflare集成**：支持Cloudflare DNS验证
- 📊 **证书管理**：查看证书历史记录和详情
- 📱 **响应式设计**：支持移动端和桌面端

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置邮件服务器

创建 `config.py` 文件并配置邮件服务器：

```python
# config.py
class Config:
    SECRET_KEY = 'your-secret-key-here'
    
    # 邮件服务器配置（以Gmail为例）
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'  # Gmail应用专用密码
    MAIL_DEFAULT_SENDER = 'your-email@gmail.com'
```

#### 邮件服务器配置说明

**Gmail配置：**
1. 开启两步验证
2. 生成应用专用密码：https://myaccount.google.com/apppasswords
3. 使用应用专用密码作为`MAIL_PASSWORD`

**QQ邮箱配置：**
```python
MAIL_SERVER = 'smtp.qq.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@qq.com'
MAIL_PASSWORD = 'your-authorization-code'  # QQ邮箱授权码
```

**163邮箱配置：**
```python
MAIL_SERVER = 'smtp.163.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@163.com'
MAIL_PASSWORD = 'your-authorization-code'  # 163邮箱授权码
```

### 3. 环境变量配置（推荐）

为了安全起见，建议使用环境变量配置敏感信息：

**Windows:**
```cmd
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=your-app-password
set SECRET_KEY=your-secret-key
```

**Linux/Mac:**
```bash
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password
export SECRET_KEY=your-secret-key
```

### 4. 运行应用

```bash
python ssl_web_app.py
```

应用将在 http://localhost:5000 启动。

## 使用说明

### 用户注册和登录

1. **注册账户**：
   - 访问 `/register` 页面
   - 输入邮箱地址和密码
   - 系统会发送验证邮件到您的邮箱
   - 点击邮件中的验证链接完成注册

2. **登录系统**：
   - 访问 `/login` 页面
   - 输入已验证的邮箱和密码
   - 登录成功后可以申请和管理SSL证书

### SSL证书申请

1. **填写申请信息**：
   - 域名：要申请证书的域名
   - 邮箱：Let's Encrypt通知邮箱
   - Cloudflare邮箱：Cloudflare账户邮箱
   - Cloudflare API密钥：用于DNS验证

2. **申请流程**：
   - 系统自动创建ACME挑战
   - 通过Cloudflare API添加DNS记录
   - 验证域名所有权
   - 生成并下载SSL证书

### 证书管理

- **查看历史记录**：访问 `/history` 查看所有申请记录
- **证书详情**：点击记录查看证书详细信息
- **下载证书**：在详情页面下载私钥和证书文件

## 快速开始（Docker）

### 使用Docker Compose（推荐）

1. **克隆或下载项目文件**

2. **配置环境变量**
   从示例文件创建.env文件：
   ```bash
   cp .env.example .env
   ```
   然后编辑.env文件，填入您的邮件服务器配置：
   ```
   # 邮件服务器配置
   MAIL_SERVER=smtp.163.com
   MAIL_PORT=465
   MAIL_USE_SSL=true
   MAIL_USERNAME=your-email@163.com
   MAIL_PASSWORD=your-authorization-code
   MAIL_DEFAULT_SENDER=your-email@163.com
   
   # Flask应用密钥
   SECRET_KEY=your-secret-key-change-this-in-production
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **访问应用**
   打开浏览器访问：http://localhost:5000

### 手动Docker构建

1. **构建Docker镜像**
   ```bash
   docker build -t ssl-cert-generator .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name ssl-certificate-generator \
     -p 5000:5000 \
     -e MAIL_SERVER=smtp.163.com \
     -e MAIL_PORT=465 \
     -e MAIL_USE_SSL=true \
     -e MAIL_USERNAME=your-email@163.com \
     -e MAIL_PASSWORD=your-authorization-code \
     -e MAIL_DEFAULT_SENDER=your-email@163.com \
     -e SECRET_KEY=your-secret-key-change-this-in-production \
     -v $(pwd)/ssl_certificates.db:/app/ssl_certificates.db \
     ssl-cert-generator
   ```
   
   或者使用环境变量文件：
   ```bash
   docker run -d \
     --name ssl-certificate-generator \
     -p 5000:5000 \
     --env-file .env \
     -v $(pwd)/ssl_certificates.db:/app/ssl_certificates.db \
     ssl-cert-generator
   ```

## 配置说明

### 环境变量

**Flask应用配置：**
- `FLASK_ENV`: Flask运行环境（development/production）
- `FLASK_DEBUG`: 是否启用调试模式（0/1）
- `SECRET_KEY`: Flask应用密钥（生产环境必须更改）

**邮件服务器配置：**
- `MAIL_SERVER`: SMTP服务器地址（如：smtp.163.com）
- `MAIL_PORT`: SMTP端口号（如：465）
- `MAIL_USE_SSL`: 是否使用SSL（true/false）
- `MAIL_USERNAME`: 邮箱用户名
- `MAIL_PASSWORD`: 邮箱密码或授权码
- `MAIL_DEFAULT_SENDER`: 默认发件人邮箱

### 数据持久化

- 数据库文件：`ssl_certificates.db`

## 使用方法

1. **准备Cloudflare信息**
   - Cloudflare账户邮箱
   - Cloudflare API密钥
   - 确保域名已添加到Cloudflare

2. **申请证书**
   - 访问Web界面
   - 填写域名、邮箱和Cloudflare信息
   - 点击"生成证书"按钮
   - 等待证书生成完成

3. **查看历史记录**
   - 点击"申请记录"查看所有申请历史
   - 点击具体记录查看证书详情
   - 支持复制和下载证书文件

## 支持的域名格式

- 单域名：`example.com`
- 通配符域名：`*.example.com`

## 技术栈

- **后端**: Flask, Python 3.11
- **数据库**: SQLite
- **证书**: Let's Encrypt ACME v2
- **DNS**: Cloudflare API
- **容器**: Docker, Docker Compose

## 文件结构

```
.
├── ssl_web_app.py          # 主应用文件
├── templates/              # HTML模板
│   ├── index.html         # 主页面
│   ├── history.html       # 历史记录页面
│   └── certificate_detail.html # 证书详情页面
├── Dockerfile             # Docker构建文件
├── docker-compose.yaml    # Docker Compose配置
├── requirements.txt       # Python依赖
├── .dockerignore         # Docker忽略文件
└── README.md             # 说明文档
```

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up --build -d

# 进入容器
docker-compose exec ssl-cert-app bash
```

## 注意事项

1. **Cloudflare API权限**：确保API密钥有DNS编辑权限
2. **域名解析**：域名必须已添加到Cloudflare并正确解析
3. **网络访问**：容器需要能够访问Let's Encrypt和Cloudflare API
4. **数据备份**：定期备份`ssl_certificates.db`数据库文件

## 故障排除

### 常见问题

1. **证书申请失败**
   - 检查Cloudflare API密钥是否正确
   - 确认域名已添加到Cloudflare
   - 查看容器日志获取详细错误信息

2. **容器启动失败**
   - 检查端口5000是否被占用
   - 确认Docker和Docker Compose已正确安装

3. **数据丢失**
   - 确保数据卷正确挂载
   - 检查文件权限设置

### 查看日志

```bash
# 查看应用日志
docker-compose logs ssl-cert-app

# 实时查看日志
docker-compose logs -f ssl-cert-app
```

## 安全建议

- 不要在生产环境中启用DEBUG模式
- 定期更新依赖包版本
- 妥善保管Cloudflare API密钥
- 定期备份证书数据

## 许可证

本项目仅供学习和个人使用。