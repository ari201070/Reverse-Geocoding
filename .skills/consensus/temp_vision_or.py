import sys
import base64
import json
import os
import urllib.request
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

REPO = os.path.dirname(os.path.abspath(__file__))
ENV = {}
with open(os.path.join(REPO, '.env'), encoding='utf-8') as f:
    for ln in f:
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            ENV[k.strip()] = v.strip()

img = os.path.join('F:/2023/10-Octubre',
                   '2023-10-04 11.33.03_IMG_20231004_113303.jpg')
with open(img, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

for model in ['google/gemma-4-31b-it:free',
              'qwen/qwen3.8-27b:free']:
    body = json.dumps({
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text',
                 'text': 'Identify this landmark. Return ONLY JSON: '
                         '{"landmark": "name", "city": "city", '
                         '"country": "country"}'},
                {'type': 'image_url',
                 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions', data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + ENV['OPENROUTER_API_KEY'],
                 'HTTP-Referer': 'http://localhost:3000',
                 'X-Title': 'Reverse Geocoding'})
    try:
        with urllib.request.urlopen(req, timeout=100) as r:
            data = json.load(r)
        print('MODEL:', model)
        print(data['choices'][0]['message']['content'][:400])
        break
    except Exception as e:
        print('MODEL:', model, 'FALLO:', str(e)[:120])
