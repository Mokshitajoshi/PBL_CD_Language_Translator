import ast
import json
from lexical_analyzer import analyze_code

class CodeParser(ast.NodeVisitor):
    def __init__(self):
        self.ir = {"functions": [], "loops": [], "variables": [], "conditionals": [], "expressions": []}

    def visit_FunctionDef(self, node):
        self.ir["functions"].append({
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "body": [ast.dump(n) for n in node.body],
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_For(self, node):
        self.ir["loops"].append({
            "type": "for",
            "target": ast.dump(node.target),
            "iter": ast.dump(node.iter),
            "body": [ast.dump(n) for n in node.body],
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_While(self, node):
        self.ir["loops"].append({
            "type": "while",
            "condition": ast.dump(node.test),
            "body": [ast.dump(stmt) for stmt in node.body],
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.ir["variables"].append({
            "type": "augassign",
            "target": ast.dump(node.target),
            "op": type(node.op).__name__,
            "value": ast.dump(node.value),
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_If(self, node):
        current = {
            "type": "if",
            "test": ast.dump(node.test),
            "body": [ast.dump(stmt) for stmt in node.body],
            "lineno": node.lineno
        }
        chain = [current]
        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                elif_node = orelse[0]
                current = {
                    "type": "elif",
                    "test": ast.dump(elif_node.test),
                    "body": [ast.dump(stmt) for stmt in elif_node.body],
                    "lineno": elif_node.lineno
                }
                chain.append(current)
                orelse = elif_node.orelse
            else:
                current = {
                    "type": "else",
                    "body": [ast.dump(stmt) for stmt in orelse],
                    "lineno": orelse[0].lineno if orelse else None
                }
                chain.append(current)
                break
        
        self.ir["conditionals"].append(chain)
        self.generic_visit(node)

    def visit_Assign(self, node):
        targets = [ast.dump(t) for t in node.targets]
        
        # Check if the value is a binary operation
        if isinstance(node.value, ast.BinOp):
            # Create a more structured representation of the binary operation
            value_info = {
                "type": "binary_operation",
                "left": self._process_operand(node.value.left),
                "op": type(node.value.op).__name__,
                "right": self._process_operand(node.value.right)
            }
        else:
            value_info = ast.dump(node.value)
        
        self.ir["variables"].append({
            "targets": targets,
            "value": value_info,
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def _process_operand(self, node):
        """Process an operand in a binary operation"""
        if isinstance(node, ast.Name):
            return {"type": "name", "id": node.id}
        elif isinstance(node, ast.Constant):
            return {"type": "constant", "value": node.value}
        elif isinstance(node, ast.BinOp):
            # Handle nested binary operations
            return {
                "type": "binary_operation",
                "left": self._process_operand(node.left),
                "op": type(node.op).__name__,
                "right": self._process_operand(node.right)
            }
        else:
            return ast.dump(node)

    def visit_BinOp(self, node):
        self.ir["expressions"].append({
            "type": "binary_operation",
            "left": ast.dump(node.left),
            "op": type(node.op).__name__,
            "right": ast.dump(node.right),
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            args = []
            for arg in node.args:
                if isinstance(arg, ast.Constant):
                    args.append({"type": "constant", "value": arg.value})
                elif isinstance(arg, ast.Name):
                    args.append({"type": "name", "id": arg.id})
                else:
                    args.append(ast.dump(arg))
            
            self.ir["expressions"].append({
                "type": "call",
                "func": node.func.id,
                "args": args,
                "lineno": node.lineno
            })
        self.generic_visit(node)

def parse_code_to_ir(code: str) -> dict:
    # Step 1: Lexical analysis
    tokens = analyze_code(code)
    
    # Step 2: Parse tree generation
    tree = ast.parse(code)
    parser = CodeParser()
    parser.visit(tree)
    
    # Add tokens to the IR
    ir = parser.ir
    ir["tokens"] = tokens
    
    return ir
