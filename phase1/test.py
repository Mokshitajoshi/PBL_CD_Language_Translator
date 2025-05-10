import requests

url = "http://127.0.0.1:5000/convert"
data = {
    "code": "print('Hello, world!')" 
}
response = requests.post(url, json=data)
print("JavaScript Output:")
print(response.json()["javascript"])  
