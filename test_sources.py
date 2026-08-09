"""
Test Invidious API instances from VPS — YouTube alternative proxy
"""
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')

import requests
import subprocess
import time

INVIDIOUS_INSTANCES = [
    'https://invidious.kavin.rocks',
    'https://inv.riverside.rocks',
    'https://invidious.projectsegfau.lt',
    'https://yewtu.be',
    'https://vid.puffyan.us',
    'https://invidious.tiekoetter.com',
    'https://invidious.namazso.eu',
    'https://invidious.flokinet.to',
    'https://invidious.nerdvpn.de',
    'https://invidious.privacy.com.de',
]

PIPED_INSTANCES = [
    'https://pipedapi.kavin.rocks',
    'https://api.piped.yt',
    'https://pipedapi.moomoo.me',
    'https://piped-api.privacy.com.de',
    'https://watchapi.whatever.social',
    'https://pipedapi.rivo.sh',
    'https://pipedapi.lasany.ovh',
    'https://piped.video/api',
]

TEST_ID = 'NJAv_7lHUIU'  # Kesariya
TEMP = '/tmp/groovia_dl'
os.makedirs(TEMP, exist_ok=True)

def test_invidious(instance):
    """Test Invidious and try to get audio stream"""
    try:
        r = requests.get(f'{instance}/api/v1/videos/{TEST_ID}',
                         timeout=10, params={'fields': 'adaptiveFormats,title'})
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        data = r.json()
        formats = data.get('adaptiveFormats', [])
        audio = [f for f in formats if f.get('type', '').startswith('audio')]
        if not audio:
            return None, "No audio formats"
        audio.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
        return audio[0].get('url'), f"OK ({len(audio)} audio formats)"
    except Exception as e:
        return None, str(e)[:60]


def test_piped(instance):
    """Test Piped instance"""
    try:
        r = requests.get(f'{instance}/streams/{TEST_ID}', timeout=10)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        data = r.json()
        streams = data.get('audioStreams', [])
        if not streams:
            return None, "No audio streams"
        streams.sort(key=lambda x: int(x.get('bitrate', 0)), reverse=True)
        return streams[0].get('url'), f"OK ({len(streams)} streams)"
    except Exception as e:
        return None, str(e)[:60]


def try_download(url, label):
    """Try to download audio via ffmpeg"""
    mp3 = f'{TEMP}/test_{label}.mp3'
    try:
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', url, '-vn', '-ar', '44100',
             '-ac', '2', '-b:a', '128k', mp3, '-t', '30'],  # only 30 sec for test
            capture_output=True, timeout=60
        )
        if os.path.exists(mp3) and os.path.getsize(mp3) > 10000:
            size = os.path.getsize(mp3)
            os.remove(mp3)
            return True, f"{size//1024} KB"
        return False, "ffmpeg failed"
    except Exception as e:
        return False, str(e)[:50]


print("=== Testing Alternative Download Sources ===")
print(f"Test song: Kesariya ({TEST_ID})")
print()

working_url = None
working_label = None

# Test Invidious
print("--- INVIDIOUS INSTANCES ---")
for inst in INVIDIOUS_INSTANCES:
    stream_url, status = test_invidious(inst)
    if stream_url:
        ok, detail = try_download(stream_url, 'invidious')
        if ok:
            print(f"  ✅ {inst}: {status} | Download: {detail}")
            working_url = stream_url
            working_label = inst
            break
        else:
            print(f"  ⚠️  {inst}: {status} | Download FAILED: {detail}")
    else:
        print(f"  ❌ {inst}: {status}")
    time.sleep(0.5)

print()
print("--- PIPED INSTANCES ---")
for inst in PIPED_INSTANCES:
    stream_url, status = test_piped(inst)
    if stream_url:
        ok, detail = try_download(stream_url, 'piped')
        if ok:
            print(f"  ✅ {inst}: {status} | Download: {detail}")
            if not working_url:
                working_url = stream_url
                working_label = inst
            break
        else:
            print(f"  ⚠️  {inst}: {status} | Download FAILED: {detail}")
    else:
        print(f"  ❌ {inst}: {status}")
    time.sleep(0.5)

print()
if working_url:
    print(f"RESULT: Found working source: {working_label}")
else:
    print("RESULT: No working source found — cookies required")
