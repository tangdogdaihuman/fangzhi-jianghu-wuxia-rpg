/* ========== 放置江湖 · 武侠传 - 游戏脚本 ========== */

/* ========== 全局状态 ========== */
var 游戏状态 = null;
var 日志列表 = [];
var 刷新计时器 = null;
var 自动滚动 = true;
var 技能面板展开 = false;
var 物品面板展开 = false;
var 已访问地点 = {};
var 正在移动 = false;
var 移动计时器 = null;

/* ========== 缓存DOM元素 ========== */
var 游戏时间元素 = document.getElementById('游戏时间');
var 游戏日期元素 = document.getElementById('游戏日期');
var 银两元素 = document.getElementById('银两显示');
var 铜钱元素 = document.getElementById('铜钱显示');
var 命令输入框 = document.getElementById('命令输入框');
var 日志区域元素 = document.getElementById('日志区域');
var 人物列表元素 = document.getElementById('人物列表');
var 操作栏元素 = document.getElementById('操作栏');
var 描述标题元素 = document.getElementById('描述标题');
var 描述时间元素 = document.getElementById('描述时间');
var 描述天气元素 = document.getElementById('描述天气');
var 描述文本元素 = document.getElementById('描述文本');
var 描述介绍元素 = document.getElementById('描述介绍');
var 出口地图元素 = document.getElementById('出口地图');
var 地图网格元素 = document.getElementById('地图网格');
var 技能列元素 = document.getElementById('技能列表');
var 物品列元素 = document.getElementById('物品列表');
var 战斗面板元素 = document.getElementById('战斗面板');
var 技能面板元素 = document.getElementById('技能面板');
var 物品面板元素 = document.getElementById('物品面板');
var 任务摘要元素 = document.getElementById('任务摘要内容');
var 境界图标元素 = document.getElementById('境界图标');
var 境界名称元素 = document.getElementById('境界名称');
var 右侧血条元素 = document.getElementById('右侧血条');
var 右侧生命元素 = document.getElementById('右侧生命');
var 右侧真气条元素 = document.getElementById('右侧真气条');
var 右侧真气元素 = document.getElementById('右侧真气元素');
var 右侧攻击元素 = document.getElementById('右侧攻击');
var 右侧防御元素 = document.getElementById('右侧防御');
var 右侧银两元素 = document.getElementById('右侧银两');
var 右侧铜钱元素 = document.getElementById('右侧铜钱');

/* ========== 应用启动 ========== */
function 初始化游戏() {
  var 遮罩 = document.getElementById('加载遮罩');
  遮罩.style.transition = 'opacity 1.2s ease';
  setTimeout(function() {
    遮罩.classList.add('隐藏');
    setTimeout(function() { 遮罩.style.display = 'none'; }, 1200);
  }, 2500);

  刷新状态();
  刷新计时器 = setInterval(刷新状态, 4000);
  setInterval(更新时间栏, 1000);

  if (命令输入框) {
    命令输入框.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') { e.preventDefault(); 执行命令(); }
    });
  }

  document.addEventListener('keydown', function(e) {
    if (e.target === 命令输入框) return;
    if (e.key === 's' || e.key === 'S') 打开状态弹窗();
    if (e.key === 'q' || e.key === 'Q') 打开任务弹窗();
    if (e.key === 'm' || e.key === 'M') 打开地图弹窗();
    if (e.key === 'h' || e.key === 'H') 显示帮助面板();
    if (e.key === 'Escape') 关闭所有弹窗();
  });
}

function 关闭所有弹窗() {
  隐藏状态弹窗();
  隐藏任务弹窗();
  隐藏帮助弹窗();
  隐藏地图弹窗();
}

/* ========== 网络请求 ========== */
function 请求数据(地址, 方式, 请求体) {
  方式 = 方式 || 'GET';
  var 选项 = {
    method: 方式,
    headers: { 'Content-Type': 'application/json' }
  };
  if (请求体) 选项.body = JSON.stringify(请求体);
  return fetch(地址, 选项).then(function(响应) {
    if (!响应.ok) throw new Error('请求失败');
    return 响应.json();
  });
}

/* ========== 状态刷新 ========== */
function 刷新状态() {
  请求数据('/api/状态').then(function(数据) {
    游戏状态 = 数据;
    更新地点信息(数据);
    更新出口面板(数据);
    更新人物列表(数据);
    更新操作按钮(数据);
    更新顶部信息(数据);
    更新右侧状态(数据);
    更新技能数据(数据);
    更新物品数据(数据);
    更新战斗界面(数据);
    if (!正在移动) 更新地图网格();
    更新访问记录(数据);
    更新任务摘要();
  }).catch(function() {
    添加日志('连接失败，请检查服务器', '系统');
  });
}
/* ========== 更新地点信息 ========== */
var 上次地点 = '';
function 更新地点信息(数据) {
  var loc = 数据.地点 || '未知之地';
  var 地点变更 = (loc !== 上次地点 && 上次地点 !== '');
  上次地点 = loc;
  if (描述标题元素) {
    if (地点变更) {
      描述标题元素.style.animation = 'none';
      描述标题元素.offsetHeight; // trigger reflow
      描述标题元素.style.animation = '地点高亮 0.8s ease-out';
    }
    描述标题元素.textContent = '【' + loc + '】';
  }

  var 时间显示 = 数据.时间显示 || {};
  var 时段 = 时间显示.time || '';
  var 天气 = 时间显示.weather || '';
  if (描述时间元素) 描述时间元素.textContent = 时段;
  if (描述天气元素) 描述天气元素.textContent = 天气;

  if (地点变更 && 描述文本元素) {
    描述文本元素.style.opacity = '0';
    描述文本元素.style.transform = 'translateY(8px)';
    setTimeout(function() {
      描述文本元素.textContent = 获取地点描述(loc);
      描述文本元素.style.transition = 'all 0.4s ease';
      描述文本元素.style.opacity = '1';
      描述文本元素.style.transform = 'translateY(0)';
    }, 200);
  } else if (描述文本元素) {
    描述文本元素.textContent = 获取地点描述(loc);
  }
  if (描述介绍元素) {
    描述介绍元素.textContent = 获取地点介绍(loc);
  }
}

function 获取地点描述(名称) {
  var 描述表 = {
    '平安镇': '天书大陆边陲的一座宁静小镇，远离江湖喧嚣。街道两旁是低矮的木屋，偶尔传来几声鸡鸣犬吠。镇口有一棵老槐树，树下常有人摆下棋局，孩童在旁嬉戏。远处可见炊烟袅袅，充满了人间烟火气。',
    '龙门客栈': '天书大陆山脚下的热闹客栈，江湖人士云集之地，消息四通八达。店内挂满了各式兵器，柜台后酒坛堆积如山。说书人吴六正说起一段江湖传奇，引得众人喝彩。',
    '黑风寨': '天书大陆阴森险峻的山寨，据传有高手盘踞。空气中弥漫着肃杀之气，寨墙上刻着帮派标记，隐约传来狼嚎之声。守门喽啰目光警惕，任何人都不得擅入。',
    '温泉谷': '天书大陆云雾缭绕的山谷，温泉有疗伤养神之效，常有高人隐居在此。泉水散发出的暖意让人精神一振，谷中鸟语花香，宛如世外桃源。',
    '襄阳城': '天书大陆繁华大城，城墙高耸，武林人士聚集之地。城中人来人往，热闹非凡。大宋英雄守城抗敌，城墙上旌旗招展，守卫森严。',
    '武林秘籍库': '天书大陆古老的藏书楼，据说藏着无数武功秘籍，非有缘人不得入内。书架上的灰尘很厚，似乎很久没人翻阅。隐约能感觉到一股古老的气息。',
    '回春堂': '天书大陆飘着药香的医馆，大夫医术高明，闻名江湖。药柜上摆满了各色药材，帘后传来轻微的咳嗽声。医馆的牌匾上写着「妙手回春」四个大字。',
    '擂台': '天书大陆巨大的演武场，擂台上经常有高手切磋比试，是扬名立万之地。擂台的木柱上刻满了深深的剑痕，每一道都诉说着一段传奇。'
  };
  return 描述表[名称] || '一个神秘的地方，等待着你去探索其中的秘密。';
}

function 获取地点介绍(名称) {
  var 介绍表 = {
    '平安镇': '传说数百年前，一位大侠在此定居，从此小镇世代习武之风盛行。镇中有武馆、医馆、客栈，应有尽有。',
    '龙门客栈': '江湖人称「龙门一拜，生死与共」，是各路英雄豪杰的必经之地。客栈老板娘美艳动人，却没人知道她的真实来历。',
    '黑风寨': '寨主原是一名没落武师，因怀才不遇落草为寇。如今手下聚集了一群山贼，专门打劫过往商客。',
    '温泉谷': '传闻谷中有温泉来自地下灵脉，长期浸泡可改善根骨，提升修炼速度。许多武林人士不惜千里而来。',
    '襄阳城': '郭靖黄蓉夫妇镇守此城数十载，城中高手如云，是抵御外敌的坚固屏障。城中设有演武场和英雄碑。',
    '武林秘籍库': '藏书楼主人身份成谜，但有缘者可得传武功秘籍。据说楼中有机关重重，非有缘人不得其门而入。',
    '回春堂': '堂主师承医仙一脉，一手医术出神入化，据说能肉白骨、活死人。不过诊金昂贵，非一般人能负担。',
    '擂台': '每月十五举办武林大会，胜者可获「武林盟主」称号。擂台上胜负一瞬间，许多人在这里一战成名，也有许多人陨落于此。'
  };
  return 介绍表[名称] || '';
}

/* ========== 出口面板 ========== */
function 更新出口面板(数据) {
  var 连接 = 获取连接地点(数据.地点);
  if (!出口地图元素) return;
  if (!连接 || Object.keys(连接).length === 0) {
    出口地图元素.innerHTML = '<div class="出口标题" style="padding:16px 0;">此地暂无通路</div>';
    return;
  }

  var 方向标签 = {'上': '北', '下': '南', '左': '西', '右': '东'};
  var html = '';
  // 上行
  html += '<div class="出口行">';
  html += '<div class="出口占位"></div>';
  if (连接.上) {
    html += '<div class="出口按钮 可用" onclick="前往地点(\'' + 连接.上 + '\')">▲ ' + 方向标签['上'] + ' ' + 连接.上 + '</div>';
  } else {
    html += '<div class="出口占位"></div>';
  }
  html += '<div class="出口占位"></div>';
  html += '</div>';
  // 中行
  html += '<div class="出口行">';
  if (连接.左) {
    html += '<div class="出口按钮 可用" onclick="前往地点(\'' + 连接.左 + '\')">◀ ' + 方向标签['左'] + ' ' + 连接.左 + '</div>';
  } else {
    html += '<div class="出口占位"></div>';
  }
  html += '<div class="出口按钮 当前">◇ ' + (数据.地点 || '???') + '</div>';
  if (连接.右) {
    html += '<div class="出口按钮 可用" onclick="前往地点(\'' + 连接.右 + '\')">' + 连接.右 + ' ' + 方向标签['右'] + ' ▶</div>';
  } else {
    html += '<div class="出口占位"></div>';
  }
  html += '</div>';
  // 下行
  html += '<div class="出口行">';
  html += '<div class="出口占位"></div>';
  if (连接.下) {
    html += '<div class="出口按钮 可用" onclick="前往地点(\'' + 连接.下 + '\')">▼ ' + 方向标签['下'] + ' ' + 连接.下 + '</div>';
  } else {
    html += '<div class="出口占位"></div>';
  }
  html += '<div class="出口占位"></div>';
  html += '</div>';

  出口地图元素.innerHTML = html;
}

function 获取连接地点(当前) {
  var 地图 = {
    '平安镇': {左: '黑风寨', 右: '龙门客栈', 上: '温泉谷', 下: '回春堂'},
    '龙门客栈': {左: '平安镇', 右: '擂台', 上: '武林秘籍库', 下: '襄阳城'},
    '黑风寨': {左: '温泉谷', 右: '平安镇', 上: '回春堂', 下: '龙门客栈'},
    '温泉谷': {左: '黑风寨', 右: '回春堂', 上: '平安镇', 下: '武林秘籍库'},
    '襄阳城': {左: '擂台', 右: '回春堂', 上: '龙门客栈', 下: '平安镇'},
    '武林秘籍库': {左: '温泉谷', 右: '黑风寨', 上: '平安镇', 下: '龙门客栈'},
    '回春堂': {左: '襄阳城', 右: '温泉谷', 上: '平安镇', 下: '黑风寨'},
    '擂台': {左: '龙门客栈', 右: '平安镇', 上: '襄阳城', 下: '黑风寨'}
  };
  return 地图[当前] || {};
}

/* ========== 人物列表 ========== */
function 更新人物列表(数据) {
  if (!人物列表元素) return;
  var 人物 = 数据.人物列表 || [];
  var 主要人物表 = ['老拳师','铁匠张伯','说书人吴六','受伤镖师','小医师阿青','武痴赵猛','看门老者','酒楼掌柜王胖子','郭靖','黄蓉','乔峰','洪七公','周伯通','欧阳锋','令狐冲','韦小宝'];
  if (!人物.length) {
    人物列表元素.innerHTML = '<span class="无人物">此处空无一人</span>';
    return;
  }
  var html = '';
  for (var i = 0; i < 人物.length; i++) {
    var 名字 = 人物[i];
    var 是否主要 = 主要人物表.indexOf(名字) >= 0;
    var 关系值 = 0;
    if (数据.关系 && 数据.关系[名字] !== undefined) 关系值 = 数据.关系[名字];
    var 关系类型 = 关系值 > 20 ? '友好' : (关系值 < -20 ? '敌对' : '陌生');
    html += '<button class="人物按钮' + (是否主要 ? ' 主要' : '') + '" onclick="与人物交谈(\'' + 名字 + '\')">';
    html += '<span class="人物名">' + 名字 + '</span>';
    html += '<span class="人物关系 ' + 关系类型 + '">' + 关系类型 + '</span>';
    html += '</button>';
  }
  人物列表元素.innerHTML = html;
}

/* ========== 操作按钮 ========== */
function 更新操作按钮(数据) {
  if (!操作栏元素) return;
  var 在战斗中 = 数据.战斗状态 && 数据.战斗状态.在战斗中;
  if (在战斗中) {
    操作栏元素.innerHTML =
      '<button class="操作按钮" onclick="战斗动作(\'攻击\')"><span class="操作图标">⚔</span>攻击</button>' +
      '<button class="操作按钮" onclick="战斗动作(\'防御\')"><span class="操作图标">🛡</span>防御</button>' +
      '<button class="操作按钮" onclick="切换技能面板()"><span class="操作图标">✨</span>技能</button>' +
      '<button class="操作按钮" onclick="切换物品面板()"><span class="操作图标">🎒</span>物品</button>' +
      '<button class="操作按钮 危险" onclick="战斗动作(\'逃跑\')"><span class="操作图标">🏃</span>逃跑</button>';
  } else {
    操作栏元素.innerHTML =
      '<button class="操作按钮" onclick="执行操作(\'观察\')"><span class="操作图标">👁</span>观察</button>' +
      '<button class="操作按钮" onclick="执行操作(\'休息\')"><span class="操作图标">💤</span>休息</button>' +
      '<button class="操作按钮" onclick="执行操作(\'练功\')"><span class="操作图标">⚡</span>练功</button>' +
      '<button class="操作按钮" onclick="执行操作(\'突破\')"><span class="操作图标">💫</span>突破</button>' +
      '<button class="操作按钮 主要" onclick="执行操作(\'战斗\')"><span class="操作图标">⚔</span>战斗</button>';
  }
  if (!在战斗中) {
    隐藏技能面板();
    隐藏物品面板();
  }
}

/* ========== 顶部信息 ========== */
function 更新顶部信息(数据) {
  var 时间显示 = 数据.时间显示 || {};
  var 时辰 = 时间显示.时辰 || '';
  var 时段 = 时间显示.时段 || '';
  if (游戏时间元素) 游戏时间元素.textContent = '【' + 时辰 + '】' + 时段;
  if (游戏日期元素) 游戏日期元素.textContent = '第' + (时间显示.day || 1) + '天';
  if (银两元素) 银两元素.textContent = (数据.银两 || 0);
  if (铜钱元素) 铜钱元素.textContent = (数据.铜钱 || 0);
}

function 更新时间栏() {
  if (!游戏状态 || !游戏状态.时间显示) return;
  var 时间显示 = 游戏状态.时间显示;
  if (游戏时间元素) 游戏时间元素.textContent = 时间显示.time || '';
}

/* ========== 右侧状态 ========== */
function 更新右侧状态(数据) {
  var 境界名称 = ['初入江湖','三流高手','二流高手','一流高手','宗师','大宗师','天下第一'];
  var 境界图标 = ['🐾','🗡','⚔','🛡','👨‍🦳','🌟','👑'];
  var 境界索引 = 数据.境界 ? (数据.境界.索引 || 0) : 0;
  if (境界图标元素) 境界图标元素.textContent = 境界图标[境界索引];
  if (境界名称元素) 境界名称元素.textContent = 境界名称[境界索引];

  var 生命比 = 数据.最大生命 ? Math.round((数据.生命 / 数据.最大生命) * 100) : 0;
  var 真气比 = 数据.最大生命 ? Math.round((数据.真气 / 数据.最大生命) * 100) : 0;

  if (右侧血条元素) {
    右侧血条元素.style.width = 生命比 + '%';
    右侧血条元素.className = '进度条填充 生命' + (生命比 < 30 ? ' 危险' : '');
  }
  if (右侧生命元素) 右侧生命元素.textContent = 数据.生命 + '/' + 数据.最大生命;
  if (右侧真气条元素) {
    右侧真气条元素.style.width = 真气比 + '%';
  }
  if (右侧真气元素) 右侧真气元素.textContent = 数据.真气;
  if (右侧攻击元素) 右侧攻击元素.textContent = 数据.攻击;
  if (右侧防御元素) 右侧防御元素.textContent = 数据.防御;
  if (右侧银两元素) 右侧银两元素.textContent = (数据.银两 || 0) + ' 两';
  if (右侧铜钱元素) 右侧铜钱元素.textContent = (数据.铜钱 || 0) + ' 文';
}

/* ========== 技能与物品 ========== */
function 更新技能数据(数据) {
  if (!技能列元素) return;
  var 技能映射 = 数据.技能 || {};
  var 键列表 = Object.keys(技能映射);
  if (!键列表.length) {
    技能列元素.innerHTML = '<span class="无技能">尚未习武</span>';
    return;
  }
  var html = '';
  for (var i = 0; i < 键列表.length; i++) {
    var 技能名 = 键列表[i];
    html += '<button class="技能按钮" onclick="施展技能(\'' + 技能名 + '\')">';
    html += '<span class="技能名">' + 技能名 + '</span>';
    html += '<span class="技能等">' + 技能映射[技能名] + '层</span>';
    html += '</button>';
  }
  技能列元素.innerHTML = html;
}

function 更新物品数据(数据) {
  if (!物品列元素) return;
  var 物品映射 = 数据.物品栏 || {};
  var 键列表 = Object.keys(物品映射).filter(function(k) { return 物品映射[k] > 0; });
  键列表.sort();
  if (!键列表.length) {
    物品列元素.innerHTML = '<span class="无物品">背包空空如也</span>';
    return;
  }
  var 名称表 = {'bread': '干粮', 'heal_potion': '金疮药', 'wine': '好酒', 'sword': '铁剑', 'manual': '武功秘籍', 'pill': '丹药', 'herb': '草药'};
  var html = '';
  for (var i = 0; i < 键列表.length; i++) {
    var k = 键列表[i];
    var 名 = 名称表[k] || k;
    html += '<button class="物品按钮" onclick="使用物品(\'' + k + '\')">';
    html += '<span class="物品名">' + 名 + '</span>';
    html += '<span class="物品数">×' + 物品映射[k] + '</span>';
    html += '</button>';
  }
  物品列元素.innerHTML = html;
}

function 施展技能(技能名) {
  if (!游戏状态 || !游戏状态.战斗状态 || !游戏状态.战斗状态.在战斗中) return;
  添加日志('施展「' + 技能名 + '」...', '系统');
  发送战斗请求('skill', 技能名);
}

function 使用物品(键) {
  if (!游戏状态 || !游戏状态.战斗状态 || !游戏状态.战斗状态.在战斗中) return;
  var 名称表 = {'bread': '干粮', 'heal_potion': '金疮药', 'wine': '好酒', 'pill': '丹药'};
  var 名 = 名称表[键] || 键;
  添加日志('使用「' + 名 + '」...', '系统');
  发送战斗请求('item', 键);
}

function 切换技能面板() {
  if (!技能面板元素) return;
  技能面板展开 = !技能面板展开;
  if (技能面板展开) 技能面板元素.classList.add('激活');
  else 隐藏技能面板();
}

function 隐藏技能面板() {
  技能面板展开 = false;
  if (技能面板元素) 技能面板元素.classList.remove('激活');
}

function 切换物品面板() {
  if (!物品面板元素) return;
  物品面板展开 = !物品面板展开;
  if (物品面板展开) 物品面板元素.classList.add('激活');
  else 隐藏物品面板();
}

function 隐藏物品面板() {
  物品面板展开 = false;
  if (物品面板元素) 物品面板元素.classList.remove('激活');
}

/* ========== 战斗面板 ========== */
function 更新战斗界面(数据) {
  if (!战斗面板元素) return;
  var 战斗中 = 数据.战斗状态 && 数据.战斗状态.在战斗中;
  if (战斗中) {
    战斗面板元素.classList.add('激活');
    var 战斗 = 数据.战斗状态;
    var 敌方名称 = 战斗.敌方名称 || '神秘敌人';
    var 敌方等级 = 战斗.敌方等级 || '?';
    var 敌方生命 = 战斗.敌方生命 || 0;
    var 敌方最大生命 = 战斗.敌方最大生命 || 100;
    var 敌方真气 = 战斗.敌方真气 || 0;
    var 我方生命 = 战斗.我方生命 || 0;
    var 我方最大生命 = 战斗.我方最大生命 || 100;
    var 我方真气 = 战斗.我方真气 || 0;
    var 敌方生命比 = Math.max(0, Math.round((敌方生命 / 敌方最大生命) * 100));
    var 我方生命比 = Math.max(0, Math.round((我方生命 / 我方最大生命) * 100));
    var 敌方真气比 = Math.min(100, Math.round((敌方真气 / 敌方最大生命) * 100));
    var 我方真气比 = Math.min(100, Math.round((我方真气 / 我方最大生命) * 100));

    var el;
    el = document.getElementById('敌方名称'); if (el) el.textContent = '⚔ ' + 敌方名称 + ' (Lv.' + 敌方等级 + ')';
    el = document.getElementById('我方名称'); if (el) el.textContent = '🗡 我方';
    el = document.getElementById('敌方等级'); if (el) el.textContent = 敌方等级;
    el = document.getElementById('敌方生命值'); if (el) el.textContent = 敌方生命 + ' / ' + 敌方最大生命;
    el = document.getElementById('我方生命值'); if (el) el.textContent = 我方生命 + ' / ' + 我方最大生命;
    el = document.getElementById('敌方真气值'); if (el) el.textContent = 敌方真气;
    el = document.getElementById('我方真气值'); if (el) el.textContent = 我方真气;

    el = document.getElementById('敌方血条'); if (el) {
      el.style.width = 敌方生命比 + '%';
      el.className = '进度条填充 生命' + (敌方生命比 < 30 ? ' 危险' : '');
    }
    el = document.getElementById('我方血条'); if (el) {
      el.style.width = 我方生命比 + '%';
      el.className = '进度条填充 生命' + (我方生命比 < 30 ? ' 危险' : '');
    }
    el = document.getElementById('敌方真气条'); if (el) el.style.width = 敌方真气比 + '%';
    el = document.getElementById('我方真气条'); if (el) el.style.width = 我方真气比 + '%';
  } else {
    战斗面板元素.classList.remove('激活');
  }
}

/* ========== 战斗操作 ========== */
function 战斗动作(动作) {
  if (!游戏状态 || !游戏状态.战斗状态 || !游戏状态.战斗状态.在战斗中) return;
  return 发送战斗请求(动作);
}

function 发送战斗请求(动作, 额外) {
  var 数据体 = {动作: 动作};
  if (额外) 数据体.技能 = 额外;
  return 请求数据('/api/战斗', 'POST', 数据体).then(function(返回) {
    if (返回.输出) 添加日志(返回.输出, 返回.类型 || '');
    if (返回.战斗状态) 更新战斗界面({战斗状态: 返回.战斗状态});
    刷新状态();
  }).catch(function() {
    添加日志('战斗操作失败', '系统');
  });
}

/* ========== 命令执行 ========== */
function 执行操作(命令) {
  添加日志('❯ ' + 命令, '系统');
  return 发送命令(命令);
}

function 执行命令() {
  var 文本 = '';
  if (命令输入框) 文本 = 命令输入框.value.trim();
  if (!文本) return;
  添加日志('❯ ' + 文本, '系统');
  if (命令输入框) 命令输入框.value = '';
  return 发送命令(文本);
}

function 发送命令(命令) {
  return 请求数据('/api/命令', 'POST', {命令: 命令}).then(function(数据) {
    if (数据.输出) 添加日志(数据.输出, 数据.类型 || '');
    if (数据.事件 && 数据.事件.length) {
      for (var i = 0; i < 数据.事件.length; i++) {
        添加日志('【' + (数据.事件[i].类型 || '事件') + '】 ' + 数据.事件[i].文本, '事件');
      }
    }
    if (数据.成功 === false && 数据.消息) 添加日志(数据.消息, '系统');
    刷新状态();
  }).catch(function() {
    添加日志('执行失败，请重试', '系统');
  });
}

/* ========== 导航系统 ========== */
function 前往地点(目标) {
  if (目标 === 游戏状态.地点) {
    var 节点 = 地图网格元素 ? 地图网格元素.querySelectorAll('.地图节点') : [];
    for (var i = 0; i < 节点.length; i++) {
      var 名称元素 = 节点[i].querySelector('.节点名称');
      if (名称元素 && 名称元素.textContent === 目标) {
        节点[i].style.animation = 'none';
        节点[i].offsetHeight;
        节点[i].style.animation = '节点抖动 0.4s ease';
      }
    }
    return;
  }
  if (正在移动) return;
  正在移动 = true;

  // 获取起点和终点坐标
  var 起点坐标 = 地点坐标[游戏状态.地点];
  var 终点坐标 = 地点坐标[目标];
  if (!起点坐标 || !终点坐标) {
    正在移动 = false;
    return;
  }

  // 添加日志
  添加日志('🚶 赶路前往「' + 目标 + '」...', '系统');

  // 动画移动角色
  移动角色到(起点坐标, 终点坐标, function() {
    // 移动完成后发送命令
    发送命令('前往 ' + 目标).then(function() {
      更新地图网格(); // 重新渲染地图
      setTimeout(function() { 正在移动 = false; }, 300);
    }).catch(function() {
      正在移动 = false;
      更新地图网格();
      添加日志('赶路失败，请重试', '系统');
    });
  });
}

function 移动角色到(起点, 终点, callback) {
  var 角色 = document.getElementById('玩家角色');
  if (!角色) {
    if (callback) callback();
    return;
  }

  // 计算路径（使用 SVG path 数据）
  var 路径点 = 计算地图路径(起点, 终点);
  var 总时长 = 800; // 动画时长 ms
  var 间隔 = 30; // 每帧间隔
  var 总帧数 = Math.ceil(总时长 / 间隔);
  var 当前帧 = 0;

  function 动画帧() {
    当前帧++;
    var 进度 = 当前帧 / 总帧数;

    if (进度 >= 1) {
      // 动画完成，移动到终点
      角色.style.left = 终点.x + '%';
      角色.style.top = 终点.y + '%';
      角色.style.transition = 'none';
      if (callback) callback();
      return;
    }

    // 沿路径插值
    var 位置 = 沿路径插值(路径点, 进度);
    角色.style.left = 位置.x + '%';
    角色.style.top = 位置.y + '%';

    setTimeout(动画帧, 间隔);
  }

  // 开始动画
  角色.style.transition = 'none';
  setTimeout(动画帧, 50);
}

function 计算地图路径(起点, 终点) {
  // 简化路径：直接直线移动（后续可改为沿道路移动）
  return [起点, 终点];
}

function 沿路径插值(路径点, 进度) {
  if (路径点.length === 1) return 路径点[0];

  var 总段数 = 路径点.length - 1;
  var 当前段 = Math.min(Math.floor(进度 * 总段数), 总段数 - 1);
  var 段进度 = (进度 * 总段数) - 当前段;

  var p1 = 路径点[当前段];
  var p2 = 路径点[当前段 + 1];

  return {
    x: p1.x + (p2.x - p1.x) * 段进度,
    y: p1.y + (p2.y - p1.y) * 段进度
  };
}

function 与人物交谈(名字) {
  添加日志('与「' + 名字 + '」交谈...', '系统');
  发送命令('交谈 ' + 名字);
}

/* ========== 地图网格 ========== */
// 地点坐标（百分比定位，模拟江湖地图布局）
var 地点坐标 = {
  '平安镇':   {x: 25, y: 55},
  '龙门客栈': {x: 45, y: 40},
  '黑风寨':   {x: 15, y: 35},
  '温泉谷':   {x: 35, y: 20},
  '襄阳城':   {x: 70, y: 45},
  '武林秘籍库': {x: 55, y: 15},
  '回春堂':   {x: 30, y: 75},
  '擂台':     {x: 65, y: 70}
};

// 连接关系（道路网络）
var 地图连接 = {
  '平安镇':   ['龙门客栈', '黑风寨', '温泉谷', '回春堂'],
  '龙门客栈': ['平安镇', '黑风寨', '襄阳城', '武林秘籍库'],
  '黑风寨':   ['平安镇', '龙门客栈', '温泉谷'],
  '温泉谷':   ['平安镇', '黑风寨', '武林秘籍库'],
  '襄阳城':   ['龙门客栈', '擂台', '回春堂'],
  '武林秘籍库': ['龙门客栈', '温泉谷', '擂台'],
  '回春堂':   ['平安镇', '襄阳城', '黑风寨'],
  '擂台':     ['襄阳城', '武林秘籍库']
};

function 更新地图网格() {
  if (!游戏状态 || !地图网格元素) return;
  var 地点图标 = {'平安镇': '🏘', '龙门客栈': '🏮', '黑风寨': '🏔', '温泉谷': '♨', '襄阳城': '🏯', '武林秘籍库': '📚', '回春堂': '🏥', '擂台': '⚔'};

  // 构建 SVG 地图
  var html = '<div class="地图画布">';

  // SVG 层：绘制道路
  html += '<svg class="地图路径" viewBox="0 0 100 100" preserveAspectRatio="none">';
  地图连接.forEach(function(目标, 起点) {
    var 坐标起点 = 地点坐标[起点];
    var 坐标终点 = 地点坐标[目标];
    if (坐标起点 && 坐标终点) {
      var 已访问 = 已访问地点[起点] && 已访问地点[目标];
      html += '<path class="地图道路' + (已访问 ? ' 已探索' : '') + '" d="M ' + 坐标起点.x + ' ' + 坐标起点.y + ' L ' + 坐标终点.x + ' ' + 坐标终点.y + '"/>';
    }
  });
  html += '</svg>';

  // 地点节点层
  Object.keys(地点坐标).forEach(function(地点名) {
    var 坐标 = 地点坐标[地点名];
    var 是否当前 = (地点名 === 游戏状态.地点);
    var 是否访问 = 已访问地点[地点名] || (游戏状态.已访问地点 && 游戏状态.已访问地点[地点名]);
    var cls = '地图节点' + (是否当前 ? ' 当前' : (是否访问 ? ' 已访问' : ''));
    html += '<div class="' + cls + '" style="left:' + 坐标.x + '%;top:' + 坐标.y + '%" onclick="点击地图节点(\'' + 地点名 + '\', this)">';
    html += '<div class="节点图标">' + (地点图标[地点名] || '📍') + '</div>';
    html += '<div class="节点名称">' + 地点名 + '</div>';
    html += '<div class="节点状态">' + (是否当前 ? '当前位置' : (是否访问 ? '已访问' : '未探索')) + '</div>';
    html += '</div>';
  });

  // 玩家角色（最后一个渲染，确保在最上层）
  if (游戏状态.地点 && 地点坐标[游戏状态.地点]) {
    var 玩家坐标 = 地点坐标[游戏状态.地点];
    html += '<div class="玩家角色" id="玩家角色" style="left:' + 玩家坐标.x + '%;top:' + 玩家坐标.y + '%">';
    html += '<div class="角色动画">🗡</div>';
    html += '</div>';
  }

  html += '</div>';
  地图网格元素.innerHTML = html;
}

function 点击地图节点(目标, 元素) {
  if (目标 === 游戏状态.地点) {
    // 已经在当前位置 — 抖动反馈
    if (元素) {
      元素.style.animation = 'none';
      元素.offsetHeight;
      元素.style.animation = '节点抖动 0.4s ease';
    }
    return;
  }
  if (正在移动) return;
  前往地点(目标);
}

/* ========== 访问记录 ========== */
function 更新访问记录(数据) {
  if (数据.地点) 已访问地点[数据.地点] = true;
  if (数据.已访问地点) {
    var keys = Object.keys(数据.已访问地点);
    for (var i = 0; i < keys.length; i++) 已访问地点[keys[i]] = true;
  }
}

/* ========== 弹窗系统 ========== */
function 打开状态弹窗() {
  请求数据('/api/状态').then(function(数据) {
    var 境界名称 = ['初入江湖','三流高手','二流高手','一流高手','宗师','大宗师','天下第一'];
    var 境界图标 = ['🐾','🗡','⚔','🛡','👨‍🦳','🌟','👑'];
    var 境界索引 = 数据.境界 ? (数据.境界.索引 || 0) : 0;
    var html = '';
    html += '<div class="状态头部">';
    html += '<div class="状态境界图标">' + 境界图标[境界索引] + '</div>';
    html += '<div class="状态境界名称">' + 境界名称[境界索引] + '</div>';
    html += '</div>';

    var 生命比 = 数据.最大生命 ? Math.round((数据.生命 / 数据.最大生命) * 100) : 0;
    var 真气比 = 数据.最大生命 ? Math.round((数据.真气 / 数据.最大生命) * 100) : 0;

    html += '<div class="进度条容器"><div class="进度条填充 生命' + (生命比 < 30 ? ' 危险' : '') + '" style="width:' + 生命比 + '%"></div></div>';
    html += '<div class="属性行"><span class="属性标签">生命</span><span class="属性值 生命">' + 数据.生命 + ' / ' + 数据.最大生命 + ' (' + 生命比 + '%)</span></div>';
    html += '<div class="进度条容器"><div class="进度条填充 真气" style="width:' + 真气比 + '%"></div></div>';
    html += '<div class="属性行"><span class="属性标签">内力</span><span class="属性值 真气">' + 数据.真气 + ' (' + 真气比 + '%)</span></div>';
    html += '<div class="状态分割线"></div>';
    html += '<div class="属性行"><span class="属性标签">攻击</span><span class="属性值">' + 数据.攻击 + '</span></div>';
    html += '<div class="属性行"><span class="属性标签">防御</span><span class="属性值">' + 数据.防御 + '</span></div>';
    html += '<div class="属性行"><span class="属性标签">银两</span><span class="属性值">' + 数据.银两 + ' 两</span></div>';
    html += '<div class="属性行"><span class="属性标签">铜钱</span><span class="属性值">' + 数据.铜钱 + ' 文</span></div>';

    var 技能项 = 数据.技能 || {};
    var 技能键 = Object.keys(技能项);
    if (技能键.length) {
      html += '<div class="状态分割线"></div>';
      html += '<div class="属性行" style="color:#c8a45c;font-size:13px;letter-spacing:2px;font-weight:600;">◆ 武功技能</div>';
      for (var i = 0; i < 技能键.length; i++) {
        html += '<div class="属性行"><span class="属性标签">' + 技能键[i] + '</span><span class="属性值">' + 技能项[技能键[i]] + ' 层</span></div>';
      }
    }

    var 物品项 = 数据.物品栏 || {};
    var 物品键 = Object.keys(物品项).filter(function(k) { return 物品项[k] > 0; });
    if (物品键.length) {
      html += '<div class="状态分割线"></div>';
      html += '<div class="属性行" style="color:#c8a45c;font-size:13px;letter-spacing:2px;font-weight:600;">◆ 随身物品</div>';
      var 物品名映射 = {'bread': '干粮', 'heal_potion': '金疮药', 'wine': '好酒', 'sword': '铁剑', 'manual': '武功秘籍', 'pill': '丹药'};
      for (var j = 0; j < 物品键.length; j++) {
        var 显示名 = 物品名映射[物品键[j]] || 物品键[j];
        html += '<div class="属性行"><span class="属性标签">' + 显示名 + '</span><span class="属性值">×' + 物品项[物品键[j]] + '</span></div>';
      }
    }

    var 状态主体 = document.getElementById('状态主体');
    if (状态主体) 状态主体.innerHTML = html;
    var 状态弹窗 = document.getElementById('状态弹窗');
    if (状态弹窗) 状态弹窗.classList.add('激活');
  });
}

function 隐藏状态弹窗() {
  var 状态弹窗 = document.getElementById('状态弹窗');
  if (状态弹窗) 状态弹窗.classList.remove('激活');
}

function 打开任务弹窗() {
  请求数据('/api/任务').then(function(数据) {
    var html = '';
    var 主线 = 数据.主线任务;
    if (主线) {
      html += '<div class="任务标签"><span class="任务图标">◆</span>主线任务</div>';
      html += '<div class="任务名称">' + 主线.名称 + '</div>';
      html += '<div class="任务描述">' + 主线.描述 + '</div>';
      var 目标列表 = 主线.目标 || [];
      for (var i = 0; i < 目标列表.length; i++) {
        html += '<div class="任务目标">· ' + 目标列表[i].描述 + '</div>';
      }
    } else {
      html += '<div class="无任务">暂无进行中的主线任务</div>';
    }
    var 成就列表 = 数据.成就 || [];
    if (成就列表.length) {
      html += '<div class="弹窗分割线"></div>';
      html += '<div class="任务标签"><span class="任务图标">🏆</span>已获成就 (' + 成就列表.length + ')</div>';
      for (var j = 0; j < Math.min(成就列表.length, 10); j++) {
        html += '<div class="任务目标">· ' + 成就列表[j] + '</div>';
      }
    }
    var 任务主体 = document.getElementById('任务主体');
    if (任务主体) 任务主体.innerHTML = html;
    var 任务弹窗 = document.getElementById('任务弹窗');
    if (任务弹窗) 任务弹窗.classList.add('激活');
  });
}

function 隐藏任务弹窗() {
  var 任务弹窗 = document.getElementById('任务弹窗');
  if (任务弹窗) 任务弹窗.classList.remove('激活');
}

function 打开地图弹窗() {
  if (!游戏状态) return;
  var 地点图标 = {'平安镇': '🏘', '龙门客栈': '🏮', '黑风寨': '🏔', '温泉谷': '♨', '襄阳城': '🏯', '武林秘籍库': '📚', '回春堂': '🏥', '擂台': '⚔'};
  var html = '<div class="地图画布">';

  // SVG 路径层
  html += '<svg class="地图路径" viewBox="0 0 100 100" preserveAspectRatio="none">';
  地图连接.forEach(function(目标, 起点) {
    var 坐标起点 = 地点坐标[起点];
    var 坐标终点 = 地点坐标[目标];
    if (坐标起点 && 坐标终点) {
      var 已访问 = 已访问地点[起点] && 已访问地点[目标];
      html += '<path class="地图道路' + (已访问 ? ' 已探索' : '') + '" d="M ' + 坐标起点.x + ' ' + 坐标起点.y + ' L ' + 坐标终点.x + ' ' + 坐标终点.y + '"/>';
    }
  });
  html += '</svg>';

  // 地点节点
  Object.keys(地点坐标).forEach(function(地点名) {
    var 坐标 = 地点坐标[地点名];
    var 是否当前 = (地点名 === 游戏状态.地点);
    var 是否访问 = 已访问地点[地点名] || (游戏状态.已访问地点 && 游戏状态.已访问地点[地点名]);
    var cls = '地图节点' + (是否当前 ? ' 当前' : (是否访问 ? ' 已访问' : ''));
    html += '<div class="' + cls + '" style="left:' + 坐标.x + '%;top:' + 坐标.y + '%" onclick="点击地图节点(\'' + 地点名 + '\', this)">';
    html += '<div class="节点图标">' + (地点图标[地点名] || '📍') + '</div>';
    html += '<div class="节点名称">' + 地点名 + '</div>';
    html += '<div class="节点状态">' + (是否当前 ? '当前位置' : (是否访问 ? '已访问' : '未探索')) + '</div>';
    html += '</div>';
  });

  // 玩家角色
  if (游戏状态.地点 && 地点坐标[游戏状态.地点]) {
    var 玩家坐标 = 地点坐标[游戏状态.地点];
    html += '<div class="玩家角色" style="left:' + 玩家坐标.x + '%;top:' + 玩家坐标.y + '%">';
    html += '<div class="角色动画">🗡</div>';
    html += '</div>';
  }

  html += '</div>';
  var 地图主体 = document.getElementById('地图主体');
  if (地图主体) 地图主体.innerHTML = html;
  var 地图弹窗 = document.getElementById('地图弹窗');
  if (地图弹窗) 地图弹窗.classList.add('激活');
}

function 隐藏地图弹窗() {
  var 地图弹窗 = document.getElementById('地图弹窗');
  if (地图弹窗) 地图弹窗.classList.remove('激活');
}

function 显示帮助面板() {
  var html = '';
  html += '<div class="帮助组"><div class="帮助组标题">📖 探索与行动</div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">👁 观察</span><span class="帮助命令说明">观察当前地点的详细信息</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">💤 休息</span><span class="帮助命令说明">恢复生命值与内力</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">⚡ 练功</span><span class="帮助命令说明">修炼武功，提升修为</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">💫 突破</span><span class="帮助命令说明">尝试突破境界瓶颈</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">⚔ 战斗</span><span class="帮助命令说明">寻找对手切磋武艺</span></div>';
  html += '</div>';
  html += '<div class="帮助组"><div class="帮助组标题">🗺 探索与交互</div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">🗺 地图</span><span class="帮助命令说明">查看世界地图 [M]</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">👥 人物</span><span class="帮助命令说明">查看周围的人物</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">💬 交谈</span><span class="帮助命令说明">与NPC交流对话</span></div>';
  html += '</div>';
  html += '<div class="帮助组"><div class="帮助组标题">⌨ 快捷键</div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[S]</span><span class="帮助命令说明">打开状态面板</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[Q]</span><span class="帮助命令说明">打开任务面板</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[M]</span><span class="帮助命令说明">打开地图面板</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[H]</span><span class="帮助命令说明">打开帮助面板</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[Enter]</span><span class="帮助命令说明">执行命令</span></div>';
  html += '<div class="帮助命令"><span class="帮助命令文本">[Esc]</span><span class="帮助命令说明">关闭所有弹窗</span></div>';
  html += '</div>';
  var 帮助主体 = document.getElementById('帮助主体');
  if (帮助主体) 帮助主体.innerHTML = html;
  var 帮助弹窗 = document.getElementById('帮助弹窗');
  if (帮助弹窗) 帮助弹窗.classList.add('激活');
}

function 隐藏帮助弹窗() {
  var 帮助弹窗 = document.getElementById('帮助弹窗');
  if (帮助弹窗) 帮助弹窗.classList.remove('激活');
}

/* ========== 任务摘要 ========== */
function 更新任务摘要() {
  请求数据('/api/任务').then(function(数据) {
    if (!任务摘要元素) return;
    var 主线 = 数据.主线任务;
    if (主线) {
      var html = '<div class="任务标签"><span class="任务图标">◆</span>主线任务</div>';
      html += '<div class="任务名称">' + 主线.名称 + '</div>';
      html += '<div class="任务描述">' + 主线.描述 + '</div>';
      var 目标列表 = 主线.目标 || [];
      for (var i = 0; i < 目标列表.length; i++) {
        html += '<div class="任务目标">· ' + 目标列表[i].描述 + '</div>';
      }
      任务摘要元素.innerHTML = html;
    } else {
      任务摘要元素.innerHTML = '<div class="无任务">暂无主线任务</div>';
    }
  }).catch(function() {});
}

/* ========== 日志系统 ========== */
function 添加日志(文本, 类型) {
  var 现在 = new Date();
  var 时间戳 = String(现在.getHours()).padStart(2, '0') + ':' + String(现在.getMinutes()).padStart(2, '0') + ':' + String(现在.getSeconds()).padStart(2, '0');
  日志列表.push({时间: 时间戳, 文本: 文本, 类型: 类型 || '普通'});
  if (日志列表.length > 80) 日志列表.shift();
  渲染日志();
}

function 渲染日志() {
  if (!日志区域元素) return;
  var html = '';
  for (var i = 0; i < 日志列表.length; i++) {
    var 条目 = 日志列表[i];
    html += '<div class="日志条目">';
    html += '<span class="日志时间">[' + 条目.时间 + ']</span>';
    html += '<span class="日志内容 ' + 条目.类型 + '">' + 条目.文本 + '</span>';
    html += '</div>';
  }
  日志区域元素.innerHTML = html;
  日志区域元素.scrollTop = 日志区域元素.scrollHeight;
}

/* ========== 通知系统 ========== */
function 显示通知(文本, 类型) {
  var 容器 = document.getElementById('通知容器');
  if (!容器) return;
  var 通知 = document.createElement('div');
  通知.className = '通知 ' + (类型 || '');
  通知.innerHTML = '<span class="通知文本">' + 文本 + '</span><span class="通知关闭" onclick="this.parentElement.remove()">✕</span>';
  容器.appendChild(通知);
  setTimeout(function() {
    if (通知.parentElement) 通知.remove();
  }, 3500);
}

/* ========== 存档系统 ========== */
function 打开存档面板() {
  请求数据('/api/存档').then(function(数据) {
    var 容器 = document.getElementById('存档列表');
    if (!容器) return;
    var 存档项 = 数据.存档 || [];
    if (!存档项.length) {
      容器.innerHTML = '<div class="无存档">暂无存档记录</div>';
    } else {
      var html = '';
      for (var i = 0; i < 存档项.length; i++) {
        var s = 存档项[i];
        html += '<div class="存档条目">';
        html += '<div class="存档信息">';
        html += '<div class="存档名称">◆ ' + s.名称 + '</div>';
        html += '<div class="存档详情">';
        html += '<span>📍 ' + s.地点 + '</span>';
        html += '<span>⚔ ' + s.境界 + '</span>';
        html += '<span>📅 ' + s.游戏天数 + '天</span>';
        html += '</div></div>';
        html += '<div class="存档操作">';
        html += '<button class="存档按钮" onclick="读取存档(\'' + s.名称 + '\')">读取</button>';
        html += '<button class="存档按钮 删除" onclick="删除存档(\'' + s.名称 + '\')">删除</button>';
        html += '</div></div>';
      }
      容器.innerHTML = html;
    }
    var 存档弹窗 = document.getElementById('存档弹窗');
    if (存档弹窗) 存档弹窗.classList.add('激活');
  });
}

function 关闭存档面板() {
  var 存档弹窗 = document.getElementById('存档弹窗');
  if (存档弹窗) 存档弹窗.classList.remove('激活');
}

function 执行保存() {
  var 时间 = new Date();
  var 默认名 = '存档_' + 时间.getFullYear() + String(时间.getMonth()+1).padStart(2,'0') + String(时间.getDate()).padStart(2,'0');
  默认名 += '_' + String(时间.getHours()).padStart(2,'0') + String(时间.getMinutes()).padStart(2,'0');
  var 名称 = prompt('请输入存档名称：', 默认名);
  if (!名称) return;
  请求数据('/api/保存', 'POST', {名称: 名称}).then(function(数据) {
    if (数据.成功) {
      显示通知('存档成功: ' + 名称, '成功');
      添加日志('游戏已保存', '系统');
    } else {
      显示通知(数据.消息 || '保存失败', '危险');
    }
  });
}

function 读取存档(名称) {
  请求数据('/api/读取', 'POST', {名称: 名称}).then(function(数据) {
    if (数据.成功) {
      显示通知('读取成功: ' + 名称, '成功');
      添加日志('已读取存档: ' + 名称, '系统');
      关闭存档面板();
      刷新状态();
    } else {
      显示通知(数据.消息 || '读取失败', '危险');
    }
  });
}

function 删除存档(名称) {
  if (!confirm('确定删除存档「' + 名称 + '」？此操作不可恢复。')) return;
  请求数据('/api/删除', 'POST', {名称: 名称}).then(function(数据) {
    if (数据.成功) {
      显示通知('已删除: ' + 名称, '信息');
      打开存档面板();
    }
  });
}

/* ========== 启动应用 ========== */
window.addEventListener('load', 初始化游戏);
