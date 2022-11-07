#No import statements.
PROPOSITIONAL_VARIABLES = {"p", "q", "r", "s"}
FIRST_ORDER_VARIABLES = {"x", "y", "z", "w"}
PREDICATE_SYMBOLS = {"P", "Q", "R", "S"}

class ParseError(Exception):
    pass

class ParseTree: # abstract class
    
    def __init__(self):
        self.is_first_order = None

class Negation(ParseTree):

    def __init__(self, child: ParseTree):
        super().__init__()
        self.child = child
    
    def __str__(self) -> str:
        return f"-{str(self.child)}"

    def parse_output(self) -> int:
        return 2 if self.is_first_order else 7

class Quantifier(ParseTree): # abstract class

    @staticmethod
    def make(symbol, variable: str, child: ParseTree):
        if symbol == "A":
            return UniversalQuantifier(variable, child)
        if symbol == "E":
            return ExistentialQuantifier(variable, child)

    def __init__(self, variable: str, child: ParseTree):
        super().__init__()
        self.variable = variable
        self.child = child
        self.symbol = None
    
    def __str__(self) -> str:
        return f"{self.symbol}{self.variable}{str(self.child)}"

class UniversalQuantifier(Quantifier):

    def __init__(self, variable: str, child: ParseTree):
        super().__init__(variable, child)
        self.symbol = "A"
    
    def parse_output(self) -> int:
        return 3
    
class ExistentialQuantifier(Quantifier):

    def __init__(self, variable: str, child: ParseTree):
        super().__init__(variable, child)
        self.symbol = "E"

    def parse_output(self) -> int:
        return 4

class BinaryConnective(ParseTree): # abstract class

    @staticmethod
    def make(left: ParseTree, right: ParseTree, symbol: str) -> ParseTree:
        if symbol == "^":
            return Conjunction(left, right)
        elif symbol == "v":
            return Disjunction(left, right)
        elif symbol == ">":
            return Implication(left, right)
        raise ParseError("Expected binary connective. Got \'", symbol, "\' instead")

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__()
        self.right = right
        self.left = left
        self.con = None
    
    def __str__(self) -> str:
        return f"({str(self.left)}{self.con}{str(self.right)})"
    
    def parse_output(self) -> int:
        return 5 if self.is_first_order else 8

class Conjunction(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = "^"

class Disjunction(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = "v"

class Implication(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = ">"

class Variable(ParseTree):

    def __init__(self, variable: str):
        super().__init__()
        if variable not in PROPOSITIONAL_VARIABLES.union(FIRST_ORDER_VARIABLES):
            raise ParseError("Invalid variable name")
        self.variable = variable
    
    def __str__(self) -> str:
        return str(self.variable)
    
    def parse_output(self) -> int:
        return 6

class Predicate(ParseTree):

    def __init__(self, symbol: str, left: Variable, right: Variable):
        super().__init__()
        if symbol not in PREDICATE_SYMBOLS:
            raise ParseError("Expected predicate symbol. Got \'", symbol, "\' instead")
        self.symbol = symbol
        self.left = left
        self.right = right
    
    def __str__(self) -> str:
        return f"{self.symbol}({str(self.left)},{self.right})"

    def parse_output(self) -> int:
        return 1

class NotAFormula(ParseTree):
    
    def parse_output(self) -> int:
        return 0

class Parser: # abstract class

    @staticmethod
    def lexer(s):
        for c in s:
            yield c
        while True:
            yield '\0'

    def __init__(self, s: str):
        self.lex = self.lexer(s)
        self.current = next(self.lex)
    
    def parse(self):
        try:
            return self.FMLA()
        except ParseError:
            return NotAFormula()
    
    def expect(self, c):
        op = (lambda lhs, rhs: lhs in rhs) if hasattr(c, '__iter__') else (lambda lhs, rhs: lhs == rhs)
        if op(self.current, c):
            self.current = next(self.lex)
            return True
        raise ParseError("Unexpected character", self.current, "expected", c)
    
    def FMLA(self) -> ParseTree:
        raise NotImplementedError

    def NEG(self):
        if self.expect("-"):
            return Negation(self.FMLA())

    def BIN(self):
        self.expect("(")
        left = self.FMLA()
        symbol = self.current
        self.expect({"^", "v", ">"})
        right = self.FMLA()
        self.expect(")")
        return BinaryConnective.make(left, right, symbol)

class PropositionalParser(Parser):

    def __init__(self, s: str):
        super().__init__(s)
    
    def parse(self) -> ParseTree:
        tree = super().parse()
        tree.is_first_order = False
        return tree
    
    def FMLA(self):
        if self.current in PROPOSITIONAL_VARIABLES:
            return self.PROP()
        elif self.current == "-":
            return self.NEG()
        elif self.current == "(":
            return self.BIN()
        raise ParseError("Not a formula")
    
    def PROP(self):
        var = self.current
        if self.expect(PROPOSITIONAL_VARIABLES):
            return Variable(var)

class FirstOrderParser(Parser):
    def __init__(self, s: str):
        super().__init__(s)
    
    def parse(self) -> ParseTree:
        tree = super().parse()
        tree.is_first_order = True
        return tree

    def FMLA(self):
        if self.current in PREDICATE_SYMBOLS:
            return self.PRED()
        elif self.current == "-":
            return self.NEG()
        elif self.current in {"E", "A"}:
            return self.QUANT()
        elif self.current == "(":
            return self.BIN()
        raise ParseError("Not a formula")
    
    def VAR(self):
        var = self.current
        if self.expect(FIRST_ORDER_VARIABLES):
            return Variable(var)
    
    def PRED(self):
        symbol = self.current
        self.expect(PREDICATE_SYMBOLS)
        self.expect("(")
        left = self.VAR()
        self.expect(",")
        right = self.VAR()
        self.expect(")")
        return Predicate(symbol, left, right)
    
    def QUANT(self):
        symbol = self.current
        self.expect({"E", "A"})
        variable = self.VAR()
        fmla = self.FMLA()
        return Quantifier.make(symbol, variable, fmla)

cache = {}
def generate_parse_tree(fmla) -> ParseTree:
    if fmla in cache: return cache[fmla]
    fmla_tokens = set(fmla)
    if len(PROPOSITIONAL_VARIABLES.intersection(fmla_tokens)):
        res = PropositionalParser(fmla).parse()
    elif len(FIRST_ORDER_VARIABLES.intersection(fmla_tokens)):
        res = FirstOrderParser(fmla).parse()
    cache[fmla] = res
    return res

'''
SKELETON CODE BELOW
'''
MAX_CONSTANTS = 10

# Parse a formula, consult parseOutputs for return values.
def parse(fmla):
    tree = generate_parse_tree(fmla)
    return tree.parse_output()

# Return the LHS of a binary connective formula
def lhs(fmla):
    tree = generate_parse_tree(fmla)
    return str(tree.left)

# Return the connective symbol of a binary connective formula
def con(fmla):
    tree = generate_parse_tree(fmla)
    return tree.con

# Return the RHS symbol of a binary connective formula
def rhs(fmla):
    tree = generate_parse_tree(fmla)
    return str(tree.right)


# You may choose to represent a theory as a set or a list
def theory(fmla):#initialise a theory with a single formula in it
    return {fmla}

#check for satisfiability
def sat(tableau):
#output 0 if not satisfiable, output 1 if satisfiable, output 2 if number of constants exceeds MAX_CONSTANTS
    return 0

#DO NOT MODIFY THE CODE BELOW
f = open('input.txt')

parseOutputs = ['not a formula',
                'an atom',
                'a negation of a first order logic formula',
                'a universally quantified formula',
                'an existentially quantified formula',
                'a binary connective first order formula',
                'a proposition',
                'a negation of a propositional formula',
                'a binary connective propositional formula']

satOutput = ['is not satisfiable', 'is satisfiable', 'may or may not be satisfiable']



firstline = f.readline()

PARSE = False
if 'PARSE' in firstline:
    PARSE = True

SAT = False
if 'SAT' in firstline:
    SAT = True

for line in f:
    if line[-1] == '\n':
        line = line[:-1]
    parsed = parse(line)

    if PARSE:
        output = "%s is %s." % (line, parseOutputs[parsed])
        if parsed in [5,8]:
            output += " Its left hand side is %s, its connective is %s, and its right hand side is %s." % (lhs(line), con(line) ,rhs(line))
        print(output)

    if SAT:
        if parsed:
            tableau = [theory(line)]
            print('%s %s.' % (line, satOutput[sat(tableau)]))
        else:
            print('%s is not a formula.' % line)
