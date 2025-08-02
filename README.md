# SSL证书申请系统 Docker部署指南

这是一个基于Flask的SSL证书申请系统，支持通过Cloudflare DNS验证自动申请Let's Encrypt证书。

## 功能特性

- 🔒 自动申请Let's Encrypt SSL证书
- 🌐 支持通配符域名证书
- ☁️ 集成Cloudflare DNS验证
- 📊 SQLite数据库存储申请记录
- 🎨 现代化Web界面
- 📋 证书申请历史记录
- 📥 证书和私钥下载功能

## 快速开始

### 使用Docker Compose（推荐）

1. **克隆或下载项目文件**

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **访问应用**
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
     -v $(pwd)/data:/app/data \
     -v $(pwd)/ssl_certificates.db:/app/ssl_certificates.db \
     ssl-cert-generator
   ```

## 配置说明

### 环境变量

- `FLASK_ENV`: Flask运行环境（development/production）
- `FLASK_DEBUG`: 是否启用调试模式（0/1）

### 数据持久化

- 数据库文件：`ssl_certificates.db`
- 数据目录：`./data`

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