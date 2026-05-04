from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # 1. Fetch number of messages
    num_messages = df.shape[0]

    # 2. Fetch number of words
    words = []
    for message in df['message']:
        words.extend(message.split())

    # 3. Fetch number of media messages
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    # 4. Fetch number of links shared
    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head()
    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'})
    return x, df

def create_wordcloud(selected_user, df):
    f = open('stop_words.txt', 'r')
    stop_words = f.read()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)

    # Create WordCloud with smaller dimensions and better resolution
    wc = WordCloud(width=500, height=300, min_font_size=10, background_color='white')
    temp['message'] = temp['message'].apply(remove_stop_words)
    df_wc = wc.generate(temp['message'].str.cat(sep=" "))
    return df_wc

def most_common_words(selected_user, df):
    f = open('stop_words.txt', 'r')
    stop_words = f.read()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    words = []
    for message in temp['message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        # emoji.emoji_list(message) returns list of specific dicts
        for c in message:
             if c in emoji.EMOJI_DATA:
                 emojis.append(c)

    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
    if emoji_df.empty:
         return pd.DataFrame(columns=['emoji', 'count'])
    emoji_df.columns = ['emoji', 'count']
    return emoji_df

def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))

    timeline['time'] = time
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    return daily_timeline

def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
    return user_heatmap

def sentiment_analysis(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    analyzer = SentimentIntensityAnalyzer()
    
    # Analyze message sentiment
    df['sentiment'] = df['message'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    
    # Categorize
    def get_analysis(score):
        if score >= 0.05:
            return 'Positive'
        elif score <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
            
    df['sentiment_category'] = df['sentiment'].apply(get_analysis)
    
    sentiment_counts = df['sentiment_category'].value_counts().reset_index()
    sentiment_counts.columns = ['category', 'count']
    
    return sentiment_counts, df

def _load_bad_words():
    path = os.path.join(os.path.dirname(__file__), 'bad_words.txt')
    if not os.path.isfile(path):
        return []
    terms = []
    seen = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            t = line.lower()
            if t not in seen:
                seen.add(t)
                terms.append(t)
    return terms

def _bad_word_triggers(msg_lower, terms):
    """Match multi-word phrases first (masked), then whole tokens for single words."""
    if not terms or not msg_lower:
        return []
    phrases = sorted([t for t in terms if ' ' in t], key=len, reverse=True)
    singles = [t for t in terms if ' ' not in t]
    masked = msg_lower
    found = []
    for p in phrases:
        c = masked.count(p)
        if c:
            found.extend([p] * c)
            masked = masked.replace(p, ' ' * len(p))
    punct = '.,!?;:()[]{}"\'-'
    tokens = []
    for raw in masked.split():
        w = raw.strip(punct).lower()
        if w:
            tokens.append(w)
    for s in singles:
        n = tokens.count(s)
        if n:
            found.extend([s] * n)
    return found

def analyze_toxicity(selected_user, df):
    bad_terms = _load_bad_words()
    if not bad_terms:
        return []

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    toxic_data = []

    # PASS 1: Collect raw bad word counts per user
    for user in df['user'].unique():
        user_msgs = df[df['user'] == user]
        bad_count = 0
        abusive_messages = []

        for index, row in user_msgs.iterrows():
            msg_lower = str(row['message']).lower()
            triggered_words = _bad_word_triggers(msg_lower, bad_terms)

            if triggered_words:
                bad_count += len(triggered_words)
                abusive_messages.append({
                    'date': row['date'],
                    'message': row['message'],
                    'words': triggered_words
                })

        if bad_count > 0:
            toxic_data.append({
                'user': user,
                'count': bad_count,
                'messages': abusive_messages
            })

    if not toxic_data:
        return []

    # PASS 2: Relative Normalization — most toxic user gets 10.0, others scale proportionally
    # Formula: score = 1 + (user_count / max_count) * 9
    # Example: max=200 words → 10.0 | 100 words → 5.5 | 50 words → 3.25
    max_count = max(entry['count'] for entry in toxic_data)

    for entry in toxic_data:
        normalized = entry['count'] / max_count        # 0.0 to 1.0
        score = 1 + (normalized * 9)                   # 1.0 to 10.0
        entry['score'] = round(score, 1)

    # Sort by score descending (most toxic first)
    toxic_data = sorted(toxic_data, key=lambda x: x['score'], reverse=True)

    return toxic_data
