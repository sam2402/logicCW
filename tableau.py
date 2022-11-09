#No import statements.
PROPOSITIONAL_VARIABLES = {"p", "q", "r", "s"}
FIRST_ORDER_VARIABLES = {"x", "y", "z", "w"}
PREDICATE_SYMBOLS = {"P", "Q", "R", "S"}

GENERATED_VARIABLES = set()

def get_new_variable():
    new_var = f"var{len(GENERATED_VARIABLES)}"
    GENERATED_VARIABLES.add(new_var)
    return new_var

class ParseError(Exception):
    pass

class ParseTree: # abstract class

    def __init__(self):
        self.is_first_order = None
    
    def replace_variable(self, old_var: str, new_var: str):
        raise NotImplementedError

class Variable(ParseTree):

    def __init__(self, variable: str):
        super().__init__()
        # if variable not in PROPOSITIONAL_VARIABLES.union(FIRST_ORDER_VARIABLES):
        #     raise ParseError("Invalid variable name")
        self.variable = variable
    
    def __str__(self) -> str:
        return str(self.variable)
    
    def parse_output(self) -> int:
        return 6
    
    def is_literal(self):
        return True
    
    def literal(self):
        return Literal(self, True)
    
    def replace_variable(self, old_var: str, new_var: str):
        return Variable(new_var) if self.variable == old_var else Variable(self.variable)
    

class Negation(ParseTree):

    def __init__(self, child: ParseTree):
        super().__init__()
        self.child = child
    
    def __str__(self) -> str:
        return f"-{str(self.child)}"

    def parse_output(self) -> int:
        return 2 if self.is_first_order else 7
    
    def is_literal(self):
        return type(self.child) in {Variable, Predicate}
    
    def literal(self):
        if not self.is_literal: raise TypeError(f"{str(self)} is not a literal")
        return Literal(self.child, False)
    
    def replace_variable(self, old_var: str, new_var: str):
        return Negation(self.child.replace_variable(old_var, new_var))
    
    def get_expansion(self):
        if type(self.child) == Negation:
            return {
                "type": "alpha",
                "formulas": (self.child.child,),
            }
        elif type(self.child) == Conjunction:
            return {
                "type": "beta",
                "formulas": (Negation(self.child.left), Negation(self.child.right)),
            }
        elif type(self.child) == Disjunction:
            return {
                "type": "alpha",
                "formulas": (Negation(self.child.left), Negation(self.child.right)),
            }
        elif type(self.child) == Implication:
            return {
                "type": "alpha",
                "formulas": (self.child.left, Negation(self.child.right)),
            }
        elif type(self.child) == UniversalQuantifier:
            bound_variable = str(self.child.variable)
            new_bound_variable = get_new_variable()
            return {
                "type": "delta",
                "formulas": (Negation(self.child.child.replace_variable(bound_variable, new_bound_variable)),),
            }

class Quantifier(ParseTree): # abstract class

    @staticmethod
    def make(symbol, variable: Variable, child: ParseTree):
        if symbol == "A":
            return UniversalQuantifier(variable, child)
        if symbol == "E":
            return ExistentialQuantifier(variable, child)

    def __init__(self, variable: Variable, child: ParseTree):
        super().__init__()
        self.variable = variable
        self.child = child
        self.symbol = None
    
    def replace_variable(self, old_var: str, new_var: str):
        return type(self)(self.variable.replace_variable(old_var, new_var), self.child.replace_variable(old_var, new_var))
    
    def __str__(self) -> str:
        return f"{self.symbol}{self.variable}{str(self.child)}"
    
    def is_literal(self) -> bool:
        return False

class UniversalQuantifier(Quantifier):

    def __init__(self, variable: Variable, child: ParseTree):
        super().__init__(variable, child)
        self.symbol = "A"
    
    def parse_output(self) -> int:
        return 3
    
class ExistentialQuantifier(Quantifier):

    def __init__(self, variable: Variable, child: ParseTree):
        super().__init__(variable, child)
        self.symbol = "E"

    def parse_output(self) -> int:
        return 4
    
    def get_expansion(self):
        return {
            "type": "delta",
            "formulas": (self.child.replace_variable(str(self.variable), get_new_variable()),),
        }

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
    
    def is_literal(self):
        return False
    
    def replace_variable(self, old_var: str, new_var: str):
        return type(self)(self.left.replace_variable(old_var, new_var), self.right.replace_variable(old_var, new_var))
    

class Conjunction(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = "^"
    
    def get_expansion(self):
        return {
            "type": "alpha",
            "formulas": (self.left, self.right),
        }

class Disjunction(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = "v"
    
    def get_expansion(self):
        return {
            "type": "beta",
            "formulas": (self.left, self.right),
        }

class Implication(BinaryConnective):

    def __init__(self, left: ParseTree, right: ParseTree):
        super().__init__(left, right)
        self.con = ">"
    
    def get_expansion(self):
        return {
            "type": "beta",
            "formulas": (Negation(self.left), self.right),
        }

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
    
    def replace_variable(self, old_var: str, new_var: str):
        return Predicate(self.symbol, self.left.replace_variable(old_var, new_var), self.right.replace_variable(old_var, new_var))
    
    def is_literal(self) -> bool:
        return True
    
    def literal(self):
        return Literal(self, True)
    

class NotAFormula(ParseTree):
    
    def parse_output(self) -> int:
        return 0

class Literal():
    def __init__(self, atom: Variable | Predicate, truth_state: bool):
        self._atom = atom
        self.truth_state = truth_state
    
    @property
    def atom(self):
        return str(self._atom)

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

def is_fully_expanded(theory: set):
    for formula in theory:
        if not formula.is_literal(): return False
    return True

def contains_contradiction(theory: set):
    
    truth_values = {}
    for formula in theory:
        if formula.is_literal():
            literal = formula.literal()
            if literal.atom in truth_values and truth_values[literal.atom] != literal.truth_state:
                return True
            truth_values[literal.atom] = literal.truth_state
    return False

def get_non_literal(theory: set):
    beta_formula = None
    delta_formula = None
    for formula in theory:
        if type(formula) is Conjunction:
            return formula
        elif type(formula) is Negation and not formula.is_literal():
            if type(formula.child) in {Negation, Disjunction, Implication}:
                return formula
            elif type(formula.child) == Conjunction:
                beta_formula = formula
            elif type(formula.child) == UniversalQuantifier:
                delta_formula = formula
        elif type(formula) in {Disjunction, Implication}:
            beta_formula = formula
        elif type(formula) == ExistentialQuantifier:
            delta_formula = formula
    if beta_formula is not None:
        return beta_formula
    elif delta_formula is not None:
        return delta_formula
    raise TypeError("No non-literals in theory")
    


def tableau_is_satisfiable(tableau: list[set]):
    while len(tableau):
        theory = tableau.pop()
        if is_fully_expanded(theory) and not contains_contradiction(theory):
            return 1
        non_literal = get_non_literal(theory)
        expansion = non_literal.get_expansion()
        if len(GENERATED_VARIABLES) > MAX_CONSTANTS:
            return 2
        theory.remove(non_literal)
        if expansion["type"] == "alpha":
            for new_formula in expansion["formulas"]:
                theory.add(new_formula)
            if theory not in tableau and not contains_contradiction(theory):
                tableau.append(theory)
        if expansion["type"] == "beta":
            for new_formula in expansion["formulas"]:
                new_theory = theory.copy()
                new_theory.add(new_formula)
                if new_theory not in tableau and not contains_contradiction(new_theory):
                    tableau.append(new_theory)
        if expansion["type"] == "delta":
            for new_formula in expansion["formulas"]:
                new_theory = theory.copy()
                new_theory.add(new_formula)
                if new_theory not in tableau and not contains_contradiction(new_theory):
                    tableau.append(new_theory)
    return 0

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
    return {generate_parse_tree(fmla)}

#check for satisfiability
def sat(tableau):
#output 0 if not satisfiable, output 1 if satisfiable, output 2 if number of constants exceeds MAX_CONSTANTS
    return tableau_is_satisfiable(tableau)

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
