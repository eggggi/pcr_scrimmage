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
	crit			暴击		float	暴击概率百分比，1为100%
	active_skills	主动技能	list[dict]
	passive_skills	被动技能	list[dict] 未实现
	extra_skills	双技能组	list[dict]


技能：
	name			技能名称	string
	text			技能描述	string
	tp_cost			消耗tp		number
	effect			技能效果	list[dict]
	trigger			触发对象	string
	passive			被动		list[number] 数字对应基础属性的passive_skill

	################（技能效果可增加，增加后在 skillEffect() 里做处理）################
	效果effect：(可选单个或多个) (被动技能：对自己和对目标的效果要分开)
		attr				属性改变，如果要同时改变多个属性值，每个属性都需要单独添加一条被动

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



EFFECT_HURT			= "hurt"			#造成伤害	tuple元组 (数值，加成类型，加成的数值对象，加成比例，是否为真实伤害)
										#加成类型：attr.py , 为0时无加成; 加成的数值对象：0自己 1目标

										#需要EFFECT_HURT作为前置	↓
EFFECT_ELIMINATE	= "eliminate"		#斩杀效果，目标生命值越低造成的伤害越高		tuple元组 (目标生命值降低比例, 伤害数值)
EFFECT_STAND		= "stand"			#背水效果，自身生命值越低造成的伤害越高		tuple元组 (自身生命值降低比例, 伤害数值)
EFFECT_LIFESTEAL	= "life_steal"		#生命偷取	float 伤害-生命值之间的转换比例
										#需要EFFECT_HURT作为前置	↑

EFFECT_BUFF = "buff"					#buff效果		list[tuple,tuple] [(BuffType.xx, 数值, 可触发次数), (...)]
EFFECT_BUFF_BY_BT = "buff_by_bt"		#buff效果触发(通过buff类型)	list[BuffType]		立即触发指定buff类型的buff效果
										#EFFECT_BUFF_BY_BT需要EFFECT_BUFF作为前置
EFFECT_ATTR_CHANGE = "attr"				#属性改变，正数为增加，负数为减少	list[tuple,tuple] [(属性类型，数值，加成类型，加成比例), (...)]
										#属性类型/加成类型：attr.py , 为0时无加成

EFFECT_MOVE = "move"					#移动，正数为前进负数为后退（触发跑道事件）	number
EFFECT_MOVE_GOAL = "move_goal"			#向目标移动（一个技能有多个效果且包括向目标移动，向目标移动效果必须最先触发） tuple元组(移动距离，是否无视攻击范围)
										#这个效果必须放在被动（不触发跑道事件）
EFFECT_IGNORE_DIST = "ignore_dist"		#无视距离效果，参数随便填，不会用到
										#这个效果必须放在被动
EFFECT_AOE = "aoe"						#范围效果			tuple	(半径范围, 是否对自己生效)
EFFECT_HIT_BACK = "hit_back"			#击退				number	填正数为击退x格子，负数为拉近
EFFECT_LOCKTURN = "lock_turn"			#锁定回合			number	不会切换到下一个玩家，当前玩家继续丢色子和放技能
EFFECT_SKILL_CHANGE = "skill_change"	#更改技能			tuple	(BuffType.xx, [被动技能编号1, 被动技能编号2])
										#当自身存在某个特定buff时，技能效果替换为特定被动效果，原效果不触发
EFFECT_JUMP = "jump"					#选择目标的移动效果，移动到目标身边，参数随便填，不会用到
										#效果相对比较特殊，最好放在被动且搭配TRIGGER_SELECT_EXCEPT_ME使用

EFFECT_OUT_TP = "make_it_out_tp"		#令目标出局时tp变动		number
EFFECT_OUT_LOCKTURN = "make_it_out_turn"#令目标出局时锁定回合	number	锁定回合：不会切换到下一个玩家，当前玩家继续丢色子和放技能

EFFECT_DIZZINESS = "dizziness"			#眩晕效果，跳过特定玩家一回合 number

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
	1701:{
		"name":"环奈",

		"health":1000,
		"distance":9,
		"attack":110,
		"defensive":80,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"冲击之刃",
				"text":"对目标造成及其半径3范围内所有玩家造成90(+1.2自身攻击力)伤害，并降低30护甲",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(90, Attr.ATTACK, 0, 1.2, False),
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -30, 0, 0)],
							EFFECT_AOE:(3, False)
						}
					}
				]
			},
			{
				"name":"天赐之物",
				"text":"所有玩家增加50点攻击力和10%暴击率，自身持续永久，其他玩家持续1个自我回合",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_BUFF:[
								(BuffType.NormalSelfAttrAtkUp, 50, 1),
								(BuffType.NormalSelfAttrCritUp, 10, 1),
							],
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.CRIT, 10, 0, 0),
								(Attr.ATTACK, 50, 0, 0)
							],
						}
					},
				]
			},
			{
				"name":"闪耀之刃",
				"text":"对目标造成及其半径4范围内所有玩家造成120(+1.2自身攻击力)伤害，并将所造成伤害的20%转为生命值。自身增加10%暴击率和0.1倍爆伤",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.CRIT, 10, 0, 0),
								(Attr.CRIT_HURT, 0.1, 0, 0)
							],
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(120, Attr.ATTACK, 0, 1.2, False),
							EFFECT_LIFESTEAL:0.2,
							EFFECT_AOE:(4, False),
						}
					},
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1068:{
		"name":"晶",

		"health":1300,
		"distance":9,
		"attack":50,
		"defensive":100,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+0.8自身攻击力)伤害,并回复10点TP",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 0.8, False)
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 10, 0, 0)],
						}
					},
				]
			},
			{
				"name":"热身!/加速！",
				"text":"热身！:增加自己80攻击力、15%的暴击率持续4回合。\n "+
				       "\t加速！:永久增加自己100点攻击、20%的暴击率，并展开+10TP上升领域3回合。",
				"tp_cost":20,

				"skill_change":(BuffType.Akirasworld, [0]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[
								(BuffType.NormalAttrAtkUp, 80, 4),
								(BuffType.NormalAttrCritUp, 15, 4),
							],
						}
					}
				]
			},
			{
				"name":"岩石穿刺",
				"text":"岩石穿刺！:降低目标20点防御力，并造成100(+0.8自身攻击力)，并将所造成伤害的10%转为生命值；\n"+
						"\t如果已释放万物改造，则该技能将额外永久降低玩家20点攻击力，且附加自身损失生命值的额外真实伤害，并附带20%生命偷取。",
				"tp_cost":30,

				"skill_change":(BuffType.Akirasworld, [1]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 20, 0, 0)],
							EFFECT_HURT:(100, Attr.ATTACK, 0, 0.8, False),
							EFFECT_LIFESTEAL:0.10,
						}
					}
				]
			},
			{
				"name":"万物改造/万物归灵",
				"text":"使用七冠权力，大幅提升自身属性，回复30tp，并将其他所有玩家防御力降为0，且继续下一回合。\n"+
					   "\t万物归灵:对所有玩家造成0(+3.0自身攻击力)的真实伤害，并回复所造成伤害2倍的生命值。",
				"tp_cost":100,

				"skill_change":(BuffType.Akirasworld, [2]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 20, 0, 0)],
							EFFECT_BUFF:[
								(BuffType.Akirasworld, 0, 99999),
								(BuffType.NormalAttrAtkUp, 200, 99999),
								(BuffType.NormalAttrCritUp, 25, 99999),
								(BuffType.NormalAttrDefUp, 30, 99999),
							],
							EFFECT_LOCKTURN:1,
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -1, Attr.DEFENSIVE, 1)],
						}
					},
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [
			{
				"trigger": TRIGGER_ME,
				"effect":{
					EFFECT_BUFF:[(BuffType.TurnAttrTPUp, 10, 3)],
					EFFECT_ATTR_CHANGE:[
						(Attr.ATTACK, 100, 0, 0),
						(Attr.CRIT, 20, 0, 0)
					],
				}
			},
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 0.8, True),
					EFFECT_STAND:(1, 1.5),
					EFFECT_LIFESTEAL:0.2,
					EFFECT_ATTR_CHANGE:[
						(Attr.DEFENSIVE, -20, 0, 0),
						(Attr.ATTACK, -20, 0, 0)
					],
				}
			},
			{
				"trigger": TRIGGER_ALL_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(0, Attr.ATTACK, 0, 3.0, True),
					EFFECT_LIFESTEAL:2,
				}
			},
		],
	},
	1063:{
		"name":"亚里莎",

		"health":875,
		"distance":15,
		"attack":130,
		"defensive":75,
		"crit":20,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"翼之光辉!",
				"text":"回复自身50点TP值；若已使用过箭贯汝身，则将双倍回复自身TP值，并额外进行下一回合。 ",
				"tp_cost":20,

				"skill_change":(BuffType.ArisasArrow, [0]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 50, 0, 0),],
						}
					}
				]
			},
			{
				"name":"缠绕藤蔓",
				"text":"使目标攻击力降为0，持续一个自我回合",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.NormalSelfAttrAtkDown, -99999, 1)],
						}
					}
				]
			},
			{
				"name":"箭贯汝身",
				"text":"对其一名玩家，造成125(+1.25物理攻击力)的物理伤害；若已使用箭贯汝身，则造成真实伤害，并将所造成伤害的50%转化为生命值",
				"tp_cost":100,

				"skill_change":(BuffType.ArisasArrow, [1]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(125, Attr.ATTACK, 0, 1.25, False)
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.ArisasArrow, 0, 9999)]
						}
					},
				]
			}
		],
		"extra_skills": [
			{
				"trigger": TRIGGER_ME,
				"effect":{
					EFFECT_LOCKTURN:1,
					EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 100, 0, 0)]
				}
			},
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(125, Attr.ATTACK, 0, 1.25, True),
					EFFECT_LIFESTEAL:0.5
				}
			}
		],
		"passive_skills": []
	},
	1061:{
		"name":"矛依未",

		"health":1200,
		"distance":5,
		"attack":130,
		"defensive":60,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害,并回复5点TP",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 5, 0, 0)],
						}
					}
				]
			},
			{
				"name":"吓到你发抖！/ 天楼回刃斩",
				"text":("吓到你发抖！:对目标造成50(+0.8自身攻击力)伤害，并降低30点攻击力持续3玩家回合，且将其击退5步 \n" + 
						"\t天楼回刃斩：对目标造成120(+1.5自身攻击力)伤害，并将造成伤害的12%转化为生命值"),
				"tp_cost":20,

				"skill_change":(BuffType.TenRouHaDanKen, [0]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 0.8, False),
							EFFECT_BUFF:[(BuffType.NormalAttrAtkDown, -30, 3)],
							EFFECT_HIT_BACK:5,
						}
					}
				]
			},
			{
				"name":"这边啦这边！/ 天楼闪薙斩",
				"text":("这边啦这边！:降低目标及其半径范围2以内所有玩家45点防御力，持续8个玩家回合，并减少20TP \n" + 
						"\t天楼闪薙斩：对目标及其半径范围3以内所有玩家造成100(+1.1自身攻击力)伤害，并将造成伤害的5%转化为生命值"),
				"tp_cost":20,

				"skill_change":(BuffType.TenRouHaDanKen, [1]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, -20, 0, 0)],
							EFFECT_BUFF:[(BuffType.NormalAttrDefDown, -45, 8)],
							EFFECT_AOE:(2, False),
						}
					}
				]
			},
			{
				"name":"天楼霸断剑",
				"text":"对目标造成50(+1.0自身攻击力)伤害，并巨幅增加自身所有属性，持续全场！",
				"tp_cost":100,

				"skill_change":(BuffType.TenRouHaDanKen, [2,3]),
				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 1, False),
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 100, 0, 0)],
							EFFECT_BUFF:[(BuffType.TenRouHaDanKen, 5, 99999),
										(BuffType.NormalAttrAtkUp, 120, 99999),
										(BuffType.NormalAttrCritUp, 30, 99999),
										(BuffType.NormalAttrMaxHelUp, 300, 99999)],
							EFFECT_BUFF_BY_BT:[ BuffType.NormalAttrAtkUp,
												BuffType.NormalAttrCritUp,
												BuffType.NormalAttrMaxHelUp],
						}
					},
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(120, Attr.ATTACK, 0, 1.5, False),
					EFFECT_LIFESTEAL:0.12,
				}
			},
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(100, Attr.ATTACK, 0, 1.1, False),
					EFFECT_AOE:(3, False),
					EFFECT_LIFESTEAL:0.05,
				}
			},
			{
				"trigger": TRIGGER_SELECT_EXCEPT_ME,
				"effect":{
					EFFECT_HURT:(50, Attr.ATTACK, 0, 1, False),
				}
			},
			{
				"trigger": TRIGGER_ME,
				"effect":{EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 90, 0, 0)],}
			},
		],
	},
	1060:{
		"name":"凯露",

		"health":1050,
		"distance":10,
		"attack":125,
		"defensive":60,
		"crit":20,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"闪电球",
				"text":"对目标及其范围2内的敌人造成100(+0.7自身攻击力)伤害并减少50防御(持续4回合)，并增加自身30点攻击力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 30, 0, 0)],
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 0.7, False),
							EFFECT_BUFF:[(BuffType.NormalAttrDefDown, -50, 4)],
							EFFECT_AOE:(2, False),
						}
					},
				]
			},
			{
				"name":"能量吸附",
				"text":"对目标造成50(+1.4自身攻击力)伤害，并将造成伤害的30%转换为自身生命值，并回复自身40点TP",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 1.4, False),
							EFFECT_LIFESTEAL:0.3,
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 40, 0, 0)],
						}
					}
				]
			},
			{
				"name":"格林爆裂",
				"text":"对所有人造成100(+2.2自身攻击力)伤害",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 2.2, False),
						}
					}
				]
			},
			{
				"name":"深渊炸裂",
				"text":"对所有人造成200(+2.2自身攻击力)真实伤害，并清空tp",
				"tp_cost":100,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(200, Attr.ATTACK, 0, 2.2, True),
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, -1, Attr.NOW_TP, 1)],
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
    },
	
	1059:{
		"name":"可可萝",

		"health":1000,
		"distance":6,
		"attack":70,
		"defensive":70,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"三连击",
				"text":"向目标移动3格，并对目标造成100(+1.5自身攻击力)伤害",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(3, False),
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.5, False)
						}
					}
				]
			},
			{
				"name":"加速",
				"text":"增加50点防御力和攻击力，并继续下一回合",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.DEFENSIVE, 50, 0, 0),
								(Attr.ATTACK, 50, 0, 0)],
							EFFECT_LOCKTURN:1
						}
					}
				]
			},
			{
				"name":"光之加护",
				"text":"自身回复300点生命值，并增加50点攻击力，且接下来4个玩家回合额外增加5Tp",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 300, 0, 0),
												(Attr.ATTACK, 50, 0, 0)],
							EFFECT_BUFF:[(BuffType.TurnAttrTPUp, 5, 4)],
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1058:{
		"name":"佩可",

		"health":1800,
		"distance":5,
		"attack":55,
		"defensive":82,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.8自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1.8, False)
						}
					}
				]
			},
			{
				"name":"跳砍",
				"text":"对目标造成50(+1.5自身防御力)伤害",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.DEFENSIVE, 0, 1.5, False)
						}
					}
				]
			},
			{
				"name":"超大饭团",
				"text":"回复自身100(+0.8自身防御力)生命值，并增加30点防御力",
				"tp_cost":25,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 100, Attr.DEFENSIVE, 0.8),
												(Attr.DEFENSIVE, 30, 0, 0)],
						}
					}
				]
			},
			{
				"name":"公主突袭",
				"text":"向目标移动5格，对目标造成350真实伤害，并增加自身45点防御力",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(5, False),
							EFFECT_HURT:(350, Attr.ATTACK, 0, 0, True),
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 45, 0, 0)],
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1057:{
		"name":"姬塔",
		"health":900,
		"distance":5,
		"attack":90,
		"defensive":60,
		"crit":15,
		"tp":0,

		"active_skills": [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0攻击力)点伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"广域斩击",
				"text":"对目标造80(+1.0攻击力)伤害，恢复自身40TP",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(80, Attr.ATTACK, 0, 1.0, False),
						}
					},
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 40, 0, 0)],
						}
					}
				]
			},
			{
				"name":"剑意迸发",
				"text":"恢复自身50TP，并提升20点TP上限和10%暴击率",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 50, 0, 0),
												(Attr.MAX_TP, 20, 0, 0),
												(Attr.CRIT, 10, 0, 0) ],
						}
					}
				]
			},
			{
				"name":"星河一天",
				"text":"对离自己最近的目标造成150(+1.5攻击力)伤害，并回复30点TP和提升0.2倍暴击伤害。所造成伤害的20%将转为生命值。",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.NOW_TP, 30, 0, 0),
								(Attr.CRIT_HURT, 0.2, 0, 0),
							],
						}
					},
					{
						"trigger": TRIGGER_NEAR,
						"effect":{
							EFFECT_HURT:(150, Attr.ATTACK, 0, 1.5, False),
							EFFECT_LIFESTEAL:0.3,
						}
					}
				]
			},
		],
		
		"passive_skills": [],
		"extra_skills" : [],
	},
	1052:{
		"name":"莉玛",
		"health":1700,
		"distance":5,
		"attack":0,
		"defensive":160,
		"crit":0,
		"tp":0,

		"active_skills":[
			{
				"name":"普通攻击",
				"text":"对目标造成50(+0.1自身防御力)点真实伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(75, Attr.DEFENSIVE, 0, 0.1, True)
						}
					}
				]
			},
			{
				"name":"护盾",
				"text":"为自己增加一个200点生命值的护盾（只可触发1次），并增加30点防御力",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 200, 1)],
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 30, 0, 0)],
						}
					}
				]
			},
			{
				"name":"毛茸茸突袭",
				"text":"向目标移动3格，对目标造成60(+0.3自身防御力)伤害，并增加自身32点防御",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(3, False),
							EFFECT_HURT:(60, Attr.DEFENSIVE, 0, 0.3, False),
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 32, 0, 0)],
						}
					}
				]
			},
			{
				"name":"毛茸茸挥击",
				"text":"向目标移动4格，对目标造成140(+0.8自身防御力)伤害，并增加自身75点防御",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(4, False),
							EFFECT_HURT:(140, Attr.DEFENSIVE, 0, 0.8, False),
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 75, 0, 0)],
						}
					}
				]
			}
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1049:{
		"name":"静流",
		"health":1200,
		"distance":5,
		"attack":70,
		"defensive":120,
		"crit":5,
		"tp":0,

		"active_skills":[
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)真实伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1.0, True),
						}
					}
				]
			},
			{
				"name":"爱的头槌",
				"text":"眩晕目标1回合，为自己和目标恢复50生命值，自身额外回复0(+1.5自身防御力)生命值",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 50, Attr.DEFENSIVE, 1.5)],
						},
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 50, 0, 0)],
							EFFECT_DIZZINESS:1,
						}
					}
				]
			},
			{
				"name":"守护",
				"text":"为自己增添一个可抵御300点伤害的护盾（可触发1次），并提升40防御力",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 300, 1)],
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 40, 0, 0),]
						}
					}
				]
			},
			{
				"name":"神圣惩击",
				"text":"对目标造成其最大生命值40%的真实伤害，并为自己增添一个可抵御300点伤害的护盾(可触发1次)",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 300, 1)],
						},
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(1, Attr.MAX_HEALTH, 1, 0.4, True),
						}
					}
				]
			},
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1044:{
		"name":"伊莉亚",
		"health":1280,
		"distance":6,
		"attack":180,
		"defensive":40,
		"crit":25,
		"tp":0,

		"active_skills":[
			{
				"name":"普通攻击",
				"text":"对目标造成0(+0.8自身攻击力)真实伤害，并回复所造成伤害50%生命值",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 0.8, True),
							EFFECT_LIFESTEAL:0.5
						}
					}
				]
			},
			{
				"name":"血腥爆破",
				"text":"对目标造成120(+0.8自身攻击力)的真实伤害,并提升自身25攻击力、回复所造成伤害30%生命值,且对自身造成60(+0.6攻击力)伤害",
				"tp_cost":25,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 25, 0, 0)],
						}
					},
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_HURT:(60, Attr.ATTACK, 0, 0.6, False),
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(120, Attr.ATTACK, 0, 0.8, True),
							EFFECT_LIFESTEAL:0.3
						}
					}
				]
			},
			{
				"name":"血腥之矛",
				"text":"对目标及其半径3范围内的所有玩家造成120(+0.5自身攻击力)的真实伤害,并回复所造成伤害25%生命值,且对自身造成45(+0.8攻击力)伤害",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_HURT:(45, Attr.ATTACK, 0, 0.8, False),
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(3, False),
							EFFECT_HURT:(120, Attr.ATTACK, 0, 0.5, True),
							EFFECT_LIFESTEAL:0.25
						}
					}
				]
			},
			{
				"name":"朱色之噬",
				"text":"对目标及其半径3范围内所有玩家造成120(+1.0自身攻击力)的真实伤害,并回复所造成伤害75%生命值",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(3, False),
							EFFECT_HURT:(120, Attr.ATTACK, 0, 1.0, True),
							EFFECT_LIFESTEAL:0.75,
						}
					}
				]
			}
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1040:{
		"name":"碧",
		"health":1000,
		"distance":15,
		"attack":100,
		"defensive":50,
		"crit":10,
		"tp":10,
		
		"active_skills":[
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"光合作用",
				"text":"自身每回合回复150生命值，持续3个玩家回合",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.TurnAttrHelUp, 150, 3)],
						}
					}
				],
			},
			{
				"name":"酸性藤曼",
				"text":"使目标每回合降低10防御力,持续4回合。并附加每回合减少60生命值的中毒效果，持续3个玩家回合",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.TurnAttrDefDown, -10, 4)],
							EFFECT_BUFF:[(BuffType.TurnAttrHelDown, -60, 3)],
						}
					}
				]
			},
			{
				"name":"剧毒绽放",
				"text":"无视距离，对目标及其半径4范围内的玩家造成130(+1.0自身攻击力)的伤害，并降低目标3点攻击距离。附加每回合减少100生命值的中毒效果，持续3个玩家回合",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(4, False),
							EFFECT_HURT:(130, Attr.ATTACK, 0, 1.0, False),
							EFFECT_BUFF:[(BuffType.TurnAttrHelDown, -100, 3)],
							EFFECT_ATTR_CHANGE:[(Attr.DISTANCE, -3, 0, 0)],
							EFFECT_IGNORE_DIST:0,
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1038:{
		"name":"栞",
		"health":875,
		"distance":12,
		"attack":80,
		"defensive":60,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+0.5自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 0.5, False)
						}
					}
				]
			},
			{
				"name":"风之箭",
				"text":"对目标造成80(+1.45自身攻击力)伤害,并自身回复40tp",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 40, 0, 0)]
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(80, Attr.ATTACK, 0, 1.45, False)
						}
					}
				]
			},
			{
				"name":"三重箭矢",
				"text":"对除自己外所有玩家造成70(+0.8自身攻击力)伤害,并自身回复50tp",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 50, 0, 0)]
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(70, Attr.ATTACK, 0, 0.8, False)
						}
					}
				]
			},
			{
				"name":"附魔之箭",
				"text":"对目标造成100(+1.5自身攻击力)伤害,并提升自身100攻击力和回复50tp，并将所造成伤害的20%转为生命值。",
				"tp_cost":100,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 50, 0, 0),
												(Attr.ATTACK, 100, 0, 0)]
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.5, False),
							EFFECT_LIFESTEAL:0.2,
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1036:{
		"name":"镜华",
		"health":800,
		"distance":15,
		"attack":150,
		"defensive":50,
		"crit":0,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"魔法增幅",
				"text":"自身增加50点攻击力, 且下次攻击增加70%暴击概率",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 50, 0, 0)],
							EFFECT_BUFF:[(BuffType.AttackAttrCritUp, 70, 1)],
						}
					}
				]
			},
			{
				"name":"冰枪术",
				"text":"对目标造成20(+1.1自身攻击力)伤害，暴击时伤害为原来的4倍",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.AttackAttrCritHurtUp, 2, 1)],
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(20, Attr.ATTACK, 0, 1.1, False)
						}
					}
				]
			},
			{
				"name":"宇宙苍蓝闪",
				"text":"无视距离，对目标造成50(+2.3自身攻击力)伤害，并将所造成伤害的20%转为生命值。",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 2.4, False),
							EFFECT_LIFESTEAL:0.2,
							EFFECT_IGNORE_DIST:0,
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1034:{
		"name":"优花梨",
		"health":1200,
		"distance":7,
		"attack":120,
		"defensive":100,
		"crit":5,
		"tp":20,

		"active_skills":[
			{
				"name":"滚动酒桶",
				"text":"对目标及其半径3范围内所有玩家造成100(+0.6自身攻击力)伤害",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 0.6, False),
							EFFECT_AOE:(3, False),
						}
					}
				]
			},
			{
				"name":"醉酒狂暴",
				"text":"下一次攻击增加50%暴击率和10%暴击伤害，并回复200生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.AttackAttrCritUp, 50, 1),
										 (BuffType.AttackAttrCritHurtUp, 0.1, 1)],
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 200, 0, 0)]
						}
					}
				]
			},
			{
				"name":"肉蛋葱鸡",
				"text":"跳到目标身边，对目标造成80(+0.8自身攻击力)真实伤害并击退1步",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(90, Attr.ATTACK, 0, 1, True),
							EFFECT_JUMP:1
						}
					}
				]
			},
			{
				"name":"爆破酒桶",
				"text":"对目标及其半径5范围内所有玩家造成150(+1.0自身攻击力)伤害，并击退5步",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(150, Attr.ATTACK, 0, 1, False),
							EFFECT_AOE:(5, False),
							EFFECT_HIT_BACK:5,
						},
					}
				]
			}
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1029:{
		"name":"望",
		"health":1200,
		"distance":7,
		"attack":100,
		"defensive":140,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.35自身攻击力)真实伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1.35, True)
						}
					}
				]
			},
			{
				"name":"悦音斩击",
				"text":"对目标造成30(+0.8自身攻击力)伤害并眩晕1个自我回合，且降低目标30攻击力持续1个自我回合",
				"tp_cost":35,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(30, Attr.ATTACK, 0, 0.8, False),
							EFFECT_BUFF:[(BuffType.NormalSelfAttrAtkDown, -30, 2)],
							EFFECT_DIZZINESS:1
						}
					}
				]
			},
			{
				"name":"偶像声援",
				"text":"全体玩家回复50(+0.5自身防御力)的生命值，自身额外回复50(+1.0自身防御力)的生命值",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 50, Attr.DEFENSIVE, 0.5)]
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 100, Attr.DEFENSIVE, 1.0)]
						},
					},
				]
			},
			{
				"name":"Live On Stage!",
				"text":"为自己增加一个1000生命值的护盾（只可触发1次）并提升70点防御力，赋予全体玩家50点攻击力，且下次攻击必爆并增加50%爆伤",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 1000, 1)],
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, 70, 0, 0)],
						}
					},
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 50, 0, 0)],
							EFFECT_BUFF:[
								(BuffType.AttackAttrCritUp, 100, 1),
								(BuffType.AttackAttrCritHurtUp, 0.5, 1)
							],
						}
					},
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1028:{
		"name":"咲恋",
		"health":1100,
		"distance":7,
		"attack":90,
		"defensive":70,
		"crit":10,
		"tp":0,
		
		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"优雅声援",
				"text":"自身恢复30TP，并提升50攻击力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.NOW_TP, 30, 0, 0),
								(Attr.ATTACK, 50, 0, 0)
							],
						}
					}
				]
			},
			{
				"name":"烈焰斩击",
				"text":"对目标及其半径2范围内的其他玩家造成80(+1.0自身攻击力)的伤害,自身每损失1%生命值额外造成3点伤害",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(2, False),
							EFFECT_HURT:(80, Attr.ATTACK, 0, 1.0, False),
							EFFECT_STAND:(1, 3),
						}
					}
				]
			},
			{
				"name":"凤凰之终结",
				"text":"对目标及其半径5范围内的玩家造成80(+1.1自身攻击力)的伤害,自身每损失1%生命值额外造成8点伤害，并将所造成伤害的20%转为生命值。",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(5, False),
							EFFECT_HURT:(80, Attr.ATTACK, 0, 1.1, False),
							EFFECT_STAND:(1, 8),
							EFFECT_LIFESTEAL:0.3,
						}
					}
				]
			},
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1022:{
		"name":"依里",
		"health":900,
		"distance":10,
		"attack":120,
		"defensive":90,
		"crit":5,
		"tp":0,


		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"极限充能",
				"text":"消耗自身150HP提高70攻击力，并自身回复30TP",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.ATTACK, 70, 0, 0),
								(Attr.NOW_TP, 30, 0, 0),
								(Attr.NOW_HEALTH, -150, 0, 0,)],
						}
					}
				]
			},
			{
				"name":"暗影吮吸",
				"text":"对目标及其半径3内的敌人造成60(+0.7自身攻击力)真实伤害，并将所造成伤害的30%转换为生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(60, Attr.ATTACK, 0, 0.7, True),
							EFFECT_AOE:(3, False),
							EFFECT_LIFESTEAL:0.30,
						}
					}
				]
			},
			{
				"name":"闪电之枪",
				"text":"对目标及其半径7范围内自己以外的玩家造成70(+2.0自身攻击力)真实伤害，并将所造成伤害的20%转换为生命值",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_AOE:(7, False),
							EFFECT_HURT:(70, Attr.ATTACK, 0, 2.0, True),
							EFFECT_LIFESTEAL:0.2,
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1020:{
		"name":"美美",
		"health":1000,
		"distance":5,
		"attack":110,
		"defensive":80,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"蹦蹦跳跳",
				"text":"自身增加40点攻击力和40点防御力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.ATTACK, 40, 0, 0),
								(Attr.DEFENSIVE, 40, 0, 0)],
						}
					}
				]
			},
			{
				"name":"崩山击",
				"text":"向目标移动3格，并对目标及其半径4范围内的所有玩家造成100(+1.5自身攻击力)伤害",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(3, False),
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.5, False),
							EFFECT_AOE:(4, False)
						}
					}
				]
			},
			{
				"name":"兰德索尔正义",
				"text":"对目标造成120(+0.5自身攻击力)点真实伤害，目标生命值每降低1%则额外造成7点真实伤害，并将所造成伤害的30%转为生命值。",#斩杀效果
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(120, Attr.ATTACK, 0, 0.5, True),
							EFFECT_ELIMINATE:(1, 7),
							EFFECT_LIFESTEAL:0.3,
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1017:{
		"name":"香织",
		"health":900,
		"distance":5,
		"attack":120,
		"defensive":60,
		"crit":15,
		"tp":0,

		"active_skills":[
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)的伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"正中突破",
				"text":"对目标造成120(+1.0自身攻击力)的伤害，并降低其25点防御力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(120, Attr.ATTACK, 0, 1.0, False),
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -25, 0, 0)],
						}
					}
				]
			},
			{
				"name":"精神统一",
				"text":"每自我回合永久提升自身40点攻击,持续3回合",
				"tp_cost":35,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.TurnSelfAttrAtkUp, 40, 3)],
						}
					}
				]
			},
			{
				"name":"琉球犬重拳出击",
				"text":"对目标造成200(+2.0自身攻击力)真实伤害，并将所造成伤害的30%转为生命值。使用后会降低自身250攻击力持续1个自我回合",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(200, Attr.ATTACK, 0, 2.0, True),
							EFFECT_LIFESTEAL:0.3,
						}
					},
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.NormalSelfAttrAtkDown, -250, 1)],
						},
					}
				]
			}
		],
		"passive_skills":[],
		"extra_skills" : [],
	},
	1016:{
		"name":"铃奈",
		"health":900,
		"distance":12,
		"attack":120,
		"defensive":50,
		"crit":15,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"魅力全开",
				"text":"每自我回合增加15%暴击率，持续全局",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.TurnSelfAttrCritUp, 15, 9999)],
						}
					}
				]
			},
			{
				"name":"会心飞镖",
				"text":"对目标造成3段伤害，每段60(+0.4自身攻击力)伤害",
				"tp_cost":25,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(60, Attr.ATTACK, 0, 0.4, False)
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(60, Attr.ATTACK, 0, 0.4, False)
						}
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(60, Attr.ATTACK, 0, 0.4, False)
						}
					}
				]
			},
			{
				"name":"一箭穿心",
				"text":"对目标造成200(+2.5自身攻击力)伤害，并将所造成伤害的30%转为生命值。",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(200, Attr.ATTACK, 0, 2.5, False),
							EFFECT_LIFESTEAL:0.3,
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1010:{
		"name":"真步",
		"health":1100,
		"distance":10,
		"attack":100,
		"defensive":50,
		"crit":30,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"真步真步治愈术",
				"text":"自身回复200生命值，并提升20攻击力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.NOW_HEALTH, 200, 0, 0),
								(Attr.ATTACK, 20, 0, 0),
							],
						}
					}
				]
			},
			{
				"name":"真步真步致盲术",
				"text":"对目标造成50(+1.0自身攻击力)伤害，并使其致盲，下次攻击不会造成伤害",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 1, False),
							EFFECT_BUFF:[(BuffType.Blind, 0, 1)],
						}
					}
				]
			},
			{
				"name":"童话王国",
				"text":"全体增加20攻击力和10TP，自身额外增加30攻击力并每回合额外回复10tp，持续4玩家回合",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.ATTACK, 20, 0, 0),
								(Attr.NOW_TP, 10, 0, 0),
							],
						}
					},
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 30, 0, 0),],
							EFFECT_BUFF:[(BuffType.TurnAttrTPUp, 10, 4)],
						},
					}
				]
			},
			{
				"name":"G36C扫射",
				"text":"掏出G36C，对所有人各造成3段伤害，每段75(+0.75自身攻击力)伤害",
				"tp_cost":100,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(75, Attr.ATTACK, 0, 0.75, False)
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(75, Attr.ATTACK, 0, 0.75, False)
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(75, Attr.ATTACK, 0, 0.75, False)
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1008:{
		"name":"雪",
		"health":800,
		"distance":10,
		"attack":110,
		"defensive":50,
		"crit":5,
		"tp":10,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身最大TP)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.MAX_TP, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"我那令人目眩的美貌♪",
				"text":"对目标造成50(+1.0自身攻击力)伤害，并使其致盲，下次攻击不会造成伤害",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(50, Attr.ATTACK, 0, 1, False),
							EFFECT_BUFF:[(BuffType.Blind, 0, 1)],
						}
					}
				]
			},
			{
				"name":"可爱的我会为你加油的♪",
				"text":"全体回复10TP，自身额外回复20%最大TP和20TP最大值",
				"tp_cost":30,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, 10, 0, 0)],
						}
					},
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.MAX_TP, 20, 0, 0),
								(Attr.NOW_TP, 0, Attr.MAX_TP, 0.2),
							],
						},
					}
				]
			},
			{
				"name":"拜倒在我的美貌之下吧！",
				"text":"自身增加30TP和50TP最大值，对自己外所有玩家造成100(+2.0自身当前TP)伤害，并降低10TP。所造成伤害的20%将转换为生命值",
				"tp_cost":100,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.MAX_TP, 50, 0, 0),
								(Attr.NOW_TP, 30, 0, 0),
							],
						},
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.NOW_TP, 0, 2.0, False),
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, -10, 0, 0)],
							EFFECT_LIFESTEAL:0.2,
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1007:{
		"name":"宫子",
		"health":1200,
		"distance":5,
		"attack":80,
		"defensive":200,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+0.25自身最大生命值)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.MAX_HEALTH, 0, 0.25, False)
						}
					}
				]
			},
			{
				"name":"我~好~恨~啊~",
				"text":"免疫下次受到的伤害，且降低自身5%最大生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Ghost, 9999, 1)],#其实就是一个超高生命值的护盾
							EFFECT_ATTR_CHANGE:[(Attr.MAX_HEALTH, -1, Attr.MAX_HEALTH, 0.05)],
						}
					}
				]
			},
			{
				"name":"点心时间到了~",
				"text":"回复50(+0.3已损失生命值)生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 50, Attr.COST_HEALTH, 0.3)],
						}
					}
				]
			},
			{
				"name":"把你变成布丁",
				"text":"对目标造成100(+0.8自身攻击力)点真实伤害，目标生命值每降低1%则额外造成5点真实伤害，且自身增加10%生命值上限",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger":TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.MAX_HEALTH, 0, Attr.MAX_HEALTH, 0.1)],
						},
					},
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 0.8, True),
							EFFECT_ELIMINATE:(1, 5)
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1006:{
		"name":"茜里",
		"health":1000,
		"distance":10,
		"attack":90,
		"defensive":80,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"小恶魔之吻",
				"text":"对目标造成100(+1.0自身攻击力)伤害，并将所造成伤害的50%转换为生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
							EFFECT_LIFESTEAL:0.5,
						}
					}
				]
			},
			{
				"name":"暗影打击",
				"text":"对目标造成100(+1.0自身攻击力)伤害，并降低目标40点护甲",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -40, 0, 0)],
						}
					}
				]
			},
			{
				"name":"甜蜜恶魔声援",
				"text":"降低除自己外所有人60点防御力，自身增加300点攻击力持续1回合，并继续下一回合",
				"tp_cost":50,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -60, 0, 0)],
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.NormalAttrAtkUp, 300, 1)],
							EFFECT_LOCKTURN:1,
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1005:{
		"name":"茉莉",
		"health":1100,
		"distance":5,
		"attack":90,
		"defensive":100,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"大杀四方",
				"text":"以自身为中心对半径5以内所有玩家造成150(+0.5自身攻击力)伤害，并将所造成伤害的75%转换为生命值",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_HURT:(150, Attr.ATTACK, 0, 0.5, False),
							EFFECT_LIFESTEAL:0.75,
							EFFECT_AOE:(5, False),
						}
					}
				]
			},
			{
				"name":"猛虎冲击",
				"text":"向目标移动3步，对其造成50(+1.0自身攻击力)伤害，并将其眩晕1回合",
				"tp_cost":35,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_MOVE_GOAL:(3, False),
							EFFECT_HURT:(50, Attr.ATTACK, 0, 1, False),
							EFFECT_DIZZINESS:1,
						}
					}
				]
			},
			{
				"name":"虎之英雄轰炸",
				"text":"跳到目标身边，以自身为中心对半径7以内所有玩家造成150(+1.5自身攻击力)真实伤害，并为自己增加一个200生命值的护盾（可触发1次）",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_JUMP:0,
							EFFECT_IGNORE_DIST:0,
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 200, 1)]
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_HURT:(150, Attr.ATTACK, 0, 1.5, True),
							EFFECT_AOE:(7, False)
						}
					}
				]
			},
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1004:{
		"name":"未奏希",
		"health":1200,
		"distance":10,
		"attack":100,
		"defensive":250,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":10,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"小炸弹",
				"text":"对目标及其半径4范围内的所有玩家造成100(+1.0自身攻击力)伤害（不包括自己）",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(100, Attr.ATTACK, 0, 1.0, False),
							EFFECT_AOE:(4, False)
						}
					}
				]
			},
			{
				"name":"中炸弹",
				"text":"对目标及其半径8范围内的所有玩家造成150(+1.5自身攻击力)伤害（包括自己）",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(150, Attr.ATTACK, 0, 1.5, False),
							EFFECT_AOE:(8, True)
						}
					}
				]
			},
			{
				"name":"大炸弹",
				"text":"对场上所有玩家造成200(+2.0自身攻击力)伤害（包括自己），并赋予自己外所有人每回合降低60生命值的灼烧状态，持续3玩家回合",
				"tp_cost":70,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_HURT:(200, Attr.ATTACK, 0, 2.0, False)
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.TurnAttrHelDown2, -60, 3)],
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1003:{
		"name":"怜",
		"health":900,
		"distance":5,
		"attack":100,
		"defensive":70,
		"crit":5,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)真实伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, True)
						}
					}
				]
			},
			{
				"name":"破甲突刺",
				"text":"无视距离，对离自己最近的目标造成50(+20%目标最大生命值)伤害，并降低目标50%防御力",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_NEAR,
						"effect":{
							EFFECT_HURT:(50, Attr.MAX_HEALTH, 1, 0.20, False),
							EFFECT_ATTR_CHANGE:[(Attr.DEFENSIVE, -1, Attr.DEFENSIVE, 0.5)],
						}
					}
				]
			},
			{
				"name":"极东骑术",
				"text":"为自己增加一个250的护盾（只可触发1次），并增加15%攻击力，且继续下一回合",
				"tp_cost":40,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[(BuffType.Shield, 250, 1)],
							EFFECT_ATTR_CHANGE:[(Attr.ATTACK, 0, Attr.ATTACK, 0.15)],
							EFFECT_LOCKTURN:1,
						}
					}
				]
			},
			{
				"name":"极光风暴",
				"text":"对自己以外的所有人造成135(+1.0自身攻击力)真实伤害，并展开攻击力上升、暴击率上升的领域4回合。",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_BUFF:[
								(BuffType.NormalAttrAtkUp, 100, 4),
								(BuffType.NormalAttrCritUp, 20, 4),
							],
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(135, Attr.ATTACK, 0, 1.0, True)
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1002:{
		"name":"优衣",
		"health":1000,
		"distance":8,
		"attack":80,
		"defensive":60,
		"crit":0,
		"tp":10,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"花瓣射击",
				"text":"对目标造成75(+1.6自身攻击力)伤害，并降低目标70点攻击力，持续3个自我回合，且降低其10点TP",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(75, Attr.ATTACK, 0, 1.6, False),
							EFFECT_BUFF:[(BuffType.NormalSelfAttrAtkDown, -70, 3)],
							EFFECT_ATTR_CHANGE:[(Attr.NOW_TP, -10, 0, 0)],
						}
					}
				]
			},
			{
				"name":"全体治愈",
				"text":"全体回复100生命值，自己额外回复300生命值，除自己外减少3点攻击距离",
				"tp_cost":60,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ALL,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 100, 0, 0)]
						}
					},
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.NOW_HEALTH, 300, 0, 0)]
						}
					},
					{
						"trigger": TRIGGER_ALL_EXCEPT_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[(Attr.DISTANCE, -3, 0, 0)],
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
	1001:{
		"name":"日和莉",
		"health":1000,
		"distance":5,
		"attack":100,
		"defensive":60,
		"crit":10,
		"tp":0,

		"active_skills" : [
			{
				"name":"普通攻击",
				"text":"对目标造成0(+1.0自身攻击力)伤害",
				"tp_cost":0,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 1, False)
						}
					}
				]
			},
			{
				"name":"勇气冲拳",
				"text":"无视距离，对离自己最近的目标造成0(+0.75自身攻击力伤害)，并将所造成伤害的30%转换为生命值，且增加自身50点攻击力和1点攻击距离",
				"tp_cost":20,

				"effect_trigger":[
					{
						"trigger": TRIGGER_ME,
						"effect":{
							EFFECT_ATTR_CHANGE:[
								(Attr.ATTACK, 50, 0, 0),
								(Attr.DISTANCE, 1, 0, 0)],
						}
					},
					{
						"trigger": TRIGGER_NEAR,
						"effect":{
							EFFECT_HURT:(0, Attr.ATTACK, 0, 0.75, False),
							EFFECT_LIFESTEAL:0.3,
						}
					}
				]
			},
			{
				"name":"日和莉烈焰冲击",
				"text":"对目标造成200(+2.5自身攻击力)伤害，并将造成伤害的30%转化为生命值。若目标被击倒，自身回复70点tp并继续下一回合",
				"tp_cost":100,

				"effect_trigger":[
					{
						"trigger": TRIGGER_SELECT_EXCEPT_ME,
						"effect":{
							EFFECT_HURT:(200, Attr.ATTACK, 0, 2.5, False),
							EFFECT_LIFESTEAL:0.3,
							EFFECT_OUT_TP:70,
							EFFECT_OUT_LOCKTURN:1
						}
					}
				]
			}
		],
		"passive_skills": [],
		"extra_skills" : [],
	},
}