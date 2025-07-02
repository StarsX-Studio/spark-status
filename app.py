# Copyright (C) 2025 StarsX Studio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import subprocess
from datetime import datetime, timedelta
import os
import json
import logging
from decimal import Decimal
from dotenv import load_dotenv
import secrets
import requests
import time  # 添加延迟防止暴力破解
from mcstatus import BedrockServer

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.urandom(24)  # 随机生成安全密钥

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StatusMonitor')

# 安全防护
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', ''),
    'user': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', ''),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
@app.context_processor
def inject_now():
    return {'now': datetime.now()}
def get_db():
    return pymysql.connect(**DB_CONFIG)
def generate_salt():
    """生成16字节的随机盐"""
    return secrets.token_hex(16)
def hash_password(password, salt=None):
    """使用PBKDF2_HMAC_SHA256算法生成带盐的密码哈希"""
    if not salt:
        salt = generate_salt()
    salted_password = salt + password
    return generate_password_hash(
        salted_password,
        method='pbkdf2:sha256:600000',
        salt_length=16
    ), salt
def verify_password(password_hash, password, salt):
    """验证带盐的密码"""
    salted_password = salt + password
    return check_password_hash(password_hash, salted_password)
def init_database():
    """
    初始化数据库结构并确保所有必需的表和用户存在
    包含修复salt列和用户数据
    """
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(64) NOT NULL DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    service VARCHAR(20) NOT NULL,
                    status BOOLEAN NOT NULL,
                    details TEXT,
                    timestamp DATETIME NOT NULL,
                    INDEX idx_service (service),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    level ENUM('critical', 'medium', 'minor') NOT NULL,
                    description TEXT NOT NULL,
                    created_by VARCHAR(50) NOT NULL,
                    created_at DATETIME NOT NULL,
                    INDEX idx_level (level),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'salt'
            """, (DB_CONFIG['database'],))
            
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN salt VARCHAR(64) NOT NULL DEFAULT ''
                    AFTER password_hash
                """)
                logger.info("已添加缺失的salt列")
            
            # 初始化/修复用户数据
            # username : 你的管理员用户名，默认1和2，密码在 .env 文件配置
            
            initial_users = [
                {
                    'username': '1',
                    'password': os.getenv('ADMIN_PASSWORD_XINRAIN', 'Lcp970920')
                },
                {
                    'username': '2',
                    'password': os.getenv('ADMIN_PASSWORD_XINGXUAN', 'waigame_admin_xingxuanpassword')
                }
            ]
            
            for user_data in initial_users:
                username = user_data['username']
                password = user_data['password']
                cursor.execute(
                    "SELECT id, password_hash, salt FROM users WHERE username = %s",
                    (username,)
                )
                existing_user = cursor.fetchone()
                
                if existing_user:
                    needs_update = False
                    if not existing_user.get('salt'):
                        logger.info(f"用户 {username} 缺少salt值，正在修复...")
                        needs_update = True
                    if not existing_user['password_hash'].startswith('pbkdf2:sha256:'):
                        logger.info(f"用户 {username} 使用旧密码哈希，正在升级...")
                        needs_update = True
                    if needs_update:
                        new_salt = generate_salt()
                        new_hash, _ = hash_password(password, new_salt)
                        cursor.execute(
                            "UPDATE users SET password_hash = %s, salt = %s WHERE username = %s",
                            (new_hash, new_salt, username)
                        )
                        logger.info(f"已更新用户 {username} 的凭据")
                else:
                    password_hash, salt = hash_password(password)
                    cursor.execute(
                        """INSERT INTO users 
                        (username, password_hash, salt) 
                        VALUES (%s, %s, %s)""",
                        (username, password_hash, salt)
                    )
                    logger.info(f"已创建新用户 {username}")
            conn.commit()
            logger.info("数据库初始化完成")
            cursor.execute("SELECT username, LENGTH(password_hash) as hash_len, LENGTH(salt) as salt_len FROM users")
            logger.debug("用户数据验证: " + str(cursor.fetchall()))
    except Exception as e:
        logger.error("数据库初始化失败", exc_info=True)
        raise RuntimeError(f"数据库初始化失败: {str(e)}") from e
    finally:
        if 'conn' in locals() and conn:
            conn.close()
@app.before_request
def protect_monitor_scripts():
    if request.path.startswith('/monitor/'):
        return "Access denied", 403

# 验证用户凭据
def verify_credentials(username, password):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE username = %s", 
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                logger.debug(f"验证用户: {username}")
                logger.debug(f"数据库盐值: {user['salt']}")
                logger.debug(f"数据库哈希: {user['password_hash']}")
                
                # 验证密码
                if verify_password(user['password_hash'], password, user['salt']):
                    return True
                else:
                    logger.warning(f"用户 {username} 密码错误")
            else:
                logger.warning(f"用户 {username} 不存在")
                
    except Exception as e:
        logger.error(f"验证凭据时出错: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
    return False
def get_user_field(user, field_name, default=None):
    if isinstance(user, dict):
        return user.get(field_name, default)
    elif isinstance(user, (tuple, list)):
        fields_order = ['id', 'username', 'password_hash', 'salt', 'created_at']
        try:
            index = fields_order.index(field_name)
            return user[index] if index < len(user) else default
        except ValueError:
            return default
    return default
def login_required(f):
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('请先登录', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# 获取服务状态（从数据库获取最新状态）
def get_service_status():
    conn = get_db()
    services = {}
    try:
        with conn.cursor() as cursor:
            # 获取每个服务的最新状态
            cursor.execute("""
                SELECT s1.* FROM service_status s1
                JOIN (
                    SELECT service, MAX(timestamp) as max_timestamp
                    FROM service_status
                    GROUP BY service
                ) s2 ON s1.service = s2.service AND s1.timestamp = s2.max_timestamp
            """)
            latest_status = cursor.fetchall()
            
            for status in latest_status:
                services[status['service']] = {
                    'status': status['status'],
                    'details': status['details'],
                    'timestamp': status['timestamp']
                }
            
            # 确保所有服务都有状态
            required_services = ['mysql', 'minecraft', 'web']
            for service in required_services:
                if service not in services:
                    services[service] = {
                        'status': False,
                        'details': '无可用状态数据',
                        'timestamp': datetime.now()
                    }
                    
    except Exception as e:
        logger.error(f"获取服务状态时出错: {e}", exc_info=True)
        # 如果出错，返回默认状态
        services = {
            'mysql': {'status': False, 'details': '获取状态失败', 'timestamp': datetime.now()},
            'minecraft': {'status': False, 'details': '获取状态失败', 'timestamp': datetime.now()},
            'web': {'status': False, 'details': '获取状态失败', 'timestamp': datetime.now()}
        }
    finally:
        if conn:
            conn.close()
    
    return services

# 获取状态历史数据（按天）
def get_status_history(days=30):
    conn = get_db()
    history = {}
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    service,
                    DATE(timestamp) as date,
                    ROUND(AVG(CASE WHEN status THEN 1 ELSE 0 END) * 100, 2) as uptime_percent
                FROM service_status
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY service, DATE(timestamp)
                ORDER BY date ASC
            """, (days,))
            results = cursor.fetchall()
            for row in results:
                service = row['service']
                date_str = row['date'].strftime('%Y-%m-%d')
                if service not in history:
                    history[service] = []
                uptime_value = float(row['uptime_percent'])
                
                history[service].append({
                    'date': date_str,
                    'uptime': uptime_value
                })
    except Exception as e:
        logger.error(f"获取状态历史时出错: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
    required_services = ['mysql', 'minecraft', 'web']
    for service in required_services:
        if service not in history:
            history[service] = []
    
    return history
def get_recent_events(limit=10):
    conn = get_db()
    events = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM events 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            events = cursor.fetchall()
    except Exception as e:
        logger.error(f"获取最近事件时出错: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
    
    return events
@app.route('/')
def dashboard():
    services = get_service_status()
    history = get_status_history(30)
    events = get_recent_events(10)
    
    return render_template('dashboard.html', 
                           services=services, 
                           history=history,
                           events=events)
@app.route('/api/status')
@limiter.limit("10 per minute")
def api_status():
    try:
        services = {
            'mysql': run_mysql_check(),
            'minecraft': run_minecraft_check(),
            'web': run_web_check()
        }
        record_status(services)
        return jsonify({
            'status': 'success',
            'data': services,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"API状态错误: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'获取状态失败: {str(e)}'
        }), 500

def run_mysql_check():
    try:
        result = subprocess.run(
            ['python', 'monitor/sqlstatus.py'],
            capture_output=True, text=True,
            timeout=30
        )
        # 解析脚本输出
        if "MySQL 连接正常" in result.stdout:
            return {'status': True, 'details': 'MySQL连接正常'}
        else:
            last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "无输出"
            return {'status': False, 'details': last_line}
    except Exception as e:
        return {'status': False, 'details': str(e)}

# 运行Mc检查(基岩版为示例)
def run_minecraft_check():
    server_address = "example.com:19132"
    try:
        server = BedrockServer.lookup(server_address)
        status = server.status()
        
        details = [
            f"服务器版本: {status.version.name}",
            f"在线玩家: {status.players.online}/{status.players.max}",
            f"延迟: {round(status.latency, 2)}ms"
        ]
        
        if status.players.online > 0 and status.players.sample:
            player_list = ", ".join([player.name for player in status.players.sample])
            details.append(f"在线玩家: {player_list}")
        
        return {
            'status': True,
            'details': '<br>'.join(details)
        }
    except Exception as e:
        return {
            'status': False,
            'details': f"服务器离线或无法连接: {str(e)}"
        }

# 运行Web检查 (站点必须拥有SSL证书且启用HTTPS)
def run_web_check():
    websites = [
        {'url': 'https://www.example.com', 'keyword': 'example', 'name': 'example.com'
        '示例网站'},
        {'url': 'https://example.com', 'keyword': 'example', 'name': 'example'}
    ]
    
    results = []
    online_count = 0
    
    for site in websites:
        try:
            response = requests.get(site['url'], timeout=10)
            if response.status_code == 200 and site['keyword'] in response.text:
                results.append(f"{site['name']} • 在线")
                online_count += 1
            else:
                results.append(f"{site['name']} • 异常 (状态码: {response.status_code})")
        except Exception as e:
            results.append(f"{site['name']} • 无法访问: {str(e)}")
    if online_count == len(websites):
        return {
            'status': True,
            'details': '所有网站均在线'
        }
    else:
        return {
            'status': False,
            'details': '<br>'.join(results)
        }

# 记录状态到数据库
def record_status(services):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            for service, data in services.items():
                cursor.execute("""
                    INSERT INTO service_status 
                    (service, status, details, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (service, data['status'], data['details'], datetime.now()))
        conn.commit()
    except Exception as e:
        logger.error(f"记录状态时出错: {str(e)}", exc_info=True)
    finally:
        if conn:
            conn.close()
@app.route('/api/history')
def api_history():
    try:
        days = request.args.get('days', 30, type=int)
        history = get_status_history(days)
        return jsonify(history)
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'获取历史数据失败: {str(e)}'
        }), 500

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_panel'))
        
    if request.method == 'POST':
        time.sleep(1)
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('admin/login.html')
        
        logger.info(f"登录尝试: {username}")
        
        if verify_credentials(username, password):
            session['logged_in'] = True
            session['username'] = username
            flash('登录成功', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('admin/login.html')
@app.route('/admin')
@login_required
def admin_panel():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM service_status 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            status_history = cursor.fetchall()
            
            cursor.execute("""
                SELECT COUNT(*) as total FROM service_status
                WHERE status = 0 AND timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            daily_errors = cursor.fetchone()['total']
            cursor.execute("""
                SELECT * FROM events 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_events = cursor.fetchall()
            
        return render_template('admin/panel.html', 
                             status_history=status_history,
                             daily_errors=daily_errors,
                             recent_events=recent_events,
                             username=session['username'])
    except Exception as e:
        logger.error(f"获取管理面板数据时出错: {str(e)}", exc_info=True)
        flash('加载数据时出错', 'danger')
        return render_template('admin/panel.html')
    finally:
        if conn:
            conn.close()
@app.route('/admin/add_event', methods=['POST'])
@login_required
def add_event():
    level = request.form.get('level')
    description = request.form.get('description')
    
    if not level or not description:
        return jsonify({
            'success': False,
            'message': '请填写所有字段'
        }), 400
    
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO events 
                (level, description, created_by, created_at)
                VALUES (%s, %s, %s, %s)
            """, (level, description, session['username'], datetime.now()))
        conn.commit()
        return jsonify({
            'success': True,
            'message': '事件已添加'
        })
    except Exception as e:
        logger.error(f"添加事件时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '添加事件失败'
        }), 500
    finally:
        if conn:
            conn.close()
@app.route('/admin/force_refresh', methods=['POST'])
@login_required
def force_refresh():
    try:
        services = {
            'mysql': run_mysql_check(),
            'minecraft': run_minecraft_check(),
            'web': run_web_check()
        }
        record_status(services)
        
        return jsonify({
            'success': True,
            'message': '状态已强制刷新'
        })
    except Exception as e:
        logger.error(f"强制刷新失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'刷新状态失败: {str(e)}'
        }), 500
@app.route('/admin/cleanup', methods=['POST'])
@login_required
def cleanup_data():
    days = request.form.get('days', 30, type=int)
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM service_status 
                WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            status_deleted = cursor.rowcount
            cursor.execute("""
                DELETE FROM events 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            events_deleted = cursor.rowcount 
            conn.commit()  
        return jsonify({
            'success': True,
            'message': f'已清理 {status_deleted} 条状态记录和 {events_deleted} 条事件记录'
        })
    except Exception as e:
        logger.error(f"清理数据时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '清理数据失败'
        }), 500
    finally:
        if conn:
            conn.close()
@app.route('/admin/delete_event/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()
            return jsonify({'success': True, 'message': '事件已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn: 
            conn.close()
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('您已退出登录', 'info')
    return redirect(url_for('admin_login'))
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
def reset_user_passwords():
    conn = get_db()
    try:
        users = [
            ('xinrain', os.getenv('ADMIN_PASSWORD_XINRAIN', 'Lcp970920')),
            ('xingxuan', os.getenv('ADMIN_PASSWORD_XINGXUAN', 'waigame_admin_xingxuanpassword'))
        ]
        with conn.cursor() as cursor:
            for username, password in users:
                password_hash, salt = hash_password(password)
                cursor.execute(
                    "UPDATE users SET password_hash = %s, salt = %s WHERE username = %s",
                    (password_hash, salt, username)
                )
                logger.info(f"已重置用户 {username} 的密码")
        
        conn.commit()
    except Exception as e:
        logger.error(f"重置密码时出错: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__': 
    # 启动应用
    #init_database() 第一次启动应用请删除该注释以初始化数据库（需要先配置.env）
    app.run(host='0.0.0.0', port=5000, debug=False)