import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Replace with your Groq API key and model name
API_KEY = os.environ.get("GROQ_API_KEY")
API_URL = 'https://api.groq.com/openai/v1/chat/completions'  # Replace with the actual Groq API endpoint
MODEL_NAME = 'llama-3.3-70b-versatile'  # Replace with the desired model, e.g., 'groq-llama', 'groq-mixtral', etc.

# Initialize context
context = []

def get_llm_response(prompt, context):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Define a system prompt template
    system_prompt = "You are a helpful assistant. You reply with very short answers."
    
    # Create the messages list
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": "user", "content": msg} for msg in context)
    messages.append({"role": "user", "content": prompt})
    
    data = {
        'model': MODEL_NAME,  
        'messages': messages,
        'max_tokens': 150,
        'temperature': 0.7,
        'top_p': 1.0,
        'n': 1
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            llm_response = result['choices'][0]['message']['content'].strip()
            return llm_response
        else:
            print("Error: No choices found in the response.")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
