import re
import pandas as pd

def preprocess(data):
    # Tuple of (regex_split, date_format, is_ios)
    # The patterns are prioritized. iOS has brackets, distinctive. 12h has AM/PM. 24h is standard
    
    patterns = [
        {
            'name': 'ios',
            # [26/01/23, 15:30:00] 
            # Note: Sometimes there is a char after ] like space.
            'regex': r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\]\s?',
            'format_str': '%d/%m/%y, %H:%M:%S',
            'dayfirst': True
        },
        {
            'name': '12h',
            # 12/31/23, 11:59 PM - 
            'regex': r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[apAP][mM]\s-\s',
            'format_str': '%m/%d/%y, %I:%M %p',
            'dayfirst': False
        },
        {
            'name': '24h',
            # 26/01/23, 15:30 - 
            'regex': r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s',
            'format_str': '%d/%m/%y, %H:%M',
            'dayfirst': True
        }
    ]
    
    selected_pattern = None
    # We check a larger subset to be sure, or the whole text?
    # Checking first few matches is safer.
    subset = data[:4000] 
    
    for p in patterns:
        if re.search(p['regex'], subset):
            selected_pattern = p
            # Priority: iOS > 12h > 24h. 
            # But 12h and 24h might overlap if AM/PM is missing? 
            # 24h regex requires " - ". 12h regex requires "AM/PM - ". 
            # So they are distinct enough.
            break
            
    if not selected_pattern:
        # Default fallback
        selected_pattern = patterns[2]
        
    pattern = selected_pattern['regex']
    
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    
    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Helper to clean date string
    def clean_date_str(d):
        d = d.strip()
        # Remove regex artifacts
        # iOS: [ and ]
        if d.startswith('['):
            d = d.replace('[', '').replace(']', '')
        # Separator " - "
        d = d.replace(' -', '')
        # Extra spaces
        return d.strip()
        
    df['message_date'] = df['message_date'].apply(clean_date_str)
    
    # Date Parsing logic
    # Try the specific format first
    try:
        # Check if year is 4 digits in data, format uses %y (2 digits). 
        # Pandas manages %y/%Y confusion well usually but specific format is better.
        # We try strict format first.
        df['date'] = pd.to_datetime(df['message_date'], format=selected_pattern['format_str'], errors='coerce')
    except:
        pass
        
    # If many failures, retry with loose parsing + dayfirst hint
    if df['date'].isna().sum() > len(df) * 0.1: # if more than 10% failed
        try:
            df['date'] = pd.to_datetime(df['message_date'], dayfirst=selected_pattern['dayfirst'], errors='coerce')
        except:
             pass

    df.dropna(subset=['date'], inplace=True)
    
    users = []
    msgs = []
    
    for message in df['user_message']:
        # Split user and message
        # Regex to find "User: " at start of message
        entry = re.split(r'([\w\W]+?):\s', message)
        if len(entry) > 1:
            users.append(entry[1])
            msgs.append(" ".join(entry[2:]))
        else:
            users.append('group_notification')
            msgs.append(entry[0])

    df['user'] = users
    df['message'] = msgs
    df.drop(columns=['user_message', 'message_date'], inplace=True)

    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    df['only_date'] = df['date'].dt.date

    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period

    return df
