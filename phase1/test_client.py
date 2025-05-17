import requests

url = "http://127.0.0.1:5000/convert"
data = {
    "code": "print('Hello, world!')" 
}

try:
    response = requests.post(url, json=data)
    print("Status code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))