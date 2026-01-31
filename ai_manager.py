import os
import threading
import urllib.request
import shutil
from sugar3 import env
from gettext import gettext as _

# Check for the library safely
try:
    from llama_cpp import Llama
    HAS_LLAMA = True
    print("AIManager: llama-cpp-python found and loaded.")
except Exception as e:
    HAS_LLAMA = False
    print(f"AIManager: Failed to load llama-cpp. Error: {e}")

MODEL_URL = "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_K_M.gguf"
MODEL_FILENAME = "SmolLM2-135M-Instruct-Q4_K_M.gguf"


class AIManager:
    def __init__(self):
        self.llm = None
        self.is_loaded = False
        self.load_error = None
        
        try:
            from sugar3 import env
            # This works on real XO laptops
            profile_path = env.get_profile_path()
            base_path = os.path.join(profile_path, 'org.sugarlabs.Speak')
        except:
            # This works for ./dev_launcher.sh
            print(" AIManager: Using local development path")
            base_path = os.getcwd()

        self.model_dir = os.path.join(base_path, 'model')
        self.model_path = os.path.join(self.model_dir, MODEL_FILENAME)

    def _download_model(self):
        """Downloads the model with RESUME support."""
        # 1. Check if complete file exists
        if os.path.exists(self.model_path):
            if os.path.getsize(self.model_path) > 100_000_000:
                return True
        
        # 2. Ensure directory exists
        if not os.path.exists(self.model_dir):
            try:
                os.makedirs(self.model_dir)
            except OSError as e:
                self.load_error = _("Write permission error: {}").format(e)
                return False

        print(f"AIManager: Attempting download to {self.model_path}...")
        
        # 3. Resume Logic
        existing_size = 0
        write_mode = 'wb'
        if os.path.exists(self.model_path):
            existing_size = os.path.getsize(self.model_path)
            write_mode = 'ab'  # Append mode
            print(f"Resuming from {existing_size} bytes...")

        try:
            req = urllib.request.Request(
                MODEL_URL, 
                headers={
                    'User-Agent': 'Sugar-Speak-Activity/1.0',
                    'Range': f'bytes={existing_size}-'  # Resume support
                }
            )
            
            with urllib.request.urlopen(req, timeout=60) as response, \
                 open(self.model_path, write_mode) as out_file:
                shutil.copyfileobj(response, out_file)
                
            print("AIManager: Download complete.")
            return True
            
        except urllib.error.HTTPError as e:
            # If server rejects Range (416), delete and restart
            if e.code == 416: 
                if os.path.exists(self.model_path):
                    os.remove(self.model_path)
                return self._download_model() # Retry from scratch
            self.load_error = _("Download server error: {}").format(e)
            return False
            
        except Exception as e:
            print(f"Download Error: {e}")
            self.load_error = _(
                "Automatic download failed. "
                "Please manually download the SmolLM2 file "
                "and place it in the 'speak/model' folder."
            )
            return False

    def load_model(self, callback):
        """
        Loads the model in a BACKGROUND THREAD.
        callback: function(success, message)
        """
        def _loader():
            # THIS PRINT IS CRUCIAL
            print(" AIManager: _loader thread is now RUNNING")
            
            if not HAS_LLAMA:
                self.load_error = _("My internal library (llama-cpp) is missing.")
                callback(False, self.load_error)
                return

            if not self._download_model():
                callback(False, self.load_error)
                return

            # 3. Load into RAM
            print(" AIManager: Loading GGUF into RAM...")
            try:
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=512,
                    n_threads=2,
                    verbose=False
                )
                self.is_loaded = True
                print("AIManager: Brain active.")
                callback(True, _("I am ready."))
            except Exception as e:
                self.load_error = _("My brain file is corrupted: {}").format(e)
                callback(False, self.load_error)

        # Start the thread
        thread = threading.Thread(target=_loader)
        thread.start()

    def ask(self, prompt, callback):
        if not self.is_loaded:
            msg = self.load_error if self.load_error else _("My brain is not loaded yet.")
            callback(msg)
            return

        def _run():
            try:
                full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
                output = self.llm(
                    full_prompt,
                    max_tokens=60,
                    stop=["<|im_end|>", "\n"],
                    echo=False
                )
                text = output['choices'][0]['text'].strip()
                callback(text)
            except Exception as e:
                print(f"Inference Error: {e}")
                callback(_("I had trouble thinking."))

        thread = threading.Thread(target=_run)
        thread.start()