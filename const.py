CARD_CODE = dict(
    xiaoqiao=b'\xb1\x36\x01\x00',
    zumao=b'\xfc\x32\x01\x00',
    lvmeng=b'\xf5\x32\x01\x00',
    zhangliao=b'\xcc\x32\x01\x00',

)


__SERVER_LIST = [{'id': 1, 'ip': '128.14.236.13', 'state': 1, 'name': '三國霸業', 'order_number': 1, 'port': 30000}, {'id': 2, 'ip': '128.14.236.13', 'state': 1, 'name': '金戈劍雨', 'order_number': 2, 'port': 30000}, {'id': 3, 'ip': '128.14.236.13', 'state': 1, 'name': '虎嘯龍吟', 'order_number': 3, 'port': 30000}, {'id': 4, 'ip': '128.14.236.13', 'state': 1, 'name': '鐵馬冰河', 'order_number': 4, 'port': 30000}, {'id': 5, 'ip': '128.14.236.13', 'state': 1, 'name': '風聲鶴唳', 'order_number': 5, 'port': 30000}, {'id': 6, 'ip': '128.14.236.13', 'state': 1, 'name': '亂石穿空', 'order_number': 6, 'port': 30000}, {'id': 7, 'ip': '128.14.236.13', 'state': 1, 'name': '飛龍在天', 'order_number': 7, 'port': 30000}, {'id': 8, 'ip': '128.14.236.13', 'state': 1, 'name': '大浪淘沙', 'order_number': 8, 'port': 30000}, {'id': 9, 'ip': '103.98.17.254', 'state': 1, 'name': '臥龍鳳雛', 'order_number': 9, 'port': 30000}, {'id': 10, 'ip': '103.98.17.254', 'state': 1, 'name': '星月交輝', 'order_number': 10, 'port': 30000}, {'id': 11, 'ip': '103.98.17.254', 'state': 1, 'name': '對酒當歌', 'order_number': 11, 'port': 30000}, {'id': 12, 'ip': '103.98.17.254', 'state': 1, 'name': '虎踞龍盤', 'order_number': 12, 'port': 30000}, {'id': 13, 'ip': '103.98.17.254', 'state': 1, 'name': '群雄逐鹿', 'order_number': 13, 'port': 30000}, {'id': 14, 'ip': '103.98.17.254', 'state': 1, 'name': '君臨天下', 'order_number': 14, 'port': 30000}, {'id': 15, 'ip': '103.98.17.254', 'state': 1, 'name': '臥虎藏龍', 'order_number': 15, 'port': 30000}, {'id': 16, 'ip': '103.98.17.254', 'state': 1, 'name': '驚濤拍岸', 'order_number': 16, 'port': 30000}, {'id': 17, 'ip': '128.14.236.45', 'state': 1, 'name': '其疾如風', 'order_number': 17, 'port': 30000}, {'id': 18, 'ip': '128.14.230.114', 'state': 1, 'name': '狼煙四起', 'order_number': 18, 'port': 30000}, {'id': 19, 'ip': '128.14.236.49', 'state': 1, 'name': '沃野千里', 'order_number': 19, 'port': 30000}, {'id': 20, 'ip': '128.14.230.246', 'state': 1, 'name': '石破天驚', 'order_number': 20, 'port': 30000}]
SERVER_LIST = dict()
for srv in __SERVER_LIST:
    SERVER_LIST[srv['id']] = (srv['id'], srv['ip'], srv['port'])

__EPISODES = ["""
              初入乱世
              初战黄巾 1-1
              应召入伍
              再战黄巾 1-2
              回禀何进
              同门相聚
              志同道合
              桃园三杰
              整备兵马
              并肩作战 1-3
              初遇孙坚
              增援长社
              解围长社 1-4
              初遇曹操
              黄巾之末 1-5
              窃取胜利
              师父消息
              """,
              """
              诸侯会合
              关东盟主
              首战汜水 2-1
              继续攻城 2-2
              孙坚受伤
              河北上将
              兵败华雄 2-3
              重振军威
              再战华雄 2-4
              勇冠三军
              并州狼骑 2-5
              作战会议
              张辽文远 2-6
              攻破汜水
              """,
              """
              主动请命
              邀刘同行
              先锋用意
              与曹联合
              继续进军 3-1
              闯关斩将 3-2
              势如破竹 3-3
              初遇吕姬 3-4
              飞将驰援
              进攻虎牢
              初战虎牢 3-5
              回援公孙 3-6
              智退李儒 3-7
              三杰救场
              天下无双 3-8
              出击洛阳
              """,
              """
              计划追击
              联盟裂痕
              星星之火
              同门决裂
              江东之虎
              追击董卓
              蔡邕消息 4-1
              文姬救父 4-2
              继续追击 4-3
              遭遇伏击 4-4
              杀出重围 4-5
              重整旗鼓
              再次出击 4-6
              袭击董军 4-7
              激战董卓 4-8
              文姬失散
              """,
              """
              狼狈回归
              曹操离开
              国之重器
              撤回江东
              袁军追击 5-1
              """]

EPISODES = list(item.strip().split("\n") for item in __EPISODES)
