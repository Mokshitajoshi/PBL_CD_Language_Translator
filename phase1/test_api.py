import requests

def test_api_convert():
    url = "http://127.0.0.1:5000/convert"
    data = {"code": "a = 10"}
    res = requests.post(url, json=data)
    assert res.status_code == 200
    assert "ir" in res.json()
    assert len(res.json()["ir"]["variables"]) == 1
