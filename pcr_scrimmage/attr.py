#属性枚举
from enum import IntEnum
class Attr(IntEnum):
	ATTACK 			= 1	#攻击力
	DEFENSIVE 		= 2	#防御力
	MAX_HEALTH		= 3	#最大生命值
	NOW_HEALTH		= 4	#当前生命值
	DISTANCE		= 5	#攻击距离
	TP				= 6	#tp

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
	elif attr_type == Attr.TP:
		return "tp值"
