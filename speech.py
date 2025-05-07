# Enhanced Speech Engine with Language, Volume, Queue, Stop Support

# ... (keep all previous imports and copyright)

SUPPORTED_LANGUAGES = {
    'en': 'en',         # English
    'es': 'es',         # Spanish
    'fr': 'fr',         # French
    'de': 'de',         # German
    'hi': 'hi',         # Hindi
    # Add more as needed
}

class Speech(GstSpeechPlayer):
    __gsignals__ = {
        'peak': (GObject.SIGNAL_RUN_FIRST, None, [GObject.TYPE_PYOBJECT]),
        'wave': (GObject.SIGNAL_RUN_FIRST, None, [GObject.TYPE_PYOBJECT]),
        'idle': (GObject.SIGNAL_RUN_FIRST, None, []),
    }

    def __init__(self):
        super().__init__()
        self.pipeline = None
        self.queue = []  # 🔹 Store multiple text chunks
        self.language = 'en'  # 🔹 Default language
        self.volume = 1.0     # 🔹 Default volume (0.0 to 1.0)
        self._cb = {cb: None for cb in ['peak', 'wave', 'idle']}

    def disconnect_all(self):
        for cb in self._cb:
            if self._cb[cb] is not None:
                self.disconnect(self._cb[cb])
                self._cb[cb] = None

    def connect_peak(self, cb): self._cb['peak'] = self.connect('peak', cb)
    def connect_wave(self, cb): self._cb['wave'] = self.connect('wave', cb)
    def connect_idle(self, cb): self._cb['idle'] = self.connect('idle', cb)

    def set_language(self, lang_code):
        if lang_code in SUPPORTED_LANGUAGES:
            self.language = SUPPORTED_LANGUAGES[lang_code]
            logger.info(f"Language set to: {self.language}")
        else:
            logger.warning(f"Unsupported language: {lang_code}")

    def set_volume(self, level):
        self.volume = max(0.0, min(level, 1.0))
        logger.info(f"Volume set to: {self.volume}")

    def make_pipeline(self):
        if self.pipeline:
            self.stop_sound_device()
            del self.pipeline

        cmd = 'espeak name=espeak' \
              ' ! capsfilter name=caps' \
              ' ! volume name=vol ! tee name=me' \
              ' me.! queue ! autoaudiosink name=ears' \
              ' me.! queue ! fakesink name=sink'

        self.pipeline = Gst.parse_launch(cmd)
        caps = self.pipeline.get_by_name('caps')
        caps.set_property('caps', Gst.caps_from_string('audio/x-raw,channels=(int)1,depth=(int)16'))

        self.pipeline.get_by_name('vol').set_property('volume', self.volume)

        # ... keep existing handoff and message handling code here ...

    def speak(self, status, text):
        if not text.strip():
            logger.debug("Empty text. Nothing to speak.")
            return

        self.queue.append((status, text))  # 🔹 Queue text

        if len(self.queue) == 1:
            self._speak_next()

    def _speak_next(self):
        if not self.queue:
            self.emit("idle")
            return

        status, text = self.queue[0]
        self.make_pipeline()

        espeak = self.pipeline.get_by_name('espeak')
        espeak.props.pitch = int(status.pitch) - 100
        espeak.props.rate = int(status.rate) - 100
        espeak.props.voice = self.language
        espeak.props.track = 1
        espeak.props.text = text

        logger.debug(f"[Speech] Speaking: '{text}' [voice={self.language}, pitch={status.pitch}, rate={status.rate}]")
        self.restart_sound_device()

    def stop(self):
        """🔹 Stop current speech and clear queue."""
        if self.pipeline:
            self.stop_sound_device()
        self.queue.clear()
        logger.info("Speech stopped and queue cleared.")

    def restart_sound_device(self):
        super().restart_sound_device()

        def check_idle():
            if self.pipeline and self.pipeline.get_state(0)[1] == Gst.State.NULL:
                self.queue.pop(0)
                self._speak_next()
            return False

        GLib.timeout_add(500, check_idle)

_speech = None

def get_speech():
    global _speech
    if _speech is None:
        _speech = Speech()
    return _speech
