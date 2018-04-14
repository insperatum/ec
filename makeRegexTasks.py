from type import tpregex
from task import Task


taskfile = './data_filtered.pt'
task_list = pickle.load(open(taskfile, 'rb'))

#make list shorter for now
task_list = task_list[0:51]


def makeRegexTasks():
	#a series of tasks

	#if I were to just dump all of them:
	regextasks = [ 
		Task("Luke data column no." + str(i), 
			tpregex, 
			[example for example in task[i]]
			) for i in range(task_list)
	]


"""
    regextasks = [
        Task("length bool", arrow(none,tstr),
             [((l,), len(l))
              for _ in range(10)
              for l in [[flip() for _ in range(randint(0,10)) ]] ]),
        Task("length int", arrow(none,tstr),
             [((l,), len(l))
              for _ in range(10)
              for l in [randomList()] ]),
    ]
"""


    return regextasks #some list of tasks 