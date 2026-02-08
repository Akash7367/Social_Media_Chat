from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from dotenv import load_dotenv
load_dotenv()

import os
import secrets
import pandas as pd
import preprocessor, helper
import instagram_scraper
import matplotlib
matplotlib.use('Agg') # Set backend to Agg for non-interactive plotting
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)
# Use a separate SECRET_KEY for production to persist sessions
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_fallback")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# GEMINI CONFIG
# API Key is loaded from .env automatically by load_dotenv()
if "GEMINI_API_KEY" not in os.environ:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")
from gemini_helper import GeminiChat
chatbot = GeminiChat()

# Helper to convert plot to base64
def get_base64_plot(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig) 
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/whatsapp')
def whatsapp():
    return render_template('whatsapp.html')

@app.route('/instagram')
def instagram():
    return render_template('instagram.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/analyze/instagram', methods=['POST'])
def analyze_instagram():
    username = request.form.get('username')
    
    # Unpack 4 values now
    profile_data, posts_df, stats, is_demo = instagram_scraper.fetch_profile_data(username)
    
    if not profile_data:
        flash("Error fetching profile. It might be private or rate limited.", "error")
        return redirect(url_for('instagram'))
    
    activity_metrics = instagram_scraper.calculate_activity_metrics(posts_df)
    
    # Generate Graphs
    graphs = {}
    
    # Daily
    if not posts_df.empty:
        daily_counts, weekly_counts, monthly_counts = instagram_scraper.get_activity_charts_data(posts_df)
        
        # Plot Daily
        fig, ax = plt.subplots(figsize=(5, 2.5)) # Reduced size
        ax.plot(daily_counts['timestamp'], daily_counts['count'], color='#fd7e14', linewidth=3)
        ax.axis('on')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False) # Clean left spine too
        ax.tick_params(left=False) # Hide left ticks
        plt.tight_layout()
        graphs['daily_chart'] = get_base64_plot(fig)
        
        # Plot Weekly
        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(weekly_counts['timestamp'], weekly_counts['count'], color='#fd7e14', linewidth=3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False)
        plt.tight_layout()
        graphs['weekly_chart'] = get_base64_plot(fig)
        
        # Plot Monthly
        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(monthly_counts['timestamp'], monthly_counts['count'], color='#fd7e14', linewidth=3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False)
        plt.tight_layout()
        graphs['monthly_chart'] = get_base64_plot(fig)
        
    most_liked, most_commented = instagram_scraper.get_top_content(posts_df)
    top_content = {
        'most_liked': most_liked,
        'most_commented': most_commented
    }

    return render_template('instagram_result.html', 
                           profile=profile_data, 
                           stats=stats, 
                           activity=activity_metrics,
                           graphs=graphs,
                           top_content=top_content,
                           is_demo=is_demo)

# WhatsApp Logic
# For simplicity in this demo, we will process the file on every request or use a simple caching mechanism 
# (e.g., save DF to temporary pickle).
# Since session size is limited, we save the file path in session.

import re

@app.route('/analyze/whatsapp', methods=['POST'])
def analyze_whatsapp():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        session['filepath'] = filepath
        
        # VALIDATION: Check first few lines for WhatsApp pattern
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first few lines to validate
            head = [next(f) for _ in range(5)]
            
            # Reset pointer for processing
            f.seek(0)
            data = f.read()

        # Regex for standard WhatsApp date formats (dd/mm/yy or mm/dd/yy)
        # Matches: "12/05/2023, 10:30" or "[12/05/23, 10:30]"
        whatsapp_pattern = re.compile(r'^\[?\d{1,2}[/-]\d{1,2}[/-]\d{2,4},? \d{1,2}:\d{2}')
        
        is_valid = False
        for line in head:
            if whatsapp_pattern.match(line):
                is_valid = True
                break
        
        if not is_valid:
            # Invalid Format
            flash('This is not a whatsapp chat. Please upload only whatsapp chat!', 'warning')
            return redirect(url_for('whatsapp'))

        # Initial Processing to get user list
            
        df = preprocessor.preprocess(data)
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
             user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, "Overall")
        
        session['user_list'] = user_list
        
        # Default to Overall
        return render_whatsapp_result("Overall", df, user_list)

@app.route('/analyze/whatsapp_result', methods=['POST'])
def whatsapp_result_update():
    selected_user = request.form.get('user')
    filepath = session.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        flash("Session expired home. Please upload file again.", "error")
        return redirect(url_for('whatsapp'))
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read()
    df = preprocessor.preprocess(data)
    user_list = session.get('user_list', [])
    
    search_query = request.form.get('search_query')
    search_results = []
    
    if search_query:
        mask = df['message'].str.contains(search_query, case=False, na=False)
        search_df = df[mask]
        # Convert to dict for template
        for i, row in search_df.iterrows():
            search_results.append({
                'user': row['user'],
                'date': row['date'],
                'message': row['message']
            })
    
    return render_whatsapp_result(selected_user, df, user_list, search_results)

    return render_whatsapp_result(selected_user, df, user_list, search_results)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/send_message', methods=['POST'])
def send_message_route():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    # 1. FILE LOGGING (Guaranteed Backup)
    log_entry = f"--- New Message ---\nName: {name}\nEmail: {email}\nMessage: {message}\n-------------------\n"
    with open("messages_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    # 2. EMAIL SENDING (SMTP)
    mail_user = os.environ.get("MAIL_USERNAME")
    mail_pass = os.environ.get("MAIL_PASSWORD")
    
    if not mail_user or "your_email" in mail_user or not mail_pass:
        print("DEBUG: Email credentials not set. Message logged to file only.")
        flash("Message received! (Logged to system, Email config pending)", "success")
        return redirect(url_for('contact'))

    try:
        # construct email
        msg = MIMEMultipart()
        msg['From'] = mail_user
        msg['To'] = mail_user # Send to self
        msg['Subject'] = f"New Contact Form Message from {name}"
        
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(mail_user, mail_pass)
        text = msg.as_string()
        server.sendmail(mail_user, mail_user, text)
        server.quit()
        
        flash("Message sent successfully!", "success")
        
    except Exception as e:
        print(f"Error sending email: {e}")
        flash(f"Error sending email: {str(e)} (Logged to file)", "error")
        
    return redirect(url_for('contact'))

@app.route('/download_report')
def download_report():
    filepath = session.get('filepath')
    selected_user = session.get('selected_user', 'Overall')
    
    if not filepath or not os.path.exists(filepath):
        flash("Session expired. Please upload file again.", "error")
        return redirect(url_for('whatsapp'))
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read()
    
    # Re-process data
    df = preprocessor.preprocess(data)
    user_list = session.get('user_list', [])
    
    # Read CSS file to embed
    css_path = os.path.join(app.root_path, 'static', 'css', 'style.css')
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css_content = f.read()
        print(f"DEBUG: CSS Content Loaded. Length: {len(css_content)}")
    else:
        print(f"DEBUG: CSS File not found at {css_path}")

    # Render full HTML report with embedded CSS and special layout
    # Pass 'download_mode=True' to hide interactive elements
    # Pass 'parent_template' to switch to standalone layout
    html_content = render_whatsapp_result(
        selected_user, 
        df, 
        user_list, 
        download_mode=True, 
        css_content=css_content,
        parent_template="report_layout.html"
    )
    
    # Create HTML response
    response = make_response(html_content)
    # Correct Content-Disposition handling
    safe_filename = f"WhatsApp_Analysis_{selected_user}.html"
    response.headers["Content-Disposition"] = f"attachment; filename={safe_filename}"
    response.headers["Content-type"] = "text/html"
    return response

def render_whatsapp_result(selected_user, df, user_list, search_results=None, download_mode=False, css_content="", parent_template="base.html"):
    print(f"DEBUG: render_whatsapp_result called with download_mode={download_mode}")
    # Stats
    num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
    
    stats = {
        'num_messages': num_messages,
        'words': words,
        'num_media_messages': num_media_messages,
        'num_links': num_links
    }
    
    charts = {}
    
    # Monthly Timeline
    timeline = helper.monthly_timeline(selected_user, df)
    fig, ax = plt.subplots()
    ax.plot(timeline['time'], timeline['message'], color='green')
    plt.xticks(rotation='vertical')
    charts['monthly_timeline'] = get_base64_plot(fig)
    
    # Daily Timeline
    daily_timeline = helper.daily_timeline(selected_user, df)
    fig, ax = plt.subplots()
    ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
    plt.xticks(rotation='vertical')
    charts['daily_timeline'] = get_base64_plot(fig)
    
    # Activity Maps
    busy_day = helper.week_activity_map(selected_user, df)
    fig, ax = plt.subplots()
    ax.bar(busy_day.index, busy_day.values, color='purple')
    plt.xticks(rotation='vertical')
    charts['busy_day'] = get_base64_plot(fig)
    
    busy_month = helper.month_activity_map(selected_user, df)
    fig, ax = plt.subplots()
    ax.bar(busy_month.index, busy_month.values, color='orange')
    plt.xticks(rotation='vertical')
    charts['busy_month'] = get_base64_plot(fig)
    
    # Heatmap
    user_heatmap = helper.activity_heatmap(selected_user, df)
    fig, ax = plt.subplots()
    sns.heatmap(user_heatmap, ax=ax)
    charts['heatmap'] = get_base64_plot(fig)
    
    # Busy Users (Only if Overall)
    if selected_user == 'Overall':
        x, new_df = helper.most_busy_users(df)
        fig, ax = plt.subplots()
        ax.bar(x.index, x.values, color='red')
        plt.xticks(rotation='vertical')
        charts['busy_users'] = get_base64_plot(fig)
    else:
        charts['busy_users'] = None
        
    # Wordcloud
    df_wc = helper.create_wordcloud(selected_user, df)
    fig, ax = plt.subplots()
    ax.imshow(df_wc)
    plt.axis('off') # Remove axis for image
    charts['wordcloud'] = get_base64_plot(fig)
    
    # Sentiment
    sentiment_counts, sentiment_df = helper.sentiment_analysis(selected_user, df)
    fig, ax = plt.subplots()
    ax.pie(sentiment_counts['count'], labels=sentiment_counts['category'], autopct='%1.1f%%', startangle=90, colors=['green', 'red', 'grey'])
    charts['sentiment'] = get_base64_plot(fig)
    
    # Toxicity Analysis
    toxicity_data = helper.analyze_toxicity(selected_user, df)

    return render_template('whatsapp_result.html', 
                           selected_user=selected_user, 
                           users=user_list,
                           stats=stats,
                           charts=charts,
                           search_results=search_results,
                           toxicity=toxicity_data,
                           download_mode=download_mode,
                           css_content=css_content,
                           parent_template=parent_template)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    frontend_context = data.get('context', "")
    
    backend_context = ""
    
    # RAG-lite for WhatsApp: Search session file
    filepath = session.get('filepath')
    if filepath and os.path.exists(filepath):
        try:
            # Re-read DF (should cache this ideally, but file read is fast enough for local)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            df = preprocessor.preprocess(content)
            
            # RAG Logic
            keywords = [w for w in user_message.split() if len(w) > 2] # lowered specificty
            
            found_msgs = []
            
            # 1. Search by Keyword
            if keywords:
                query = '|'.join(keywords)
                # Filter by message content
                results = df[df['message'].str.contains(query, case=False, na=False)].tail(50) # Get last 50 matches (more relevant)
                
                if not results.empty:
                    found_msgs.append("--- Search Results ---")
                    for _, row in results.iterrows():
                        # Include Time!
                        found_msgs.append(f"[{row['date'].strftime('%Y-%m-%d %H:%M')}] {row['user']}: {row['message']}")
            
            # 2. Add Recent Context (Last 15 messages) regardless of search
            # This helps with questions like "who sent the last message?"
            recent = df.tail(15)
            found_msgs.append("\n--- Recent Chat Window ---")
            for _, row in recent.iterrows():
                 found_msgs.append(f"[{row['date'].strftime('%Y-%m-%d %H:%M')}] {row['user']}: {row['message']}")
            
            backend_context = "\n".join(found_msgs)
            
            # Add general stats context if query asks for it?
            # frontend_context usually covers stats.
            
        except Exception as e:
            print(f"Chat Context Error: {e}")
            
    full_context = f"Frontend Stats: {frontend_context}\n\nBackend Data: {backend_context}"
    
    response = chatbot.get_response(user_message, full_context)
    return {"response": response}

if __name__ == "__main__":
    app.run(debug=True)
