#属性枚举
from enum import IntEnum
class Attr(IntEnum):
	ATTACK 			= 1	#攻击力
	DEFENSIVE 		= 2	#防御力
	MAX_HEALTH		= 3	#最大生命值
	NOW_HEALTH		= 4	#当前生命值
	DISTANCE		= 5	#攻击距离
	NOW_TP			= 6	#当前tp
	MAX_TP			= 7 #最大tp
	CRIT			= 8	#暴击
	CRIT_HURT		= 9	#暴击伤害

def AttrTextChange(attr_type):
	if attr_type == Attr.ATTACK:
		return "攻击力"
	elif attr_type == Attr.DEFENSIVE:
		return "防御力"
	elif attr_type == Attr.MAX_HEALTH:
		return "最大生命值"
	elif attr_type == Attr.NOW_HEALTH:
		return "生命值"
	elif attr_type == Attr.DISTANCE:
		return "攻击距离"
	elif attr_type == Attr.NOW_TP:
		return "TP"
	elif attr_type == Attr.MAX_TP:
		return "最大TP"
	elif attr_type == Attr.CRIT:
		return "暴击"
	elif attr_type == Attr.CRIT_HURT:
		return "暴击伤害"
