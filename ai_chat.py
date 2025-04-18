import json
import os
import random
from fuzzywuzzy import process
from llamacpp import Llama

# Load invented‑spelling map
with open(os.path.join(os.path.dirname(__file__), 'invented_spelling.json')) as f:
    SPELL_MAP = json.load(f)

# Initialize LLM singleton
MODEL_PATH = os.environ.get('LLM_MODEL', '/models/llama-7B/ggml-model.bin')
_llm = Llama(model_path=MODEL_PATH)

SYSTEM_PROMPT = (
    "You are Ms. Robin, a kind tutor speaking to a beginning reader. "
    "Use short, simple sentences and encourage the learner.\n"
)
COACHING_PROMPTS = [
    "Have you tried sounding this word out?",
    "Here's a fun word: butterfly!",
    "Great job – keep going!",
]

def normalize_spelling(text: str) -> str:
    words = text.split()
    normalized = []
    for w in words:
        lw = w.lower()
        if lw in SPELL_MAP:
            normalized.append(SPELL_MAP[lw])
        else:
            best, score = process.extractOne(w, SPELL_MAP.keys())
            normalized.append(SPELL_MAP[best] if score > 80 else w)
    return ' '.join(normalized)

def get_response(user_text: str) -> str:
    # 1) correct obvious invented spelling
    cleaned = normalize_spelling(user_text)

    # 2) build prompt
    prompt = f"{SYSTEM_PROMPT}Child: {cleaned}\nTutor:"

    # 3) call the LLM
    resp = _llm(prompt, max_tokens=128, temperature=0.7)
    reply = resp['choices'][0]['text'].strip()

    # 4) randomly append a coaching tip
    if random.random() < 0.3:
        reply += " " + random.choice(COACHING_PROMPTS)

    return reply
