##跑道上的事件

'''
	事件可继续添加，增加后在 caseTrigger() 里做处理

	text	触发后的显示
	name	在跑道上的显示
	color	在跑道上显示的颜色
	range	触发后在这个范围随机一个数值
'''


#事件编号 编号顺序和RUNWAY_CASE对应
CASE_NONE = 0
CASE_HEALTH = 1		#生命值事件
CASE_DEFENSIVE = 2	#防御力事件
CASE_ATTACK = 3		#攻击力事件
CASE_TP = 4			#tp值事件
CASE_MOVE = 5		#移动位置事件

RUNWAY_CASE = [
	{
		"text":"",#占个空位，代表不触发事件
		"name":"",
		"color":(0,0,0),
		"range":(0,0)
	},
	{
		"text":"{0}了{1}点生命值",
		"name":"生",
		"color":(30,230,100),
		"range":(-100,100)
	},
	{
		"text":"{0}了{1}点防御力",
		"name":"防",
		"color":(225,195,0),
		"range":(-30,50)
	},
	{
		"text":"{0}了{1}点攻击力",
		"name":"攻",
		"color":(255,0,0),
		"range":(-50,50)
	},
	{
		"text":"{0}了{1}点TP值",
		"color":(30,144,255),
		"name":"tp",
		"range":(-30,30)
	},
	{
		"text":"向{0}移动了{1}步",
		"name":"移",
		"color":(100,100,100),
		"range":(-10,10)
	}
]