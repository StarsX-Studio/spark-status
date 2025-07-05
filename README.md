# StarsX 服务状态监控（spark-status）

## 项目简介

StarsX 服务状态监控（spark-status）是一个实时监控多个服务状态的仪表盘系统，可监控 MySQL 数据库、Minecraft 服务器和网站的运行状态。系统提供实时状态展示、历史数据可视化和管理面板，界面简洁直观，扩展性强，前端参考至StarsX状态面板[status.starsx.cn](https://status.starsx.cn)。

## 主要功能

- **实时服务状态监控**
  - MySQL 数据库状态
  - Minecraft 服务器状态（支持基岩版）
  - 网站可用性检查
- **历史数据可视化**
  - 30天服务可用率图表
  - 状态历史记录
- **事件管理系统**
  - 添加服务事件（严重/中等/轻微）
  - 事件时间线展示
- **管理功能**
  - 管理员登录系统
  - 强制刷新状态
  - 数据清理工具

## 技术栈

- **后端**: Python, Flask
- **前端**: Bootstrap, HTML5, CSS3
- **数据库**: MySQL
- **监控组件**:
  >> `mcstatus` (Minecraft 服务器状态)
  >> `requests` (网站状态检查)
  >> `pymysql` (MySQL 连接)
- **安全**: Flask-Limiter (速率限制), PBKDF2_HMAC_SHA256 (密码哈希)

## 安装指南

### 前提条件

- Python 3.8+
- MySQL 5.7+
- 服务器开放端口: 5000 (Flask) 或 绑定至域名

### 安装步骤

1. **克隆仓库**
>>
git clone https://github.com/StarsX-Studio/spark-status.git
cd spark-status
>>

2. **安装依赖**
>>
pip install -r requirements.txt
>>

3. **配置环境变量**
创建 `.env` 文件：
>>
DB_HOST=your_mysql_host<br/>
DB_USER=your_db_user<br/>
DB_PASSWORD=your_db_password<br/>
DB_NAME=status_monitor<br/>
ADMIN_PASSWORD_1=your_admin_password<br/>
ADMIN_PASSWORD_2=your_admin_password
>>

4. **初始化数据库**
>>
# 在 app.py 中取消注释以下行并运行一次
if __name__ == '__main__': <br/>
    init_database()<br/>
    app.run(host='0.0.0.0', port=5000, debug=False)
>>

5. **启动应用**
>>
python app.py
>>

## 配置说明

### 主要配置文件

- **app.py**: 主应用逻辑
- **config.py**: 数据库配置
- **.env**: 环境变量配置

### 监控服务配置

修改 `app.py` 中的服务配置：
>>
# Minecraft 服务器地址
server_address = "example.com:19132"

# 监控的网站列表
websites = [
    {'url': 'https://example.com', 'keyword': 'example', 'name': 'example（示例网站）'},
    {'url': 'https://www.example.com', 'keyword': 'example', 'name': 'example（示例网站）'}
]
>>

### 管理员账户

默认管理员账户：
- 用户名: `1` 或 `2`（实际需要自行更改）
- 密码: 通过环境变量设置

## 使用指南

### 仪表盘功能

1. **服务状态卡片**
   - 实时显示 MySQL、Minecraft 和网站状态
   - 颜色标识：绿色（在线）、红色（离线）
   - 显示最后检查时间戳

2. **可用率图表**
   - 30天服务可用率可视化
   - 悬停查看每日具体可用率
   - 按服务类型着色区分

3. **最近事件面板**
   - 按严重程度分类（严重/中等/轻微）
   - 显示事件时间和描述

### 管理功能

1. **添加事件**
   - 选择事件级别（严重/中等/轻微）
   - 输入事件描述
   - 提交后立即显示在仪表盘

2. **数据管理**
   - 清理超过指定天数的历史数据
   - 强制刷新所有服务状态
   - 删除事件记录

## 开源协议

本项目采用 GNU GPLv3 许可证开源，您可以自由使用、修改和分发代码，但必须遵循以下要求：
1. 任何基于本项目的衍生作品必须以相同许可证开源
2. 必须保留原始版权声明和许可证文件
3. 修改后的代码必须明确标注修改内容
4. 不得将本项目用于专利诉讼
5. 不得通过此项目破解导致影响其使用人与程序的正常运行
## 贡献指南

欢迎提交 Pull Request 或 Issue。贡献前请阅读：
1. Fork 项目并创建新分支
2. 更新相关文档
3. 测试所有修改功能
4. 提交清晰的 commit 信息

## 问题反馈

遇到问题请提交 Issue，包括：
- 问题描述
- 复现步骤
- 期望行为
- 环境信息

---

**StarsX Studio** © 2025 | [www.starsx.cn](https://www.starsx.cn)
