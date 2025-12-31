#!/usr/bin/env python3
import requests
import json
import sys
import argparse
import markdown
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- Configuration & Helpers ---

# Configure the API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"

# (LANG_MAP and INSTRUCTION_MAP remain the same)
# Mapping ISO 639-1 codes to full English names for better prompting
LANG_MAP = {
    'it': 'Italian', 'fr': 'French', 'es': 'Spanish', 'de': 'German',
    'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese', 'zh': 'Chinese',
    'ko': 'Korean', 'hi': 'Hindi', 'ar': 'Arabic', 'nl': 'Dutch',
    'sv': 'Swedish', 'pl': 'Polish', 'tr': 'Turkish'
}

# Mapping tokens to specific instructions
INSTRUCTION_MAP = {
    'translate': "translate the word to English and provide an English definition",
    'definition': "provide a definition of this word in its own language",
    'etymology': "describe the etymology of this word",
    'usage': "provide a description and notes on contemporary usage of this word in its own language",
    'history': "give a history of this word, such as when it entered the language",
    'phrases': "provide some sample phrases and/or sentences that use this word, in its own language",
    'synonyms': "provide a list of synonyms of this word in its own language, including information on shades of differences in meaning",
    'cognates': "provide a list of English cognates to this word, if any exist",
    'idioms': "provide a list of common idioms that use this word, in its own language",
    'irregular': "provide notes about any deviances from standard grammar rules this word may have (e.g., irregular conjugations)"
}

def get_full_lang_name(code):
    return LANG_MAP.get(code.lower(), f"language (ISO code: {code})")

def build_prompt(lang_code, text, req_types):
    """Constructs the prompt for the AI."""
    lang_name = get_full_lang_name(lang_code)
    prompt_instructions = [f"{i}) {INSTRUCTION_MAP.get(r_type, f'provide info on {r_type}')}" for i, r_type in enumerate(req_types, 1)]
    instructions_str = ", ".join(prompt_instructions)
    return (
        f"Given the {lang_name} word (or phrase) '{text}', please: {instructions_str}. "
    )

def get_response(prompt, model):
    """Invokes the AI via Ollama REST API and returns the parsed JSON response."""

    # Prepare the request payload
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        # Make the HTTP request
        response = requests.post(OLLAMA_URL, json=payload)

        # Parse and display the response
        if response.status_code == 200:
            result = response.json()
            return result, None
        elif response.status_code == 404:
            raise Exception(f"Model not found: {payload.get('model')}")
        elif response.status_code == 500:
            raise Exception("Ollama server error")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    except json.JSONDecodeError:
        return None, f"Failed to parse JSON response. Raw Output: {response.content}"
    except Exception as e:
        return None, str(e)

# --- Web Server Mode ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReadAssist: {{ text }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
        h1 { border-bottom: 2px solid #4285f4; padding-bottom: 10px; }
        .word-header { background: #f1f3f4; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin-bottom: 25px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
        .section-title { background: #e8f0fe; color: #1967d2; padding: 10px 15px; font-weight: bold; text-transform: uppercase; font-size: 0.9em; }
        .section-content { padding: 15px; }
        .error { color: #d32f2f; background: #fdecea; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="word-header">
        <h2>Query: <em>{{ text }}</em> ({{ lang }})</h2>
        <p>Model: {{ model }}</p>
    </div>
    {% if error %}
        <div class="error"><h3>Error Processing Request</h3><p>{{ error }}</p></div>
    {% else %}
        <div class="section">
            <div class="section-content">{{ results }}</div>
        </div>
    {% endif %}
</body>
</html>
"""

@app.route('/readassist', methods=['GET'])
def read_assist_web():
    req_types = request.args.getlist('req_type')
    lang_code = request.args.get('lang', 'en')
    text = request.args.get('text', '')
    model = request.args.get('model', 'gemma3:4b') # Default model for web

    if not text or not req_types:
        return render_template_string(HTML_TEMPLATE, text="Missing Input", lang="N/A", model=model, error="Please provide 'text' and at least one 'req_type'.", results={})

    lang_name = get_full_lang_name(lang_code)
    prompt = build_prompt(lang_code, text, req_types)
    json_data, error = get_response(prompt, model)

    if error:
        return render_template_string(HTML_TEMPLATE, text=text, lang=lang_name, model=model, results=json_data, error=error)

    formatted_results = markdown.markdown(json_data.get('response', "<p><em>No information returned.</em></p>"))
    return render_template_string(HTML_TEMPLATE, text=text, lang=lang_name, model=model, results=formatted_results, error=None)

def run_web(host, port):
    """Starts the Flask web server."""
    print(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)

# --- Main Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ReadAssist: A tool to help with reading foreign languages using Ollama.")

    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for the web server.')
    parser.add_argument('--port', type=int, default=5000, help='Port for the web server.')

    args = parser.parse_args()
    run_web(args.host, args.port)
