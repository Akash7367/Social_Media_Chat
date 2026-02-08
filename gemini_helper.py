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
            You are a smart assistant for a Whatsapp/Instagram Analytics tool.
            
            DATA CONTEXT:
            {context_data}
            
            USER QUESTION: {user_input}
            
            INSTRUCTIONS:
            1. Answer the question DIRECTLY and BRIEFLY.
            2. Do NOT mention "According to the analysis" or "The context suggests". 
            3. If the user asks for a specific fact (e.g. "most usage", "who sent this"), give JUST that fact.
            4. Keep the tone casual and helpful.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini Generation Error: {e}")
            return f"I encountered an error: {str(e)}.\nTry checking your API Key or quota."
