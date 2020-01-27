import discord

from rampage.operations.check_logs import generate_attendance_report
from rampage.operations.raid_signup import raid_roster_commands
from rampage.settings import TOKEN

client = discord.Client()


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    channel = message.channel
    if channel.name == 'bot_test':
        await raid_roster_commands(message)
        await generate_attendance_report(message)
    if channel.name == 'raid-signups':
        await raid_roster_commands(message)
    elif channel.name == 'raid-attendance':
        await generate_attendance_report(message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
