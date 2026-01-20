import requests

headers = {"Authorization": "RglJRbk4RvBJrKzeF_TYsPh-08bolWyW"}

response = requests.get('https://csfloat.com/api/v1/listings/AK-47%20%7C%20Redline%20%28Field-Tested%29', headers=headers)

print(response)

