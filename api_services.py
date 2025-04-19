import openai
import os

class AIChatProcessor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key  # [6]
    
    def generate_response(self, user_input):
        """Replace AIML with GPT-3.5-turbo responses"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
