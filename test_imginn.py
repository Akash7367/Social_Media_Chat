import requests
import re

username = "codewithharry"
url = f"https://imginn.com/{username}/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Testing Imginn for {username}...")
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        # Check for followers
        print(r.text[:500])
        followers = re.search(r'<span class="num">([^<]+)</span>', r.text)
        if followers:
            print(f"Found something: {followers.group(1)}")
    else:
        print("Imginn failed.")
except Exception as e:
    print(f"Error: {e}")
