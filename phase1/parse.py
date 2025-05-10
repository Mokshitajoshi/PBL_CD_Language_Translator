import ast
import json

class CodeParser(ast.NodeVisitor):
    def __init__(self):
        self.ir = {"functions": [], "loops": [], "variables": []}

    def visit_FunctionDef(self, node):
        self.ir["functions"].append({
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_For(self, node):
        self.ir["loops"].append({
            "type": "for",
            "target": ast.dump(node.target),
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_While(self, node):
        self.ir["loops"].append({
            "type": "while",
            "condition": ast.dump(node.test),
            "lineno": node.lineno
        })
        self.generic_visit(node)

    def visit_Assign(self, node):
        targets = [ast.dump(t) for t in node.targets]
        self.ir["variables"].append({
            "targets": targets,
            "value": ast.dump(node.value),
            "lineno": node.lineno
        })
        self.generic_visit(node)

def parse_code_to_ir(code: str) -> dict:
    tree = ast.parse(code)
    parser = CodeParser()
    parser.visit(tree)
    return parser.ir
