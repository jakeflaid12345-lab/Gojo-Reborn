import os
import nextcord
from nextcord.ext import commands
from datetime import timedelta

# ------------------------------
# CONFIG
# ------------------------------
TOKEN = os.getenv("TOKEN")  # Only variable needed

GUILD_ID = 1455565972541931553       # Your server ID
VERIFY_ROLE_ID = 1476696223527206962 # Role to give on verification
UNVERIFIED_ROLE_ID = 1455578347219320842 # Role to remove

# ------------------------------
# INTENTS & BOT SETUP
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

verify_messages = set()  # track verification messages
warnings_db = {}         # user_id: [reasons]

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
    print(f"Logged in as {bot.user}")

@bot.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent):
    if payload.message_id not in verify_messages:
        return
    if str(payload.emoji) != "✅":
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member.bot:
        return

    verify_role = guild.get_role(VERIFY_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

    if verify_role:
        await member.add_roles(verify_role)
    if unverified_role:
        await member.remove_roles(unverified_role)

# ------------------------------
# PREFIX COMMANDS
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

@bot.command(name="ban")
async def ban(ctx, member: nextcord.Member, *, reason="No reason provided"):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention}")

@bot.command(name="kick")
async def kick(ctx, member: nextcord.Member, *, reason="No reason provided"):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention}")

@bot.command(name="mute")
async def mute(ctx, member: nextcord.Member, minutes: int, *, reason="No reason provided"):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"🔇 Muted {member.mention} for {minutes} minutes")

@bot.command(name="warn")
async def warn(ctx, member: nextcord.Member, *, reason="No reason provided"):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    warnings_db.setdefault(member.id, []).append(reason)
    await ctx.send(f"⚠️ Warned {member.mention}")

@bot.command(name="warnings")
async def warnings(ctx, member: nextcord.Member):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    user_warnings = warnings_db.get(member.id, [])
    if not user_warnings:
        await ctx.send("No warnings for this member.")
        return
    formatted = "\n".join(f"{i+1}. {r}" for i, r in enumerate(user_warnings))
    await ctx.send(f"Warnings for {member.mention}:\n{formatted}")

@bot.command(name="unwarn")
async def unwarn(ctx, member: nextcord.Member, index: int):
    if not is_admin(ctx):
        await ctx.send("❌ Only admins can use this command.")
        return
    user_warnings = warnings_db.get(member.id, [])
    if 0 < index <= len(user_warnings):
        removed = user_warnings.pop(index - 1)
        await ctx.send(f"Removed warning: {removed}")
    else:
        await ctx.send("Invalid warning number.")

@bot.command(name="embed")
async def embed(ctx, *, text):
    embed = nextcord.Embed(
        description=text,
        color=nextcord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = nextcord.Embed(title="Help Commands", color=nextcord.Color.gold())
    embed.add_field(name="?verify", value="Sends verification embed (Admin only)", inline=False)
    embed.add_field(name="?ban @user reason", value="Ban a member (Admin only)", inline=False)
    embed.add_field(name="?kick @user reason", value="Kick a member (Admin only)", inline=False)
    embed.add_field(name="?mute @user minutes reason", value="Timeout a member (Admin only)", inline=False)
    embed.add_field(name="?warn @user reason", value="Warn a member (Admin only)", inline=False)
    embed.add_field(name="?warnings @user", value="Check warnings (Admin only)", inline=False)
    embed.add_field(name="?unwarn @user index", value="Remove a warning (Admin only)", inline=False)
    embed.add_field(name="?embed text", value="Sends an embed with your text", inline=False)
    await ctx.send(embed=embed)

# ------------------------------
# RUN BOT
# ------------------------------
bot.run(TOKEN)