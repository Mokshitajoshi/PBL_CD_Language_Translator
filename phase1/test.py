# test.py
import requests

# Step 1: Write your Python code (you can change this anytime)
python_code = """
def add(a, b):
    return a + b
"""

# Step 2: Send it to the main app.py backend
response = requests.post("http://127.0.0.1:5000/convert", json={"code": python_code})

# Step 3: Print the converted Java-like structure
if response.status_code == 200:
    result = response.json()
    print("\n✅ Java Code Representation:\n")
    
    print("Functions:")
    for func in result.get("functions", []):
        print(func)
    
    print("\nVariables:")
    for var in result.get("variables", []):
        print(var)

    print("\nLoops:")
    for loop in result.get("loops", []):
        print(loop)
else:
    print("❌ Error:", response.json().get("error"))
