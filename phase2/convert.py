# phase2/convert.py

from flask import Flask, request, jsonify
import ast

app = Flask(__name__)

# Generate Java function from IR
def generate_java_function(func_ir):
    name = func_ir.get("name", "function")
    args = ", ".join(f"int {arg}" for arg in func_ir.get("args", []))  # Assume all args are int
    return f"public int {name}({args}) {{\n    // TODO: function body\n}}"

# Generate Java variable declarations from IR
def generate_java_variable(var_ir):
    declarations = []
    for target in var_ir.get("targets", []):
        declarations.append(f"int {target} = 0;  // TODO: assign proper value")
    return declarations

# Improved: Convert loops from IR to Java-style
def generate_java_loop(loop_ir):
    if loop_ir.get("type") == "for":
        target = loop_ir.get("target", "")
        try:
            target_ast = ast.literal_eval(target)
            if isinstance(target_ast, ast.Name):
                var_name = target_ast.id
            else:
                var_name = "i"
        except:
            var_name = "i"
        return f"for (int {var_name} = 0; {var_name} < N; {var_name}++) {{\n    // TODO: loop body\n}}"

    elif loop_ir.get("type") == "while":
        condition_ast_str = loop_ir.get("condition", "")
        try:
            # Parse AST condition string
            condition_expr = ast.parse(condition_ast_str, mode='eval').body
            if isinstance(condition_expr, ast.Compare):
                left = condition_expr.left.id if isinstance(condition_expr.left, ast.Name) else "x"
                op = type(condition_expr.ops[0]).__name__
                comparator = condition_expr.comparators[0].value if isinstance(condition_expr.comparators[0], ast.Constant) else "?"

                op_map = {
                    "Eq": "==",
                    "NotEq": "!=",
                    "Lt": "<",
                    "LtE": "<=",
                    "Gt": ">",
                    "GtE": ">="
                }
                op_symbol = op_map.get(op, "??")
                condition = f"{left} {op_symbol} {comparator}"
            else:
                condition = "/* complex condition */"
        except:
            condition = "/* error parsing condition */"

        return f"while ({condition}) {{\n    // TODO: loop body\n}}"

    return "// Unknown loop type"

# Flask route to convert IR to Java-like output
@app.route("/convert", methods=["POST"])
def convert_ir():
    data = request.get_json()
    ir = data.get("ir", {})  # Expecting IR from parse.py

    java_code = {
        "functions": [],
        "variables": [],
        "loops": []
    }

    for func in ir.get("functions", []):
        java_code["functions"].append(generate_java_function(func))

    for var in ir.get("variables", []):
        java_code["variables"].extend(generate_java_variable(var))

    for loop in ir.get("loops", []):
        java_code["loops"].append(generate_java_loop(loop))

    return jsonify(java_code)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
