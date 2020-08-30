async def chunk_message(channel, msg):
    # Splitting report into 2000 character messages to abide by discord's limits
    chunks = []
    curr_chunk = ''
    char_total = 0
    for line in msg.split('\n'):
        line += '\n'
        char_total += len(line)
        if char_total > 1950:
            chunks.append(curr_chunk)
            char_total = len(line)
            curr_chunk = line
        else:
            curr_chunk += line
    else:
        chunks.append(curr_chunk)

    for chunk in chunks:
        await channel.send(f'```\n{chunk}\n```')

def get_emoji_from_name(server, emoji):
    """
    Returns string of emoji name and id for use in messages
    """
    emojis = server.emojis 

    for server_emoji in emojis:
        if server_emoji.name == emoji:
            return f"{server_emoji}"