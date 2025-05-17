from flask import Flask, request, jsonify
from flask_cors import CORS
from lexical_analyzer import analyze_code
from parse import parse_code_to_ir
from ir_to_js import convert_ir_to_js

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # More explicit CORS configuration

@app.route('/convert', methods=['POST'])
def convert():
    print("Received request:", request)
    data = request.get_json()
    print("Request data:", data)
    python_code = data.get('code', '')
    print("Python code:", python_code)
    
    try:
        # Step 1: Lexical Analysis
        tokens = analyze_code(python_code)
        
        # Step 2: Parse Tree Generation
        ir = parse_code_to_ir(python_code)
        
        # Step 3: Target Code Generation
        js_code = convert_ir_to_js(ir)
        
        result = {
            'tokens': tokens,
            'ir': ir,
            'javascript': js_code
        }
        print("Sending response:", result)
        return jsonify(result)
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 400

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
