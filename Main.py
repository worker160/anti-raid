import discord
from discord.ext import commands
import time
from collections import defaultdict
import threading
from flask import Flask, request, render_template_string

class AntiRaidBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True  # Needed for message content
        super().__init__(command_prefix='!', intents=intents)
        self.join_tracker = []
        self.spam_tracker = defaultdict(list)
        self.bad_words = ["badword1", "badword2"]  # Add your list of profanity words here
        self.setup_events()

    def setup_events(self):
        @self.event
        async def on_ready():
            print(f'Logged in as {self.user}')

        @self.event
        async def on_member_join(member):
            current_time = time.time()
            self.join_tracker.append(current_time)
            # Remove joins older than 60 seconds
            self.join_tracker = [t for t in self.join_tracker if current_time - t < 60]
            if len(self.join_tracker) > 10:  # Adjust threshold: 10 joins in 60 seconds
                print(f"Raid detected in {member.guild.name}!")
                # Ban the last 10 members (adjust as needed)
                recent_members = sorted(member.guild.members, key=lambda m: m.joined_at)[-10:]
                for m in recent_members:
                    try:
                        await m.ban(reason="Anti-raid protection: suspected raid")
                    except discord.Forbidden:
                        print(f"Missing permissions to ban {m}")

        @self.event
        async def on_message(message):
            if message.author.bot:
                return
            # Anti-spam
            current_time = time.time()
            self.spam_tracker[message.author.id].append(current_time)
            self.spam_tracker[message.author.id] = [t for t in self.spam_tracker[message.author.id] if current_time - t < 30]
            if len(self.spam_tracker[message.author.id]) > 5:  # 5 messages in 30 seconds
                mute_role = discord.utils.get(message.guild.roles, name="Muted")
                if mute_role:
                    try:
                        await message.author.add_roles(mute_role)
                        await message.channel.send(f"{message.author.mention} has been muted for spamming.")
                    except discord.Forbidden:
                        print("Missing permissions to mute")
            # Anti-profanity
            if any(word in message.content.lower() for word in self.bad_words):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, watch your language!")
            await self.process_commands(message)

        @self.command(name='setup')
        async def setup_command(ctx):
            # Create Muted role if it doesn't exist
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted_role:
                muted_role = await ctx.guild.create_role(name="Muted")
            # Set permissions for Muted role in all channels
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
            await ctx.send("Setup complete: Muted role created and permissions set.")

# Flask app for the hosting panel
app = Flask(__name__)
running_bots = []  # List of (thread, token)
MAX_BOTS = 5

@app.route('/')
def home():
    return render_template_string("""
    <html>
    <body>
    <h1>Anti-Raid Bot Hosting Panel</h1>
    <p>This panel allows you to add up to 5 bot tokens. Each bot will run as an independent anti-raid protector.</p>
    <form action="/add" method="post">
        <input name="token" placeholder="Bot Token" required>
        <button type="submit">Add Bot</button>
    </form>
    <h2>Running Bots</h2>
    <ul>
    {% for i, bot in enumerate(running_bots) %}
        <li>Bot {{ i+1 }} (Token ending in {{ bot[1][-4:] }}): Running</li>
    {% endfor %}
    </ul>
    </body>
    </html>
    """, running_bots=running_bots)

@app.route('/add', methods=['POST'])
def add_bot():
    if len(running_bots) >= MAX_BOTS:
        return "Maximum of 5 bots reached."
    token = request.form['token']
    def run_bot():
        bot = AntiRaidBot()
        bot.run(token)
    thread = threading.Thread(target=run_bot)
    thread.start()
    running_bots.append((thread, token))
    return "Bot added and started successfully!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
