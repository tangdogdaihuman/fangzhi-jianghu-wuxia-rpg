REGIONS = {
    '中原': {
        'desc': '天书大陆的核心地带，武林门派林立，商贸繁华',
        'color': '#c8a45c',
        'areas': ['平安镇', '龙门客栈', '襄阳城', '擂台', '武林秘籍库'],
        'level_range': '1-30',
        'npcs': ['老拳师', '酒楼掌柜王胖子', '郭靖', '黄蓉', '说书人吴六']
    },
    '西域': {
        'desc': '天书大陆西部的神秘地带，大漠孤烟，高手隐现',
        'color': '#e8d5a3',
        'areas': ['黑风寨', '光明顶', '星宿海'],
        'level_range': '15-50',
        'npcs': ['欧阳锋', '丁春秋', '鸠摩智', '受伤镖师']
    },
    '江南': {
        'desc': '水乡泽国，桃花岛上剑气纵横，姑苏城中暗流涌动',
        'color': '#7ec8e3',
        'areas': ['桃花岛', '姑苏城', '太湖', '嘉兴'],
        'level_range': '20-45',
        'npcs': ['黄药师', '慕容复', '王语嫣']
    },
    '西域高山': {
        'desc': '天山飞雪，灵鹫宫中藏绝学，武当山上论道忙',
        'color': '#a89580',
        'areas': ['武当山', '天山', '昆仑山', '灵鹫宫'],
        'level_range': '30-60',
        'npcs': ['张三丰', '虚竹', '天山童姥', '李秋水']
    },
    '终南一带': {
        'desc': '重阳宫内藏玄机，活死人墓传佳话，华山论剑定乾坤',
        'color': '#d4c5b0',
        'areas': ['终南山', '重阳宫', '活死人墓', '华山', '百花谷'],
        'level_range': '25-70',
        'npcs': ['王重阳', '杨过', '小龙女', '周伯通', '令狐冲', '林朝英']
    },
    '大理岭南': {
        'desc': '大理国中多奇遇，万劫谷里藏真情，绝情谷底断肠声',
        'color': '#2ecc71',
        'areas': ['大理', '万劫谷', '绝情谷', '天龙寺'],
        'level_range': '15-55',
        'npcs': ['段誉', '钟灵', '木婉清', '李莫愁', '公孙绿萼']
    },
    '关外': {
        'desc': '雪原莽莽，大漠苍苍，关外英雄多豪情',
        'color': '#f39c12',
        'areas': ['大漠', '雪原', '药王谷', '商家堡', '苗家'],
        'level_range': '20-50',
        'npcs': ['胡斐', '苗人凤', '程灵素', '胡一刀']
    },
    '藏边': {
        'desc': '雪山冰川，藏边雪谷藏杀机',
        'color': '#3498db',
        'areas': ['藏边雪谷', '冰火岛', '侠客岛', '神龙岛'],
        'level_range': '40-80',
        'npcs': ['血刀老祖', '水笙', '狄云', '谢逊', '石破天']
    },
}

SUB_AREAS = {
    '平安镇': {'region': '中原', 'type': 'town', 'safe': True, 'can_rest': True, 'can_practice': True},
    '龙门客栈': {'region': '中原', 'type': 'inn', 'safe': True, 'can_rest': True},
    '襄阳城': {'region': '中原', 'type': 'city', 'safe': True, 'can_rest': True},
    '擂台': {'region': '中原', 'type': 'arena', 'safe': True, 'can_practice': True},
    '武林秘籍库': {'region': '中原', 'type': 'library', 'safe': True},
    '回春堂': {'region': '中原', 'type': 'heal', 'safe': True, 'can_rest': True},
    '温泉谷': {'region': '中原', 'type': 'spring', 'safe': True, 'can_rest': True, 'can_practice': True},
    '黑风寨': {'region': '西域', 'type': 'danger', 'safe': False, 'can_practice': True},
    '光明顶': {'region': '西域', 'type': 'sect', 'safe': True, 'can_practice': True},
    '星宿海': {'region': '西域', 'type': 'danger', 'safe': False, 'can_practice': True},
    '武当山': {'region': '西域高山', 'type': 'sect', 'safe': True, 'can_practice': True},
    '天山': {'region': '西域高山', 'type': 'mountain', 'safe': False, 'can_practice': True},
    '昆仑山': {'region': '西域高山', 'type': 'mountain', 'safe': False, 'can_practice': True},
    '灵鹫宫': {'region': '西域高山', 'type': 'sect', 'safe': True, 'can_practice': True},
    '华山': {'region': '终南一带', 'type': 'mountain', 'safe': False, 'can_practice': True},
    '桃花岛': {'region': '江南', 'type': 'sect', 'safe': True, 'can_practice': True},
    '姑苏城': {'region': '江南', 'type': 'city', 'safe': True, 'can_rest': True},
    '大理': {'region': '大理岭南', 'type': 'city', 'safe': True, 'can_rest': True},
    '万劫谷': {'region': '大理岭南', 'type': 'valley', 'safe': True, 'can_practice': True},
    '绝情谷': {'region': '大理岭南', 'type': 'danger', 'safe': False, 'can_practice': True},
    '大漠': {'region': '关外', 'type': 'desert', 'safe': False, 'can_practice': True},
    '雪原': {'region': '关外', 'type': 'snow', 'safe': False, 'can_practice': True},
    '药王谷': {'region': '关外', 'type': 'valley', 'safe': True, 'can_rest': True, 'can_practice': True},
}
