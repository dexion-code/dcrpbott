import discord  # type: ignore[import]
from discord.ext import commands  # type: ignore[import]
from discord import app_commands  # type: ignore[import]
import asyncio


# Define intents. GUILD_MEMBERS is privileged and must be enabled in Developer Portal.
intents = discord.Intents.default()
intents.members = True # Required to access member information
intents.message_content = True # Required for message-based commands, good practice

# Initialize the bot with a command prefix (though we'll use slash commands)
# and the defined intents.
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    # Sync slash commands to make them available in Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print('Bot is ready!')

# Define the /raid slash command
@bot.tree.command(name="raid", description="Bans all members without specified roles.")
@app_commands.describe(
    role1="1449181706731917442",
    role2="1395308561575186574",
    role3="1524761475997241486"
)
@commands.has_permissions(ban_members=True) # Only users with ban permissions can use this
async def raid(interaction: discord.Interaction, role1: str, role2: str, role3: str):
    await interaction.response.send_message("Initiating raid protection... This may take a moment.", ephemeral=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
        return

    # Convert role IDs (strings) to actual Role objects
    try:
        protected_role_ids = {int(role1), int(role2), int(role3)}
        protected_roles = [guild.get_role(role_id) for role_id in protected_role_ids if guild.get_role(role_id)]
        if len(protected_roles) != 3:
            await interaction.followup.send("One or more provided role IDs are invalid or do not exist.", ephemeral=True)
            return
    except ValueError:
        await interaction.followup.send("Invalid role ID format. Please provide numeric IDs.", ephemeral=True)
        return

    members_to_ban = []
    async for member in guild.fetch_members(limit=None):
        # Skip bots and the invoker of the command for safety
        if member.bot or member == interaction.user:
            continue

        # Check if the member has ANY of the protected roles
        has_protected_role = False
        for protected_role in protected_roles:
            if protected_role in member.roles:
                has_protected_role = True
                break
        
        if not has_protected_role:
            members_to_ban.append(member)

    if not members_to_ban:
        await interaction.followup.send("No members found to ban without the specified roles.", ephemeral=True)
        return

    # Confirmation step (highly recommended for destructive commands)
    confirm_message = f"Are you sure you want to ban {len(members_to_ban)} members who do not have roles: {', '.join([r.name for r in protected_roles])}? This action is irreversible. Reply with 'confirm' within 30 seconds."
    await interaction.followup.send(confirm_message)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel and m.content.lower() == 'confirm'

    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await interaction.followup.send("Confirmation timed out. No members were banned.", ephemeral=True)
        return

    banned_count = 0
    failed_bans = []
    for member in members_to_ban:
        try:
            await guild.ban(member, reason="Raid protection: Did not possess required roles.")
            banned_count += 1
            await asyncio.sleep(0.5) # Small delay to avoid rate limits
        except discord.Forbidden:
            failed_bans.append(f"{member.display_name} (Bot lacks permissions)")
        except Exception as e:
            failed_bans.append(f"{member.display_name} (Error: {e})")

    result_message = f"Raid protection complete. Banned {banned_count} members."
    if failed_bans:
        result_message += f"\nFailed to ban: {', '.join(failed_bans)}"
    
    await interaction.followup.send(result_message)

# Run the bot
bot.run("MTUyNDgxNDAwMTE0MDI3MzE1Mg.G2P3ei.FDS6ar4aV6hIE_41-qrV5QQcQd6c3_3mjKu5hg") 