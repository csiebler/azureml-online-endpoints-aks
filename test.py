import requests

url = 'http://10.0.2.100/api/v1/endpoint/testprivendpoint1/score'
key = 'something secret goes here'

test_data = {
  'data': [{
    "Age": 20,
    "Sex": "male",
    "Job": 0,
    "Housing": "own",
    "Saving accounts": "little",
    "Checking account": "little",
    "Credit amount": 100,
    "Duration": 48,
    "Purpose": "radio/TV"
  }]
}

headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
resp = requests.post(url, json=test_data, headers=headers)

print(f"Prediction from url {url} (good, bad) {resp.text}")
