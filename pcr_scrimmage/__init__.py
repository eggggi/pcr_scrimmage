import re
from .pcr_scrimmage import *
from hoshino.modules.priconne import chara

mgr = Manager()

@sv.on_fullmatch(('创建大乱斗'))
async def game_create(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	if mgr.is_playing(gid):
		await bot.finish(ev, '游戏仍在进行中…')

	image = R.img(f'{IMAGE_PATH}/{gid}.png')
	if os.path.exists(image.path):
		os.remove(image.path)

	with mgr.start(gid, uid) as scrimmage:
		msg = ['大乱斗房间已创建，等待加入中。。。',
				f'{WAIT_TIME}分钟后不开始会自动结束',
				f'当前人数({scrimmage.getPlayerNum()}/{MAX_PLAYER})',
				f'（发送“加入大乱斗”加入）']
		await bot.send(ev, '\n'.join(msg))
		scrimmage.user_card_dict = await get_user_card_dict(bot, gid)
		
		for i in range(60):				#从等待到正式开始的循环等待
			await asyncio.sleep(WAIT_TIME)
			if scrimmage.now_statu == NOW_STATU_OPEN :
				scrimmage.gameOpen()
				img = scrimmage.getNowImage()
				img.save(image.path)
				await bot.send(ev, image.cqcode)
				await asyncio.sleep(PROCESS_WAIT_TIME)
				await scrimmage.stageRemind(bot, ev)
				break
			elif scrimmage.now_statu == NOW_STATU_END : break

		if scrimmage.now_statu == NOW_STATU_OPEN :
			while True:								#开始后的循环等待
				await asyncio.sleep(WAIT_TIME)
				await scrimmage.PlayerStageTimer(gid, bot, ev)		#玩家阶段计时器
				if (scrimmage.now_statu == NOW_STATU_END or 
					scrimmage.now_statu == NOW_STATU_WIN): break
		if scrimmage.now_statu == NOW_STATU_WIN:
			msg = ['大乱斗已结束，排名如下：']
			for i in range(len(scrimmage.rank)):
				user_card = uid2card(scrimmage.rank[i + 1], scrimmage.user_card_dict)
				msg.append(f'第{i + 1}名：{user_card}')
			await bot.send(ev, '\n'.join(msg))
		else:
			await bot.send(ev, f'游戏结束')

@sv.on_fullmatch(('加入大乱斗'))
async def game_join(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id
	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_WAIT:
		return
	if uid in scrimmage.player_list :
		await bot.finish(ev, '您已经在准备房间里了', at_sender=True)
	if scrimmage.getPlayerNum() >= MAX_PLAYER:
		await bot.finish(ev, '人数已满，无法继续加入', at_sender=True)

	scrimmage.ready(uid)

	msg = []
	for user_id in scrimmage.player_list:
		user_card = uid2card(user_id, scrimmage.user_card_dict)
		msg.append(user_card)
	await bot.send(ev, f'已加入\n当前人数({scrimmage.getPlayerNum()}/{MAX_PLAYER})\n{" ".join(msg)}')
	if scrimmage.getPlayerNum() == MAX_PLAYER:
		await bot.send(ev, f'人数已满，可开始游戏。\n（[CQ:at,qq={scrimmage.room_master}]发送“开始大乱斗”开始）')

@sv.on_fullmatch(('开始大乱斗'))
async def game_start(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id
	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_WAIT:
		return
	if not uid == scrimmage.room_master:
		await bot.finish(ev, '只有房主才能开始', at_sender=True)
	if scrimmage.getPlayerNum() < 2:
		await bot.finish(ev, '要两个人以上才能开始', at_sender=True)

	scrimmage.now_statu = NOW_STATU_SELECT_ROLE
	role_list = '游戏开始，请选择角色，当前可选角色：\n（'
	for role in ROLE.values():
		role_list += f'{role["name"]} '
	role_list += ')\n输入“角色详情 角色名” 可查看角色属性和技能\n（所有人都选择角色后自动开始）\n'
	for player_id in scrimmage.player_list:
		role_list += f'[CQ:at,qq={player_id}]'
	await bot.send(ev, role_list)

@sv.on_message()#选择角色
async def select_role(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id
	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_SELECT_ROLE:
		return
	#已加入房间的玩家才能选择角色
	if uid not in scrimmage.player_list:
		return

	image = R.img(f'{IMAGE_PATH}/{gid}.png')

	character = chara.fromname(ev.message.extract_plain_text())
	if character.id != chara.UNKNOWN and character.id in ROLE:
		player = scrimmage.getPlayerObj(uid)
		player.initData(character.id, character, scrimmage)

		img = player.role_icon
		img.save(image.path)
		await bot.send(ev, f"您选择的角色是：{player.name}\n{image.cqcode}", at_sender=True)

		if scrimmage.checkAllPlayerSelectRole():
			await asyncio.sleep(PROCESS_WAIT_TIME)
			await bot.send(ev, "所有人都选择了角色，大乱斗即将开始！\n碾碎他们")
			await asyncio.sleep(PROCESS_WAIT_TIME)
			scrimmage.now_statu = NOW_STATU_OPEN

@sv.on_fullmatch(('扔色子','扔骰子','丢色子','丢骰子','丢','扔'))
async def throw_dice(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_OPEN:
		return
	#已加入房间的玩家才能丢色子
	if uid not in scrimmage.player_list:
		return
	#不是当前回合的玩家无法丢色子
	if scrimmage.getNowTurnPlayerObj().user_id != uid:
		return
	#当前回合不是丢色子状态无法丢色子
	if scrimmage.getPlayerObj(uid).now_stage != NOW_STAGE_DICE:
		return

	step = random.choice(range(1,9))
	await bot.send(ev, '色子结果为：' + str(step))
	await scrimmage.throwDice(uid, step, bot, ev)
	scrimmage.refreshNowImageStatu()

	image = R.img(f'{IMAGE_PATH}/{gid}.png')
	img = scrimmage.getNowImage()
	img.save(image.path)
	await bot.send(ev, image.cqcode)
	await asyncio.sleep(PROCESS_WAIT_TIME)
	await scrimmage.stageRemind(bot, ev)

@sv.on_message()#使用技能
async def use_skill(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	msg_text = ev.raw_message
	match = re.match(r'^(\d+)( |) *(?:\[CQ:at,qq=(\d+)\])?', msg_text)
	if not match and msg_text != '跳过':
		return
	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_OPEN:
		return
	#已加入房间的玩家才能释放技能
	if uid not in scrimmage.player_list:
		return
	#不是当前回合的玩家无法释放技能
	if scrimmage.getNowTurnPlayerObj().user_id != uid:
		return
	#当前回合不是放技能状态无法放技能
	if scrimmage.getPlayerObj(uid).now_stage != NOW_STAGE_SKILL:
		return
	
	skill_id = ''
	goal_player_id = ''
	if match:
		skill_id = match.group(1)
		goal_player_id = match.group(3) or '0'
	else:
		skill_id = '0'
		goal_player_id = '0'
	
	goal_player_id = int(goal_player_id)
	skill_id = int(skill_id)

	if goal_player_id != 0 and goal_player_id not in scrimmage.player_list:
		await bot.send(ev, "不能选择场外玩家")
		return

	ret = await scrimmage.useSkill(skill_id, uid, goal_player_id, bot, ev)
	if ret == RET_ERROR:
		return

	scrimmage.turnChange()				#回合切换
	scrimmage.refreshNowImageStatu()	#刷新当前显示状态

	image = R.img(f'{IMAGE_PATH}/{gid}.png')
	img = scrimmage.getNowImage()
	img.save(image.path)
	await bot.send(ev, image.cqcode)
	await asyncio.sleep(PROCESS_WAIT_TIME)
	await scrimmage.stageRemind(bot, ev)

@sv.on_fullmatch(('认输','投降','不玩了'))
async def throw_dice(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_OPEN:
		return
	#已加入房间的玩家才能投降
	if uid not in scrimmage.player_list:
		return
	#不是当前回合的玩家无法投降
	if scrimmage.getNowTurnPlayerObj().user_id != uid:
		return
	
	player = scrimmage.getPlayerObj(uid)
	scrimmage.outDispose(player)
	await bot.send(ev, f'{uid2card(uid, scrimmage.user_card_dict)}已投降')
	if scrimmage.now_statu == NOW_STATU_OPEN:
		scrimmage.turnChange()
		scrimmage.refreshNowImageStatu()
		image = R.img(f'{IMAGE_PATH}/{gid}.png')
		img = scrimmage.getNowImage()
		img.save(image.path)
		await bot.send(ev, image.cqcode)
		await asyncio.sleep(PROCESS_WAIT_TIME)
		await scrimmage.stageRemind(bot, ev)


@sv.on_message()#查看属性
async def check_property(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu != NOW_STATU_OPEN:
		return
	msg_text = ev.raw_message
	match = re.match(r'^查看属性(?: |) *(?:\[CQ:at,qq=(\d+)\])?', msg_text)
	if not match: return
	if match.group(1): uid = int(match.group(1))
	if uid not in scrimmage.player_list: return
	player = scrimmage.getPlayerObj(uid)
	msg = player.checkStatu(scrimmage)
	await bot.send(ev, "\n".join(msg))

@sv.on_rex(r'^角色详情( |)([\s\S]*)')
async def check_role(bot, ev: CQEvent):
	match = ev['match']
	if not match : return

	role_name = match.group(2)
	character = chara.fromname(role_name)
	if character.id != chara.UNKNOWN and character.id in ROLE:
		role_info = ROLE[character.id]
		msg = [
			f"名字：{role_info['name']}",
			f"生命值：{role_info['health']}",
			f"TP：{role_info['tp']}",
			f"攻击距离：{role_info['distance']}",
			f"攻击力：{role_info['attack']}",
			f"防御力：{role_info['defensive']}",
			f"暴击率：{role_info['crit'] > MAX_CRIT and MAX_CRIT or role_info['crit']}%",
			f"技能：",
		]
		skill_num = 1
		for skill in role_info['active_skills']:
			msg.append(f"  技能{skill_num}：{skill['name']}({skill['tp_cost']}tp)：{skill['text']}")
			skill_num += 1
		return await bot.send(ev, "\n".join(msg))

	await bot.send(ev, '不存在的角色')

@sv.on_fullmatch(('结束大乱斗'))
async def game_end(bot, ev: CQEvent):
	gid, uid = ev.group_id, ev.user_id

	scrimmage = mgr.get_game(gid)
	if not scrimmage  or scrimmage.now_statu == NOW_STATU_END:
		return
	if not priv.check_priv(ev, priv.ADMIN) and not uid == scrimmage.room_master:
		await bot.finish(ev, '只有群管理或房主才能强制结束', at_sender=True)

	scrimmage.now_statu = NOW_STATU_END
	await bot.send(ev, f"您已强制结束大乱斗，请等待结算")

@sv.on_fullmatch(('PCR大乱斗','pcr大乱斗','大乱斗帮助','PCR大乱斗帮助','pcr大乱斗帮助'))
async def game_help(bot, ev: CQEvent):
	msg = '''《PCR大乱斗帮助》
（游戏决出胜利者后可按排名获得贵族金币）
基础命令：
	1、大乱斗规则
	可查看大乱斗相关规则
	2、大乱斗角色
	可查看所有可用角色
	3、角色详情 （角色名）
	如：角色详情 黑猫
	可查看角色的基础属性和技能
	4、结束大乱斗
	可以强制结束正在进行的大乱斗游戏
	（该命令只有管理员和房主可用）
一、创建阶段：
	1、创建大乱斗
	2、加入大乱斗
	3、开始大乱斗
二、选择角色阶段：
	1、（角色名）
	如：凯露 / 黑猫
	（名字和外号都行）
三、对战阶段：
	1、丢色子
	2、（技能编号） @xxx
	如：1 @xxx
	发送技能编号并@目标，如果这个技能不需要指定目标，直接发送技能编号即可
	3、查看属性
	可查看自己当前角色详细属性
	4、投降 / 认输
'''
	await bot.send(ev, msg)

@sv.on_fullmatch(('大乱斗规则'))
async def game_help_all_role(bot, ev: CQEvent):
	msg = '''《PCR大乱斗规则》
1、和大富翁类似，一个正方形环形跑道，跑道上有多个事件，通过丢色子走到特定的位置触发事件
2、可多个玩家同时玩，最多4个，最少2个。每个玩家可选择一个pcr里的角色，不同的角色有不同的属性、技能
3、角色有tp值，可用来释放技能。每次投掷色子，所有玩家都会增加tp值，受到伤害也会增加tp值
4、需要选择目标的技能释放范围可能有距离限制，以角色属性的攻击距离为准
5、避免游戏时长过长，每(场上玩家数量)个玩家回合增加一次攻击力和攻击距离
6、可投降
7、活到最后获胜（吃鸡？）

--回合机制：
玩家回合：当前默认的回合机制，每个玩家丢一次色子为经过一回合
自我回合：另一种回合机制，每次轮到自己后才为经过一回合

（游戏决出胜利者后可按排名获得贵族金币）
'''
	await bot.send(ev, msg)

@sv.on_fullmatch(('大乱斗角色'))
async def game_help_rule(bot, ev: CQEvent):
	msg = '当前可选角色有：\n'
	for role in ROLE.values():
		msg += f'{role["name"]} '
	msg += f'\n共{len(ROLE)}位角色'
	await bot.send(ev, msg)
