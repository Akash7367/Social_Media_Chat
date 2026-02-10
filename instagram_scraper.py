import instaloader
import pandas as pd
import requests
import re
import json
from datetime import datetime, timedelta


def get_mock_data(username):
    print(f"Generating mock data for {username}")
    # Sample Profile
    profile_data = {
        "username": username,
        "profile_pic_url": "https://cdn-icons-png.flaticon.com/512/1077/1077114.png", # Generic user icon
        "followers": 12500,
        "following": 450,
        "uploads": 120,
        "full_name": f"{username} (Demo)",
        "biography": "This is a demo profile generated because live fetching was rate-limited. \n\n❤️ Love Coding | 📷 Photography | ✈️ Travel",
        "external_url": f"https://instagram.com/{username}"
    }
    
    # Sample Posts
    posts_data = []
    base_time = datetime.now()
    
    # Generate 50 sample posts
    for i in range(50):
        # Randomize complexity
        likes = 100 + (i * 5) + (i % 7 * 20)
        comments = 5 + (i % 5 * 2)
        
        posts_data.append({
            "timestamp": base_time - timedelta(days=i*2), # Every 2 days
            "likes": likes,
            "comments": comments,
            "caption": f"Sample caption for post {i} #demo #instagram",
            "url": "https://via.placeholder.com/600", # Placeholder image
            "shortcode": f"code_{i}",
            "is_video": (i % 5 == 0) # Every 5th post is video
        })
        
    df = pd.DataFrame(posts_data)
    
    stats = {
        "engagement_rate": 5.4,
        "average_likes": 250,
        "average_comments": 20,
        "posts_fetched": 50
    }
    
    return profile_data, df, stats, True  # Added True for is_demo

def fetch_profile_data(username):
    # Initialize with conservative settings
    L = instaloader.Instaloader(max_connection_attempts=1, request_timeout=10, fatal_status_codes=[429])
    
    # Generic User Agent
    L.context.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    profile = None
    real_profile_data = None
    is_demo = False
    
    # 1. Try to fetch PROFILE METADATA (Low risk)
    try:
        print(f"Attempting to fetch profile for {username} via Instaloader...")
        profile = instaloader.Profile.from_username(L.context, username)
        print("Instaloader success.")
        
        real_profile_data = {
            "username": profile.username,
            "profile_pic_url": profile.profile_pic_url,
            "followers": profile.followers,
            "following": profile.followees,
            "uploads": profile.mediacount,
            "full_name": profile.full_name,
            "biography": profile.biography,
            "external_url": profile.external_url
        }
    except Exception as e:
        print(f"Error fetching profile metadata via Instaloader: {e}")
        # FALLBACK: Try requests + regex (HTML scraping)
        try:
            print("Attempting HTML scraping fallback...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            r = requests.get(f"https://www.instagram.com/{username}/", headers=headers, timeout=10)
            
            if r.status_code == 200:
                print("HTML scraping connection successful.")
                
                # Meta description for stats
                meta_desc = re.search(r'<meta property="og:description" content="([^"]+)"', r.text)
                followers = 0
                following = 0
                uploads = 0
                
                if meta_desc:
                    desc_text = meta_desc.group(1)
                    parts = desc_text.split(',')
                    for part in parts:
                        if 'Followers' in part:
                            followers_str = part.strip().split(' ')[0]
                            # Handle K/M
                            if 'M' in followers_str: followers = float(followers_str.replace('M','')) * 1000000
                            elif 'K' in followers_str: followers = float(followers_str.replace('K','')) * 1000
                            else: followers = int(followers_str.replace(',',''))
                        elif 'Following' in part:
                            try: following = int(part.strip().split(' ')[0])
                            except: pass
                        elif 'Posts' in part:
                            try: uploads = int(part.strip().split(' ')[0])
                            except: pass
                            
                # Profile Pic (og:image)
                pic_match = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
                if pic_match:
                    profile_pic = pic_match.group(1)
                    print(f"Found profile pic via og:image: {profile_pic}")
                else:
                    # Try searching for the JSON object in sharedData if og:image fails
                    print("og:image not found, searching in sharedData...")
                    shared_data_match = re.search(r'window\._sharedData\s*=\s*({.+?});', r.text)
                    if shared_data_match:
                         # This is complex to parse robustly with regex, but let's try a simple extraction for pic
                         # The key usually looks like "profile_pic_url":"..."
                         pic_json_match = re.search(r'"profile_pic_url":"([^"]+)"', shared_data_match.group(1))
                         if pic_json_match:
                             # Decode unicode escapes if any
                             profile_pic = bytes(pic_json_match.group(1), "utf-8").decode("unicode_escape")
                         else:
                             profile_pic = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
                    else:
                        profile_pic = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"

                real_profile_data = {
                    "username": username,
                    "profile_pic_url": profile_pic,
                    "followers": int(followers),
                    "following": int(following),
                    "uploads": int(uploads),
                    "full_name": f"{username}",
                    "biography": "Bio partially fetched via fallback.",
                    "external_url": f"https://instagram.com/{username}"
                }
            else:
                raise Exception(f"HTTP {r.status_code}")
                
        except Exception as html_e:
            print(f"HTML Scraping failed: {html_e}")
            # Final Fallback to Mock
            p, d, s, _ = get_mock_data(username) # Unpack 4, return 4
            return p, d, s, True

    # 2. Try to fetch POSTS (High risk)
    try:
        posts_data = []
        limit = 50 
        count = 0
        total_likes = 0
        total_comments = 0
        
        for post in profile.get_posts():
            if count >= limit:
                break
            
            posts_data.append({
                "timestamp": post.date,
                "likes": post.likes,
                "comments": post.comments,
                "caption": post.caption if post.caption else "",
                "url": post.url, 
                "shortcode": post.shortcode,
                "is_video": post.is_video
            })
            
            total_likes += post.likes
            total_comments += post.comments
            count += 1
            
        df = pd.DataFrame(posts_data)
        
        # Calculate Real Stats
        if count > 0 and profile.followers > 0:
            engagement_rate = ((total_likes + total_comments) / count) / profile.followers * 100
        else:
            engagement_rate = 0
            
        stats = {
            "engagement_rate": engagement_rate,
            "average_likes": total_likes / count if count else 0,
            "average_comments": total_comments / count if count else 0,
            "posts_fetched": count
        }
        
        return real_profile_data, df, stats, False # Real Data

    except Exception as e:
        print(f"Error fetching posts (Rate Limit?): {e}")
        # 3. FALLBACK: Real Profile + Mock Posts
        print("Falling back to MOCK POSTS but REAL PROFILE.")
        _, mock_df, mock_stats, _ = get_mock_data(username)
        return real_profile_data, mock_df, mock_stats, True # Partial Demo

def calculate_activity_metrics(df):
    if df.empty:
        return {}

    # Activity Graphs Data
    # 1. Posts per Day (Frequency over time? Or Day of Week?)
    # Screenshot shows "0.08 Posts per day", "0.58 Posts per week". 
    # This implies a rate. Total Posts / Days Range.
    
    earliest_date = df['timestamp'].min()
    latest_date = df['timestamp'].max()
    days_diff = (latest_date - earliest_date).days
    if days_diff < 1: 
        days_diff = 1
        
    posts_per_day = len(df) / days_diff
    posts_per_week = posts_per_day * 7
    posts_per_month = posts_per_day * 30
    
    return {
        "posts_per_day": posts_per_day,
        "posts_per_week": posts_per_week,
        "posts_per_month": posts_per_month
    }

def get_activity_charts_data(df):
    # Prepare data for line charts
    # We need counts aggregated by Day, Week, Month for the timeline
    
    # Daily Count
    daily_counts = df.groupby(df['timestamp'].dt.date).size().reset_index(name='count')
    
    # Weekly Count (resample)
    df = df.set_index('timestamp')
    weekly_counts = df.resample('W').size().reset_index(name='count')
    
    # Monthly Count
    monthly_counts = df.resample('M').size().reset_index(name='count')
    
    return daily_counts, weekly_counts, monthly_counts

def get_top_content(df):
    if df.empty:
        return None, None
        
    most_liked = df.loc[df['likes'].idxmax()]
    most_commented = df.loc[df['comments'].idxmax()]
    
    return most_liked, most_commented
