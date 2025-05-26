def convert_ir_to_js(ir):
    """
    Convert Intermediate Representation (IR) to JavaScript code.
    
    This function takes the IR produced by the parser and generates
    equivalent JavaScript code.
    
    Args:
        ir: Dictionary containing the intermediate representation
        
    Returns:
        JavaScript code as a string
    """
    converter = IRToJsConverter()
    return converter.convert(ir)

class IRToJsConverter:
    """Class to handle IR to JavaScript conversion"""
    
    def __init__(self):
        self.js_code = []
        self.indent = 0
        self.declared_vars = set()
        self.current_scope = "global"
        self.function_stack = []
    
    def convert(self, ir):
        """Main conversion method"""
        # Process functions
        self._process_functions(ir.get('functions', []))
        
        # Process variables
        self._process_variables(ir.get('variables', []))
        
        # Process loops
        self._process_loops(ir.get('loops', []))
        
        # Process conditionals
        self._process_conditionals(ir.get('conditionals', []))
        
        # Process expressions
        self._process_expressions(ir.get('expressions', []))
        
        return "\n".join(self.js_code)
    
    def _add_line(self, line):
        """Add a line of code with proper indentation"""
        self.js_code.append("  " * self.indent + line)
    
    def _camel_case(self, name):
        """Convert snake_case to camelCase for JavaScript conventions"""
        if "_" not in name:
            return name
        parts = name.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])
    
    def _process_functions(self, functions):
        """Process function definitions from IR"""
        for func in functions:
            name = func.get('name', '')
            js_name = self._camel_case(name)
            args = func.get('args', [])
            body = func.get('body', [])
            
            # Function declaration
            self._add_line(f"function {js_name}({', '.join(args)}) {{")
            
            # Process function body with increased indent
            old_scope = self.current_scope
            self.current_scope = name
            self.function_stack.append(name)
            self.indent += 1
            
            # Process each statement in the function body
            for stmt in body:
                self._process_statement(stmt)
            
            self.indent -= 1
            self.function_stack.pop()
            self.current_scope = old_scope
            self._add_line("}")
            self._add_line("")  # Empty line after function
    
    def _process_variables(self, variables):
        """Process variable assignments from IR"""
        for var in variables:
            # Handle different variable assignment types
            if 'targets' in var:
                # Regular assignment
                target = self._extract_name(var.get('targets', [''])[0])
                value = var.get('value', '')
                
                # Convert value to JS
                js_value = self._convert_value(value)
                
                # Determine declaration type (let for global, const for function scope)
                declaration = ""
                if target not in self.declared_vars:
                    if self.function_stack and self.current_scope != "global":
                        declaration = "const "
                    else:
                        declaration = "let "
                    self.declared_vars.add(target)
                
                self._add_line(f"{declaration}{target} = {js_value};")
            
            elif 'type' in var and var['type'] == 'augassign':
                # Augmented assignment (+=, -=, etc.)
                target = self._extract_name(var.get('target', ''))
                op = var.get('op', '')
                value = var.get('value', '')
                
                # Convert operator and value
                js_op = self._convert_operator(op)
                js_value = self._convert_value(value)
                
                self._add_line(f"{target} {js_op} {js_value};")
    
    def _process_loops(self, loops):
        """Process loop statements from IR"""
        for loop in loops:
            loop_type = loop.get('type', '')
            
            if loop_type == 'for':
                target = self._extract_name(loop.get('target', ''))
                iter_expr = loop.get('iter', '')
                body = loop.get('body', [])
                
                # Check if it's a range-based loop
                if "Call(func=Name(id='range'" in iter_expr:
                    # Extract range arguments
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
                else:
                    # For-of loop for other iterables
                    iter_name = self._convert_value(iter_expr)
                    self._add_line(f"for (let {target} of {iter_name}) {{")
                
                # Process loop body
                self.indent += 1
                for stmt in body:
                    self._process_statement(stmt)
                self.indent -= 1
                self._add_line("}")
            
            elif loop_type == 'while':
                condition = self._convert_value(loop.get('condition', ''))
                body = loop.get('body', [])
                
                self._add_line(f"while ({condition}) {{")
                
                # Process loop body
                self.indent += 1
                for stmt in body:
                    self._process_statement(stmt)
                self.indent -= 1
                self._add_line("}")
    
    def _process_conditionals(self, conditionals):
        """Process conditional statements from IR"""
        for cond_chain in conditionals:
            if isinstance(cond_chain, list):
                for i, cond in enumerate(cond_chain):
                    cond_type = cond.get('type', '')
                    
                    if cond_type == 'if':
                        test = self._convert_value(cond.get('test', ''))
                        self._add_line(f"if ({test}) {{")
                    elif cond_type == 'elif':
                        test = self._convert_value(cond.get('test', ''))
                        self._add_line(f"else if ({test}) {{")
                    elif cond_type == 'else':
                        self._add_line("else {")
                    
                    # Process conditional body
                    self.indent += 1
                    for stmt in cond.get('body', []):
                        self._process_statement(stmt)
                    self.indent -= 1
                    
                    # Close the block
                    self._add_line("}")
    
    def _process_expressions(self, expressions):
        """Process expressions from IR"""
        for expr in expressions:
            expr_type = expr.get('type', '')
            
            if expr_type == 'call':
                # Handle function calls
                func = expr.get('func', '')
                args = expr.get('args', [])
                
                # Special handling for print
                if func == 'print':
                    js_args = [self._convert_value(arg) for arg in args]
                    self._add_line(f"console.log({', '.join(js_args)});")
                else:
                    js_func = self._camel_case(func)  # Apply camelCase to function names
                    js_args = [self._convert_value(arg) for arg in args]
                    self._add_line(f"{js_func}({', '.join(js_args)});")
            
            elif expr_type == 'binary_operation':
                # Binary operations are usually part of other expressions
                # and handled by _convert_value
                pass
    
    def _process_statement(self, stmt):
        """Process a single statement from the AST dump"""
        if isinstance(stmt, dict):
            # Handle structured statements
            stmt_type = stmt.get('type', '')
            
            if stmt_type == 'call':
                func = stmt.get('func', '')
                args = stmt.get('args', [])
                
                # Special handling for print
                if func == 'print':
                    js_args = [self._convert_value(arg) for arg in args]
                    
                    # Check for f-strings
                    if any("JoinedStr" in str(arg) for arg in args):
                        # Handle f-string
                        fstring_parts = []
                        for arg in args:
                            if "JoinedStr" in str(arg):
                                # Extract parts from JoinedStr
                                parts = self._extract_fstring_parts(arg)
                                fstring_parts.append(f"`{parts}`")
                            else:
                                fstring_parts.append(self._convert_value(arg))
                        self._add_line(f"console.log({', '.join(fstring_parts)});")
                    else:
                        self._add_line(f"console.log({', '.join(js_args)});")
                else:
                    js_func = self._camel_case(func)  # Apply camelCase to function names
                    js_args = [self._convert_value(arg) for arg in args]
                    self._add_line(f"{js_func}({', '.join(js_args)});")
            
            # Add other statement types as needed
            
        else:
            # Handle AST dump strings
            if "Call(func=Name(id='print'" in stmt:
                # Handle print statements
                if "JoinedStr" in stmt:
                    # Handle f-string in print
                    fstring_parts = self._extract_fstring_from_dump(stmt)
                    self._add_line(f"console.log(`{fstring_parts}`);")
                else:
                    args = self._extract_print_args(stmt)
                    self._add_line(f"console.log({', '.join(args)});")
            
            elif "Call(func=Name(id='" in stmt:
                # Handle function calls
                func_name = stmt.split("Call(func=Name(id='")[1].split("'")[0]
                js_func_name = self._camel_case(func_name)  # Apply camelCase to function names
                args = self._extract_call_args(stmt)
                
                # Skip built-in functions that are handled specially
                if func_name in ['print', 'len', 'str', 'int', 'float']:
                    if func_name == 'print':
                        self._add_line(f"console.log({', '.join(args)});")
                    elif func_name == 'len':
                        # Handle len() function
                        if args:
                            self._add_line(f"{args[0]}.length;")
                    elif func_name == 'str':
                        # Handle str() function
                        if args:
                            self._add_line(f"String({args[0]});")
                    elif func_name == 'int':
                        # Handle int() function
                        if args:
                            self._add_line(f"parseInt({args[0]}, 10);")
                    elif func_name == 'float':
                        # Handle float() function
                        if args:
                            self._add_line(f"parseFloat({args[0]});")
                    return
                elif func_name == 'range':
                    # Handle range function
                    if len(args) == 2:
                        start, stop = args
                        self._add_line(f"Array.from({{length: {stop} - {start}}}, (_, i) => i + {start});")
                    elif len(args) == 3:
                        start, stop, step = args
                        self._add_line(f"Array.from({{length: Math.ceil(({stop} - {start}) / {step})}}, (_, i) => i * {step} + {start});")
                    elif len(args) == 1:
                        stop = args[0]
                        self._add_line(f"Array.from({{length: {stop}}}, (_, i) => i);")
                    return
                
                self._add_line(f"{js_func_name}({', '.join(args)});")
            
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
                    value = self._convert_value(value_part)
                    
                    # Determine declaration type (let for global, const for function scope)
                    declaration = ""
                    if var_name not in self.declared_vars:
                        if self.function_stack and self.current_scope != "global":
                            declaration = "const "
                        else:
                            declaration = "let "
                        self.declared_vars.add(var_name)
                    
                    self._add_line(f"{declaration}{var_name} = {value};")
            
            elif "If(" in stmt:
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
                    left = self._convert_value(left_part)
                    comparators = self._split_args(comparators_part)
                    right = self._convert_value(comparators[0]) if comparators else ""
                    
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
            
            elif "While(" in stmt:
                # Handle while loops
                if "test=" in stmt:
                    test_part = stmt.split("test=")[1].split(", body=")[0]
                    body_part = stmt.split("body=[")[1].split("], orelse=")[0]
                    
                    # Process test condition
                    test = self._convert_value(test_part)
                    
                    self._add_line(f"while ({test}) {{")
                    
                    # Process while body
                    self.indent += 1
                    body_stmts = self._split_statements(body_part)
                    for body_stmt in body_stmts:
                        self._process_statement(body_stmt)
                    self.indent -= 1
                    
                    self._add_line("}")
            
            elif "AugAssign(" in stmt:
                # Handle augmented assignments (+=, -=, etc.)
                if "target=" in stmt and "op=" in stmt and "value=" in stmt:
                    target_part = stmt.split("target=")[1].split(", op=")[0]
                    op_part = stmt.split("op=")[1].split(", value=")[0]
                    value_part = stmt.split("value=")[1]
                    
                    target = self._convert_value(target_part)
                    value = self._convert_value(value_part)
                    
                    # Map Python operator to JavaScript operator
                    op_map = {
                        "Add()": "+=",
                        "Sub()": "-=",
                        "Mult()": "*=",
                        "Div()": "/=",
                        "Mod()": "%=",
                        "Pow()": "**="  # This will need special handling
                    }
                    
                    js_op = op_map.get(op_part, "+=")
                    
                    # Special case for power operator
                    if "Pow()" in op_part:
                        self._add_line(f"{target} = Math.pow({target}, {value});")
                    else:
                        self._add_line(f"{target} {js_op} {value};")
    
    # Helper methods
    def _extract_name(self, name_str):
        """Extract name from AST string"""
        if isinstance(name_str, str) and "Name(id='" in name_str:
            return name_str.split("Name(id='")[1].split("'")[0]
        return name_str
    
    def _extract_print_args(self, stmt):
        """Extract arguments from print statement"""
        args = []
        if "args=[" in stmt:
            args_str = stmt.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._convert_value(part))
        
        return args
    
    def _extract_call_args(self, stmt):
        """Extract arguments from function call statement"""
        args = []
        if "args=[" in stmt:
            args_str = stmt.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._convert_value(part))
        
        return args
    
    def _extract_return_value(self, stmt):
        """Extract return value from return statement"""
        if "value=None" in stmt:
            return ""
        elif "value=" in stmt:
            value_part = stmt.split("value=")[1]
            return self._convert_value(value_part)
        return ""
    
    def _extract_range_args(self, iter_expr):
        """Extract arguments from range() function"""
        args = []
        if "args=[" in iter_expr:
            args_str = iter_expr.split("args=[")[1].split("]")[0]
            parts = self._split_args(args_str)
            
            for part in parts:
                args.append(self._convert_value(part))
        
        return args
    
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
    
    def _convert_operator(self, op):
        """Convert Python operator to JavaScript operator"""
        op_map = {
            'Add': '+=',
            'Sub': '-=',
            'Mult': '*=',
            'Div': '/=',
            'Mod': '%=',
            'FloorDiv': '//=',  # This will need special handling
            'Pow': '**='        # This will need special handling
        }
        return op_map.get(op, '+=')  # Default to += if operator not found
    
    def _convert_value(self, value):
        """Convert a value to its JavaScript representation"""
        if isinstance(value, dict):
            # Handle structured values
            value_type = value.get('type', '')
            
            if value_type == 'binary_operation':
                left = self._convert_value(value.get('left', ''))
                op = value.get('op', '')
                right = self._convert_value(value.get('right', ''))
                
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
                    return f'"{val}"'  # Use double quotes for strings
                elif val is None:
                    return "null"
                elif val is True:
                    return "true"
                elif val is False:
                    return "false"
                return str(val)
            
            else:
                # For other structured values, convert to string
                return str(value)
        
        elif isinstance(value, str):
            # Handle AST dump strings
            if "Name(id='" in value:
                return value.split("Name(id='")[1].split("'")[0]
            
            elif "Constant(value=" in value:
                const_value = value.split("Constant(value=")[1].split(")")[0]
                
                # Handle different constant types
                if const_value == "None":
                    return "null"
                elif const_value == "True":
                    return "true"
                elif const_value == "False":
                    return "false"
                elif const_value.startswith("'") or const_value.startswith('"'):
                    # Keep string quotes
                    return const_value
                
                return const_value
            
            elif "BinOp(" in value:
                # Handle binary operations in AST dump
                if "left=" in value and "op=" in value and "right=" in value:
                    left_part = value.split("left=")[1].split(", op=")[0]
                    op_part = value.split("op=")[1].split(", right=")[0]
                    right_part = value.split("right=")[1].split(")")[0]
                    
                    left = self._convert_value(left_part)
                    right = self._convert_value(right_part)
                    
                    # Map Python operator to JavaScript operator
                    op_map = {
                        "Add()": "+",
                        "Sub()": "-",
                        "Mult()": "*",
                        "Div()": "/",
                        "Mod()": "%",
                        "FloorDiv()": "Math.floor(/)",  # Special case
                        "Pow()": "**"
                    }
                    
                    js_op = op_map.get(op_part, "+")
                    
                    # Special case for floor division
                    if js_op == "Math.floor(/)":
                        return f"Math.floor({left} / {right})"
                    
                    return f"{left} {js_op} {right}"
            
            elif "List(" in value:
                # Handle list literals
                if "elts=[" in value:
                    elts_str = value.split("elts=[")[1].split("]")[0]
                    elements = self._split_args(elts_str)
                    js_elements = [self._convert_value(el) for el in elements]
                    return f"[{', '.join(js_elements)}]"
            
            elif "Dict(" in value:
                # Handle dictionary literals
                if "keys=[" in value and "values=[" in value:
                    keys_str = value.split("keys=[")[1].split("]")[0]
                    values_str = value.split("values=[")[1].split("]")[0]
                    
                    keys = self._split_args(keys_str)
                    values = self._split_args(values_str)
                    
                    pairs = []
                    for k, v in zip(keys, values):
                        key = self._convert_value(k)
                        val = self._convert_value(v)
                        
                        # If key is a string literal, use as object property
                        if key.startswith('"') or key.startswith("'"):
                            pairs.append(f"{key}: {val}")
                        else:
                            pairs.append(f"[{key}]: {val}")
                    
                    return f"{{{', '.join(pairs)}}}"
            
            else:
                # For other strings, return as is
                return value
        else:
            # For other types, return as is
            return value

    def _extract_fstring_parts(self, fstring_expr):
        """Extract parts from an f-string expression"""
        parts = []
        
        if isinstance(fstring_expr, str) and "JoinedStr" in fstring_expr:
            # Extract from AST dump string
            return self._extract_fstring_from_dump(fstring_expr)
        
        # For structured representation
        if isinstance(fstring_expr, dict) and fstring_expr.get('type') == 'joined_str':
            values = fstring_expr.get('values', [])
            for value in values:
                if isinstance(value, dict):
                    if value.get('type') == 'str':
                        parts.append(value.get('value', ''))
                    elif value.get('type') == 'formatted_value':
                        expr = value.get('value', {})
                        parts.append(f"${{{self._convert_value(expr)}}}")
        
        return "".join(parts)

    def _extract_fstring_from_dump(self, stmt):
        """Extract f-string parts from AST dump string"""
        parts = []
        
        # Extract values from JoinedStr
        if "values=[" in stmt:
            values_str = stmt.split("values=[")[1].split("]")[0]
            values = self._split_args(values_str)
            
            for value in values:
                if "Constant" in value:
                    # Extract string constant
                    if "value='" in value:
                        str_value = value.split("value='")[1].split("'")[0]
                        parts.append(str_value)
                elif "FormattedValue" in value:
                    # Extract formatted expression
                    if "value=" in value:
                        expr_str = value.split("value=")[1].split(", conversion=")[0]
                        expr = self._convert_value(expr_str)
                        parts.append(f"${{{expr}}}")
        
        return "".join(parts)







