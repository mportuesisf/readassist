#!/usr/bin/env python3
import subprocess
import json
import shlex
import sys
import argparse
import markdown
from flask import Flask, request, render_template_string

app = Flask(__name__)
CACHE = {}

# --- Configuration & Helpers ---

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
    """Constructs the prompt for the Gemini CLI."""
    lang_name = get_full_lang_name(lang_code)
    prompt_instructions = [f"{i}) {INSTRUCTION_MAP.get(r_type, f'provide info on {r_type}')}" for i, r_type in enumerate(req_types, 1)]
    instructions_str = ", ".join(prompt_instructions)
    return (
        f"Given the {lang_name} word (or phrase) '{text}', please: {instructions_str}. "
        f"IMPORTANT: Return the response strictly as a raw JSON object (no markdown code blocks like ```json). "
        f"The keys of the JSON object must be the exact request type tokens provided: {', '.join(req_types)}. "
        f"The values should be the informative text formatted in Markdown."
    )

def get_gemini_response(prompt, model):
    """Invokes the Gemini CLI, with caching, and returns the parsed JSON response."""
    cache_key = f"{model}|{prompt}"
    if cache_key in CACHE:
        print("DEBUG: Returning response from cache.", file=sys.stderr)
        return CACHE[cache_key], None

    try:
        command = ['gemini']
        if model:
            # Assuming the gemini CLI uses a --model flag
            command.extend(['--model', model])
        command.append(prompt)
        
        print(f"DEBUG: Running command: {' '.join(shlex.quote(c) for c in command)}", file=sys.stderr)

        result = subprocess.run(command, capture_output=True, text=True, check=True)
        raw_output = result.stdout.strip()

        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3]

        json_data = json.loads(raw_output)
        CACHE[cache_key] = json_data  # Store in cache
        return json_data, None
    except FileNotFoundError:
        return None, "The 'gemini' executable was not found. Please ensure the Gemini CLI is installed and in your PATH."
    except subprocess.CalledProcessError as e:
        return None, f"Gemini CLI Error: {e.stderr}"
    except json.JSONDecodeError:
        return None, f"Failed to parse JSON response from Gemini. Raw Output: {raw_output}"
    except Exception as e:
        return None, str(e)

# --- CLI Mode ---
def run_cli(text, lang_code, req_types, model):
    """Handles the command-line execution."""
    print(f"Querying for '{text}' ({get_full_lang_name(lang_code)}) using model '{model}'...")
    
    prompt = build_prompt(lang_code, text, req_types)
    json_data, error = get_gemini_response(prompt, model)

    if error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("\n--- RESULTS ---")
    for r_type in req_types:
        print(f"\n[{r_type.upper()}]")
        if r_type in json_data:
            print(json_data[r_type])
        else:
            print("No information returned for this section.")

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
        {% for key, content in results.items() %}
        <div class="section">
            <div class="section-title">{{ key }}</div>
            <div class="section-content">{{ content | safe }}</div>
        </div>
        {% endfor %}
    {% endif %}
</body>
</html>
"""

@app.route('/readassist', methods=['GET'])
def read_assist_web():
    req_types = request.args.getlist('req_type')
    lang_code = request.args.get('lang', 'en')
    text = request.args.get('text', '')
    model = request.args.get('model', 'gemini-2.5-flash') # Default model for web

    if not text or not req_types:
        return render_template_string(HTML_TEMPLATE, text="Missing Input", lang="N/A", model=model, error="Please provide 'text' and at least one 'req_type'.", results={})

    lang_name = get_full_lang_name(lang_code)
    prompt = build_prompt(lang_code, text, req_types)
    json_data, error = get_gemini_response(prompt, model)

    if error:
        return render_template_string(HTML_TEMPLATE, text=text, lang=lang_name, model=model, results={}, error=error)

    formatted_results = {r_type: markdown.markdown(json_data.get(r_type, "<p><em>No information returned.</em></p>")) for r_type in req_types}
    return render_template_string(HTML_TEMPLATE, text=text, lang=lang_name, model=model, results=formatted_results, error=None)

def run_web(host, port):
    """Starts the Flask web server."""
    print(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)

# --- Main Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ReadAssist: A tool to help with reading foreign languages using Gemini.")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # --- CLI Sub-command ---
    parser_cli = subparsers.add_parser('cli', help='Run in command-line mode.')
    parser_cli.add_argument('text', type=str, help='The word or phrase to look up.')
    parser_cli.add_argument('req_types', nargs='+', choices=list(INSTRUCTION_MAP.keys()), help='One or more information types to request.')
    parser_cli.add_argument('--lang', type=str, default='it', help=f'The two-letter language code.')
    parser_cli.add_argument('--model', type=str, default='gemini-2.5-flash', help='The Gemini model to use (e.g., gemini-2.5-flash, gemini-pro).')
    
    # --- Web Sub-command ---
    parser_web = subparsers.add_parser('web', help='Run as a web server.')
    parser_web.add_argument('--host', type=str, default='0.0.0.0', help='Host for the web server.')
    parser_web.add_argument('--port', type=int, default=5000, help='Port for the web server.')

    args = parser.parse_args()

    if args.command == 'cli':
        run_cli(args.text, args.lang, args.req_types, args.model)
    elif args.command == 'web':
        run_web(args.host, args.port)
