# admin.py
import discord
from discord.ext import commands

# List of allowed role IDs that can use the admin commands below
# You can edit this list directly in the code, or later make it load from config/dashboard
ALLOWED_ROLE_IDS = [
    123456789012345678,   # Replace with your actual admin/mod role ID(s)
    987654321098765432,   # Add more as needed (comma separated)
    # 111222333444555666,
]

def is_admin():
    """Custom check: user must have at least one of the allowed role IDs"""
    async def predicate(ctx):
        if not ctx.guild:  # Prevent DM usage if you want
            return False
        user_role_ids = [role.id for role in ctx.author.roles]
        if any(rid in ALLOWED_ROLE_IDS for rid in user_role_ids):
            return True
        # Optional: send a nice error message
        await ctx.send("❌ You don't have permission to use this command (missing required role).")
        return False
    return commands.check(predicate)

# If your bot supports it, you could also use the built-in decorator like this (simpler):
# @commands.has_any_role(*ALLOWED_ROLE_IDS)
# But the custom check above lets you send custom messages and is more flexible.

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    @is_admin()   # ← This restricts it to your chosen roles
    async def ping(self, ctx):
        """Simple test command: shows latency"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! Latency: **{latency}ms**")

    @commands.command(name="addadminrole")
    @is_admin()   # Only admins can add more roles (self-managed)
    async def add_admin_role(self, ctx, role: discord.Role):
        """Add a role ID to the allowed list (temporary in-memory)"""
        if role.id in ALLOWED_ROLE_IDS:
            await ctx.send(f"Role {role.name} ({role.id}) is already allowed.")
            return
        
        ALLOWED_ROLE_IDS.append(role.id)
        await ctx.send(f"Added role **{role.name}** ({role.id}) to allowed admins. "
                       f"Now {len(ALLOWED_ROLE_IDS)} roles can use admin commands.\n"
                       "(Note: this is in-memory — restarts reset the list)")

    @commands.command(name="listadminroles")
    @is_admin()
    async def list_admin_roles(self, ctx):
        """Show current allowed role IDs and names (if still in guild)"""
        if not ALLOWED_ROLE_IDS:
            await ctx.send("No admin roles configured yet.")
            return
        
        lines = []
        for rid in ALLOWED_ROLE_IDS:
            role = ctx.guild.get_role(rid)
            name = role.name if role else "❌ Role not found (deleted?)"
            lines.append(f"• {name} (`{rid}`)")
        
        embed = discord.Embed(title="Allowed Admin Roles", color=0x00ff00)
        embed.description = "\n".join(lines)
        embed.set_footer(text="Only these roles can use admin commands like !ping")
        await ctx.send(embed=embed)

    # Add more commands here as needed, e.g.:
    # @commands.command()
    # @is_admin()
    # async def status(self, ctx):
    #     await ctx.send("Bot is running normally.")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
