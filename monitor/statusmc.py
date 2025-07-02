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
from mcstatus import BedrockServer
import global_mod
def check_server_status(server_address):
    try:
        server = BedrockServer.lookup(server_address)
        status = server.status()
        print("服务器在线")
        global_mod.mc_state = True
        print("服务器版本: ", status.version.name)
        print("在线玩家数量: ", status.players.online)
        print("最大玩家数量: ", status.players.max)
    except Exception as e:
        print("服务器离线或无法连接")
        global_mod.mc_state = False

server_address = "pstars.top:19132"

check_server_status(server_address)