# 项目架构说明

## 模块化重构概述

本项目已完成模块化重构，将原本集中在单个文件中的代码分离到不同的模块中，提高了代码的可维护性和可扩展性。

## 项目结构

```
ssl-certificate-system/
├── app.py                 # 主应用入口文件
├── ssl_web_app.py         # 原始文件（已废弃，保留作参考）
├── database.py            # 数据库操作模块
├── ssl_generator.py       # SSL证书生成模块
├── config.py              # 配置文件
├── requirements.txt       # 依赖包列表
├── ssl_certificates.db    # SQLite数据库文件
├── routes/                # 路由模块目录
│   ├── __init__.py       # 路由包初始化
│   ├── auth.py           # 认证相关路由
│   └── main.py           # 主要功能路由
└── templates/             # HTML模板目录
    ├── index.html
    ├── login.html
    ├── register.html
    ├── history.html
    └── certificate_detail.html
```

## 模块说明

### 1. app.py - 主应用文件
- Flask应用初始化
- 配置加载
- 扩展初始化（Flask-Login, Flask-Mail）
- 蓝图注册
- 数据库初始化

### 2. database.py - 数据库操作模块
- **用户管理**：
  - `User` 类：用户模型
  - `create_user()`: 创建新用户
  - `verify_user()`: 验证用户登录
  - `get_user_by_id()`: 根据ID获取用户
  - `verify_email_token()`: 验证邮箱令牌
  - `send_verification_email()`: 发送验证邮件

- **证书管理**：
  - `save_certificate_record()`: 保存证书记录
  - `get_user_certificates()`: 获取用户证书列表
  - `get_certificate_by_id()`: 获取证书详情

- **数据库初始化**：
  - `init_db()`: 初始化数据库表结构

### 3. ssl_generator.py - SSL证书生成模块
- **SSLCertificateGenerator 类**：
  - `get_zone_id()`: 获取Cloudflare Zone ID
  - `add_dns_record()`: 添加DNS验证记录
  - `delete_dns_record()`: 删除DNS记录
  - `generate_private_key()`: 生成私钥
  - `generate_csr()`: 生成证书签名请求
  - `generate_certificate()`: 主要证书生成方法

### 4. routes/ - 路由模块

#### routes/auth.py - 认证路由
- `/login` - 用户登录
- `/register` - 用户注册
- `/verify/<token>` - 邮箱验证
- `/logout` - 用户退出

#### routes/main.py - 主要功能路由
- `/` - 首页（证书申请）
- `/history` - 证书历史记录
- `/certificate/<int:cert_id>` - 证书详情
- `/generate` - 证书生成API

### 5. config.py - 配置模块
- Flask应用配置
- 邮件服务器配置
- 支持环境变量配置
- 多种邮件服务商配置示例

## 模块化优势

### 1. 代码组织清晰
- **单一职责**：每个模块负责特定功能
- **逻辑分离**：认证、数据库、证书生成等功能独立
- **易于维护**：修改某个功能不影响其他模块

### 2. 可扩展性强
- **新功能添加**：可以轻松添加新的路由模块
- **功能扩展**：每个模块可以独立扩展功能
- **第三方集成**：便于集成新的服务或API

### 3. 测试友好
- **单元测试**：每个模块可以独立测试
- **模拟测试**：可以轻松模拟依赖模块
- **集成测试**：模块间接口清晰，便于集成测试

### 4. 团队协作
- **并行开发**：不同开发者可以同时开发不同模块
- **代码审查**：模块化的代码更容易进行代码审查
- **版本控制**：减少代码冲突，提高协作效率

## 使用说明

### 启动应用
```bash
python app.py
```

### 添加新功能
1. **新路由**：在 `routes/` 目录下创建新的蓝图文件
2. **数据库操作**：在 `database.py` 中添加新的数据库函数
3. **业务逻辑**：创建新的业务逻辑模块
4. **配置**：在 `config.py` 中添加新的配置项

### 模块依赖关系
```
app.py
├── routes/auth.py → database.py
├── routes/main.py → database.py, ssl_generator.py
├── database.py → config.py (mail)
└── ssl_generator.py
```

## 迁移说明

原始的 `ssl_web_app.py` 文件已被拆分为多个模块：
- 应用初始化 → `app.py`
- 数据库操作 → `database.py`
- SSL证书生成 → `ssl_generator.py`
- 路由处理 → `routes/auth.py` 和 `routes/main.py`

所有功能保持不变，但代码结构更加清晰和模块化。