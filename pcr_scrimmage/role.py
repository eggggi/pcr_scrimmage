##可用角色

"""
##可用角色可自定义增加，详细看下面的示例

基础属性：
	name			名字		string
	health			生命值		number
	distance		攻击距离	number
	attack			攻击力		number
	defensive		防御力		number
	tp				能量值		number
	active_skills	主动技能	list[dict]
	passive_skills	被动技能	list[dict] 依赖主动技能
		被动技能的主要作用，是为了让一个主动技能可以同时选择不同的触发对象
		例如：yly，砍别人一刀自己掉血
		被动技能优先级比主动高，可以先对自身增加攻击力后再进行攻击
		（其实，把这个 “被动技能” 说成是 “附带效果” 也可以，单纯为了区分不同的触发对象而已）

技能：
	name			技能名称	string
	text			技能描述	string
	tp_cost			消耗tp		number
	effect			技能效果	list[dict]
	trigger			触发对象	string
	passive			被动		list[number] 数字对应基础属性的passive_skill

	################（技能效果可增加，增加后在 skillEffect() 里做处理）################
	效果effect：(可选单个或多个) (被动技能：对自己和对目标的效果要分开)
		health_change			生命值改变，正数为回血，负数为造成伤害
		defensive_change		防御改变，正数为增加，负数为减少
		distance_change
		attack_change
		tp_change

		move				移动，正数为前进负数为后退	number
		move_goal			向目标移动（一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发）
							这个效果必须放在被动
		ignore_dist			无视距离，参数填啥都行，不会用到

		make_it_out_tp		令目标出局时tp变动
		make_it_out_turn	令目标出局时锁定回合

	################触发对象可继续增加，添加后在 skillTrigger() 里做处理################
	触发对象trigger：
		select				选择目标

		all					对所有人有效(包括自己)
		all_except_me		对所有人有效(除了自己)
		me					只对自己有效

		near				离自己最近

"""



EFFECT_HURT = "hurt"					#造成伤害	tuple元组 (数值，加成类型，加成的数值对象，加成比例，是否为真实伤害)
										#加成类型：attr.py , 为0时无加成; 加成的数值对象：0自己 1目标
EFFECT_ELIMINATE = "eliminate"			#斩杀效果，目标生命值越低造成的伤害越高		tuple元组 (目标生命值降低比例, 伤害数值)
										#EFFECT_ELIMINATE需要EFFECT_HURT作为前置
EFFECT_LIFESTEAL = "life_steal"			#生命偷取	float 伤害-生命值之间的转换比例
										#EFFECT_LIFESTEAL需要EFFECT_HURT作为前置

EFFECT_BUFF = "buff"					#buff效果	tuple元组 (BuffType.xx, 数值, 可触发次数)


EFFECT_HEALTH = "health_change"			#生命值改变，正数为回血，负数为扣血			tuple元组 (数值，加成类型，加成比例)
										#加成类型：attr.py , 为0时无加成

EFFECT_ATTR_CHANGE = "attr"				#属性改变，正数为增加，负数为减少			tuple元组 (属性类型，数值，加成类型，加成比例)
										#属性类型/加成类型：attr.py , 为0时无加成

EFFECT_DEFENSIVE = "defensive_change"	#防御改变，正数为增加，负数为减少 			number ↓同理
EFFECT_DISTANCE = "distance_change"
EFFECT_ATTACK = "attack_change"
EFFECT_TP = "tp_change"					#↑同理

EFFECT_MOVE = "move"					#移动，正数为前进负数为后退（触发跑道事件）	number
EFFECT_MOVE_GOAL = "move_goal"			#向目标移动（一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发） tuple元组(移动距离，是否无视攻击范围)
										#这个效果必须放在被动（不触发跑道事件）
EFFECT_IGNORE_DIST = "ignore_dist"		#无视距离效果，参数随便填，不会用到
										#这个效果必须放在被动
EFFECT_AOE = "aoe"						#范围效果			tuple (半径范围, 是否对自己生效)

EFFECT_OUT_TP = "make_it_out_tp"		#令目标出局时tp变动		number
EFFECT_OUT_TURN = "make_it_out_turn"	#令目标出局时锁定回合	number（锁定回合：不会切换到下一个玩家，当前玩家继续丢色子和放技能）


TRIGGER_SELECT = "select"						#选择目标(包括自己)
TRIGGER_SELECT_EXCEPT_ME = "select_except_me"	#选择目标(除了自己)
TRIGGER_ALL = "all"								#对所有人有效(包括自己)
TRIGGER_ALL_EXCEPT_ME = "all_except_me"			#对所有人有效(除了自己)
TRIGGER_ME = "me"								#只对自己有效
TRIGGER_NEAR = "near"							#离自己最近的目标

from .attr import Attr
from .buff import BuffType

# 角色字典
ROLE = {
	#注意：id要和_pcr_data.py里对应角色一样
	1060:{
		"name":"凯露",

		"health":800,
		"distance":10,
		"attack":100,
		"defensive":60,
		"tp":0,

		"active_skills" : [
			{
				"name":"闪电球",
				"text":"对目标造成100(+0.5自身攻击力)伤害并减少50防御，自身增加20点攻击力",
				"tp_cost":20,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[0],
				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 0.5, False),
					EFFECT_ATTR_CHANGE:(Attr.DEFENSIVE, -50, 0, 0),
				}
			},
			{
				"name":"能力吸附",
				"text":"对目标造成100(+1.0自身攻击力)伤害，所造成伤害的50%将转换为自身生命值",
				"tp_cost":40,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],
				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
					EFFECT_LIFESTEAL:0.5,
				}
			},
			{
				"name":"格林爆裂",
				"text":"对所有人造成200(+1.5自身攻击力)伤害",
				"tp_cost":50,
				"trigger": TRIGGER_ALL_EXCEPT_ME,
				"passive":[],
				"effect":{
					EFFECT_HURT:(200, Attr.ATTACK, 0, 1.5, False),
				}
			}
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_ME,
				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 20, 0, 0),
				}
			}
		]
	},
	1059:{
		"name":"可可萝",

		"health":1000,
		"distance":6,
		"attack":50,
		"defensive":70,
		"tp":0,

		"active_skills" : [
			{
				"name":"三连击",
				"text":"向目标移动3格，并对目标造成100(+1.5自身攻击力)伤害",
				"tp_cost":20,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[0],
				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.5, False)
				}
			},
			{
				"name":"光之守护",
				"text":"自身回复250点生命值，并增加50点攻击力",
				"tp_cost":50,
				"trigger": TRIGGER_ME,
				"passive":[],
				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.NOW_HEALTH, 250, 0, 0),
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 50, 0, 0),
				}
			}
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_MOVE_GOAL:(3, False),
				}
			}
		]
	},
	1058:{
		"name":"佩可",

		"health":1500,
		"distance":5,
		"attack":60,
		"defensive":100,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
				}
			},
			{
				"name":"超大饭团",
				"text":"回复自身100(+0.5自身防御力)生命值，并增加10点攻击力",
				"tp_cost":20,
				"trigger": TRIGGER_ME,
				"passive":[],

				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.NOW_HEALTH, 100, Attr.DEFENSIVE, 0.5),
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 10, 0, 0),
				}
			},
			{
				"name":"公主突袭",
				"text":"向目标移动5格，对目标造成150(+1.0自身攻击力)伤害，并增加自身50防御",
				"tp_cost":50,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[0,1],

				"effect":{
					EFFECT_HURT:(150, Attr.ATTACK, 0, 1.0, False),
				}
			}
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_MOVE_GOAL:(5, False),
				}
			},
			{
				"trigger": TRIGGER_ME,
				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.DEFENSIVE, 50, 0, 0),
				}
			}
		]
	},

	1036:{
		"name":"镜华",
		"health":700,
		"distance":15,
		"attack":150,
		"defensive":50,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
				}
			},
			{
				"name":"魔法增幅",
				"text":"自身增加50点攻击力",
				"tp_cost":30,
				"trigger": TRIGGER_ME,
				"passive":[],

				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 50, 0, 0),
				}
			},
			{
				"name":"冰枪术",
				"text":"对目标造成20(+1.8自身攻击力)伤害",
				"tp_cost":30,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(20, Attr.ATTACK, 0, 1.8, False)
				}
			},
			{
				"name":"宇宙苍蓝闪",
				"text":"无视距离，对目标造成50(+2.5自身攻击力)伤害",
				"tp_cost":70,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[0],

				"effect":{
					EFFECT_HURT:(50, Attr.ATTACK, 0, 2.5, False),
				}
			}
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_IGNORE_DIST:0,
				}
			},
		]
	},
	1020:{
		"name":"美美",
		"health":1000,
		"distance":5,
		"attack":110,
		"defensive":80,
		"tp":0,

		"active_skills" : [
			{
				"name":"蹦蹦跳跳",
				"text":"自身增加20点攻击力和20点防御力",
				"tp_cost":20,
				"trigger": TRIGGER_ME,
				"passive":[],

				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 20, 0, 0),
					EFFECT_ATTR_CHANGE:(Attr.DEFENSIVE, 20, 0, 0),
				}
			},
			{
				"name":"崩山击",
				"text":"向目标移动3格，并对目标及其半径5范围内的所有玩家造成100(+0.9自身攻击力)伤害",
				"tp_cost":30,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[0],

				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 0.9, False),
					EFFECT_AOE:(5, False)
				}
			},
			{
				"name":"兰德索尔正义",
				"text":"对目标造成100点真实伤害，目标当前生命值每降低1%则额外造成7点真实伤害",#斩杀效果
				"tp_cost":60,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 0, True),
					EFFECT_ELIMINATE:(1, 7)
				}
			},
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_MOVE_GOAL:(3, False),
				}
			},
		]
	},
	1004:{
		"name":"未奏希",
		"health":1500,
		"distance":10,
		"attack":100,
		"defensive":150,
		"tp":0,

		"active_skills" : [
			{
				"name":"小炸弹",
				"text":"对目标及其半径4范围内的所有玩家造成100(+1.0自身攻击力)伤害（包括自己）",
				"tp_cost":20,
				"trigger": TRIGGER_SELECT,
				"passive":[],

				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
					EFFECT_AOE:(4, True)
				}
			},
			{
				"name":"中炸弹",
				"text":"对目标及其半径8范围内的所有玩家造成150(+1.5自身攻击力)伤害（包括自己）",
				"tp_cost":40,
				"trigger": TRIGGER_SELECT,
				"passive":[],

				"effect":{
					EFFECT_HURT:(150, Attr.ATTACK, 0, 1.5, False),
					EFFECT_AOE:(8, True)
				}
			},
			{
				"name":"大炸弹",
				"text":"对场上所有玩家造成200(+2.0自身攻击力)伤害（包括自己）",
				"tp_cost":60,
				"trigger": TRIGGER_ALL,
				"passive":[],

				"effect":{
					EFFECT_HURT:(200, Attr.ATTACK, 0, 2.0, False)
				}
			}
		],
		"passive_skills": []
	},
	1003:{
		"name":"怜",
		"health":900,
		"distance":5,
		"attack":100,
		"defensive":70,
		"tp":0,

		"active_skills" : [
			{
				"name":"破甲突刺",
				"text":"无视距离，对离自己最近的目标造成100(+1.0自身攻击力)伤害，并降低目标50点防御力",
				"tp_cost":20,
				"trigger": TRIGGER_NEAR,
				"passive":[],

				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
					EFFECT_ATTR_CHANGE:(Attr.DEFENSIVE, -50, 0, 0),
				}
			},
			{
				"name":"格挡",
				"text":"为自己增加一个200点生命值的护盾（只可触发1次），并增加30点攻击力",
				"tp_cost":30,
				"trigger": TRIGGER_ME,
				"passive":[],

				"effect":{
					EFFECT_BUFF:(BuffType.Shield, 200, 1),
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 30, 0, 0),
				}
			},
			{
				"name":"极·鬼剑术-暴风式",
				"text":"对自己以外的所有人造成200(+1.0自身攻击力)真实伤害",
				"tp_cost":60,
				"trigger": TRIGGER_ALL_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(200, Attr.ATTACK, 0, 1.0, True)
				}
			}
		],
		"passive_skills": []
	},
	1002:{
		"name":"优衣",
		"health":1000,
		"distance":8,
		"attack":80,
		"defensive":60,
		"tp":10,

		"active_skills" : [
			{
				"name":"花瓣射击",
				"text":"对目标造成100(+1.5自身攻击力)伤害，并降低目标10点攻击力和10点TP",
				"tp_cost":20,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.5, False),
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, -10, 0, 0),
					EFFECT_ATTR_CHANGE:(Attr.TP, -10, 0, 0),
				}
			},
			{
				"name":"全体治愈",
				"text":"全体回复100生命值，自己额外回复100生命值，除自己外减少3点攻击距离",
				"tp_cost":50,
				"trigger": TRIGGER_ALL,
				"passive":[0,1],

				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.NOW_HEALTH, 100, 0, 0)
				}
			}
		],
		"passive_skills": [
			{
				"trigger": TRIGGER_ALL_EXCEPT_ME,
				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.DISTANCE, -3, 0, 0),
				}
			},
			{
				"trigger": TRIGGER_ME,
				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.NOW_HEALTH, 100, 0, 0)
				}
			}
		],
	},
	1001:{
		"name":"日和莉",
		"health":900,
		"distance":5,
		"attack":100,
		"defensive":60,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
				}
			},
			{
				"name":"勇气迸发",
				"text":"自身增加50点攻击力和1点攻击距离",
				"tp_cost":30,
				"trigger": TRIGGER_ME,
				"passive":[],

				"effect":{
					EFFECT_ATTR_CHANGE:(Attr.ATTACK, 50, 0, 0),
					EFFECT_ATTR_CHANGE:(Attr.DISTANCE, 1, 0, 0),
				}
			},
			{
				"name":"日和莉烈焰冲击",
				"text":"对目标造成300(+2.0自身攻击力)伤害，若目标被击倒，自身回复60点tp并继续下一回合",
				"tp_cost":100,
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"passive":[],

				"effect":{
					EFFECT_HURT:(300, Attr.ATTACK, 0, 2, False),
					EFFECT_OUT_TP:60,
					EFFECT_OUT_TURN:1
				}
			}
		],
		"passive_skills": []

	}

}
