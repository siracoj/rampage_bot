async def chunk_message(channel, msg):
    # Splitting report into 2000 character messages to abide by discord's limits
    chunks = []
    curr_chunk = ''
    char_total = 0
    for line in msg.split('\n'):
        line += '\n'
        char_total += len(line)
        if char_total > 2000:
            chunks.append(curr_chunk)
            char_total = len(line)
            curr_chunk = line
        else:
            curr_chunk += line
    else:
        chunks.append(curr_chunk)

    for chunk in chunks:
        await channel.send(chunk)