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
import requests
import global_mod

url = 'https://www.starsx.cn'
keyword = '自我创新'

def check_website():
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            if keyword in response.text:
                return True, f'{url} 页面可以正常访问（识别到了字符 "{keyword}"）'
            else:
                return False, f'{url} 页面不可正常访问（未找到关键词）'
        else:
            return False, f'{url} 访问异常，状态码：{response.status_code}'
    except requests.RequestException as e:
        return False, f'请求发生错误：{e}'

if __name__ == "__main__":
    status, message = check_website()
    print(message)
    global_mod.web_state = status