#analog of list.py for regex tasks. Responsible for actually running the task.

from ec import explorationCompression, commandlineArguments, Task
from grammar import Grammar
from utilities import eprint, testTrainSplit, numberOfCPUs
from makeRegexTasks import makeTasks, delimiters
from textPrimitives import primitives
from program import *
from recognition import *

class MyJSONFeatureExtractor(JSONFeatureExtactor):
	#TODO
	def _featuresOfProgram(self, program, tp):
		#TODO


if __name__ == "__main__":
	tasks = makeTasks() #TODO




