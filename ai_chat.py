import json
import os
import random
import logging
import importlib.util

logger = logging.getLogger('speak')

# Load invented‑spelling map
try:
    with open(os.path.join(os.path.dirname(__file__), 'invented_spelling.json')) as f:
        SPELL_MAP = json.load(f)
except Exception as e:
    logger.error(f"Error loading spelling map: {e}")
    SPELL_MAP = {}

# Initialize LLM with fallback mechanism
_has_llm = False
_llm = None

# Check for llamacpp availability - don't try to import directly
if importlib.util.find_spec("llamacpp") is not None:
    try:
        from llamacpp import Llama
        MODEL_PATH = os.environ.get('LLM_MODEL', '/models/llama-7B/ggml-model.bin')
        # Only try to initialize if model exists
        if os.path.exists(MODEL_PATH):
            _llm = Llama(model_path=MODEL_PATH)
            _has_llm = True
            logger.info(f"LLM loaded successfully from {MODEL_PATH}")
        else:
            logger.warning(f"LLM model not found at {MODEL_PATH}")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM: {e}")
else:
    logger.warning("llamacpp module not found")

# Check for fuzzywuzzy availability
_has_fuzzy = False
try:
    from fuzzywuzzy import process
    _has_fuzzy = True
except ImportError:
    logger.warning("fuzzywuzzy not available - spelling correction will be limited")

SYSTEM_PROMPT = (
    "You are Ms. Robin, a kind tutor speaking to a beginning reader. "
    "Use short, simple sentences and encourage the learner.\n"
)
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

# Fallback responses when LLM is not available
FALLBACK_RESPONSES = [
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

def normalize_spelling(text: str) -> str:
    """Correct common invented spellings from young readers."""
    if not SPELL_MAP:
        return text
        
    words = text.split()
    normalized = []
    for w in words:
        lw = w.lower()
        if lw in SPELL_MAP:
            normalized.append(SPELL_MAP[lw])
        elif _has_fuzzy and len(lw) > 2:
            # Only use fuzzy matching if available and for words longer than 2 characters
            try:
                best, score = process.extractOne(w, SPELL_MAP.keys())
                normalized.append(SPELL_MAP[best] if score > 80 else w)
            except Exception:
                normalized.append(w)
        else:
            normalized.append(w)
    return ' '.join(normalized)

def simple_spelling_correction(text: str) -> str:
    """Basic spelling correction without fuzzy matching."""
    words = text.split()
    normalized = []
    for w in words:
        lw = w.lower()
        if lw in SPELL_MAP:
            normalized.append(SPELL_MAP[lw])
        else:
            normalized.append(w)
    return ' '.join(normalized)

def get_response(user_text: str) -> str:
    """Generate a response to user text using the LLM with fallback options."""
    # 1) correct obvious invented spelling
    try:
        if _has_fuzzy:
            cleaned = normalize_spelling(user_text)
        else:
            cleaned = simple_spelling_correction(user_text)
    except Exception as e:
        logger.error(f"Error normalizing spelling: {e}")
        cleaned = user_text
    
    # 2) Use LLM if available, otherwise use fallback
    if _has_llm and _llm is not None:
        try:
            # build prompt
            prompt = f"{SYSTEM_PROMPT}Child: {cleaned}\nTutor:"
            
            # call the LLM
            resp = _llm(prompt, max_tokens=128, temperature=0.7)
            reply = resp['choices'][0]['text'].strip()
            
            # 4) randomly append a coaching tip
            if random.random() < 0.3:
                reply += " " + random.choice(COACHING_PROMPTS)
            
            return reply
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fall through to fallback
    
    # Fallback response
    response = random.choice(FALLBACK_RESPONSES)
    
    # If the input contained a question, try to give a more specific response
    if "?" in user_text:
        question_responses = [
            "That's a great question! What do you think?",
            "I wonder about that too. Let's learn together!",
            "Hmm, let's think about that together.",
            "That's something we can explore more!"
        ]
        response = random.choice(question_responses)
    
    # Echo back part of their input to seem more responsive
    words = cleaned.split()
    if len(words) > 3 and random.random() > 0.5:
        word_to_echo = random.choice(words)
        if len(word_to_echo) > 3:  # Only echo substantial words
            response += f" I like how you used the word '{word_to_echo}'!"
    
    # Add a coaching prompt
    if random.random() < 0.3:
        response += " " + random.choice(COACHING_PROMPTS)
        
    return response
