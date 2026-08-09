import requests
import json

def test_cobalt(yt_id):
    url = "https://co.wuk.sh/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "url": f"https://www.youtube.com/watch?v={yt_id}",
        "isAudioOnly": True,
        "aFormat": "mp3"
    }
    r = requests.post(url, headers=headers, json=data)
    print("STATUS:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

test_cobalt("yQ1uabb0MVA")
