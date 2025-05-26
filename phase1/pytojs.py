import ast
import json
import traceback

class PyToJSTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.imports = set()
        self.indent_level = 0
        self.function_stack = []
    
    def _indent(self, code):
        return "    " * self.indent_level + code
    
    def _camel_case(self, name):
        if "_" not in name:
            return name
        parts = name.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])
    
    def visit_Module(self, node):
        self.imports.clear()
        body = [self.visit(n) for n in node.body]
        body = [b for b in body if b is not None and b.strip()]
        
        js_code = []
        if self.imports:
            js_code.extend(sorted(self.imports))
            js_code.append("")
        js_code.extend(body)
        return "\n".join(js_code)
    
    def visit_FunctionDef(self, node):
        self.function_stack.append(node.name)
        func_name = self._camel_case(node.name)
        args = [arg.arg for arg in node.args.args]
        js_args = ", ".join(args)
        
        self.indent_level += 1
        body = [self.visit(n) for n in node.body]
        body = [b for b in body if b is not None and b.strip()]
        self.indent_level -= 1
        
        js_body = "\n".join([self._indent(line) for line in body if line])
        if not js_body:
            js_body = self._indent("// pass")
        
        self.function_stack.pop()
        return f"function {func_name}({js_args}) {{\n{js_body}\n}}"

    def visit_Return(self, node):
        if node.value:
            return f"return {self.visit(node.value)};"
        return "return;"
    
    def visit_Assign(self, node):
        target = node.targets[0]
        if isinstance(target, ast.Name):
            target_name = target.id
        else:
            target_name = self.visit(target)
            
        value = self.visit(node.value)
        declaration = "let " if not self.function_stack else "const "
        return f"{declaration}{target_name} = {value};"
    
    def visit_AugAssign(self, node):
        target = self.visit(node.target)
        op = self.visit(node.op)
        value = self.visit(node.value)
        
        # Special case for power operator
        if isinstance(node.op, ast.Pow):
            return f"{target} = Math.pow({target}, {value});"
        
        return f"{target} {op}= {value};"
    
    def visit_Name(self, node):
        return node.id
    
    def visit_Str(self, node):
        return json.dumps(node.s)
    
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return json.dumps(node.value)
        elif isinstance(node.value, bool):
            return "true" if node.value else "false"
        elif node.value is None:
            return "null"
        return str(node.value)
    
    def visit_List(self, node):
        elements = [self.visit(e) for e in node.elts]
        return f"[{', '.join(elements)}]"
    
    def visit_Dict(self, node):
        pairs = []
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Str) or (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                key_val = key.s if hasattr(key, 's') else key.value
                pairs.append(f"{json.dumps(key_val)}: {self.visit(value)}")
            else:
                pairs.append(f"[{self.visit(key)}]: {self.visit(value)}")
        return f"{{{', '.join(pairs)}}}"
    
    def visit_Call(self, node):
        func = self.visit(node.func)
        
        # Handle built-in functions
        if isinstance(node.func, ast.Name):
            if func == "print":
                func = "console.log"
            elif func == "int":
                args = [self.visit(arg) for arg in node.args]
                if len(args) == 1:
                    return f"parseInt({args[0]}, 10)"
            elif func == "float":
                args = [self.visit(arg) for arg in node.args]
                if len(args) == 1:
                    return f"parseFloat({args[0]})"
            elif func == "str":
                args = [self.visit(arg) for arg in node.args]
                if len(args) == 1:
                    return f"String({args[0]})"
            elif func == "len":
                args = [self.visit(arg) for arg in node.args]
                if len(args) == 1:
                    return f"{args[0]}.length"
            elif func == "range":
                args = [self.visit(arg) for arg in node.args]
                if len(args) == 2:
                    start, stop = args
                    return f"Array.from({{length: {stop} - {start}}}, (_, i) => i + {start})"
                elif len(args) == 3:
                    start, stop, step = args
                    return f"Array.from({{length: Math.ceil(({stop} - {start}) / {step})}}, (_, i) => i * {step} + {start})"
                elif len(args) == 1:
                    stop = args[0]
                    return f"Array.from({{length: {stop}}}, (_, i) => i)"
        
        args = [self.visit(arg) for arg in node.args]
        
        # Handle f-strings (formatted values)
        if isinstance(node.func, ast.Name) and func == "console.log":
            if len(node.args) == 1 and isinstance(node.args[0], ast.JoinedStr):
                return f"{func}({self.visit(node.args[0])})"
        
        return f"{func}({', '.join(args)})"
    
    def visit_JoinedStr(self, node):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Str) or (isinstance(value, ast.Constant) and isinstance(value.value, str)):
                string_value = value.s if hasattr(value, 's') else value.value
                parts.append(json.dumps(string_value)[1:-1])  # Remove quotes
            elif isinstance(value, ast.FormattedValue):
                parts.append(f"${{{self.visit(value.value)}}}")
        return f'`{"".join(parts)}`'
    
    def visit_FormattedValue(self, node):
        return f"${{{self.visit(node.value)}}}"
    
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        op = self.visit(node.op)
        right = self.visit(node.right)
        
        # Special case for power operator
        if isinstance(node.op, ast.Pow):
            return f"Math.pow({left}, {right})"
        
        # Add parentheses for complex expressions to ensure correct precedence
        if isinstance(node.left, ast.BinOp) or isinstance(node.right, ast.BinOp):
            return f"({left} {op} {right})"
        
        return f"{left} {op} {right}"
    
    def visit_Compare(self, node):
        left = self.visit(node.left)
        ops = [self.visit(op) for op in node.ops]
        comparators = [self.visit(comp) for comp in node.comparators]
        
        comparisons = []
        for i, op in enumerate(ops):
            comparisons.append(f"{left if i == 0 else comparators[i-1]} {op} {comparators[i]}")
        
        return " && ".join(comparisons)
    
    def visit_If(self, node):
        test = self.visit(node.test)
        
        self.indent_level += 1
        body = [self.visit(n) for n in node.body]
        body = [b for b in body if b is not None and b.strip()]
        self.indent_level -= 1
        
        js_body = "\n".join([self._indent(line) for line in body if line])
        
        orelse = []
        if node.orelse:
            self.indent_level += 1
            orelse = [self.visit(n) for n in node.orelse]
            orelse = [b for b in orelse if b is not None and b.strip()]
            self.indent_level -= 1
        
        js_orelse = ""
        if orelse:
            if len(orelse) == 1 and isinstance(orelse[0], str) and orelse[0].startswith("if "):
                js_orelse = f" else {orelse[0]}"
            else:
                js_orelse_lines = "\n".join([self._indent(line) for line in orelse if line])
                js_orelse = f" else {{\n{js_orelse_lines}\n{self._indent('')}}}"
        
        return f"if ({test}) {{\n{js_body}\n}}{js_orelse}"
    
    def visit_For(self, node):
        target = self.visit(node.target)
        iterable = self.visit(node.iter)
        
        self.indent_level += 1
        body = [self.visit(n) for n in node.body]
        body = [b for b in body if b is not None and b.strip()]
        self.indent_level -= 1
        
        js_body = "\n".join([self._indent(line) for line in body if line])
        
        return f"for (let {target} of {iterable}) {{\n{js_body}\n}}"
    
    def visit_While(self, node):
        test = self.visit(node.test)
        
        self.indent_level += 1
        body = [self.visit(n) for n in node.body]
        body = [b for b in body if b is not None and b.strip()]
        self.indent_level -= 1
        
        js_body = "\n".join([self._indent(line) for line in body if line])
        
        return f"while ({test}) {{\n{js_body}\n}}"
    
    def visit_Expr(self, node):
        value = self.visit(node.value)
        # Check if the value already ends with a semicolon
        if value.endswith(';'):
            return value
        return f"{value};"
    
    # Operator visitors
    def visit_Add(self, node):
        return "+"
    
    def visit_Sub(self, node):
        return "-"
    
    def visit_Mult(self, node):
        return "*"
    
    def visit_Div(self, node):
        return "/"
    
    def visit_Mod(self, node):
        return "%"
    
    def visit_Pow(self, node):
        return "**"  
    
    def visit_Lt(self, node):
        return "<"
    
    def visit_LtE(self, node):
        return "<="
    
    def visit_Gt(self, node):
        return ">"
    
    def visit_GtE(self, node):
        return ">="
    
    def visit_Eq(self, node):
        return "==="
    
    def visit_NotEq(self, node):
        return "!=="
    
    def visit_And(self, node):
        return "&&"
    
    def visit_Or(self, node):
        return "||"
    
    def visit_Not(self, node):
        return "!"
    
    def visit_USub(self, node):
        return "-"
    
    def visit_UAdd(self, node):
        return "+"

    def visit_AugAssign(self, node):
        target = self.visit(node.target)
        op = self.visit(node.op)
        value = self.visit(node.value)
        
        # Map Python's augmented assignment operators to JavaScript
        op_map = {
            "+": "+=",
            "-": "-=",
            "*": "*=",
            "/": "/=",
            "%": "%=",
            "**": "**="  # This will need special handling
        }
        
        js_op = op_map.get(op, "+=")
        
        # Special case for power operator
        if op == "**":
            return f"{target} = Math.pow({target}, {value});"
        
        return f"{target} {js_op} {value};"

def transpile_python_to_js(python_code):
    try:
        # Parse Python code to AST
        py_ast = ast.parse(python_code)
        
        # Transform AST to JavaScript
        transformer = PyToJSTransformer()
        js_code = transformer.visit(py_ast)
        
        return js_code, None
    except SyntaxError as e:
        return None, f"Python syntax error: {str(e)}"
    except Exception as e:
        error_msg = f"Transpilation error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return None, error_msg

if __name__ == "__main__":
    import traceback
    
    test_cases = {
        "Basic Test": """
def greet(name):
    print(f"Hello, {name}!")

greet("World")

x = 10
y = 20
if x < y:
    print("x is smaller")
else:
    print("y is smaller")

numbers = [1, 2, 3]
for num in numbers:
    print(num * 2)

person = {
    "name": "Alice",
    "age": 30,
    "is_student": False
}

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
    }

    for test_name, py_code in test_cases.items():
        print(f"\n{'='*5} TESTING CASE: {test_name} {'='*5}")
        print(f"--- Input Python: ---\n{py_code}\n--------------------")
        js_code, error = transpile_python_to_js(py_code)
        if error:
            print(f"--- RESULT (Error): ---\n{error}")
        else:
            print(f"--- RESULT (JavaScript Code): ---\n{js_code}")
        print(f"--- END OF TEST CASE: {test_name} ---\n")
