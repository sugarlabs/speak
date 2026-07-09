What is this?
=============

Speak is a voice synthesis activity for the Sugar desktop.

Speak shows a face that will talk what is typed, within reason.

How to use?
===========

Speak is part of the Sugar desktop and is often included.  Please refer to;

* [How to Get Sugar on sugarlabs.org](https://sugarlabs.org/),
* [How to use Sugar](https://help.sugarlabs.org/),
* [Download Speak using Browse](https://v4.activities.sugarlabs.org/), search for `Speak`, then download, and;
* [How to use Speak](https://help.sugarlabs.org/en/speak.html).

How to upgrade?
===============

On Sugar desktop systems;
* use [My Settings](https://help.sugarlabs.org/en/my_settings.html), [Software Update](https://help.sugarlabs.org/en/my_settings.html#software-update), or;
* use Browse to open [v4.activities.sugarlabs.org](https://v4.activities.sugarlabs.org/), search for `Speak`, then download.

How to integrate?
=================

Speak depends on Python, [Sugar Toolkit for GTK+ 3](https://github.com/sugarlabs/sugar-toolkit-gtk3), GStreamer 1, GTK+ 3, and gst-plugins-espeak.

Speak is started by [Sugar](https://github.com/sugarlabs/sugar).

Speak is [packaged by Fedora](https://src.fedoraproject.org/rpms/sugar-speak).  On Fedora systems;

```
dnf install sugar-speak
```

Speak is not packaged by Debian and Ubuntu distributions.  On Debian
and Ubuntu systems dependencies include `gstreamer1.0-espeak`,
`gir1.2-gstreamer-1.0`, and `gir1.2-gst-plugins-base-1.0`.

Branch master
=============

The `master` branch targets an environment with latest stable release
of [Sugar](https://github.com/sugarlabs/sugar), with dependencies on
latest stable release of Fedora and Debian distributions.

Branch not-gstreamer1
=====================

The `not-gstreamer1` branch is a backport of features and bug fixes
from the `master` branch for ongoing maintenance of the activity on
Fedora 18 systems which don't have well-functioning GStreamer 1
packages.

## AI Chatbot Features (Generative AI)

This activity includes an experimental offline Generative AI backend using `SmolLM2-135M` (GGUF format). It replaces the legacy AIML pattern matcher with a generative model capable of answering general knowledge questions locally on the device.

### Development Setup
To run the AI features in a local development environment:

1. **Install Dependencies:**
   `pip install -r requirements-dev.txt`

2. **Run the activity**
Ensure the dependencies are visible to Sugar (e.g., in your PYTHONPATH or system packages), then run the standard tool
    Example: If installed in a local venv
    `export PYTHONPATH=$PYTHONPATH:$(pwd)/.venv/lib/python3.12/site-packages`
    `sugar-activity3`

3. **Building for Distribution (Fat Bundle)**
Maintainers can create a "Fat Bundle" (approx. 106MB) that includes the AI model pre-installed, ensuring 100% offline functionality out-of-the-box.

1. **Create the Model Directory:**
    `mkdir -p model`

2. **Download the Model:** 
    Download the quantized GGUF model into the model/ directory.
    Manually download the model file:
    `wget -O model/SmolLM2-135M-Instruct-Q4_K_M.gguf https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_K_M.gguf`

3. **Build the Bundle:** 
    Run the standard build command. The MANIFEST should automatically include the model/ directory if present.
    `./setup.py dist_xo`

**Performance & Specifications**
Model: SmolLM2-135M-Instruct (Quantized to Q4_K_M)
Engine: llama.cpp (via python bindings)
RAM Usage: ~300MB (Suitable for XO-4 and newer)
Response Time: 2-5 seconds on average CPU.

**License & Open Source Compliance**
Model License: Apache 2.0 (Hosted by Hugging Face).
Training Data: The model was trained on Cosmopedia, a dataset of synthetic textbooks, ensuring open data compliance.
Privacy: The inference runs entirely offline. No user data is sent to external servers.