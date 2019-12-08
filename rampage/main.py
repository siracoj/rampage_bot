import discord

from rampage.operations.raid_signup import raid_roster_commands
from rampage.settings import TOKEN

client = discord.Client()


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    channel = message.channel
    if channel.name in ['bot_test', 'raid-signups']:
        await raid_roster_commands(message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
