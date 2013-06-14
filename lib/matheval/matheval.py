import ast
import operator as op

# based on stack overflow discussion ...
# http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string

## sample:

#me = MathEval()
#x = "(8 % 3) * 2 / 3"
#print me.eval_expr(x)

class MathEval:

    def __init__(self):
        # supported operators
        self.operators = {ast.Add: op.add, 
            ast.Sub: op.sub, 
            ast.Mult: op.mul,
            ast.Div: op.truediv, 
            ast.Pow: op.pow, 
            ast.BitXor: op.xor, 
            ast.Mod: op.mod}

    def eval_expr(self, expr):
        """
        >>> eval_expr('2^6')
        4
        >>> eval_expr('2**6')
        64
        >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
        -5.0
        """
        if not len(expr):
            raise Exception("math error, expression cannot be empty")
        try:
            return self.eval_(ast.parse(expr).body[0].value)
        except (SyntaxError, TypeError):
            msg = "math syntax error in expression: %s" % (expr)
            raise Exception(msg)
        except ZeroDivisionError:
            msg = "math division by zero error in expression: %s" % (expr)
            raise Exception(msg)

    def eval_(self, node):
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.operator): # <operator>
            return self.operators[type(node)]
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return self.eval_(node.op)(self.eval_(node.left), self.eval_(node.right))
        else:
            raise TypeError(node)
