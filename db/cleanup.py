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
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()
# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'monitor_user'),
    'password': os.getenv('DB_PASSWORD', 'monitor_pass'),
    'database': os.getenv('DB_NAME', 'status_monitor')
}

def cleanup_old_data(days=30):
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # 删除30天前的状态记录
            delete_date = datetime.utcnow() - timedelta(days=days)
            cursor.execute("""
                DELETE FROM service_status
                WHERE timestamp < %s
            """, (delete_date,))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            
            print(f"已删除 {deleted_rows} 条超过 {days} 天的旧状态记录")
            
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_old_data()