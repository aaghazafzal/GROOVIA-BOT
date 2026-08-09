import requests
import json
import base64
from pyDes import des, ECB, PAD_PKCS5

def decrypt_url(url):
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
    dec_url = dec_url.replace("_96.mp4", "_320.mp4")
    return dec_url

def test_jiosaavn(title):
    query = title.replace(' ', '+')
    url = f"https://www.jiosaavn.com/api.php?_format=json&_marker=0&api_version=4&ctx=web6dot0&n=1&p=1&q={query}&__call=search.getResults"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    print(f"Fetching: {url}")
    r = requests.get(url, headers=headers)
    print("STATUS:", r.status_code)
    try:
        data = r.json()
        results = data.get('results', [])
        if not results:
            print("No results found")
            return
            
        song = results[0]
        print(f"FOUND: {song.get('title')} - {song.get('subtitle')}")
        
        enc_url = song.get('media_preview_url', '')
        if enc_url:
            pass
        else:
            print("KEYS:", song.keys())
            print("MORE INFO:", song.get('more_info', {}).keys())
            
        song_id = song.get('id')
        print(f"Song ID: {song_id}")
        
        detail_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids={song_id}"
        r2 = requests.get(detail_url, headers=headers)
        print("DETAIL STATUS:", r2.status_code)
        d2 = r2.json()
        if song_id in d2:
            enc_url = d2[song_id].get('more_info', {}).get('encrypted_media_url')
            if not enc_url:
                enc_url = d2[song_id].get('encrypted_media_url')
            print("Encrypted Media URL:", enc_url)
            if enc_url:
                dec_url = decrypt_url(enc_url)
                print("\n✅ DIRECT DOWNLOAD URL:")
                print(dec_url)
    except Exception as e:
        print("Error:", e)

test_jiosaavn("Kesariya Brahmastra")
