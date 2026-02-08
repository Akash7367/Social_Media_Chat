import requests
import re

username = "codewithharry"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

print(f"Testing connection for {username}...")
try:
    r = requests.get(f"https://www.instagram.com/{username}/", headers=headers, timeout=10)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        print("Response Snippet (first 500 chars):")
        print(r.text[:500])
        
        meta = re.search(r'<meta property="og:description" content="([^"]+)"', r.text)
        if meta:
            print(f"FOUND META: {meta.group(1)}")
        else:
            print("NO META DESCRIPTION FOUND. Probably Login Page.")
            if "Login" in r.text or "Log In" in r.text:
                print("Detected Login Page.")
    else:
        print("Request failed.")
except Exception as e:
    print(f"Exception: {e}")
