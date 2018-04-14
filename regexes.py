#analog of list.py for regex tasks. Responsible for actually running the task.

from ec import explorationCompression, commandlineArguments, Task
from grammar import Grammar
from utilities import eprint, testTrainSplit, numberOfCPUs
from makeRegexTasks import makeTasks, delimiters
from regexPrimitives import basePrimitives, altPrimitives
#from program import *
from recognition import HandCodedFeatureExtractor, MLPFeatureExtractor, RecurrentFeatureExtractor, JSONFeatureExtractor

#class MyJSONFeatureExtractor(JSONFeatureExtactor):
	#TODO
#	def _featuresOfProgram(self, program, tp):
		#TODO

def regex_options(parser):
	parser.add_argument("--maxTasks", type=int,
		default=1000,
		help="truncate tasks to fit within this boundary")
	parser.add_argument("--primitives",
						default="base",
						help="Which primitive set to use",
						choices=["base","alt1"])
	parser.add_argument("--extractor", type=str,
		choices=["hand", "deep", "learned", "json"],
		default="json") #if i switch to json it breaks
	parser.add_argument("--split", metavar="TRAIN_RATIO",
		type=float,
		default=0.2,
		help="split test/train")
	parser.add_argument("-H", "--hidden", type=int,
		default=16,
		help="number of hidden units")
	parser.add_argument("--likelihoodModel", 
						default="probabilistic",
						help="likelihood Model",
						choices=["probabilistic", "all-or-nothing"])


#Lucas recommends putting a struct with the definitions of the primitives here.
#TODO:
#Build likelihood funciton
#modify NN
#make primitives 
#make tasks

if __name__ == "__main__":
	args = commandlineArguments(
        frontierSize=None, activation='sigmoid', iterations=10,
        a=3, maximumFrontier=10, topK=2, pseudoCounts=10.0,
        helmholtzRatio=0.5, structurePenalty=1.,
        CPUs=numberOfCPUs(),
        extras=regex_options)

	tasks = makeTasks() #TODO
	eprint("Generated", len(tasks),"tasks")

	maxTasks = args.pop("maxTasks")
	if len(tasks) > maxTasks:
		eprint("Unwilling to handle {} tasks, truncating..".format(len(tasks)))
		random.seed(42)
		random.shuffle(tasks)
		del tasks[maxTasks:]

	split = args.pop("split")
	test, train = testTrainSplit(tasks, split)
	eprint("Split tasks into %d/%d test/train"%(len(test),len(train)))



    #from list stuff 
	prims = {"base": basePrimitives,
             "alt1": altPrimitives}[args.pop("primitives")]
    
	extractor = {
		"hand": FeatureExtractor,
		"deep": DeepFeatureExtractor,
		"learned": LearnedFeatureExtractor,
		"json": MyJSONFeatureExtractor
	}[args.pop("extractor")]

	extractor.H = args.pop("hidden")
	extractor.USE_CUDA = args["cuda"]

	args.update({
		"featureExtractor": extractor,
		"outputPrefix": "experimentOutputs/regex",
		"evaluationTimeout": 0.0005,
		"topK": 5,
		"maximumFrontier": 5,
		"solver": "python",
		"compressor": "rust"
	})
    ####


	baseGrammar = Grammar.uniform(prims())

	explorationCompression(baseGrammar, train,
							testingTasks = test,
							**args)




