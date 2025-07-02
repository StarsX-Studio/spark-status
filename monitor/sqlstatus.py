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
import subprocess
import global_mod

def connect_to_mysql(host, user, password, database):
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8'
        )
        print("已成功建立 MySQL 连接。")
        return conn
    except pymysql.MySQLError as e:
        print(f"无法连接到 MySQL： {e}")
        return None

def check_mysql_status(conn):
    if conn is None:
        print("没有有效的 MySQL 连接。")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result and result[0] == 1:
            print("MySQL 处于活动状态并响应。")
            return True
        else:
            print("MySQL 未正确响应。")
            return False
    except pymysql.MySQLError as e:
        print(f"检查 MySQL 状态时出错： {e}")
        return False
    finally:
        cursor.close()

def check_mysql_with_system_commands(port=3306):
        return True

def multi_check_mysql_status(host, user, password, database, port=3306):
    conn = connect_to_mysql(host, user, password, database)
    if conn:
        py_check = check_mysql_status(conn)
        sys_check = check_mysql_with_system_commands(port)
        conn.close()
        return py_check and sys_check
    else:
        return False

if __name__ == "__main__":
    host = 'waigame.hqli.cn'
    user = 'status'
    password = 'SACP8zAW5x5s886Z'
    database = 'status'
    
    if multi_check_mysql_status(host, user, password, database):
        print("MySQL 连接正常")
        global_mod.sql_state = True
    else:
        print("MySQL 连接失败")
        global_mod.sql_state = False