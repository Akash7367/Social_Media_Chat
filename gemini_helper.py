import google.generativeai as genai
import os

class GeminiChat:
    def __init__(self, api_key=None):
        # Allow passing key directly or from env
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # 'gemini-2.0-flash' had 0 quota. Trying 'gemini-flash-latest' which usually maps to a stable free-tier model.
                self.model = genai.GenerativeModel('gemini-flash-latest')
                print(f"✅ Gemini Configured. Model: gemini-flash-latest. Key: ...{self.api_key[-5:]}")
            except Exception as e:
                print(f"❌ Gemini Configuration Error: {e}")
                self.model = None
        else:
            print("❌ Gemini API Key Missing!")
            self.model = None

    def get_response(self, user_input, context_data=None):
        if not self.model:
            return "Error: Gemini API Key is missing or invalid. Check server logs."

        try:
            # Construct a prompt with context
            prompt = f"""
            You are an assistant for a WhatsApp chat analytics app. Use ONLY the sections below; do not invent chat topics or messages.

            DATA:
            {context_data}

            USER QUESTION: {user_input}

            RULES:
            1. Questions about toxicity, abuse, rude language, or "most toxic user": answer ONLY from the "Toxicity / abuse analysis" section.
               - If that section lists users with scores, name the top user (#1) and their score. If there are no rows, say the bad-word scanner found no matches for this scope—not that the chat is "about cricket" or other topics unless those words appear in "Recent messages" or "Retrieved lines".
            2. For other questions, use "Retrieved lines" and "Recent messages" when relevant. Do not contradict the toxicity section with guesses from unrelated snippets.
            3. If something is truly missing from all sections, say the export does not show it—do not fabricate.
            4. When dashboard scope is a single user (not "Overall"), toxicity rows may be only for that user.
            5. Answer directly and briefly.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini Generation Error: {e}")
            return f"I encountered an error: {str(e)}.\nTry checking your API Key or quota."
