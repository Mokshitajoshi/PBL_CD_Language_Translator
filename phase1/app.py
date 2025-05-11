# app.py
from flask import Flask, request, jsonify
import requests
from parse import parse_code_to_ir  # From parse.py (Collaborator 1)

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    python_code = data.get('code', '')

    try:
        # Step 1: Convert Python code to IR using Collaborator 1
        ir = parse_code_to_ir(python_code)

        # Step 2: Send IR to Collaborator 2's backend (/convert on port 5001)
        response = requests.post("http://127.0.0.1:5001/convert", json={"ir": ir})
        java_output = response.json()

        return jsonify(java_output)  # Send Java-style code back to the caller

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
