#!/usr/bin/env python3
"""
Interview Copilot — Job Setup Web App
Run:  python job_setup.py
Then open http://localhost:5000 in your browser.
"""

import json
import os
import webbrowser
import threading
from flask import Flask, request, render_template_string

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_config.json")

# ─── HTML Template ────────────────────────────────────────────
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Interview Copilot — Job Setup</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #12121f;
    color: #e8e8f0;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 40px 20px 60px;
  }

  .page-header {
    text-align: center;
    margin-bottom: 32px;
  }
  .page-header .logo {
    font-size: 28px;
    font-weight: 700;
    color: #00d4aa;
    letter-spacing: -0.5px;
  }
  .page-header .logo span { color: #e8e8f0; }
  .page-header p {
    color: #6b6b88;
    font-size: 14px;
    margin-top: 8px;
  }

  .card {
    background: #1c1c2e;
    border: 1px solid #2a2a42;
    border-radius: 14px;
    padding: 40px;
    width: 100%;
    max-width: 680px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #e8e8f0;
    margin-bottom: 6px;
  }
  .card-sub {
    font-size: 13px;
    color: #6b6b88;
    margin-bottom: 28px;
    line-height: 1.5;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(0,212,170,0.12);
    border: 1px solid rgba(0,212,170,0.35);
    border-radius: 8px;
    padding: 12px 16px;
    color: #00d4aa;
    font-size: 14px;
    margin-bottom: 24px;
  }
  .toast .icon { font-size: 18px; }

  .field { margin-bottom: 22px; }
  .field label {
    display: block;
    font-size: 11px;
    font-weight: 700;
    color: #6b6b88;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
  }
  .field label .required { color: #00d4aa; margin-left: 2px; }

  .field input,
  .field textarea {
    width: 100%;
    background: #0d0d1a;
    border: 1px solid #2a2a42;
    border-radius: 7px;
    padding: 11px 14px;
    color: #e8e8f0;
    font-size: 14px;
    font-family: inherit;
    line-height: 1.5;
    transition: border-color 0.15s, box-shadow 0.15s;
    outline: none;
  }
  .field input::placeholder,
  .field textarea::placeholder { color: #3a3a52; }
  .field input:focus,
  .field textarea:focus {
    border-color: #00d4aa;
    box-shadow: 0 0 0 3px rgba(0,212,170,0.12);
  }
  .field textarea {
    resize: vertical;
    min-height: 220px;
    line-height: 1.65;
  }

  .row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  @media (max-width: 480px) { .row { grid-template-columns: 1fr; } }

  .hint {
    font-size: 12px;
    color: #4a4a62;
    margin-top: 6px;
    line-height: 1.5;
  }

  .divider {
    border: none;
    border-top: 1px solid #2a2a42;
    margin: 28px 0;
  }

  .btn-row { display: flex; gap: 12px; margin-top: 4px; }

  .btn-save {
    flex: 1;
    background: #00d4aa;
    color: #000;
    border: none;
    border-radius: 7px;
    padding: 13px 24px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
    letter-spacing: 0.2px;
  }
  .btn-save:hover { opacity: 0.88; }
  .btn-save:active { transform: scale(0.98); }

  .btn-clear {
    background: transparent;
    color: #6b6b88;
    border: 1px solid #2a2a42;
    border-radius: 7px;
    padding: 13px 20px;
    font-size: 14px;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
  }
  .btn-clear:hover { border-color: #ff5f57; color: #ff5f57; }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #6b6b88;
    margin-top: 16px;
  }
  .status-badge .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: {{ '#00d4aa' if config.role else '#3a3a52' }};
  }
</style>
</head>
<body>

<div class="page-header">
  <div class="logo">🎯 Interview <span>Copilot</span></div>
  <p>Configure your target job so every answer is tailored to this specific role &amp; company.</p>
</div>

<div class="card">
  <div class="card-title">Target Job Details</div>
  <div class="card-sub">
    Fill in the role you're interviewing for. The copilot will use this to frame
    your resume experience in the most relevant way for each question.
  </div>

  {% if saved %}
  <div class="toast">
    <span class="icon">✓</span>
    Saved! Restart <strong>copilot.py</strong> to apply the new job context.
  </div>
  {% endif %}

  <form method="POST" autocomplete="off">
    <div class="field">
      <label>Job Title / Role <span class="required">*</span></label>
      <input type="text" name="role"
             placeholder="e.g. Principal Software Engineer, Data Governance Lead"
             value="{{ config.role or '' }}" required>
    </div>

    <div class="row">
      <div class="field">
        <label>Company <span class="required">*</span></label>
        <input type="text" name="company"
               placeholder="e.g. Google, Amazon"
               value="{{ config.company or '' }}" required>
      </div>
      <div class="field">
        <label>Location</label>
        <input type="text" name="location"
               placeholder="e.g. New York, NY / Remote"
               value="{{ config.location or '' }}">
      </div>
    </div>

    <div class="field">
      <label>Job Description <span class="required">*</span></label>
      <textarea name="job_description"
                placeholder="Paste the full job description here — responsibilities, required skills, qualifications, etc. The more detail, the better the copilot can align your answers to what this company is looking for.">{{ config.job_description or '' }}</textarea>
      <div class="hint">
        Tip: paste the entire JD including responsibilities and requirements.
        The copilot will automatically surface the most relevant parts of your background.
      </div>
    </div>

    <hr class="divider">

    <div class="btn-row">
      <button type="submit" class="btn-save">💾  Save &amp; Apply to Copilot</button>
      <button type="button" class="btn-clear"
              onclick="if(confirm('Clear all fields?')){
                document.querySelectorAll('input,textarea').forEach(e=>e.value='');
              }">Clear</button>
    </div>

    <div class="status-badge">
      <span class="dot"></span>
      {% if config.role %}
        Currently set: <strong style="color:#e8e8f0;margin-left:4px;">
          {{ config.role }}{% if config.company %} at {{ config.company }}{% endif %}
        </strong>
      {% else %}
        No job configured yet
      {% endif %}
    </div>
  </form>
</div>

</body>
</html>"""


# ─── Helpers ──────────────────────────────────────────────────
def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Routes ───────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    saved = False
    config = load_config()

    if request.method == "POST":
        config = {
            "role":            request.form.get("role", "").strip(),
            "company":         request.form.get("company", "").strip(),
            "location":        request.form.get("location", "").strip(),
            "job_description": request.form.get("job_description", "").strip(),
        }
        save_config(config)
        saved = True

    return render_template_string(TEMPLATE, config=config, saved=saved)


# ─── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("JOB_SETUP_PORT", "4003"))
    url  = f"http://localhost:{port}"
    print("=" * 50)
    print("  🎯  Interview Copilot — Job Setup")
    print("=" * 50)
    print(f"\n  Open in browser: {url}\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(debug=False, port=port, use_reloader=False)
