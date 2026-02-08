from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
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

def analyze_toxicity(selected_user, df):
    # Valid "Bad Words" List (English + Hindi/Hinglish)
    # Added common Romanized Hindi abusive words
    BAD_WORDS = [
        "stupid", "idiot", "shut up", "damn", "hell", "useless", "dumb", "crazy", "nonsense", "rubbish", "mad",
        "pagal", "kutta", "kamina", "saala", "bhaad", "besharam", "behaya", "ullu", "gadha", "bewakoof", "nalayak",
        "chutiya", "gandu", "bhosdike", "bsdk", "mc", "bc", "behenchod", "madarchod", "harami", "kamine"
    ]
    
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
        
    toxic_data = []
    
    # Iterate through users
    for user in df['user'].unique():
        user_msgs = df[df['user'] == user]
        bad_count = 0
        abusive_messages = []
        
        for index, row in user_msgs.iterrows():
            msg_lower = str(row['message']).lower()
            triggered_words = [word for word in BAD_WORDS if word in msg_lower.split()]
            
            if triggered_words:
                bad_count += len(triggered_words)
                abusive_messages.append({
                    'date': row['date'],
                    'message': row['message'],
                    'words': triggered_words
                })
        
        if bad_count > 0:
            # Score Calculation (Heuristic)
            # 1 = Good, 10 = Abusive
            # Base 1. Each bad word adds 0.5? Cap at 10.
            score = 1 + (bad_count * 0.5)
            if score > 10: score = 10
            
            toxic_data.append({
                'user': user,
                'score': round(score, 1),
                'count': bad_count,
                'messages': abusive_messages
            })
            
    # Sort by Score Descending
    toxic_data = sorted(toxic_data, key=lambda x: x['score'], reverse=True)
    
    return toxic_data
