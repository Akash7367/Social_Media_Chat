import instaloader
import pandas as pd
import requests
import re
import json
import os
from datetime import datetime, timedelta


# ──────────────────────────────────────────────
#  CACHING (file-based, 6-hour TTL)
# ──────────────────────────────────────────────
CACHE_DIR = os.path.join(os.path.dirname(__file__), "uploads", "ig_cache")
CACHE_TTL_HOURS = 6


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(username):
    return os.path.join(CACHE_DIR, f"{username.lower()}.json")


def _load_cache(username):
    """Return cached profile dict if fresh, else None."""
    path = _cache_path(username)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_time = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_time < timedelta(hours=CACHE_TTL_HOURS):
            print(f"[Cache] HIT for {username}")
            return data
        else:
            print(f"[Cache] EXPIRED for {username}")
            return None
    except Exception as e:
        print(f"[Cache] Read error: {e}")
        return None


def _save_cache(username, profile_data):
    """Save profile data to file cache."""
    _ensure_cache_dir()
    try:
        profile_data["_cached_at"] = datetime.now().isoformat()
        with open(_cache_path(username), "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)
        print(f"[Cache] SAVED for {username}")
    except Exception as e:
        print(f"[Cache] Write error: {e}")


# ──────────────────────────────────────────────
#  LAYER 3: MOCK / DEMO DATA (last resort)
# ──────────────────────────────────────────────
def get_mock_data(username):
    print(f"[Mock] Generating demo data for {username}")
    profile_data = {
        "username": username,
        "profile_pic_url": "https://cdn-icons-png.flaticon.com/512/1077/1077114.png",
        "followers": 12500,
        "following": 450,
        "uploads": 120,
        "full_name": f"{username} (Demo)",
        "biography": "This is a demo profile generated because live fetching was rate-limited.\n\n❤️ Love Coding | 📷 Photography | ✈️ Travel",
        "external_url": f"https://instagram.com/{username}",
    }

    posts_data = []
    base_time = datetime.now()
    for i in range(50):
        likes = 100 + (i * 5) + (i % 7 * 20)
        comments = 5 + (i % 5 * 2)
        posts_data.append({
            "timestamp": base_time - timedelta(days=i * 2),
            "likes": likes,
            "comments": comments,
            "caption": f"Sample caption for post {i} #demo #instagram",
            "url": "https://via.placeholder.com/600",
            "shortcode": f"code_{i}",
            "is_video": (i % 5 == 0),
        })

    df = pd.DataFrame(posts_data)
    stats = {
        "engagement_rate": 5.4,
        "average_likes": 250,
        "average_comments": 20,
        "posts_fetched": 50,
    }
    return profile_data, df, stats


# ──────────────────────────────────────────────
#  LAYER 1: INSTALOADER (best quality)
# ──────────────────────────────────────────────
def _fetch_via_instaloader(username):
    """
    Returns (profile_data_dict, instaloader_profile_obj) or (None, None).
    The profile_obj is needed to iterate posts later.
    """
    try:
        print(f"[Layer 1] Trying Instaloader for {username}...")
        L = instaloader.Instaloader(
            max_connection_attempts=1,
            request_timeout=10,
            fatal_status_codes=[429],
        )
        L.context.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"[Layer 1] SUCCESS — Instaloader fetched profile for {username}")

        data = {
            "username": profile.username,
            "profile_pic_url": profile.profile_pic_url,
            "followers": profile.followers,
            "following": profile.followees,
            "uploads": profile.mediacount,
            "full_name": profile.full_name,
            "biography": profile.biography or "",
            "external_url": profile.external_url or f"https://instagram.com/{username}",
        }
        return data, profile

    except Exception as e:
        print(f"[Layer 1] FAILED — {e}")
        return None, None


# ──────────────────────────────────────────────
#  LAYER 2: HTML META TAG SCRAPING (fallback)
# ──────────────────────────────────────────────
def _parse_count(text):
    """Parse '12.5K' / '1.2M' / '1,234' style strings into int."""
    text = text.strip().replace(",", "")
    try:
        if "M" in text.upper():
            return int(float(text.upper().replace("M", "")) * 1_000_000)
        elif "K" in text.upper():
            return int(float(text.upper().replace("K", "")) * 1_000)
        else:
            return int(text)
    except (ValueError, TypeError):
        return 0


def _fetch_via_html(username):
    """
    Scrape Instagram's public HTML page for meta-tag data.
    Returns profile_data dict or None.
    """
    try:
        print(f"[Layer 2] Trying HTML scraping for {username}...")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        r = requests.get(
            f"https://www.instagram.com/{username}/",
            headers=headers,
            timeout=15,
            allow_redirects=True,
        )

        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        html = r.text
        print(f"[Layer 2] Got HTTP 200, parsing HTML ({len(html)} chars)...")

        # ── Parse og:description for counts ──
        # Format: "12.5K Followers, 450 Following, 120 Posts - ..."
        followers = 0
        following = 0
        uploads = 0

        meta_desc = re.search(
            r'<meta\s+(?:property|name)=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE,
        )
        if not meta_desc:
            # Try reversed attribute order
            meta_desc = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:description["\']',
                html, re.IGNORECASE,
            )

        if meta_desc:
            desc_text = meta_desc.group(1)
            print(f"[Layer 2] og:description = {desc_text[:120]}")
            parts = desc_text.split(",")
            for part in parts:
                part_clean = part.strip()
                if "Followers" in part_clean:
                    followers = _parse_count(part_clean.split(" ")[0])
                elif "Following" in part_clean:
                    following = _parse_count(part_clean.split(" ")[0])
                elif "Posts" in part_clean:
                    uploads = _parse_count(part_clean.split(" ")[0])
        else:
            print("[Layer 2] og:description NOT found")

        # ── Parse og:image for profile pic ──
        profile_pic = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"  # default
        pic_match = re.search(
            r'<meta\s+(?:property|name)=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE,
        )
        if not pic_match:
            pic_match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:image["\']',
                html, re.IGNORECASE,
            )
        if pic_match:
            profile_pic = pic_match.group(1)
            print(f"[Layer 2] Found og:image")

        # ── Parse og:title for full name ──
        full_name = username
        title_match = re.search(
            r'<meta\s+(?:property|name)=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE,
        )
        if not title_match:
            title_match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:title["\']',
                html, re.IGNORECASE,
            )
        if title_match:
            raw_title = title_match.group(1)
            # Format is usually "Full Name (@username) • Instagram photos and videos"
            name_match = re.match(r'^(.+?)\s*\(@', raw_title)
            if name_match:
                full_name = name_match.group(1).strip()
            else:
                # Fallback: take text before bullet/dash
                full_name = raw_title.split("•")[0].split("—")[0].split("|")[0].strip()
            print(f"[Layer 2] Parsed full name: {full_name}")

        # Check if we got ANY real data
        if followers == 0 and following == 0 and uploads == 0:
            print("[Layer 2] No counts found — HTML scraping yielded no useful data")
            return None

        data = {
            "username": username,
            "profile_pic_url": profile_pic,
            "followers": int(followers),
            "following": int(following),
            "uploads": int(uploads),
            "full_name": full_name,
            "biography": "",  # Not available via meta tags
            "external_url": f"https://instagram.com/{username}",
        }
        print(f"[Layer 2] SUCCESS — Followers: {followers}, Following: {following}, Posts: {uploads}")
        return data

    except Exception as e:
        print(f"[Layer 2] FAILED — {e}")
        return None


# ──────────────────────────────────────────────
#  FETCH POSTS (from Instaloader profile object)
# ──────────────────────────────────────────────
def _fetch_posts(profile_obj, followers_count):
    """
    Attempt to fetch recent posts from an Instaloader profile object.
    Returns (DataFrame, stats_dict) or (None, None) on failure.
    """
    if profile_obj is None:
        return None, None

    try:
        print(f"[Posts] Fetching up to 50 posts...")
        posts_data = []
        limit = 50
        count = 0
        total_likes = 0
        total_comments = 0

        for post in profile_obj.get_posts():
            if count >= limit:
                break
            posts_data.append({
                "timestamp": post.date,
                "likes": post.likes,
                "comments": post.comments,
                "caption": post.caption if post.caption else "",
                "url": post.url,
                "shortcode": post.shortcode,
                "is_video": post.is_video,
            })
            total_likes += post.likes
            total_comments += post.comments
            count += 1

        if count == 0:
            return None, None

        df = pd.DataFrame(posts_data)

        engagement_rate = 0
        if count > 0 and followers_count > 0:
            engagement_rate = ((total_likes + total_comments) / count) / followers_count * 100

        stats = {
            "engagement_rate": engagement_rate,
            "average_likes": total_likes / count,
            "average_comments": total_comments / count,
            "posts_fetched": count,
        }

        print(f"[Posts] SUCCESS — Fetched {count} posts")
        return df, stats

    except Exception as e:
        print(f"[Posts] FAILED (likely rate limited) — {e}")
        return None, None


# ──────────────────────────────────────────────
#  MAIN ENTRY POINT
# ──────────────────────────────────────────────
def fetch_profile_data(username):
    """
    Fetch Instagram profile data using a 3-layer fallback strategy.

    Returns: (profile_data, posts_df, stats, data_source)
        data_source: "live" | "cached" | "partial" | "demo"
    """
    username = username.strip().lstrip("@").lower()

    # ── Check cache first ──
    cached = _load_cache(username)
    if cached:
        cached.pop("_cached_at", None)
        _, mock_df, mock_stats = get_mock_data(username)
        return cached, mock_df, mock_stats, "cached"

    # ── Layer 1: Instaloader ──
    profile_data, profile_obj = _fetch_via_instaloader(username)

    if profile_data:
        _save_cache(username, profile_data.copy())

        # Try fetching real posts
        posts_df, posts_stats = _fetch_posts(profile_obj, profile_data["followers"])
        if posts_df is not None:
            return profile_data, posts_df, posts_stats, "live"
        else:
            # Real profile but mock posts
            _, mock_df, mock_stats = get_mock_data(username)
            return profile_data, mock_df, mock_stats, "partial"

    # ── Layer 2: HTML Meta Tag Scraping ──
    profile_data = _fetch_via_html(username)

    if profile_data:
        _save_cache(username, profile_data.copy())
        _, mock_df, mock_stats = get_mock_data(username)
        return profile_data, mock_df, mock_stats, "partial"

    # ── Layer 3: Full Mock ──
    profile_data, mock_df, mock_stats = get_mock_data(username)
    return profile_data, mock_df, mock_stats, "demo"


# ──────────────────────────────────────────────
#  ANALYTICS HELPERS (unchanged)
# ──────────────────────────────────────────────
def calculate_activity_metrics(df):
    if df.empty:
        return {"posts_per_day": 0, "posts_per_week": 0, "posts_per_month": 0}

    earliest_date = df["timestamp"].min()
    latest_date = df["timestamp"].max()
    days_diff = (latest_date - earliest_date).days
    if days_diff < 1:
        days_diff = 1

    posts_per_day = len(df) / days_diff
    posts_per_week = posts_per_day * 7
    posts_per_month = posts_per_day * 30

    return {
        "posts_per_day": posts_per_day,
        "posts_per_week": posts_per_week,
        "posts_per_month": posts_per_month,
    }


def get_activity_charts_data(df):
    daily_counts = df.groupby(df["timestamp"].dt.date).size().reset_index(name="count")

    df_indexed = df.set_index("timestamp")
    weekly_counts = df_indexed.resample("W").size().reset_index(name="count")
    monthly_counts = df_indexed.resample("M").size().reset_index(name="count")

    return daily_counts, weekly_counts, monthly_counts


def get_top_content(df):
    if df.empty:
        return None, None

    most_liked = df.loc[df["likes"].idxmax()]
    most_commented = df.loc[df["comments"].idxmax()]

    return most_liked, most_commented
