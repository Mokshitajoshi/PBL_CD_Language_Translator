def convert_ir_to_js(ir):
    """
    Convert IR to JavaScript code using pattern-based conversion.
    """
    converter = PyToJsConverter()
    return converter.convert(ir)

class PyToJsConverter:
    """Class to handle Python to JavaScript conversion using IR"""
    
    def __init__(self):
        self.js_code = []
        self.declared_vars = set()
        self.indent = 0
        self.processed_calls = set()  # Track processed function calls
        self.processed_statements = set()  # Track processed statements
        self.temp_vars = {}  # For three-address code generation
        self.current_scope = "global"  # Track current scope for variable declarations
    
    def convert(self, ir):
        """Main conversion method"""
        # Process functions first
        self._process_functions(ir.get('functions', []))
        
        # Process loops
        self._process_loops(ir.get('loops', []))
        
        # Process variables
        self._process_variables(ir.get('variables', []))
        
        # Process conditionals
        self._process_conditionals(ir.get('conditionals', []))
        
        # Process expressions (including function calls)
        self._process_expressions(ir.get('expressions', []))
        
        return "\n".join(self.js_code)
    
    def _add_line(self, line):
        """Add a line of code with proper indentation"""
        self.js_code.append("  " * self.indent + line)
    
    def _process_functions(self, functions):
        """Process function definitions"""
        for func in functions:
            name = func.get('name', '')
            args = func.get('args', [])
            body = func.get('body', [])
            lineno = func.get('lineno', 0)
            
            # Function declaration
            self._add_line(f"function {name}({', '.join(args)}) {{")
            self.indent += 1
            
            # Set current scope to function name
            old_scope = self.current_scope
            self.current_scope = name
            
            # Process function body
            for stmt in body:
                self._process_statement(stmt)
            
            # Restore scope
            self.current_scope = old_scope
            
            self.indent -= 1
            self._add_line("}")
            self._add_line("")  # Empty line after function
    
    def _process_variables(self, variables):
        """Process variable assignments"""
        for var in variables:
            targets = var.get('targets', [])
            value = var.get('value', '')
            var_type = var.get('type', '')
            
            if targets:
                var_name = self._extract_name(targets[0])
                
                if var_type == 'augassign':
                    # Handle augmented assignments (+=, -=, etc.)
                    op = var.get('op', '')
                    js_op = self._convert_operator(op)
                    js_expr = self._process_value(value)
                    self._add_line(f"{var_name} {js_op} {js_expr};")
                else:
                    # Handle regular assignments
                    js_expr = self._process_value(value)
                    if var_name in self.declared_vars:
                        self._add_line(f"{var_name} = {js_expr};")
                    else:
                        self._add_line(f"let {var_name} = {js_expr};")
                        self.declared_vars.add(var_name)

    def _process_value(self, value):
        """Process a value which could be a string or a structured object"""
        if isinstance(value, dict):
            value_type = value.get('type', '')
            
            if value_type == 'binary_operation':
                left = self._process_value(value.get('left', ''))
                op = value.get('op', '')
                right = self._process_value(value.get('right', ''))
                
                # Map Python operator to JavaScript operator
                op_map = {
                    "Add": "+",
                    "Sub": "-",
                    "Mult": "*",
                    "Div": "/",
                    "Mod": "%",
                    "FloorDiv": "Math.floor(/)",  # Special case
                    "Pow": "**"
                }
                
                js_op = op_map.get(op, "+")
                
                # Special case for floor division
                if js_op == "Math.floor(/)":
                    return f"Math.floor({left} / {right})"
                
                return f"{left} {js_op} {right}"
            elif value_type == 'name':
                return value.get('id', '')
            elif value_type == 'constant':
                val = value.get('value', '')
                if isinstance(val, str):
                    return f"'{val}'"
                return str(val)
        else:
            # If it's a string (ast.dump output), use the existing processing
            return self._process_expression_node(value)
    
    def _process_loops(self, loops):
        """Process loop statements"""
        for loop in loops:
            loop_type = loop.get('type', '')
            
            if loop_type == 'for':
                target = self._extract_name(loop.get('target', ''))
                iter_expr = loop.get('iter', '')
                
                # Handle range() function in for loops
                if "Call(func=Name(id='range'" in iter_expr:
                    args = self._extract_range_args(iter_expr)
                    
                    if len(args) == 1:
                        # range(stop)
                        self._add_line(f"for (let {target} = 0; {target} < {args[0]}; {target}++) {{")
                    elif len(args) == 2:
                        # range(start, stop)
                        self._add_line(f"for (let {target} = {args[0]}; {target} < {args[1]}; {target}++) {{")
                    elif len(args) == 3:
                        # range(start, stop, step)
                        self._add_line(f"for (let {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]}) {{")
                    else:
                        # Default case
                        self._add_line(f"for (let {target} = 0; {target} < 0; {target}++) {{")
                    
                    # Process loop body
                    self.indent += 1
                    for stmt in loop.get('body', []):
                        self._process_statement(stmt)
                    self.indent -= 1
                    self._add_line("}")
                else:
                    # Generic iterable
                    iter_name = self._process_expression_node(iter_expr)
                    self._add_line(f"for (let {target} of {iter_name}) {{")
                    
                    # Process loop body
                    self.indent += 1
                    for stmt in loop.get('body', []):
                        self._process_statement(stmt)
                    self.indent -= 1
                    self._add_line("}")
            
            elif loop_type == 'while':
                condition = self._process_expression_node(loop.get('condition', ''))
                self._add_line(f"while ({condition}) {{")
                
                # Process loop body
                self.indent += 1
                for stmt in loop.get('body', []):
                    self._process_statement(stmt)
                self.indent -= 1
                self._add_line("}")
    
    def _process_conditionals(self, conditionals):
        """Process conditional statements"""
        # Skip conditionals in global scope - they're handled by the functions
        if self.current_scope != "global":
            return
        
        for cond_chain in conditionals:
            if isinstance(cond_chain, list):
                for i, cond in enumerate(cond_chain):
                    cond_type = cond.get('type', '')
                    
                    if cond_type == 'if':
                        test = self._process_expression_node(cond.get('test', ''))
                        self._add_line(f"if ({test}) {{")
                    elif cond_type == 'elif':
                        test = self._process_expression_node(cond.get('test', ''))
                        self._add_line(f"else if ({test}) {{")
                    elif cond_type == 'else':
                        self._add_line("else {")
                    
                    # Process conditional body
                    self.indent += 1
                    for stmt in cond.get('body', []):
                        self._process_statement(stmt)
                    self.indent -= 1
                    self._add_line("}")
    
    def _process_expressions(self, expressions):
        """Process expressions including function calls"""
        # Skip expressions in global scope - they're handled by the functions
        if self.current_scope != "global":
            return
        
        for expr in expressions:
            expr_type = expr.get('type', '')
            
            if expr_type == 'call':
                func_name = expr.get('func', '')
                args = expr.get('args', [])
                
                # Skip built-in functions that are handled specially
                if func_name in ['print', 'len', 'str', 'int', 'float', 'range']:
                    if func_name == 'print':
                        js_args = self._format_call_args(args)
                        self._add_line(f"console.log({', '.join(js_args)});")
                    return
                
                # Format arguments
                js_args = self._format_call_args(args)
                self._add_line(f"{func_name}({', '.join(js_args)});")
            elif expr_type == 'binary_operation':
                # This is handled in _process_expression_node
                pass
    
    def _process_statement(self, stmt):
        """Process a single statement"""
        # Create a unique identifier for this statement
        stmt_hash = hash(stmt)
        
        # Skip if already processed
        if stmt_hash in self.processed_statements:
            return
        self.processed_statements.add(stmt_hash)
        
        if "If(" in stmt:
            # Handle if statements
            if "test=Compare(" in stmt:
                test_part = stmt.split("test=Compare(")[1]
                left_part = test_part.split("left=")[1].split(", ops=")[0]
                ops_part = test_part.split("ops=[")[1].split("]")[0]
                comparators_part = test_part.split("comparators=[")[1].split("]")[0]
                
                # Extract body and orelse parts
                body_part = stmt.split("body=[")[1].split("], orelse=")[0]
                orelse_part = stmt.split("orelse=")[1]
                
                # Process left and right operands
                left = self._process_expression_node(left_part)
                comparators = self._split_args(comparators_part)
                right = self._process_expression_node(comparators[0]) if comparators else ""
                
                # Map Python comparison operators to JavaScript
                op = "==="  # Default
                if "Eq()" in ops_part:
                    op = "==="
                elif "NotEq()" in ops_part:
                    op = "!=="
                elif "Lt()" in ops_part:
                    op = "<"
                elif "LtE()" in ops_part:
                    op = "<="
                elif "Gt()" in ops_part:
                    op = ">"
                elif "GtE()" in ops_part:
                    op = ">="
                
                # Write the if statement
                self._add_line(f"if ({left} {op} {right}) {{")
                
                # Process if body
                self.indent += 1
                body_stmts = self._split_statements(body_part)
                for body_stmt in body_stmts:
                    self._process_statement(body_stmt)
                self.indent -= 1
                
                # Process else part if it exists
                if orelse_part and orelse_part != "[]":
                    self._add_line("} else {")
                    self.indent += 1
                    orelse_stmts = self._split_statements(orelse_part.strip("[]"))
                    for else_stmt in orelse_stmts:
                        self._process_statement(else_stmt)
                    self.indent -= 1
                
                self._add_line("}")
        elif "Call(func=Name(id='print'" in stmt:
            # Handle print statements
            args = self._extract_print_args(stmt)
            self._add_line(f"console.log({', '.join(args)});")
        elif "Call(func=Name(id='" in stmt:
            # Handle function calls
            func_name = stmt.split("Call(func=Name(id='")[1].split("'")[0]
            args = self._extract_call_args(stmt)
            
            # Skip built-in functions that are handled specially
            if func_name in ['print', 'len', 'str', 'int', 'float']:
                if func_name == 'print':
                    self._add_line(f"console.log({', '.join(args)});")
                return
            
            # Skip range() in global scope (it's handled in for loops)
            if func_name == 'range' and self.current_scope == 'global':
                return
            
            self._add_line(f"{func_name}({', '.join(args)});")
        elif "Return(" in stmt:
            # Handle return statements
            return_value = self._extract_return_value(stmt)
            if return_value:
                self._add_line(f"return {return_value};")
            else:
                self._add_line("return;")
        elif "Assign(" in stmt:
            # Handle assignments
            if "targets=[Name(id='" in stmt:
                var_name = stmt.split("targets=[Name(id='")[1].split("'")[0]
                value_part = stmt.split("value=")[1]
                value = self._process_expression_node(value_part)
                
                if var_name in self.declared_vars or self.current_scope != "global":
                    self._add_line(f"{var_name} = {value};")
                else:
                    self._add_line(f"let {var_name} = {value};")
                    self.declared_vars.add(var_name)
        else:
            # For unhandled statements, add a comment
            pass

    def _split_statements(self, stmts_str):
        """Split a string of statements into individual statements"""
        result = []
        depth = 0
        current = ""
        
        for char in stmts_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            current += char
            
            if depth == 0 and char == ')':
                if current.strip():
                    result.append(current.strip())
                current = ""
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def _process_expression_node(self, expr_str):
        """Process an expression node and return JS code"""
        if not expr_str:
            return ""
        
        # Handle string literals
        if expr_str.startswith("'") and expr_str.endswith("'"):
            return expr_str
        
        # Handle simple cases directly
        if "Name(id='" in expr_str:
            return expr_str.split("Name(id='")[1].split("'")[0]
        elif "Constant(value=" in expr_str:
            value = expr_str.split("Constant(value=")[1].split(")")[0]
            if value.startswith("'") or value.startswith('"'):
                # Return string literals with quotes
                return value
            return value
        
        # Handle binary operations
        if "BinOp(" in expr_str:
            # Extract the parts of the binary operation
            if "left=" in expr_str and "op=" in expr_str and "right=" in expr_str:
                left_part = expr_str.split("left=")[1].split(", op=")[0]
                op_part = expr_str.split("op=")[1].split(", right=")[0]
                right_part = expr_str.split("right=")[1].split(")")[0]
                
                # Process left and right operands recursively
                left = self._process_expression_node(left_part)
                right = self._process_expression_node(right_part)
                
                # Map Python operator to JavaScript operator
                op_map = {
                    "Add": "+",
                    "Sub": "-",
                    "Mult": "*",
                    "Div": "/",
                    "Mod": "%",
                    "FloorDiv": "Math.floor(/)",  # Special case
                    "Pow": "**"
                }
                
                op = op_map.get(op_part, "+")
                
                # Special case for floor division
                if op == "Math.floor(/)":
                    return f"Math.floor({left} / {right})"
                
                return f"{left} {op} {right}"
        
        # Handle comparisons
        if "Compare(" in expr_str:
            if "left=" in expr_str and "ops=[" in expr_str and "comparators=[" in expr_str:
                left_part = expr_str.split("left=")[1].split(", ops=")[0]
                ops_part = expr_str.split("ops=[")[1].split("]")[0]
                comparators_part = expr_str.split("comparators=[")[1].split("]")[0]
                
                left = self._process_expression_node(left_part)
                comparators = self._split_args(comparators_part)
                right = self._process_expression_node(comparators[0]) if comparators else ""
                
                # Map Python comparison operators to JavaScript
                if "Eq()" in ops_part:
                    return f"{left} === {right}"
                elif "NotEq()" in ops_part:
                    return f"{left} !== {right}"
                elif "Lt()" in ops_part:
                    return f"{left} < {right}"
                elif "LtE()" in ops_part:
                    return f"{left} <= {right}"
                elif "Gt()" in ops_part:
                    return f"{left} > {right}"
                elif "GtE()" in ops_part:
                    return f"{left} >= {right}"
                elif "Is()" in ops_part:
                    return f"{left} === {right}"
                elif "IsNot()" in ops_part:
                    return f"{left} !== {right}"
                else:
                    return f"{left} === {right}"  # Default case
        
        # Handle function calls
        if "Call(" in expr_str:
            if "func=Name(id='" in expr_str:
                func_name = expr_str.split("func=Name(id='")[1].split("'")[0]
                args = self._extract_call_args(expr_str)
                
                # Special case for Python built-ins
                if func_name == "len":
                    if args:
                        return f"{args[0]}.length"
                elif func_name == "str":
                    if args:
                        return f"String({args[0]})"
                elif func_name == "int":
                    if args:
                        return f"parseInt({args[0]})"
                elif func_name == "float":
                    if args:
                        return f"parseFloat({args[0]})"
                
                return f"{func_name}({', '.join(args)})"
        
        # If we can't process it, return as is (with a comment)
        return f"/* Unprocessed: {expr_str} */"
    
    # Helper methods
    def _extract_name(self, name_str):
        """Extract name from AST string"""
        if "Name(id='" in name_str:
            return name_str.split("Name(id='")[1].split("'")[0]
        return name_str
    
    def _extract_print_args(self, stmt):
        """Extract arguments from print statement"""
        args = []
        if "args=[" in stmt:
            args_str = stmt.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._process_expression_node(part))
        
        return args
    
    def _extract_call_args(self, stmt):
        """Extract arguments from function call statement"""
        args = []
        if "args=[" in stmt:
            args_str = stmt.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._process_expression_node(part))
        
        return args
    
    def _extract_return_value(self, stmt):
        """Extract return value from return statement"""
        if "value=None" in stmt:
            return ""
        elif "value=" in stmt:
            value_part = stmt.split("value=")[1]
            return self._process_expression_node(value_part)
        return ""
    
    def _extract_range_args(self, iter_expr):
        """Extract arguments from range() function"""
        args = []
        if "args=[" in iter_expr:
            args_str = iter_expr.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._process_expression_node(part))
        
        return args
    
    def _format_call_args(self, args):
        """Format function call arguments"""
        js_args = []
        for arg in args:
            if isinstance(arg, dict):
                if arg.get('type') == 'constant':
                    value = arg.get('value', '')
                    if isinstance(value, str):
                        js_args.append(f"'{value}'")
                    else:
                        js_args.append(str(value))
                elif arg.get('type') == 'name':
                    js_args.append(arg.get('id', ''))
                else:
                    # For complex expressions in the IR
                    js_args.append(self._process_expression_node(str(arg)))
            else:
                js_args.append(self._process_expression_node(str(arg)))
        
        return js_args
    
    def _split_args(self, args_str):
        """Split arguments string into individual arguments"""
        args = []
        depth = 0
        current = ""
        
        for char in args_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            if char == ',' and depth == 0:
                if current.strip():
                    args.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            args.append(current.strip())
        
        return args
    
    def _convert_operator(self, op):
        """Convert Python operator to JavaScript operator"""
        op_map = {
            'Add': '+=',
            'Sub': '-=',
            'Mult': '*=',
            'Div': '/=',
            'Mod': '%='
        }
        return op_map.get(op, '+=')



















