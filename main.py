import os
import json
import asyncio
import nextcord
from nextcord.ext import commands

# ------------------------------
# CONFIG
# ------------------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN environment variable not set! Set TOKEN in Railway settings.")

GUILD_ID = 1455565972541931553        # Your server ID
VERIFY_ROLE_ID = 1476696223527206962  # Role to give on verification
UNVERIFIED_ROLE_ID = 1455578347219320842  # Role to remove

VERIFY_MESSAGES_FILE = "verify_messages.json"

# ------------------------------
# INTENTS & BOT SETUP
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

# ------------------------------
# LOAD/STORE VERIFY MESSAGES
# ------------------------------
try:
    with open(VERIFY_MESSAGES_FILE, "r") as f:
        verify_messages = set(json.load(f))
except (FileNotFoundError, json.JSONDecodeError):
    verify_messages = set()

def save_verify_messages():
    with open(VERIFY_MESSAGES_FILE, "w") as f:
        json.dump(list(verify_messages), f)

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# ------------------------------
# EVENTS
# ------------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is online and ready!")

@bot.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent):
    if payload.message_id not in verify_messages:
        return
    if str(payload.emoji) != "✅":
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return

    verify_role = guild.get_role(VERIFY_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

    if verify_role:
        await member.add_roles(verify_role)
    if unverified_role:
        await member.remove_roles(unverified_role)

@bot.event
async def on_raw_reaction_remove(payload: nextcord.RawReactionActionEvent):
    if payload.message_id not in verify_messages:
        return
    if str(payload.emoji) != "✅":
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return

    verify_role = guild.get_role(VERIFY_ROLE_ID)
    if verify_role:
        await member.remove_roles(verify_role)

# ------------------------------
# COMMANDS
# ------------------------------
@bot.command(name="verify")
async def verify(ctx):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can send verification embed.")
        return

    embed = nextcord.Embed(
        title="Server Verification",
        description="React with ✅ to get verified!",
        color=nextcord.Color.green()
    )
    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    verify_messages.add(message.id)
    save_verify_messages()  # persist across restarts

# Example ping command
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# ------------------------------
# RUN BOT
# ------------------------------
asyncio.run(bot.start(TOKEN))
