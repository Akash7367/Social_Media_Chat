# Social Media Chat & Profile Analyzer

A comprehensive Flask-based web application to analyze exported WhatsApp chats and public Instagram profiles, extracting deep insights, statistics, behavioral patterns, and visualizations.

## 🚀 Features

### 🟢 WhatsApp Chat Analysis
- **Robust Date Parsing**: Automatically handles various exported date formats including iOS (`[dd/mm/yy, HH:MM:SS]`), 12-hour AM/PM, and standard 24-hour formats.
- **Core Statistics**: Total messages, words, media shared, and links shared per user or overall.
- **Timelines**: Visualize monthly and daily chat activity trends.
- **Activity Maps**: Identify the busiest days of the week, months, and a detailed heatmap of activity by hour.
- **Word & Emoji Analysis**: Visual representation of most used words (Word Cloud) and frequency of emojis used.
- **Sentiment & Toxicity Analysis**: 
  - Analyze the sentiment (Positive/Negative/Neutral) using VADER.
  - Generates toxicity scores based on abusive language using a custom heuristic algorithm covering English, Hindi, and Hinglish profanity.
- **AI Chat Assistant**: Integrated "RAG-lite" Gemini AI chat (`gemini-flash-latest`) to ask contextual questions about your specific chat history!
- **Search & Downloadable Reports**: Search for specific messages and download a standalone HTML report with embedded CSS for offline viewing.

### 🟣 Instagram Profile Analysis
- **Resilient Scraping Engine**: Utilizes a highly robust 3-layer fallback strategy to bypass rate limits:
  1. **Instaloader** for deep fetch.
  2. **HTML Meta Scraping** fallback for profile metrics (Followers/Following/Posts).
  3. **Mock/Demo Data** final fallback to always guarantee a user experience.
- **Efficient Caching**: Implements a 6-hour file-based local caching mechanism (`ig_cache`) to prevent redundant API calls and rate-limiting.
- **Profile Summary**: Fetch details like followers, following, posts, and bio.
- **Engagement Metrics**: Calculate engagement rates, average likes, and average comments.
- **Activity Charts**: Plot daily, weekly, and monthly posting frequency.
- **Top Content**: Identify most liked and most commented posts.

### 📧 Additional Features
- **Contact Form**: Built-in contact form that logs messages locally (`messages_log.txt`) and sends emails via SMTP.

## 🛠️ Tech Stack
- **Backend**: Python, Flask
- **Data Processing**: Pandas, Regex
- **NLP & Sentiment**: vaderSentiment, wordcloud
- **Scraping**: Instaloader, Requests, BeautifulSoup (implied from HTML regex)
- **AI Integration**: Google Generative AI (Gemini)
- **Visualizations**: Matplotlib, Seaborn

## ⚙️ How to Run Locally

1. **Clone the repository \& navigate to it**:
   ```bash
   git clone <your-repo-url>
   cd Whatsapp_Chat
   ```

2. **Set up a Virtual Environment (Optional but recommended)**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_flask_secret_key
   MAIL_USERNAME=your_gmail_address
   MAIL_PASSWORD=your_gmail_app_password
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://127.0.0.1:5000/`.

## 🚀 Deployment (Production)

This application is configured for deployment on platforms like Render or Heroku. 
- **Procfile**: Included for WSGI server configuration (`web: gunicorn app:app`).
- **render.yaml**: Included for automated deployment on Render as a Python Web Service.

## 📁 Project Structure
- `app.py`: Main Flask application handling routes and logic.
- `helper.py`: Core functions for generating stats, charts, and performing sentiment/toxicity analysis.
- `preprocessor.py`: Parses exported WhatsApp text files using robust regex and converts them into Pandas DataFrames.
- `instagram_scraper.py`: Engine for scraping Instagram accounts using a 3-layer fallback and caching.
- `gemini_helper.py`: Wrapper for connecting with the Google Generative AI API (`gemini-flash-latest`) for chat functionality.
- `templates/`: HTML templates for rendering the web application.
- `requirements.txt`: Python package dependencies.
