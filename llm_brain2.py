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
    messages = [{"role": "system", "content": system_prompt}]  # Add the system prompt
    messages.extend({"role": "user", "content": msg} for msg in context)  # Add context messages
    messages.append({"role": "user", "content": prompt})  # Add the current user prompt
    
    data = {
        'model': MODEL_NAME,  # Specify the model here
        'messages': messages,  # Use the messages list
        'max_tokens': 150,  # Adjust as needed
        'temperature': 0.7,  # Adjust as needed
        'top_p': 1.0,  # Adjust as needed
        'n': 1  # Number of completions
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        # Check if 'choices' exists and has at least one item
        if 'choices' in result and len(result['choices']) > 0:
            llm_response = result['choices'][0]['message']['content'].strip()
            return llm_response
        else:
            print("Error: No choices found in the response.")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def main():
    global context
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
        
        # Get the LLM response
        llm_response = get_llm_response(user_input, context)
        
        if llm_response:
            print(f"LLM: {llm_response}")
            # Save the response to context
            context.append(f"You: {user_input}")
            context.append(f"LLM: {llm_response}")
        else:
            print("Failed to get a response from the LLM.")

if __name__ == "__main__":
    main()