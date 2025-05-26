from flask import Flask, request, jsonify
from flask_cors import CORS
from pytojs import transpile_python_to_js
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    python_code = data.get('code', '')
    
    try:
        # Direct AST-based transpilation
        js_code, error = transpile_python_to_js(python_code)
        if error:
            return jsonify({'error': error}), 400
            
        result = {
            'javascript': js_code
        }
        return jsonify(result)
    except Exception as e:
        error_msg = f"Conversion error: {str(e)}"
        return jsonify({'error': error_msg}), 400

if __name__ == "__main__":
    app.run(debug=True)
