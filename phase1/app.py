from flask import Flask, request, jsonify
from parse import parse_code_to_ir

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    python_code = data.get('code', '')
    try:
        js_code = parse_code_to_ir(python_code)
        return jsonify({'ir': js_code})   # <- Return it under 'ir'
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
