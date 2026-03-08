import os
import json
import threading
from flask import Flask, request, render_template_string
import discord
from discord.ext import commands

app = Flask(__name__)

# Persistence file
TOKEN_FILE = "bot_tokens.json"

# In-memory list of running bots (token + thread)
running_bots = []

# HTML template for the dashboard
HTML = """
<!doctype html>
<html>
<head><title>Anti-Raid Multi-Bot Panel</title></head>
<body>
<h1>Anti-Raid Bot Panel</h1>
<p>Status: {{ status }}</p>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
<form method="post" action="/add">
    <label>Discord Bot Token:</label><br>
    <input type="text" name="token" required style="width:400px;"><br><br>
    <input type="submit" value="Add & Run Bot">
</form>
<h2>Running Bots ({{ count }} / 1 max on free tier)</h2>
<ul>
{% for bot in bots %}
    <li>Bot active (token starts with: {{ bot[:10] }}...)</li>
{% endfor %}
</ul>
<a href="/health">Health Check</a>
</body>
</html>
"""

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                return data.get("tokens", [])
        except:
            return []
    return []

def save_tokens():
    tokens = [b["token"] for b in running_bots]
    with open(TOKEN_FILE, "w") as f:
        json.dump({"tokens": tokens}, f)

def run_bot(token):
    try:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        bot = commands.Bot(command_prefix="!", intents=intents)
        bot.load_extension("admin")   # ← add this line here
        
        @bot.event
        async def on_ready():
            print(f"Bot {bot.user} is ready!")

        # Your existing raid/spam/profanity logic here...
        # (copy from original Main.py - assuming it's there; add if missing)
        # For example placeholder:
        @bot.event
        async def on_member_join(member):
            print(f"{member} joined - raid check placeholder")

        @bot.command()
        async def setup(ctx):
            await ctx.send("Setup placeholder")

        bot.run(token)
    except Exception as e:
        print(f"Bot crashed: {e}")

@app.route("/", methods=["GET"])
def index():
    status = "All good" if running_bots else "No bots running yet"
    bots_tokens = [b["token"] for b in running_bots]
    return render_template_string(HTML, status=status, error=None, count=len(running_bots), bots=bots_tokens)

@app.route("/add", methods=["POST"])
def add_bot():
    token = request.form.get("token").strip()
    if not token:
        return render_template_string(HTML, status="Error", error="No token provided", count=len(running_bots), bots=[])

    if len(running_bots) >= 1:
        return render_template_string(HTML, status="Limit reached", error="Free tier supports only 1 bot. Remove or upgrade.", count=1, bots=[running_bots[0]["token"] if running_bots else ""])

    # Start bot in thread
    thread = threading.Thread(target=run_bot, args=(token,), daemon=True)
    thread.start()

    running_bots.append({"token": token, "thread": thread})
    save_tokens()

    return render_template_string(HTML, status="Bot added & starting!", error=None, count=len(running_bots), bots=[b["token"] for b in running_bots])

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Auto-load and start saved bots
    saved_tokens = load_tokens()
    for token in saved_tokens:
        if len(running_bots) < 1:  # still enforce limit
            thread = threading.Thread(target=run_bot, args=(token,), daemon=True)
            thread.start()
            running_bots.append({"token": token, "thread": thread})

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
