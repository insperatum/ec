from scipy.stats import geom
from collections import namedtuple

import random
import math
from string import ascii_letters, digits, punctuation, ascii_lowercase, ascii_uppercase, whitespace, printable


"""
This file contains the backend of the regex model. 
Was copied from Luke's textpatterns repo on April 12, 2018. 
For the actual regex tasks, try regexes.py
"""

PartialMatch = namedtuple("PartialMatch", ["numCharacters", "score", "reported_score", "continuation", "state"])

OPEN = "BRACKET_OPEN"
CLOSE = "BRACKET_CLOSE"

class regex(namedtuple("regex", ["type", "arg"])):
	def __new__(cls, arg):
		return super().__new__(cls, cls.__name__, arg)

	def __getnewargs__(self):
		return (self.arg,)

	def __repr__(self):
		return str("(" + type(self).__name__ + " " + repr(self.arg) + ")")

	def __str__(self):
		char_map = {
			dot: ".",
			d: "\\d",
			s: "\\s",
			w: "\\w",
			l: "\\l",
			u: "\\u",
			KleeneStar: "*",
			Plus: "+",
			Maybe: "?",
			Alt: "|",
			OPEN: "(",
			CLOSE: ")"
		}
		flat = flatten(self, char_map=char_map, escape_strings=True)
		return "".join([x if type(x) is str else repr(x) if issubclass(type(x), regex) else str(x) for x in flat])

	def flatten(self, char_map={}, escape_strings=False):
		return [char_map.get(type(self), self)]

	def sample(self, state=None):
		"""
		Returns a sample
		"""
		raise NotImplementedError()

	def consume(self, s, state=None):
		"""
		:param s str:
		Consume some of s
		Yield the score, the number of tokens consumed, the remainder of the regex, and the final state
		Returns generator(PartialMatch)
		"""
		raise NotImplementedError()

	def leafNodes(self):
		"""
		returns a list of leaves for this regex
		"""
		return []

	def match(self, string, state=None, mergeState=True, returnPartials=False):
		"""
		:param bool mergeState: if True, only retain the highest scoring state for each continuation 
		"""
		initialState = state
		partialsAt = [[] for i in range(len(string)+1)]
		finalMatches = [[] for i in range(len(string)+1)]
		partialsAt[0] = [(0, self, initialState, 0)]
		# partialsAt[num characters consumed] = [(score, continuation, state, reported_score), ...]
		
		def merge(partials):
			#partials: [(score, continuation, state), ...]
			best = {} # best: continuation -> (score, continuation, state, reported_score)
			for x in partials:
				key = x[1] if mergeState else x[1:]
				x_best = best.get(key, None)
				if x_best is None or x_best[0] < x[0]:
					best[key] = x
			return list(best.values())
		
		for i in range(len(string)+1):
			#Merge to find MAP
			partialsAt[i] = merge(partialsAt[i])
			#Match some characters
			remainder = string[i:]
			while partialsAt[i]:
				score, continuation, state, reported_score = partialsAt[i].pop()
				if continuation is None:
					finalMatches[i].append((score, continuation, state, reported_score))
					continue
				for remainderMatch in continuation.consume(remainder, state):
					j = i + remainderMatch.numCharacters
					if i==j and continuation == remainderMatch.continuation and state == remainderMatch.state:
						raise Exception()
					else:
						partialsAt[j].append((score + remainderMatch.score, remainderMatch.continuation, remainderMatch.state, reported_score + remainderMatch.reported_score))

		def getOutput(matches):
			matches = merge(matches)
			if matches:
				score, _, state, reported_score = matches[0]
			else:
				score, state, reported_score = float("-inf"), None, float("-inf")

			if initialState is None:
				return reported_score
			else:
				return reported_score, state

		if returnPartials:
			return [(numCharacters, getOutput(finalMatches[numCharacters])) for numCharacters in range(len(finalMatches)) if finalMatches[numCharacters]]
		else:
			return getOutput(finalMatches[-1])

class CharacterClass(regex):
	def __repr__(self):
		return "[" + self.arg + "]"

	def flatten(self, char_map={}, escape_strings=False):
		return [char_map.get(self, self)]

	def sample(self, state=None):
		return random.choice(self.arg)

	def consume(self, s, state=None):
		if len(s)>=1 and s[:1] in self.arg:
			score = -math.log(len(self.arg))
			yield PartialMatch(numCharacters=1, score=score, reported_score=score, continuation=None, state=state)

dot = CharacterClass(printable[:-4]) #Don't match newline characters
d = CharacterClass(digits)
s = CharacterClass(whitespace)
w = CharacterClass(ascii_letters + digits)
l = CharacterClass(ascii_lowercase)
u = CharacterClass(ascii_uppercase)

class String(regex):
	def flatten(self, char_map={}, escape_strings=False):
		if escape_strings:
			return list(self.arg.replace("\\", "\\\\").replace(".", "\\.").replace("+", "\\+").replace("*", "\\*").replace("?", "\\?").replace("|", "\\|").replace("(", "\\(").replace(")", "\\)"))
		else:
			return list(self.arg)
		
	def sample(self, state=None):
		return self.arg

	def consume(self, s, state=None):
		if s[:len(self.arg)]==self.arg:
			yield PartialMatch(numCharacters=len(self.arg), score=0, reported_score=0, continuation=None, state=state)

class Concat(regex):
	def __new__(cls, *args):
		return super().__new__(cls, args)

	def __getnewargs__(self):
		return self.arg

	def flatten(self, char_map={}, escape_strings=False):
		return sum([flatten(x, char_map, escape_strings) for x in self.arg], [])

	def sample(self, state=None):
		return "".join(value.sample(state) for value in self.arg)

	def leafNodes(self):
		return [x for child in self.arg for x in child.leafNodes()]

	def consume(self, s, state=None):
		for partialMatch in self.arg[0].consume(s, state):
			if partialMatch.continuation is None:
				continuation = None if len(self.arg)==1 else Concat(*self.arg[1:])
			else:
				continuation = partialMatch.continuation if len(self.arg)==0 else Concat(partialMatch.continuation, *self.arg[1:])
			yield partialMatch._replace(continuation=continuation)

class Alt(regex):
	def __new__(cls, *args):
		return super().__new__(cls, args)

	def __getnewargs__(self):
		return self.arg

	def flatten(self, char_map={}, escape_strings=False):
		def bracket(value):
			if (type(value) is String and len(value.arg)>1) or type(value) == Concat:
				return [char_map.get(OPEN, OPEN)] + flatten(value, char_map, escape_strings) + [char_map.get(CLOSE, CLOSE)]
			else:
				return flatten(value, char_map, escape_strings)
		
		out = []
		for i in range(len(self.arg)):
			if i>0: out.append(char_map.get(type(self), type(self)))
			out.extend(bracket(self.arg[i]))
		return out

	def sample(self, state=None):
		value = random.choice(self.arg)
		return value.sample(state)

	def leafNodes(self):
		return [x for child in self.arg for x in child.leafNodes()]

	def consume(self, s, state=None):
		for value in self.arg:
			for partialMatch in value.consume(s, state):
				extraScore = -math.log(len(self.arg))
				yield partialMatch._replace(score=partialMatch.score+extraScore, reported_score=partialMatch.reported_score+extraScore)

class NonEmpty(regex):
	"""
	(Used in KleeneStar.match)
	"""
	def consume(self, s, state=None):
		stack = [PartialMatch(numCharacters=0, score=0, reported_score=0, continuation=self.arg, state=state)]
		while stack:
			p = stack.pop()
			if p.continuation is not None:
				for p2 in p.continuation.consume(s[p.numCharacters:], p.state):
					partialMatch = p2._replace(score=p.score+p2.score, reported_score=p.reported_score+p2.reported_score)
					if partialMatch.numCharacters>0:
						yield partialMatch
					else:
						stack.append(partialMatch)

class KleeneStar(regex):
	def __new__(cls, arg, p=0.5):
		return super().__new__(cls, (p, arg))

	def __getnewargs__(self):
		return self.arg[1], self.arg[0]

	@property
	def p(self):
		return self.arg[0]

	@property
	def val(self):
		return self.arg[1]

	def __repr__(self):
		return str("(" + type(self).__name__ + " " + str(self.p) + " " + repr(self.val) + ")")

	def flatten(self, char_map={}, escape_strings=False):
		if type(self.val) in (Alt, Concat) or (type(self.val)==String and len(self.val.arg)>1):
			return [char_map.get(OPEN, OPEN)] + flatten(self.val, char_map, escape_strings) + [char_map.get(CLOSE, CLOSE), char_map.get(type(self), type(self))]
		else:
			return flatten(self.val, char_map, escape_strings) + [char_map.get(type(self), type(self))]
			
	def sample(self, state=None):
		n = geom.rvs(self.p, loc=-1)
		return "".join(self.val.sample(state) for i in range(n))

	def leafNodes(self):
		return self.val.leafNodes()

	def consume(self, s, state=None):
		yield PartialMatch(score=math.log(self.p), reported_score=math.log(self.p), numCharacters=0, continuation=None, state=state)
		for partialMatch in NonEmpty(self.val).consume(s, state):
			assert(partialMatch.numCharacters > 0)
			# Force matching to be nonempty, to avoid infinite recursion when matching fo?* -> foo
			# This is only valid for MAP. If we want to get the marginal, we should first calculate 
			# probability q=P(o?->\epsilon), then multiply all partialmatches by 1/[1-q(1-p))]. (TODO)

			if partialMatch.continuation is None:
				continuation = KleeneStar(self.val)
			else:
				continuation = Concat(partialMatch.continuation, KleeneStar(self.val))

			extraScore = math.log(1-self.p) 
			yield partialMatch._replace(score=partialMatch.score+extraScore, reported_score=partialMatch.reported_score+extraScore, continuation=continuation)


class Plus(regex):
	def __new__(cls, arg, p=0.5):
		return super().__new__(cls, (p, arg))

	def __getnewargs__(self):
		return self.arg[1], self.arg[0]

	@property
	def p(self):
		return self.arg[0]

	@property
	def val(self):
		return self.arg[1]

	def __repr__(self):
		return str("(" + type(self).__name__ + " " + str(self.p) + " " + repr(self.val) + ")")

	def flatten(self, char_map={}, escape_strings=False):
		if type(self.val) in (Alt, Concat) or (type(self.val)==String and len(self.val.arg)>1):
			return [char_map.get(OPEN, OPEN)] + flatten(self.val, char_map, escape_strings) + [char_map.get(CLOSE, CLOSE), char_map.get(type(self), type(self))]
		else:
			return flatten(self.val, char_map, escape_strings) + [char_map.get(type(self), type(self))]

	def sample(self, state=None):
		n = geom.rvs(self.p, loc=0)
		return "".join(self.val.sample(state) for i in range(n))	

	def leafNodes(self):
		return self.val.leafNodes()

	def consume(self, s, state=None):
		for partialMatch in self.val.consume(s, state):
			if partialMatch.continuation is None:
				continuation = KleeneStar(self.val)
			else:
				continuation = Concat(partialMatch.continuation, KleeneStar(self.val))

			yield partialMatch._replace(continuation=continuation)	


class Maybe(regex):
	def __new__(cls, arg, p=0.5):
		return super().__new__(cls, (p, arg))

	def __getnewargs__(self):
		return self.arg[1], self.arg[0]

	@property
	def p(self):
		return self.arg[0]

	@property
	def val(self):
		return self.arg[1]

	def __repr__(self):
		return str("(" + type(self).__name__ + " " + str(self.p) + " " + repr(self.val) + ")")

	def flatten(self, char_map={}, escape_strings=False):
		if type(self.val) in (Alt, Concat) or (type(self.val)==String and len(self.val.arg)>1):
			return [char_map.get(OPEN, OPEN)] + flatten(self.val, char_map, escape_strings) + [char_map.get(CLOSE, CLOSE), char_map.get(type(self), type(self))]
		else:
			return flatten(self.val, char_map, escape_strings) + [char_map.get(type(self), type(self))]

	def sample(self, state=None):
		if random.random() < self.p:
			return self.val.sample(state)
		else:
			return ""

	def leafNodes(self):
		return self.val.leafNodes()

	def consume(self, s, state=None):
		yield PartialMatch(score=math.log(1-self.p), reported_score=math.log(1-self.p), numCharacters=0, continuation=None, state=state)
		for partialMatch in self.val.consume(s, state):
			extraScore = math.log(self.p)
			yield partialMatch._replace(score=partialMatch.score+extraScore, reported_score=partialMatch.reported_score+extraScore)


# ------------------------------------

def flatten(obj, char_map, escape_strings):
	if issubclass(type(obj), regex):
		return obj.flatten(char_map, escape_strings)
	else:
		return [obj]

# ------------------------------------

class ParseException(Exception):
	pass

def create(seq, lookup=None):
	"""
	Seq is a string or a list
	"""
	def head(x):
		if type(seq) is str:
			return {"*":KleeneStar, "+":Plus, "?":Maybe, "|":Alt, "(":OPEN, ")":CLOSE}.get(x[0], x[0])
		elif type(seq) is list:
			return x[0]

	def precedence(x):
		return {KleeneStar:2, Plus:2, Maybe:2, Alt:1, OPEN:0, CLOSE:-1}.get(x, 0)

	def parseToken(seq):
		if len(seq) == 0: raise ParseException()

		if lookup is not None and seq[0] in lookup:
			return lookup[seq[0]], seq[1:]

		elif issubclass(type(seq[0]), regex):
			return seq[0], seq[1:]

		elif type(seq) is str and (seq[:2] in ("\\*", "\\+", "\\?", "\\|", "\\(", "\\)", "\\.", "\\\\", "\\d", "\\s", "\\w", "\\l", "\\u") or seq[:1] == "."):
			if   seq[:2] == "\\*": return String("*"), seq[2:]
			elif seq[:2] == "\\+": return String("+"), seq[2:]
			elif seq[:2] == "\\?": return String("?"), seq[2:]
			elif seq[:2] == "\\|": return String("|"), seq[2:]
			elif seq[:2] == "\\(": return String("("), seq[2:]
			elif seq[:2] == "\\)": return String(")"), seq[2:]
			elif seq[:2] == "\\.": return String("."), seq[2:]
			elif seq[:2] == "\\\\": return String("\\"), seq[2:]

			elif seq[:2] == "\\d": return d, seq[2:]
			elif seq[:2] == "\\s": return s, seq[2:]
			elif seq[:2] == "\\w": return w, seq[2:]
			elif seq[:2] == "\\l": return l, seq[2:]
			elif seq[:2] == "\\u": return u, seq[2:]
			elif seq[:1] == ".":  return dot, seq[1:]

		elif head(seq) == OPEN:
				if len(seq)<=1: raise ParseException() #Lookahead
				inner_lhs, inner_remainder = parseToken(seq[1:])
				rhs, seq = parse(inner_lhs, inner_remainder, -1, True)
				return rhs, seq[1:]

		elif type(seq[0]) is str and seq[0] in printable:
			return String(seq[0]), seq[1:]

		else:
			raise ParseException()

	def parse(lhs, remainder, min_precedence=0, inside_brackets=False):
		if not remainder:
			if inside_brackets: raise ParseException()
			return lhs, remainder

		else:
			if precedence(head(remainder)) < min_precedence:
				return lhs, remainder
			
			elif head(remainder) == CLOSE:
				if not inside_brackets: raise ParseException()
				return lhs, remainder

			elif head(remainder) not in (KleeneStar, Plus, Maybe, Alt): #Atom
				rhs, remainder = parseToken(remainder)

				while remainder and head(remainder) != CLOSE:
					rhs, remainder = parse(rhs, remainder, 0, inside_brackets)

				if type(lhs) is String and type(rhs) is String:
					return String(lhs.arg + rhs.arg), remainder
				elif type(lhs) is String and type(rhs) is Concat and type(rhs.arg[0]) is String:
					return Concat(String(lhs.arg + rhs.arg[0].arg), *rhs.arg[1:]), remainder
				elif type(rhs) is Concat:
					return Concat(lhs, *rhs.arg), remainder
				else:
					return Concat(lhs, rhs), remainder

			else:
				op, remainder = head(remainder), remainder[1:]
				if op in (KleeneStar, Plus, Maybe): 
					#Don't need to look right
					lhs = op(lhs)
					return parse(lhs, remainder, min_precedence, inside_brackets)
				elif op == Alt:
					#Need to look right
					rhs, remainder = parseToken(remainder)

					while remainder and precedence(head(remainder)) >= precedence(op):
						rhs, remainder = parse(rhs, remainder, precedence(op), inside_brackets)

					if type(rhs) is Alt:
						lhs = Alt(lhs, *rhs.arg)
					else:
						lhs = Alt(lhs, rhs)
					return parse(lhs, remainder, min_precedence, inside_brackets)

	lhs, remainder = parseToken(seq)
	return parse(lhs, remainder)[0]






# ------------------------------------------------------------------------------------------------
class Wrapper(regex):
	"""
	:param state->value arg.sample: 
	:param string,state->score,state arg.match:
	"""
	def __repr__(self):
		return "(" + type(self.arg).__name__ + ")"

	def sample(self, state=None):
		return self.arg.sample(state)

	def consume(self, s, state=None):
		for i in range(len(s)+1):
			matchScore, newState = self.arg.match(s[:i], state)
			if matchScore > float("-inf"):
				yield PartialMatch(numCharacters=i, score=matchScore, reported_score=matchScore, continuation=None, state=newState)









# ------------ Unit tests ------------

if __name__=="__main__":


	assert(create("f(a|o)*") == Concat(String("f"), KleeneStar(Alt(String("a"), String("o")))))
	assert(create("fa|o*") == Concat(String("f"), Alt(String("a"), KleeneStar(String("o")))))
	assert(create("(f.*)+") == Plus(Concat(String("f"), KleeneStar(dot))))

	test_cases = [
		("foo", "fo", False),
		("foo", "foo", True),
		("foo", "fooo", False),
		("foo", "fo*", True),
		("foo", "fo+", True),
		("foo", "f(oo)*", True),
		("foo", "f(a|b)*", False),
		("foo", "f(a|o)*", True),
		("foo", "fa|o*", True),
		("foo", "fo|a*", False),
		("foo", "f|ao|ao|a", True),
		("f"+"o"*50, "f"+"o*"*10, True),
		("foo", "fo?+", True),
		("foo", "fo**", True),
		("(foo)", "\\(foo\\)", True),
		("foo foo. foo foo foo.", "foo(\\.? foo)*\\.", True),
		("123abcABC ", ".+", True),
		("123abcABC ", '\\w+', False),
		("123abcABC ", "\\w+\\s", True),
		("123abcABC ", "\\d+\\l+\\u+\\s", True)
	]
	for (string, regex, matches) in test_cases:
		print("Parsing", regex)
		r = create(regex)
		print("Matching", string, r)
		assert(matches == (r.match(string)>float("-inf")))


	class Foobar():
		def sample(self, state=None):
			if random.random() > 0.5:
				return "foo"
			else:
				return "bar"

		def match(self, string, state):
			if string=="foo" or string=="bar":
				return math.log(1/2), state + 1
			else:
				return float("-inf"), None
	foobar = Wrapper(Foobar())

	class Empty():
		def sample(self, state=None):
			return ""

		def match(self, string, state):
			if string=="":
				return 0, state
			else:
				return float("-inf"), None
	empty = Wrapper(Empty())

	string = "foobar"

	regex = create("%%%", {"%":foobar, "&":empty})
	print("Testing", string, regex)
	score, state = regex.match("foobar", state=0)
	assert(score == float("-inf"))

	regex = create("%%", {"%":foobar, "&":empty})
	print("Testing", string, regex)
	score, state = regex.match("foobar", state=0)
	assert(score == 2 * math.log(1/2))
	assert(state == 2)

	regex = create("%*", {"%":foobar, "&":empty})
	print("Testing", string, regex)
	score, state = regex.match("foobar", state=0)
	assert(score > float("-inf"))
	assert(state == 2)

	regex = create("foo%", {"%":foobar, "&":empty})
	print("Testing", string, regex)
	score, state = regex.match("foobar", state=0)
	assert(score > float("-inf"))
	assert(state == 1)

	regex = create("%*&", {"%":foobar, "&":empty})
	print("Testing", string, regex)
	score, state = regex.match("foobar", state=0)
	assert(score > float("-inf"))

	#Test save/load:
	import pickle
	import os
	r = create("\\d*|foo?|.+")
	with open('regex_Test.p', 'wb') as file:
		pickle.dump(r, file)
	with open('regex_Test.p', 'rb') as file:
		print(r)
		assert(r == pickle.load(file))
	os.remove("regex_Test.p")