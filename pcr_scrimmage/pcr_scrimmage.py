'''
<A little game base on hoshino_bot, gameplay like RichMan>
Copyright (C) <2021/06/11>  <eggggi>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from typing import Dict, List
import os
import asyncio
import math
import random

from  PIL  import   Image, ImageFont, ImageDraw
from hoshino.typing import CQEvent
from hoshino import R, Service, priv, log

from .attr import Attr, AttrTextChange
from .buff import BuffEffectType, BuffTriggerType, Buff, BuffType
from .runway_case import CASE_NONE, CASE_HEALTH, CASE_MOVE, RUNWAY_CASE
from .role import *


sv = Service(	'pcr_scrimmage',
				manage_priv=priv.ADMIN,
				enable_on_default=True,
				visible=True,
				bundle='pcr娱乐',
				help_='[大乱斗帮助] 击剑')

FILE_PATH = os.path.dirname(__file__)

IMAGE_PATH = R.img('pcr_scrimmage').path
logger = log.new_logger('pcr_scrimmage')
if not os.path.exists(IMAGE_PATH):
	os.mkdir(IMAGE_PATH)
	logger.info('create folder succeed')
IMAGE_PATH = 'pcr_scrimmage'

async def get_user_card_dict(bot, group_id):
	mList = await bot.get_group_member_list(group_id=group_id)
	d = {}
	for m in mList:
		d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
	return d
def uid2card(uid, user_card_dict):
	return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]

#防御力计算机制。
#100点防御力内，每1点防御力增加0.1%伤害减免；
#100点防御力后，每1点防御力增加0.05%伤害减免；
#最高有效防御力为1000
#（防御力可无限提升，但最高只能获得55%伤害减免）
def hurt_defensive_calculate(hurt, defensive):
	percent = 0.0
	if defensive <= 100:
		percent = defensive * 0.001
	else:
		if defensive <= 1000:
			percent = 100 * 0.001 + (defensive - 100) * 0.0005
		else:
			percent = 100 * 0.001 + 900 * 0.0005
	return hurt - hurt * percent


###显示偏移###	（可以改）
OFFSET_X = 45		#整体右移
OFFSET_Y = 50		#整体下移

###线宽###		（别改）
RUNWAY_LINE_WIDTH = 4		#跑道线宽
STATU_LINE_WIDTH = 2	#状态条线宽 血条tp条

###常用颜色###
COLOR_BLACK = (0,0,0)
COLOR_WRITE = (255,255,255)
COLOR_RED = (255,0,0)
COLOR_GREEN = (0,255,0)
COLOR_BLUE = (0,0,255)
COLOR_CAM_GREEN = (30,230,100)	#血条填充色
COLOR_CAM_BLUE = (30,144,255)	#tp条填充色

###当前房间状态###
NOW_STATU_WAIT = 0
NOW_STATU_SELECT_ROLE = 1
NOW_STATU_OPEN = 2
NOW_STATU_END = 3
NOW_STATU_WIN = 4

###当前玩家处于什么阶段###
NOW_STAGE_WAIT	= 0 #等待
NOW_STAGE_DICE	= 1 #丢色子
NOW_STAGE_SKILL = 2 #释放技能
NOW_STAGE_OUT	= 3 #出局

MAX_PLAYER = 4		#最大玩家数量
MAX_CRIT = 100		#最大暴击
MAX_TP = 100		#tp值上限
MAX_DIST = 15		#最大攻击距离

ONE_ROUND_TP = 10	#单回合获得tp量
ROUND_DISTANCE = 2	#每隔x回合增加的攻击距离(x为当前存活人数)
ROUND_ATTACK = 10	#每隔x回合增加的攻击力
HIT_DOWN_TP = 20	#击倒获得的tp

RET_ERROR = -1	#错误
RET_NORMAL = 0
RET_SUCCESS = 1	#成功


WAIT_TIME = 3			#每x秒检查一次房间状态
PROCESS_WAIT_TIME = 1	#避免发送太快增加的缓冲时间

STAGE_WAIT_TIME = 30	#玩家阶段等待时间，超过这个时间判负。
						#实际时间是 STAGE_WAIT_TIME * WAIT_TIME

#角色
class Role:
	def __init__(self, user_id) -> None:
		self.user_id = user_id	#玩家的qq号

		self.role_id = 0		#pcr角色编号
		self.name = ''			#角色名
		self.role_icon = None	#角色头像
		self.player_num = 0		#玩家在这个房间的编号
		self.room_obj = None	#房间对象

		self.attr = {}			#角色属性列表
		'''
		{
			Attr.xx = 数值,
			Attr.xx = 数值,
		}
		'''

		self.buff = {}			#角色buff列表
		'''
		NormalBuffFlag: 用来标记是否是普通buff，该类buff在结束后会返还扣除的属性值或扣除增加的属性值
		NormalBuffChangeNum: 用来记录普通buff改变的数值，用来处理有上限的属性
		{
			BuffType1 = [数值, 次数, NormalBuffFlag, NormalBuffChangeNum],
			BuffType2 = [数值, 次数, NormalBuffFlag, NormalBuffChangeNum],
		}
		'''

		self.now_location = 0				#当前位置
		self.now_stage = NOW_STAGE_WAIT		#当前处于什么阶段
		self.skip_turn = 0					#跳过x回合

		self.active_skills = []				#主动技能列表
		self.passive_skills = []			#被动技能列表
		self.extra_skills = []				#额外技能列表（用于双技能组）

	#选择角色后对数据的初始化
	def initData(self, role_id, role_info, room_obj):
		role_data = ROLE[role_id]
		if role_data :
			self.role_id = role_id

			self.name = role_data['name']
			self.role_icon = role_info.icon.open()
			self.room_obj:PCRScrimmage = room_obj

			self.attr[Attr.MAX_HEALTH] = role_data['health']
			self.attr[Attr.NOW_HEALTH] = self.attr[Attr.MAX_HEALTH]
			self.attr[Attr.DISTANCE] = role_data['distance']
			self.attr[Attr.ATTACK] = role_data['attack']
			self.attr[Attr.DEFENSIVE] = role_data['defensive']
			self.attr[Attr.CRIT] = role_data['crit']
			self.attr[Attr.CRIT_HURT] = 2
			self.attr[Attr.NOW_TP] = role_data['tp']
			self.attr[Attr.MAX_TP] = MAX_TP

			self.attr[Attr.COST_HEALTH] = 0

			self.active_skills = role_data['active_skills']
			self.passive_skills = role_data['passive_skills']
			self.extra_skills = role_data['extra_skills']

	
	#属性数值改变的统一处理
	def attrChange(self, attr_type, num):
		if self.now_stage == NOW_STAGE_OUT: return

		#属性数值改变前的处理
		if attr_type == Attr.NOW_HEALTH and num < 0:
			#如果生命值减少，则按百分比回复tp
			hurt_tp = math.floor(abs(num) / self.attr[Attr.MAX_HEALTH] * 100 / 2)
			self.attrChange(Attr.NOW_TP, hurt_tp)

		self.attr[attr_type] += num

		#属性数值改变后的处理
		if attr_type == Attr.MAX_HEALTH and num > 0 :
			#如果增加的是生命最大值，则当前生命也增加同等数值
			self.attr[Attr.NOW_HEALTH] += num
		if attr_type == Attr.MAX_TP and num > 0:
			#如果增加的是tp最大值，则当前tp也增加同等数值
			self.attr[Attr.NOW_TP] += num
		if ((attr_type == Attr.NOW_HEALTH or attr_type == Attr.MAX_HEALTH) and 
			self.attr[Attr.NOW_HEALTH] > self.attr[Attr.MAX_HEALTH]):
			#当前生命值不能超过最大生命值
			self.attr[Attr.NOW_HEALTH] = self.attr[Attr.MAX_HEALTH]
		if ((attr_type == Attr.NOW_TP or attr_type == Attr.MAX_TP) and 
			self.attr[Attr.NOW_TP] > self.attr[Attr.MAX_TP]):
			#不能超过最大tp
			self.attr[Attr.NOW_TP] = self.attr[Attr.MAX_TP]
		if attr_type == Attr.DISTANCE and self.attr[Attr.DISTANCE] > MAX_DIST:
			#不能超过最大攻击距离
			self.attr[Attr.DISTANCE] = MAX_DIST
		if attr_type == Attr.CRIT and self.attr[Attr.CRIT] > MAX_CRIT:
			#不能超过最大暴击
			self.attr[Attr.CRIT] = MAX_CRIT
		
		#已消耗生命值特殊处理
		if attr_type == Attr.NOW_HEALTH:
			self.attr[Attr.COST_HEALTH] = self.attr[Attr.MAX_HEALTH] - self.attr[Attr.NOW_HEALTH]

		if self.attr[attr_type] <= 0:
			self.attr[attr_type] = 0
			if attr_type == Attr.NOW_HEALTH:
				#如果是生命值降为0，则调用出局接口
				self.room_obj.outDispose(self)
		return self.attr[attr_type]
	#位置改变	flag:如果为真，则直接设置固定位置；如果为假，根据原位置改变
	def locationChange(self, num, runway, flag = False):
		if self.now_stage == NOW_STAGE_OUT: return
		runway[self.now_location]["players"].remove(self.user_id)
		if flag:
			self.now_location = num
		else:
			self.now_location += num
		while(self.now_location >= len(runway) or self.now_location < 0):
			if self.now_location >= len(runway):
				self.now_location -= len(runway)
			elif self.now_location < 0:
				self.now_location += len(runway)
		runway[self.now_location]["players"].append(self.user_id)

	#状态改变
	def stageChange(self, stage):
		self.now_stage = stage

	#眩晕x回合
	def dizziness(self, turn):
		self.skip_turn = turn

	#被攻击
	def beHurt(self, num):
		num = self.buffTriggerByTriggerType(BuffTriggerType.Hurt, num)
		self.attrChange(Attr.NOW_HEALTH, num)
		return num

	#添加buff
	def addBuff(self, buff_info):
		self.buff[buff_info[0]] = [buff_info[1], buff_info[2], 0, 0]
	#删除buff（不要在迭代self.buff时调用）
	def deleteBuff(self, buff_type):
		if buff_type in self.buff:
			trigger_type = Buff[buff_type]['trigger_type']
			if (trigger_type == BuffTriggerType.Normal or 
				trigger_type == BuffTriggerType.NormalSelf or 
				trigger_type == BuffTriggerType.Attack) and 'attr_type' in Buff[buff_type]:
				self.attrChange(Buff[buff_type]['attr_type'], -self.buff[buff_type][3])
			del self.buff[buff_type]
	#删除失效buff
	def deleteInvalidBuff(self):
		buff_keys = []
		for keys in self.buff.keys():
			buff_keys.append(keys)
		for buff_type in buff_keys:
			if self.buff[buff_type][1] <= 0 :
				self.deleteBuff(buff_type)

	#通过触发类型触发buff
	def buffTriggerByTriggerType(self, trigger_type, num = 0):
		for buff_type in self.buff.keys():
			need_trigger_type = Buff[buff_type]['trigger_type']
			if need_trigger_type == trigger_type:
				effect_type = Buff[buff_type]['effect_type']
				num = self.buffEffect(trigger_type, effect_type, buff_type, num)
			if len(self.buff) == 0 : break
		return num

	#通过buff类型触发buff
	def buffTriggerByBuffType(self, buff_type, num = 0):
		trigger_type = Buff[buff_type]['trigger_type']
		effect_type = Buff[buff_type]['effect_type']
		if buff_type in self.buff:
			num = self.buffEffect(trigger_type, effect_type, buff_type, num)
		return num

	#buff效果生效
	def buffEffect(self, trigger_type, effect_type, buff_type, num):
		if self.buff[buff_type][1] <= 0: return num
		if effect_type == BuffEffectType.Attr:
			attr_type = Buff[buff_type]['attr_type']
			if (trigger_type == BuffTriggerType.Normal or 
				trigger_type == BuffTriggerType.NormalSelf or 
				trigger_type == BuffTriggerType.Attack):
				if self.buff[buff_type][2] == 0:
					old_num = self.attr[attr_type]
					new_num = self.attrChange(attr_type, self.buff[buff_type][0])
					self.buff[buff_type][2] = 1
					self.buff[buff_type][3] = new_num - old_num
			else:
				self.attrChange(attr_type, self.buff[buff_type][0])
		elif effect_type == BuffEffectType.Shield:
			num += self.buff[buff_type][0]
			self.buff[buff_type][0] += num - self.buff[buff_type][0]
			if num > 0:num = 0
		elif effect_type == BuffEffectType.Blind:
			num = 0

		self.buff[buff_type][1] -= 1

		return num


	#检查当前状态
	def checkStatu(self, scrimmage):
		msg = [
			f"玩家：{uid2card(self.user_id, scrimmage.user_card_dict)}",
			f"角色：{self.name}",
			f"生命值：{self.attr[Attr.NOW_HEALTH]}/{self.attr[Attr.MAX_HEALTH]}",
			f"TP：{self.attr[Attr.NOW_TP]}/{self.attr[Attr.MAX_TP]}",
			f"攻击距离：{self.attr[Attr.DISTANCE]}",
			f"攻击力：{self.attr[Attr.ATTACK]}",
			f"防御力：{self.attr[Attr.DEFENSIVE]}",
			f"暴击率：{self.attr[Attr.CRIT]}%",
			f"暴击伤害：{self.attr[Attr.CRIT_HURT]}倍",
			f'位置：{self.now_location}'
		]
		if len(self.buff) != 0:
			msg.append('\nbuff效果列表:')
			for buff_type, buff_info in self.buff.items():
				buff_text:str = Buff[buff_type]['text']
				buff_text = buff_text.format(abs(buff_info[0]), buff_info[1] == 0 and 1 or (buff_info[1] > 10000 and "无限" or buff_info[1]))
				msg.append(f'{Buff[buff_type]["name"]}:{buff_text}')
		return msg


#公主连结大乱斗
class PCRScrimmage:
	#初始化
	def __init__(self, gid, manager, room_master, across_range = 10, vertical_range = 10, grid_size = 50) -> None:
		##核心数据
		self.gid = gid						#群号
		self.mgr = manager					#管理器
		self.room_master = room_master		#房主
		self.player_list = {}				#玩家列表  ####这个东西不能迭代values，不懂原理
		self.now_statu = NOW_STATU_WAIT		#当前游戏状态
		self.now_turn = 0					#现在是玩家x的回合
		self.dice_num = 0					#已丢色子次数的总数
		self.lock_turn = 0					#回合锁定，x回合内都是同个玩家
		self.now_playing_players = []		#当前正在游玩的玩家id	[xxx, xxx]
		self.rank = {}						#结算排行	{1:xxx,2:xxx}
		self.player_stage_timer = 0			#玩家阶段计时器。回合切换时重置

		self.user_card_dict = {}			#群内所有成员信息

		#初始化跑道，总共36个格子
		self.runway = [{"players":[], "case":0} for i in range((across_range - 1) * 4)]
		for runway_case in self.runway :
			runway_case["case"] = random.choice(range(len(RUNWAY_CASE)))

		##显示数据	注意：显示数据别乱改
		self.grid_size = grid_size	##本来想做自定义跑道数量的，但显示适配太麻烦了，躺平
		self.vertical_range_x = vertical_range
		self.across_range_y = across_range
		width = (self.vertical_range_x + 2) * self.grid_size
		hight = (self.across_range_y + 2) * self.grid_size

		#基础图片，初始化完成后不会再改变
		self.base_image = Image.new('RGB', (width, hight), COLOR_WRITE)
		self.draw = ImageDraw.Draw(self.base_image)
		
		#当前状态图片，会随着游戏进度一直改变
		self.now_image = Image.new('RGB', (width, hight), COLOR_WRITE)
		self.now_draw = ImageDraw.Draw(self.now_image)

		FONTS_PATH = os.path.join(FILE_PATH,'fonts')
		FONTS = os.path.join(FONTS_PATH,'msyh.ttf')
		self.runwayTextFont = ImageFont.truetype(FONTS, 30)
		self.font = ImageFont.truetype(FONTS, 15)
		pass


	def __enter__(self):
		self.mgr.playing[self.gid] = self
		self.displayInit()
		self.ready(self.room_master)
		return self
	def __exit__(self, type_, value, trace):
		del self.mgr.playing[self.gid]


	#加入房间准备
	def ready(self, user_id):
		if self.getPlayerNum() < MAX_PLAYER:
			self.player_list[user_id] = Role(user_id)
		pass
	#检查是否全部玩家都选择了角色
	def checkAllPlayerSelectRole(self):
		num = 0
		for player_id in self.player_list:
			if self.getPlayerObj(player_id).role_id != 0:
				num += 1
		if num >= len(self.player_list):
			return True
		else:
			return False
	#游戏正式开始需要做的处理
	def gameOpen(self):
		num = 0
		for player_id in self.player_list :
			offset_x , offset_y = 0, 0
			if num == 1 : offset_x = 1
			elif num == 2 : offset_y = 1
			elif num == 3 : offset_x, offset_y = 1, 1

			self.now_playing_players.append(player_id)
			player = self.getPlayerObj(player_id)
			player.now_location = num * 9	#玩家保存的位置
			self.runway[num * 9]["players"].append(player_id)	#跑道保存的位置
			player.player_num = num			#玩家编号
			head = player.role_icon			#玩家头像

			after_head = head.resize((95, 97))

			#放置玩家头像
			self.base_image.paste(after_head,
						(OFFSET_X + self.grid_size * 2 				 + offset_x * 200 + 3,
						 OFFSET_Y + math.floor(self.grid_size * 1.5) + offset_y * 190 + 2 ))
			#显示玩家名字
			self.playerInfoText(offset_x, offset_y, 12,text = f'名字：{uid2card(player.user_id, self.user_card_dict)}')
			#攻击距离
			self.playerInfoText(offset_x, offset_y, 28,text = f'距离：{player.attr[Attr.DISTANCE]}')

			num += 1
		
		#房主的状态改为丢色子状态
		self.getPlayerObj(self.room_master).stageChange(NOW_STAGE_DICE)
		
		#更新当前显示状态
		self.refreshNowImageStatu()



	#玩家阶段计时器，超过一定时间不操作直接判负
	async def PlayerStageTimer(self, gid, bot, ev):
		self.player_stage_timer += 1
		if self.player_stage_timer > STAGE_WAIT_TIME:
			now_turn_player = self.getNowTurnPlayerObj()
			self.outDispose(now_turn_player)
			await bot.send(ev, f'[CQ:at,qq={now_turn_player.user_id}]已超时，出局')
			self.turnChange()			#回合切换
			self.refreshNowImageStatu()	#刷新当前显示状态
			image = R.img(f'{IMAGE_PATH}/{gid}.png')
			img = self.getNowImage()
			img.save(image.path)
			await bot.send(ev, image.cqcode)
			await asyncio.sleep(PROCESS_WAIT_TIME)
			await self.stageRemind(bot, ev)
	
	#回合改变，到下一个玩家
	def turnChange(self):
		now_turn_player:Role = self.getNowTurnPlayerObj()
		if now_turn_player.now_stage != NOW_STAGE_OUT:#如果当前玩家已经出局，则不改变状态
			now_turn_player.stageChange(NOW_STAGE_WAIT)#已结束的玩家
		else:
			self.lock_turn = 0 #如果玩家已出局，则取消回合锁定
		
		self.player_stage_timer = 0 #重置玩家阶段计时器
		
		#游戏胜利或结束则直接退出
		if (self.now_statu == NOW_STATU_WIN or 
			self.now_statu == NOW_STATU_END):
			return
		
		skip_flag = False
		i = 0
		#寻找下一回合的玩家
		while (i < len(self.player_list)):
			self.now_turn += 1
			if self.now_turn >= len(self.player_list):
				self.now_turn = 0
			next_turn_player = self.getNowTurnPlayerObj()#下一个玩家
			if next_turn_player.skip_turn > 0:	#跳过被眩晕的玩家
				next_turn_player.skip_turn -= 1
				skip_flag = True
				continue
			if next_turn_player.now_stage != NOW_STAGE_OUT:	#跳过已出局的玩家
				if self.lock_turn > 0:	#检查是否锁定了当前回合
					now_turn_player.stageChange(NOW_STAGE_DICE)
					self.now_turn = now_turn_player.player_num
					self.lock_turn -= 1
					return
				next_turn_player.stageChange(NOW_STAGE_DICE)
				return
			if skip_flag and len(self.now_playing_players) > 1:	#如果检测到有跳过眩晕玩家，则重新循环
				i = 0
				skip_flag = False
			i += 1

		#找不到直接结束游戏
		self.now_statu = NOW_STATU_WIN
	
	#玩家出局处理
	def outDispose(self, player:Role):
		player.stageChange(NOW_STAGE_OUT)
		self.rank[len(self.now_playing_players)] = player.user_id
		if player.user_id in self.now_playing_players:
			self.now_playing_players.remove(player.user_id)
		if len(self.now_playing_players) == 1:
			self.rank[1] = self.now_playing_players[0]
			self.now_statu = NOW_STATU_WIN


	#丢色子
	async def throwDice(self, player_id, step, bot, ev):
		player = self.getPlayerObj(player_id)
		
		player.locationChange(step, self.runway)

		for iter_player_id in self.now_playing_players:	#每丢1次色子为一个回合
			iter_player = self.getPlayerObj(iter_player_id)
			iter_player.deleteInvalidBuff()
			iter_player.attrChange(Attr.NOW_TP, ONE_ROUND_TP)
			iter_player.buffTriggerByTriggerType(BuffTriggerType.Normal)
			iter_player.buffTriggerByTriggerType(BuffTriggerType.Turn)
			if iter_player_id == player_id:
				player.buffTriggerByTriggerType(BuffTriggerType.NormalSelf)
				player.buffTriggerByTriggerType(BuffTriggerType.TurnSelf)

		self.dice_num += 1
		#每丢(场上玩家数量)次色子，所有玩家增加攻击距离和攻击力
		if self.dice_num % (len(self.now_playing_players) + 1) == 0:
			for iter_player_id in self.now_playing_players:
				self.getPlayerObj(iter_player_id).attrChange(Attr.DISTANCE, ROUND_DISTANCE)
				self.getPlayerObj(iter_player_id).attrChange(Attr.ATTACK, ROUND_ATTACK)
			self.dice_num = 1

		if player.now_stage == NOW_STAGE_OUT:
			await bot.send(ev, f'[CQ:at,qq={player.user_id}]出局')
			self.turnChange()	#回合切换
			self.refreshNowImageStatu()	#刷新当前显示状态
			return

		await self.caseTrigger(player, bot, ev)

	#触发跑道事件
	async def caseTrigger(self, player:Role, bot, ev:CQEvent):
		case = self.runway[player.now_location]["case"]
		str1, num = "", 0
		if case == CASE_NONE:
			pass
		elif case == CASE_MOVE:
			numRange = RUNWAY_CASE[CASE_MOVE]["range"]
			num = random.choice(range(numRange[0],numRange[1]))
			if num == 0 : num += 1
			player.locationChange(num, self.runway)
		else:
			numRange = RUNWAY_CASE[case]["range"]
			num = random.choice(range(numRange[0],numRange[1]))
			player.attrChange(RUNWAY_CASE[case]["attr"], num)


		if num > 0:
			if case == CASE_MOVE:
				str1 = "前"
			else:
				str1 = "增加"
		else:
			if case == CASE_MOVE:
				str1 = "后"
			else:
				str1 = "减少"
		text = "触发事件，"
		text += RUNWAY_CASE[case]["text"].format( str1, abs(num) )
		if case != CASE_NONE and num == 0:
			text += "，所以什么都不会发生"
		elif case == CASE_NONE:
			text = "什么也没发生"
		await bot.send(ev, text)

		if case == CASE_MOVE and num != 0:
			self.refreshNowImageStatu()
			image = R.img(f'{IMAGE_PATH}/{ev.group_id}.png')
			img = self.getNowImage()
			img.save(image.path)
			await bot.send(ev, image.cqcode)
			await asyncio.sleep(1)
			await self.caseTrigger(player, bot, ev)
		if player.now_stage == NOW_STAGE_OUT:
			await bot.send(ev, f'[CQ:at,qq={player.user_id}]出局')
			self.turnChange()	#回合切换
			self.refreshNowImageStatu()	#刷新当前显示状态
		else:
			player.stageChange(NOW_STAGE_SKILL)


	#使用技能
	async def useSkill(self, skill_id, use_player_id, goal_player_id, bot, ev):
		if skill_id != 0:
			use_player_obj = self.getPlayerObj(use_player_id)
			if skill_id > len(use_player_obj.active_skills) or skill_id <= 0:
				await bot.send(ev, '技能编号不正确')
				return RET_ERROR
			
			real_skill_id = skill_id - 1	#实际技能id
			skill = use_player_obj.active_skills[real_skill_id]
			skill_tp_cost = skill["tp_cost"]			#tp消耗
			if skill_tp_cost > use_player_obj.attr[Attr.NOW_TP]:		#检查tp是否足够
				await bot.send(ev, 'tp不足，无法使用这个技能')
				return RET_ERROR
			
			#先扣除tp
			use_player_obj.attrChange(Attr.NOW_TP, -skill_tp_cost)
			
			use_player_name = uid2card(use_player_obj.user_id, self.user_card_dict)
			use_skill_name = skill["name"]
			await bot.send(ev, f'{use_player_name}尝试使用{use_skill_name}') 

			back_msg = []

			
			ret, msg = self.skillCheckAndUse(use_player_obj, goal_player_id, skill, back_msg)

			if ret == RET_ERROR:
				await bot.send(ev, msg)
				#技能释放失败，返还tp
				use_player_obj.attrChange(Attr.NOW_TP, skill_tp_cost)
				return ret

			try:
				await bot.send(ev, '\n'.join(back_msg))
			except:
				logger.info('\n'.join(back_msg))
				await bot.send(ev, '触发了很多效果，但是发不出去。')
			
		return RET_SUCCESS

	#使用技能前的检查
	def skillCheckAndUse(self, use_player_obj:Role, goal_player_id, skill, back_msg):
		skill_effect_triggers = skill["effect_trigger"]

		#检查是否存在双技能组
		if "skill_change" in skill and len(skill["skill_change"]) == 2:
			buff_type = skill["skill_change"][0]
			new_skill_goal = skill["skill_change"][1]
			if buff_type in use_player_obj.buff :
				skill_effect_triggers = []
				for skill_id in new_skill_goal :
					skill_effect_triggers.append(use_player_obj.extra_skills[skill_id])

		#检查所有技能
		for skill_effect_trigger in skill_effect_triggers:
			skill_trigger = skill_effect_trigger["trigger"]
			skill_effect = skill_effect_trigger["effect"]
			#检查是否有选定目标的技能触发类型
			if skill_trigger == TRIGGER_SELECT or skill_trigger == TRIGGER_SELECT_EXCEPT_ME:
				if goal_player_id > 0:
					goal_player_obj = self.getPlayerObj(goal_player_id)
					if not goal_player_obj:
						return RET_ERROR, '目标不在房间里'
					if goal_player_obj.now_stage == NOW_STAGE_OUT:
						return RET_ERROR, '目标已出局'
					if skill_trigger == TRIGGER_SELECT_EXCEPT_ME and goal_player_id == use_player_obj.user_id:
						return RET_ERROR, '不能选择自己'
				else:
					return RET_ERROR, '该技能需要选择一个目标'
				#检查技能里是否带有无视距离的技能效果
				disregard_dist = False
				move_goal_dist = 0
				if EFFECT_IGNORE_DIST in skill_effect:
					disregard_dist = True
				if EFFECT_MOVE_GOAL in skill_effect : #向目标移动效果，需要加上向目标移动的距离进行计算
					move_goal_dist = skill_effect[EFFECT_MOVE_GOAL][0]
					disregard_dist = skill_effect[EFFECT_MOVE_GOAL][1]

				#计算攻击距离
				dist = self.getTwoPlayerDist(use_player_obj, self.getPlayerObj(goal_player_id)) - move_goal_dist
				if (dist > use_player_obj.attr[Attr.DISTANCE]) and not disregard_dist:
					return RET_ERROR, '攻击距离不够'

		#触发所有技能的技能效果
		for skill_effect_trigger in skill_effect_triggers:
			ret, msg = self.skillTrigger(use_player_obj, goal_player_id, skill_effect_trigger, back_msg)
			if ret == RET_ERROR : return ret, msg
		return RET_SUCCESS, ''
	
	#技能释放对象选择
	def skillTrigger(self, use_skill_player:Role, goal_player_id, skill, back_msg):
		skill_trigger = skill["trigger"]						#技能的触发对象
		skill_effect = skill["effect"]							#技能效果

		#选择触发对象
		if skill_trigger == TRIGGER_SELECT or skill_trigger == TRIGGER_SELECT_EXCEPT_ME:	#特定目标
			goal_player_obj = self.getPlayerObj(goal_player_id)
			return self.skillEffect(use_skill_player, goal_player_obj, skill_effect, back_msg)
		elif skill_trigger == TRIGGER_ME:				#自己
			ret, msg = self.skillEffect(use_skill_player, use_skill_player, skill_effect, back_msg)
			if ret == RET_ERROR : return ret, msg
		elif skill_trigger == TRIGGER_ALL:				#所有人
			for player_id in self.player_list:
				goal_player = self.getPlayerObj(player_id)
				ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
				if ret == RET_ERROR : return ret, msg
		elif skill_trigger == TRIGGER_ALL_EXCEPT_ME:	#除了自己的其它人
			for player_id in self.player_list:
				if player_id == use_skill_player.user_id : continue
				goal_player = self.getPlayerObj(player_id)
				ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
				if ret == RET_ERROR : return ret, msg
		elif skill_trigger == TRIGGER_NEAR:				#离自己最近的目标
			goal_player = self.getNearPlayer(use_skill_player)
			ret, msg = self.skillEffect(use_skill_player, goal_player, skill_effect, back_msg)
			if ret == RET_ERROR : return ret, msg
		else:
			return RET_ERROR, '技能配置出错'

		return RET_SUCCESS, msg

	#技能效果生效
	def skillEffect(self, use_skill_player:Role, goal_player:Role, skill_effect_base, back_msg:List):
		if goal_player.now_stage == NOW_STAGE_OUT : return RET_NORMAL, ''

		skill_effect:Dict = skill_effect_base.copy()	#拷贝一份，避免修改保存在角色信息的技能效果
		use_player_name = uid2card(use_skill_player.user_id, self.user_card_dict)
		goal_player_name = uid2card(goal_player.user_id, self.user_card_dict)


		#aoe效果
		if EFFECT_AOE in skill_effect:
			aoe_dist = skill_effect[EFFECT_AOE][0]	# aoe范围
			to_self = skill_effect[EFFECT_AOE][1]	# 是否对自己生效
			del skill_effect[EFFECT_AOE] # 删掉aoe效果，避免无限递归
			for i in range(goal_player.now_location - aoe_dist, goal_player.now_location + aoe_dist):
				location = i #处理后的位置，避免下标不在跑道上的数组里
				if location >= len(self.runway) : location -= len(self.runway)
				elif location < 0 : location = len(self.runway) + location
				if len(self.runway[location]["players"]) > 0:
					for runway_player_id in self.runway[location]["players"]:
						if runway_player_id == use_skill_player.user_id and not to_self : continue
						runway_player_obj = self.getPlayerObj(runway_player_id)
						self.skillEffect(use_skill_player, runway_player_obj, skill_effect, back_msg)
			skill_effect.clear() # 递归完成清空所有效果，不需要再次触发

		#向目标移动
		if EFFECT_MOVE_GOAL in skill_effect:
			num = skill_effect[EFFECT_MOVE_GOAL][0]
			distance = use_skill_player.now_location - goal_player.now_location
			half_circle = len(self.runway) / 2

			if distance > 0:
				if distance > half_circle:
					use_skill_player.locationChange(num, self.runway)
				else:
					use_skill_player.locationChange(-num, self.runway)
			else:
				if abs(distance) < half_circle:
					use_skill_player.locationChange(num, self.runway)
				else:
					use_skill_player.locationChange(-num, self.runway)
			back_msg.append(f'{use_player_name}往离{goal_player_name}较近的方向移动了{num}步')

		#选择目标的移动效果
		if EFFECT_JUMP in skill_effect:
			use_skill_player.locationChange(goal_player.now_location + random.choice([-1, 1]), self.runway, True)
			back_msg.append(f'{use_player_name}移动到了{goal_player_name}的身边')

		#击退/拉近
		if EFFECT_HIT_BACK in skill_effect:
			num = skill_effect[EFFECT_HIT_BACK]
			distance = use_skill_player.now_location - goal_player.now_location
			half_circle = len(self.runway) / 2
			if distance > 0:
				if distance > half_circle:
					goal_player.locationChange(num, self.runway)
				else:
					goal_player.locationChange(-num, self.runway)
			else:
				if abs(distance) < half_circle:
					goal_player.locationChange(num, self.runway)
				else:
					goal_player.locationChange(-num, self.runway)
			if num > 0:
				back_msg.append(f'{use_player_name}将{goal_player_name}击退了{num}步')
			else:
				back_msg.append(f'{use_player_name}将{goal_player_name}拉近了{abs(num)}步')

		#位置改变
		if EFFECT_MOVE in skill_effect:
			num = skill_effect[EFFECT_MOVE]
			goal_player.locationChange(num, self.runway)
			if num < 0:
				back_msg.append(f'{goal_player_name}后退了{abs(num)}步')
			else:
				back_msg.append(f'{goal_player_name}前进了{num}步')
		
		#buff效果
		if EFFECT_BUFF in skill_effect:
			for buff_info in skill_effect[EFFECT_BUFF]:
				buff_name = Buff[buff_info[0]]['name']
				buff_text:str = Buff[buff_info[0]]['text']
				buff_text = buff_text.format(abs(buff_info[1]), buff_info[2] > 1000 and "无限" or buff_info[2] )
				goal_player.addBuff(buff_info)
				back_msg.append(f'{goal_player_name}获得buff《{buff_name}》，{buff_text}')
		
		#立即触发特定buff
		if EFFECT_BUFF_BY_BT in skill_effect:
			for buffType in skill_effect[EFFECT_BUFF_BY_BT]:
				self.getPlayerObj(goal_player.user_id).buffTriggerByBuffType(buffType)

		#属性改变
		if EFFECT_ATTR_CHANGE in skill_effect:
			for effect in skill_effect[EFFECT_ATTR_CHANGE]:
				attr_type	  = effect[0]	#属性类型
				num 		  = effect[1]	#基础数值
				addition_type = effect[2]	#加成类型
				addition_prop = effect[3]	#加成比例
				text = AttrTextChange(attr_type)

				if addition_type != 0 and addition_prop != 0 :
					add = goal_player.attr[addition_type] * addition_prop
					num = math.floor(num + (num < 0 and -add or add))	#计算加成后的数值
				goal_player.attrChange(attr_type, num)

				if num < 0:
					back_msg.append(f'{goal_player_name}降低了{abs(num)}点{text}')
					if goal_player.now_stage == NOW_STAGE_OUT:
						back_msg.append(f'[CQ:at,qq={goal_player.user_id}]出局')
				else:
					back_msg.append(f'{goal_player_name}增加了{num}点{text}')
		
		#造成伤害
		if EFFECT_HURT in skill_effect:
			num, crit_flag = self.hurtCalculate(skill_effect, use_skill_player, goal_player, back_msg)
			num = goal_player.beHurt(num)
			back_msg.append(f'{crit_flag and "暴击！" or ""}{goal_player_name}受到了{abs(num)}点伤害')
			if goal_player.now_stage == NOW_STAGE_OUT:
				use_skill_player.attrChange(Attr.NOW_TP, HIT_DOWN_TP)#击倒回复tp
				back_msg.append(f'[CQ:at,qq={goal_player.user_id}]出局')

		#效果击倒tp
		if EFFECT_OUT_TP in skill_effect:
			if goal_player.now_stage == NOW_STAGE_OUT:
				num = skill_effect[EFFECT_OUT_TP]
				use_skill_player.attrChange(Attr.NOW_TP, num)
				if num < 0:
					back_msg.append(f'{goal_player_name}被击倒，{use_player_name}降低了{abs(num)}点TP')
				else:
					back_msg.append(f'{goal_player_name}被击倒，{use_player_name}增加了{num}点TP')

		#回合锁定效果
		if EFFECT_LOCKTURN in skill_effect:
			num = skill_effect[EFFECT_LOCKTURN]
			self.lock_turn = num
			back_msg.append(f'{use_player_name}锁定了{num}回合')

		#击退回合锁定效果
		if EFFECT_OUT_LOCKTURN in skill_effect:
			if goal_player.now_stage == NOW_STAGE_OUT:
				num = skill_effect[EFFECT_OUT_LOCKTURN]
				self.lock_turn = num
				back_msg.append(f'{use_player_name}锁定了{num}回合')

		#眩晕效果	
		if EFFECT_DIZZINESS in skill_effect:
			num = skill_effect[EFFECT_DIZZINESS]
			goal_player.dizziness(num)
			back_msg.append(f'{goal_player_name}被眩晕{num}回合')

		if len(back_msg) == 0:
			back_msg.append('什么都没发生')
		return RET_SUCCESS, ''

	#伤害计算独立出来处理
	def hurtCalculate(self, skill_effect, use_skill_player:Role, goal_player:Role, back_msg:List):
		num 		  = abs(skill_effect[EFFECT_HURT][0])				#基础数值
		addition_type = skill_effect[EFFECT_HURT][1]					#加成类型
		addition_goal = (skill_effect[EFFECT_HURT][2] == 0 				#（三目）
							and use_skill_player or goal_player) 		#加成的数值对象：0自己 1目标
		addition_prop = skill_effect[EFFECT_HURT][3]					#加成比例
		is_real 	  = skill_effect[EFFECT_HURT][4]					#是否是真实伤害

		use_skill_player.buffTriggerByTriggerType(BuffTriggerType.Attack)
		crit_flag = random.choice(range(0, MAX_CRIT)) < use_skill_player.attr[Attr.CRIT]

		if addition_type != 0 and addition_prop != 0 :				#计算加成后的数值
			num = num + addition_goal.attr[addition_type] * addition_prop	
		if use_skill_player.attr[Attr.CRIT] != 0 and crit_flag:		#计算暴击
			num *= use_skill_player.attr[Attr.CRIT_HURT]
		if not is_real:#如果是真实伤害则不计算目标的防御
			goal_player_def = goal_player.attr[Attr.DEFENSIVE]		#目标防御力
			num = hurt_defensive_calculate(num, goal_player_def)	#计算目标防御力后的数值


		#斩杀效果
		if EFFECT_ELIMINATE in skill_effect:
			#cons_prop：目标已消耗的生命值比例; real_prop：真正的伤害比例
			cons_prop = 1 - goal_player.attr[Attr.NOW_HEALTH] / goal_player.attr[Attr.MAX_HEALTH]
			real_prop = cons_prop / skill_effect[EFFECT_ELIMINATE][0]
			num += real_prop * 100 * skill_effect[EFFECT_ELIMINATE][1]
		#背水效果
		if EFFECT_STAND in skill_effect:
			cons_prop = 1 - use_skill_player.attr[Attr.NOW_HEALTH] / use_skill_player.attr[Attr.MAX_HEALTH]
			real_prop = cons_prop / skill_effect[EFFECT_STAND][0]
			num += real_prop * 100 * skill_effect[EFFECT_STAND][1]
		#生命偷取
		if EFFECT_LIFESTEAL in skill_effect:
			steal_prop = skill_effect[EFFECT_LIFESTEAL]
			add = math.floor(num * steal_prop)
			use_skill_player.attrChange(Attr.NOW_HEALTH, add)
			back_msg.append(f'{uid2card(use_skill_player.user_id, self.user_card_dict)}增加了{add}点生命值')

		#判断一下是否有致盲buff
		num = use_skill_player.buffTriggerByBuffType(BuffType.Blind, num)

		num = math.floor(num)	#小数数值向下取整
		num = 0 - num			#变回负数，代表扣血
		return num, crit_flag


	#阶段提醒，丢色子/放技能阶段
	async def stageRemind(self, bot, ev: CQEvent):
		player = self.getNowTurnPlayerObj()
		stage = player.now_stage
		msg = [f'回合剩余{WAIT_TIME * (STAGE_WAIT_TIME - self.player_stage_timer)}秒']
		if stage == NOW_STAGE_DICE:
			msg.append(f'[CQ:at,qq={player.user_id}]的丢色子阶段(发送 丢色子)')
			await bot.send(ev, "\n".join(msg))
		elif stage == NOW_STAGE_SKILL:
			msg.append(f'[CQ:at,qq={player.user_id}]的放技能阶段：\n(发送技能编号，如需选择目标则@目标)')
			skill_list = player.active_skills
			skill_num = 0
			for skill in skill_list:
				tp_cost = skill["tp_cost"]
				now_tp = player.attr[Attr.NOW_TP]
				success = now_tp >= tp_cost and "√" or "×"
				msg.append(f'  技能{skill_num + 1}:{skill["name"]}({tp_cost}TP){success}:\n   {skill["text"]}')
				skill_num += 1
			msg.append('(发送"跳过"跳过出技能阶段)')
			await bot.send(ev, "\n".join(msg))



	#获取基础图片
	def getBaseImage(self):
		return self.base_image
	#获取当前状态图片
	def getNowImage(self):
		return self.now_image
	#获取当前玩家数量
	def getPlayerNum(self):
		return len(self.player_list)
	#获取玩家对象
	def getPlayerObj(self, player_id):
		if player_id in self.player_list:
			player:Role = self.player_list[player_id]
			return player
		else:return None
	#获取当前回合的玩家对象
	def getNowTurnPlayerObj(self):
		for player_id in self.player_list:
			player = self.getPlayerObj(player_id)
			if player.player_num == self.now_turn:
				return player
	#获取两个玩家之间的距离
	def getTwoPlayerDist(self, p1:Role, p2:Role):
		dist = abs(p1.now_location - p2.now_location)
		half_circle = len(self.runway) / 2
		if abs(dist) > half_circle : dist = half_circle - abs(half_circle - dist)
		return dist
	#获取离玩家最近的一个目标玩家id
	def getNearPlayer(self, own_player:Role):
		dist_list = []	#距离列表 [[玩家id,距离],[]]
		for player_id in self.player_list:
			player = self.getPlayerObj(player_id)
			if player == own_player : continue
			if player.now_stage == NOW_STAGE_OUT : continue
			dist_list.append([player.user_id, self.getTwoPlayerDist(own_player, player)])
		#极其低效的排序算法，时间复杂度为O(n^2)，数据量小，懒得改了_(:3)∠)_
		for i in range(len(dist_list)):#类似插入排序，从小到大
			save_info = dist_list[i]
			save_location = -1
			del dist_list[i]
			for j in range(len(dist_list)):
				comp_info = dist_list[j]
				if save_info[1] > comp_info[1]:
					save_location = j
			dist_list.insert(save_location + 1, save_info)
		return self.getPlayerObj(dist_list[0][0])




	#刷新当前状态图片
	def refreshNowImageStatu(self):
		self.now_image = self.base_image.copy()
		self.now_draw = ImageDraw.Draw(self.now_image)

		#遍历玩家列表，刷新玩家当前状态
		num = 0
		for player_id in self.player_list :
			offset_x , offset_y = 0, 0
			if num == 1 : offset_x = 1
			elif num == 2 : offset_y = 1
			elif num == 3 : offset_x, offset_y = 1, 1

			player = self.getPlayerObj(player_id)
			health_line_length = 96 * (player.attr[Attr.NOW_HEALTH] / player.attr[Attr.MAX_HEALTH])
			tp_line_length = 96 * (player.attr[Attr.NOW_TP] / player.attr[Attr.MAX_TP])

			self.statuLineFill(health_line_length, offset_x, offset_y, -16, COLOR_CAM_GREEN)	#血条填充
			self.statuLineFill(tp_line_length, offset_x, offset_y, 1, COLOR_CAM_BLUE)			#tp条填充
			self.roleStatuText(offset_x, offset_y, -23, text = str(player.attr[Attr.NOW_HEALTH]) )			#血条数值
			self.roleStatuText(offset_x, offset_y, -5, text = str(player.attr[Attr.NOW_TP]))					#tp条数值
			self.playerInfoText(offset_x, offset_y, 28,text = f'dist   ：{player.attr[Attr.DISTANCE]}')		#攻击距离
			self.playerInfoText(offset_x, offset_y, 12,text = f'name：{uid2card(player.user_id, self.user_card_dict)}')#玩家名字
			
			if self.now_turn == player.player_num:	#当前回合的玩家，头像框为绿色
				self.drawBox(100, 100, self.grid_size * 2 + offset_x * 200, self.grid_size * 1.5 + offset_y * 190, COLOR_GREEN, is_now = True)
			if player.now_stage == NOW_STAGE_OUT:	#已出局的玩家，头像框为黑色，且跑道旁不显示头像
				self.drawBox(100, 100, self.grid_size * 2 + offset_x * 200, self.grid_size * 1.5 + offset_y * 190, COLOR_BLACK, is_now = True)
			else:
				self.roleIconLocation(player.role_icon, player.now_location)	#显示玩家角色位置
			num += 1

	#显示初始化
	def displayInit(self):
		j = 0
		for i in range(self.across_range_y + 1) :#画横线
			self.draw.line( (0 + OFFSET_X, j + OFFSET_Y) +
							(self.grid_size * self.vertical_range_x + OFFSET_X, j + OFFSET_Y),
							fill = COLOR_BLACK, width = RUNWAY_LINE_WIDTH )
			j += self.grid_size
		j = 0
		for i in range(self.vertical_range_x + 1) :#画竖线
			self.draw.line( (j + OFFSET_X, 0 + OFFSET_Y) +
							(j + OFFSET_X, self.grid_size * self.across_range_y + OFFSET_Y),
							fill = COLOR_BLACK, width = RUNWAY_LINE_WIDTH )
			j += self.grid_size
		#中间遮掩
		self.draw.rectangle( (RUNWAY_LINE_WIDTH + self.grid_size + OFFSET_X - 1, RUNWAY_LINE_WIDTH + self.grid_size + OFFSET_Y - 1,
							  self.grid_size - (RUNWAY_LINE_WIDTH/2) + (self.vertical_range_x - 2) * self.grid_size + OFFSET_X,
							  self.grid_size - (RUNWAY_LINE_WIDTH/2) + (self.across_range_y - 2) * self.grid_size + OFFSET_Y),
							  fill = COLOR_WRITE )
		#画框
		for i in range(2):
			for j in range(2):
				self.drawBox(100, 100, self.grid_size * 2 + i * 200, self.grid_size * 1.5 + j * 190,	  COLOR_RED)#头像框
				self.drawBox(100, 10,  self.grid_size * 2 + i * 200, self.grid_size * 4   + j * 190 - 17, COLOR_BLACK, STATU_LINE_WIDTH)#血条框
				self.drawBox(100, 10,  self.grid_size * 2 + i * 200, self.grid_size * 4   + j * 190,      COLOR_BLACK,  STATU_LINE_WIDTH)#TP框
		#填充跑道事件文字
		self.fillCaseText()

	#画盒子（画框）
	def drawBox(self, length, width, offset_x, offset_y, color = COLOR_BLACK, line_width = RUNWAY_LINE_WIDTH, is_now = False):
		draw = self.draw 
		if is_now : draw = self.now_draw
		draw.line(( (OFFSET_X + offset_x, 			OFFSET_Y + offset_y),
						 (OFFSET_X + offset_x, 			OFFSET_Y + width + offset_y),
						 (OFFSET_X + length + offset_x, OFFSET_Y + width + offset_y),
						 (OFFSET_X + length + offset_x, OFFSET_Y + offset_y),
						 (OFFSET_X + offset_x, 			OFFSET_Y + offset_y) ),
						 fill = color, width = line_width )
	
	#填充跑道事件文字
	def fillCaseText(self):
		i = 0
		for runway in self.runway:
			runway_case = RUNWAY_CASE[runway["case"]]
			name = runway_case["name"]
			color = runway_case["color"]
			if i <= 9:
				self.fillText(i, 0, color, name)
			elif i <= 18:
				self.fillText(9, i - 9, color, name)
			elif i <= 27:
				self.fillText(9 - (i - 9 * 2), 9, color, name)
			else:
				self.fillText(0, 9 - (i - 9 * 3), color, name)
			i += 1
	#同上，封装一下
	def fillText(self, grid_x, grid_y, textColor = COLOR_BLACK, text = ''):
		self.draw.text( (grid_x * self.grid_size + OFFSET_X + 10, grid_y * self.grid_size + OFFSET_Y + 5), 
						text, font = self.runwayTextFont, fill = textColor)

	#状态条填充   最大长度96  血条offset填-16，tp条填1
	def statuLineFill(self, length, offset_x, offset_y, offset, color = COLOR_BLACK, width = 8):
		self.now_draw.rectangle( (OFFSET_X + self.grid_size * 2 + offset_x * 200 + 2,
								  OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset,
								  OFFSET_X + length + self.grid_size * 2 + offset_x * 200 + 2,
								  OFFSET_Y + width + self.grid_size * 4 + offset_y * 190 + offset),
								  fill = color )
	
	#角色当前状态数字（血量/tp）
	def roleStatuText(self, offset_x, offset_y, offset, textColor = COLOR_BLACK, text = ''):
		self.now_draw.text( (OFFSET_X + 100 + self.grid_size * 2 + offset_x * 200 + 2,
						 OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset), 
						text, font = self.font, fill = textColor)
	
	#玩家信息文字
	def playerInfoText(self, offset_x, offset_y, offset, textColor = COLOR_BLACK, text = ''):
		self.now_draw.text( (OFFSET_X + self.grid_size * 2 + offset_x * 200 + 2,
						 OFFSET_Y + self.grid_size * 4 + offset_y * 190 + offset), 
						text, font = self.font, fill = textColor)
	
	#角色头像位置
	def roleIconLocation(self, icon, location):
		small_icon = icon.resize((25,25))
		if location <= 9:
			self.now_image.paste(small_icon, (OFFSET_X + 14 + self.grid_size * location , 
											  OFFSET_Y - 30 ) )
		elif location <= 18:
			self.now_image.paste(small_icon, (OFFSET_X + 10 + self.grid_size * 10, 
											  OFFSET_Y + 14 + self.grid_size * (location - 9)) )
		elif location <= 27:
			self.now_image.paste(small_icon, (OFFSET_X + 14 + self.grid_size * (9 - (location - 9 * 2)) ,
											  OFFSET_Y + 10 + self.grid_size * 10) )
		else:
			self.now_image.paste(small_icon, (OFFSET_X - 30, 
											  OFFSET_Y + 14 + self.grid_size * (9 - (location - 9 * 3)) ) )



#管理器
class Manager:
	def __init__(self):
		self.playing:List[PCRScrimmage] = {}

	def is_playing(self, gid):
		return gid in self.playing

	def start(self, gid, uid):
		return PCRScrimmage(gid, self, uid)

	def get_game(self, gid):
		return self.playing[gid] if gid in self.playing else None

