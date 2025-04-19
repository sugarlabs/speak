"""
AI Chat module for Speak activity - Python 2 compatible version
This is a simplified version for OLPC XO laptops running Python 2 on Fedora 18
"""
import json
import os
import random
import logging
import re

logger = logging.getLogger('speak')

# Load invented-spelling map
try:
    with open(os.path.join(os.path.dirname(__file__), 'invented_spelling.json')) as f:
        SPELL_MAP = json.load(f)
except Exception as e:
    logger.error("Error loading spelling map: %s" % e)
    SPELL_MAP = {}

# For Python 2 compatibility, we're using a simplified AI approach
_has_llm = False
_llm = None

# Educational coaching prompts for reading assistance
COACHING_PROMPTS = [
    "Have you tried sounding this word out?",
    "Here's a fun word: butterfly!",
    "Great job – keep going!",
    "I like the way you're reading!",
    "Let's try reading that together!",
    "You're becoming such a good reader!",
    "Can you spell that word for me?",
    "What does that word mean to you?",
    "That's a tricky word, isn't it?",
    "I believe in you!"
]

# Age-appropriate educational responses
EDUCATIONAL_RESPONSES = [
    "I like talking with you! Tell me more.",
    "That's interesting! How do you feel about that?",
    "Can you tell me more about that?",
    "I'm here to help you learn to read. What book are you reading?",
    "Let's practice some words together!",
    "Good job with your reading practice!",
    "I think you're doing great with your reading.",
    "Reading is so much fun, isn't it?",
    "What's your favorite story?",
    "Do you have a favorite character in a book?",
    "Let's read a sentence together!",
    "Can you read what you wrote out loud?",
    "That's a great thought! Can you tell me more?",
    "I enjoy our reading practice together!",
    "Let's sound out some words together.",
    "What other books have you been reading lately?",
    "You're making great progress with your reading!",
    "I'm proud of how you're working on your reading skills!"
]

# Topic-based responses to make the conversation more contextual
TOPIC_RESPONSES = {
    "animal": [
        "Animals are fascinating! What's your favorite animal?",
        "Did you know that dolphins sleep with one eye open?",
        "I love learning about different animals too!"
    ],
    "book": [
        "Reading books helps us learn new words!",
        "What's your favorite part of the story?",
        "Books can take us on amazing adventures!"
    ],
    "school": [
        "What's your favorite subject in school?",
        "Learning new things is so exciting!",
        "I enjoy helping you with your schoolwork."
    ],
    "friend": [
        "Friends are important! What do you like to do with your friends?",
        "Being a good friend means being kind and helpful.",
        "It's fun to share stories with friends!"
    ],
    "family": [
        "Families come in all shapes and sizes!",
        "What activities do you enjoy with your family?",
        "Family time is special time."
    ]
}

def simple_spelling_correction(text):
    """Basic spelling correction using the invented spelling map."""
    words = text.split()
    normalized = []
    for w in words:
        lw = w.lower()
        if lw in SPELL_MAP:
            normalized.append(SPELL_MAP[lw])
        else:
            normalized.append(w)
    return ' '.join(normalized)

def detect_topic(text):
    """Detect topics in the user's text to provide more relevant responses."""
    text = text.lower()
    for topic in TOPIC_RESPONSES:
        if topic in text:
            return topic
    return None

def get_response(user_text):
    """Generate a response to user text using our educational response system.
    This is a simplified version of an AI chatbot for Python 2 compatibility."""
    
    # 1) Correct obvious invented spelling
    try:
        cleaned = simple_spelling_correction(user_text)
    except Exception as e:
        logger.error("Error normalizing spelling: %s" % e)
        cleaned = user_text
    
    # 2) Check for topic-specific responses
    topic = detect_topic(cleaned)
    if topic and random.random() > 0.5:
        response = random.choice(TOPIC_RESPONSES[topic])
    else:
        # Use general educational response
        response = random.choice(EDUCATIONAL_RESPONSES)
    
    # 3) If the input contained a question, give question-specific response
    if "?" in user_text:
        question_responses = [
            "That's a great question! What do you think?",
            "I wonder about that too. Let's learn together!",
            "Hmm, let's think about that together.",
            "That's something we can explore more!"
        ]
        response = random.choice(question_responses)
    
    # 4) Echo back part of their input to seem more responsive
    words = cleaned.split()
    if len(words) > 3 and random.random() > 0.5:
        word_to_echo = random.choice(words)
        if len(word_to_echo) > 3:  # Only echo substantial words
            response += " I like how you used the word '%s'!" % word_to_echo
    
    # 5) Add a coaching prompt occasionally
    if random.random() < 0.3:
        response += " " + random.choice(COACHING_PROMPTS)
        
    return response
