import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def get_likes_stats(df):
    total_likes = len(df)
    
    # Infer target account from title if possible
    # Title format often included "You liked [Account]'s photo" (older) or just account name
    # We will try to clean 'target_account'
    
    # Simple logic: assume title IS the account or contains it.
    # Group by title to see "Most Liked Accounts"
    
    top_accounts = df['target_account'].value_counts().head(10)
    
    return total_likes, top_accounts

def get_comments_stats(df):
    total_comments = len(df)
    return total_comments

def likes_timeline(df):
    daily_timeline = df.groupby(df['date'].dt.date).count()['timestamp'].reset_index()
    daily_timeline.columns = ['date', 'count']
    return daily_timeline

def comments_timeline(df):
    daily_timeline = df.groupby(df['date'].dt.date).count()['timestamp'].reset_index()
    daily_timeline.columns = ['date', 'count']
    return daily_timeline
