import json
import pandas as pd
from datetime import datetime

def parse_likes(json_file):
    try:
        data = json.load(json_file)
        
        # Structure varies, typically:
        # { "likes_media_likes": [ { "title": "...", "string_list_data": [ { "timestamp": ... } ] } ] }
        # Or just a list. We need to handle common structure.
        
        likes_data = []
        
        # Check for key wrapping
        if isinstance(data, dict):
            if 'likes_media_likes' in data:
                 items = data['likes_media_likes']
            else:
                 # Try finding any list value
                 items = []
                 for k, v in data.items():
                     if isinstance(v, list):
                         items = v
                         break
        elif isinstance(data, list):
            items = data
        else:
            return pd.DataFrame() # Unknown formats

        for item in items:
            title = item.get('title', 'Unknown')
            
            # Timestamp extraction
            # usually in string_list_data list
            string_list = item.get('string_list_data', [])
            for s in string_list:
                timestamp = s.get('timestamp')
                href = s.get('href', '')
                
                if timestamp:
                    likes_data.append({
                        'title': title,
                        'timestamp': timestamp,
                        'href': href
                    })

        df = pd.DataFrame(likes_data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            df['target_account'] = df['title'] # Often 'title' is "User liked [Account]'s post" or similar
        
        return df
    except Exception as e:
        print(f"Error parsing likes: {e}")
        return pd.DataFrame()

def parse_comments(json_file):
    try:
        data = json.load(json_file)
        
        # Structure: { "comments_media_comments": [ { "string_list_data": [...], "title": ... } ] }
        
        comments_data = []
        
        if isinstance(data, dict):
             if 'comments_media_comments' in data:
                 items = data['comments_media_comments']
             else:
                 items = []
                 for k, v in data.items():
                     if isinstance(v, list):
                         items = v
                         break
        elif isinstance(data, list):
             items = data
        else:
            return pd.DataFrame()

        for item in items:
             # structure varies
             string_list = item.get('string_list_data', [])
             for s in string_list:
                 timestamp = s.get('timestamp')
                 value = s.get('value', '') # Comment text
                 
                 if timestamp:
                     comments_data.append({
                         'timestamp': timestamp,
                         'comment': value
                     })
                     
        df = pd.DataFrame(comments_data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            
        return df
    except Exception as e:
        print(f"Error parsing comments: {e}")
        return pd.DataFrame()
