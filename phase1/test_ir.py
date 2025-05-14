from parse import parse_code_to_ir

def test_function_parsing():
    code = "def hello(x): return x"
    ir = parse_code_to_ir(code)
    assert len(ir["functions"]) == 1
    assert ir["functions"][0]["name"] == "hello"

def test_loop_parsing():
    code = "for i in range(5): pass"
    ir = parse_code_to_ir(code)
    assert len(ir["loops"]) == 1
    assert ir["loops"][0]["type"] == "for"

def test_variable_parsing():
    code = "a = 5"
    ir = parse_code_to_ir(code)
    assert len(ir["variables"]) == 1
    assert "a" in ir["variables"][0]["targets"][0]
