import requests
import re

username = "codewithharry"
url = f"https://www.picuki.com/profile/{username}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Testing Picuki for {username}...")
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        # Extract Followers
        # <span class="counts">123</span> Follower
        followers_match = re.search(r'class="followed_by">(\d+)</span>', r.text) # Check pattern later
        # Actually picuki structure is usually: <span class="counts">1.5M</span>
        
        # Let's just print a snippet to check structure
        print("Snippet:")
        print(r.text[:1000])
        
        if "Followers" in r.text or "followed_by" in r.text:
            print("Found Followers text!")
    else:
        print("Picuki failed.")
except Exception as e:
    print(f"Error: {e}")
