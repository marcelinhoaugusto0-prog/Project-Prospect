import urllib.request
import json
import urllib.error

data = json.dumps({'segment':'clinicas odontologicas', 'location':'São Paulo', 'radius':5}).encode()
req = urllib.request.Request('http://localhost:8000/api/prospects', headers={'Content-Type': 'application/json'}, data=data)

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.read().decode())
