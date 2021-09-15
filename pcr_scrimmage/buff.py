# buff会一直保存在玩家身上，达到触发条件时扣除触发次数，次数扣完后删除
# 保存在玩家身上的buff结构 (BuffType.xx, 数值, 可触发次数)

from enum import IntEnum
from .attr import Attr

#buff触发类型
class BuffTriggerType(IntEnum):
	Normal		= 1		#普通型buff，初始触发一次，结束后解除（造成的属性变化在解除后还原）
	Turn		= 2		#回合触发型buff，每回合都触发一次（造成的属性变化会永久保留）
	Hurt		= 3		#受伤时触发型buff，每次被主动攻击时触发一次（跑道事件或其他buff造成的伤害不会算入）
						#简单来说就是被 EFFECT_HURT 触发的

#buff效果类型
class BuffEffectType(IntEnum):
	Attr		= 1		#属性变化型buff，属性的升降
	Shield		= 2		#护盾，配合 BuffTriggerType.Hurt 使用，数值为护盾值

#buff类型
class BuffType(IntEnum):
	NormalAttrAtkUp		= 10101
	NormalAttrAtkDown	= 10102
	TurnAttrAtkUp		= 20101
	TurnAttrAtkDown		= 20102
	Shield				= 30201

Buff = {
	BuffType.NormalAttrAtkUp:{
		'name':'攻击增强',
		'text':'增加{0}点攻击力，持续{1}回合',
		'trigger_type':BuffTriggerType.Normal,
		'effect_type':BuffEffectType.Attr,
		'attr_type':Attr.ATTACK,
	},
	BuffType.NormalAttrAtkDown:{
		'name':'虚弱',
		'text':'降低{0}点攻击力，持续{1}回合',
		'trigger_type':BuffTriggerType.Normal,
		'effect_type':BuffEffectType.Attr,
		'attr_type':Attr.ATTACK,
	},
	BuffType.TurnAttrAtkUp:{
		'name':'攻击成长',
		'text':'每回合永久增加{0}点攻击力，持续{1}回合',
		'trigger_type':BuffTriggerType.Turn,
		'effect_type':BuffEffectType.Attr,
		'attr_type':Attr.ATTACK,
	},
	BuffType.TurnAttrAtkDown:{
		'name':'极度虚弱',
		'text':'每回合永久降低{0}点攻击力，持续{1}回合',
		'trigger_type':BuffTriggerType.Turn,
		'effect_type':BuffEffectType.Attr,
		'attr_type':Attr.ATTACK,
	},
	BuffType.Shield:{
		'name':'护盾',
		'text':'增加一个能承受{0}伤害的护盾，可触发{1}次',
		'trigger_type':BuffTriggerType.Hurt,
		'effect_type':BuffEffectType.Shield,
	},
}
