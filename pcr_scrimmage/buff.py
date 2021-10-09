# buff会一直保存在玩家身上，达到触发条件时扣除触发次数，次数扣完后删除
# buff结构 (BuffType.xx, 数值, 可触发次数)

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
# 数字第1位是BuffTriggerType，第3位是BuffEffectType，最后两位在1 3位相同时递增
# （其实遵不遵守这个规矩都可以，保证不会重复就行了）
# （不过也不排除以后会根据这个规则做判断 _(:з)∠)_ ）
class BuffType(IntEnum):
	NormalAttrAtkUp		= 10101
	NormalAttrAtkDown	= 10102
	NormalAttrDefUp		= 10103

	TurnAttrAtkUp		= 20101
	TurnAttrAtkDown		= 20102
	TurnAttrHelDown		= 20103

	Shield				= 30201

Buff = {
	BuffType.NormalAttrAtkUp:{
		'name':'强化',
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
	BuffType.NormalAttrDefUp:{
		'name':'守护',
		'text':'增加{0}点防御力，持续{1}回合',
		'trigger_type':BuffTriggerType.Normal,
		'effect_type':BuffEffectType.Attr,

		'attr_type':Attr.DEFENSIVE,
	},

	BuffType.TurnAttrAtkUp:{
		'name':'越战越勇',
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
	BuffType.TurnAttrHelDown:{
		'name':'中毒',
		'text':'每回合降低{0}点生命值，持续{1}回合',
		'trigger_type':BuffTriggerType.Turn,
		'effect_type':BuffEffectType.Attr,
		'attr_type':Attr.NOW_HEALTH,
	},

	BuffType.Shield:{
		'name':'护盾',
		'text':'增加一个能承受{0}伤害的护盾，可触发{1}次',
		'trigger_type':BuffTriggerType.Hurt,
		'effect_type':BuffEffectType.Shield,
	},
}
