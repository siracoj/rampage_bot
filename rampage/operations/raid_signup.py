from beautifultable import BeautifulTable
from discord.message import Message

from rampage.enums import RAIDS, ROLES, CLASS_ROLES, CLASSES


class RaidRoster:
    """
    Class to handle raid roster operations
    """
    
    def __init__(self, message: Message):
        self.message = message
        
    def get_message_parts(self):
        """
        Splitting message into a list based on spaces
        :return: 
        """
        message_parts = self.message.content.split(' ')
        for message_part in message_parts:
            if message_part == '':
                message_parts.remove(message_part)
                
        return message_parts
    
    def get_raider_name(self):
        """
        Gets raider's name based on discord information
        :return: 
        """
        return self.message.author.nick or self.message.author.name

    async def help(self):
        """
        Raid roster bot help message
        :return: 
        """

        msg = f'''
               This is your helpful rampage bot made for all your rampage guild needs!

               Commands:
                   !signup <class> <role> <raid>
                       This adds you to the raid roster for the week
                   !raidroster <raid>
                       This command displays the raidroster for the week
                   !clearroster <raid>
                       Clears the raid roster (officer only command)
                   !removesignup <raid>
                       removes you from the raid roster
                   !removesignup <raid> <name>
                       Removes the specified member from the roster (Officer only command)
                   !help
                       Displays this text

               Valid Options:
                   <class>: {", ".join(CLASSES)}
                   <role>: {", ".join(ROLES)}
                   <raid>: {", ".join(RAIDS)}
                       Note: Choosing permanent signs you up for ALL future raids

               If you have any questions, issues or suggestions please message Crowley
                       '''
        await self.message.channel.send(msg)
        
    async def raid_signup(self):
        """
        Adds raider to selected raid saving it to a text file (I know lol)
        :return: 
        """
        channel = self.message.channel
        raider = [self.get_raider_name()]
        raider.extend(self.get_message_parts()[1:])
        
        # Clearing out extra whitespace
        for raider_part in raider:
            if raider_part == '':
                raider.remove(raider_part)

        # Validating raider message
        if len(raider) != 4:
            await channel.send(
                f'Invalid sign up {self.message.content}. Must be in the format "!signup <class> <role> <raid>"')
            return
        # Raider chose a valid class
        elif raider[1].lower() not in CLASSES:
            await channel.send(f'Invalid Class {raider[1]}, must be one of: {", ".join(CLASSES)}')
            return
        # Raider chose a valid raid
        elif raider[3].upper() not in RAIDS:
            await channel.send(f'Invalid Raid {raider[3]}, must be one of: {", ".join(RAIDS)}')
            return
        # Raider chose a valid role
        elif raider[2].lower() not in ROLES:
            # Trying to handle the various ways people write "healer"
            if raider[2].lower() in ['heal', 'healer', 'heals']:
                raider[2] = 'heals'
            else:
                await channel.send(f'Invalid Role {raider[2]}, must be one of: {", ".join(ROLES)}')
                return
        # Raider chose a valid rol for their class
        elif raider[2].lower() not in CLASS_ROLES.get(raider[1].lower()):
            await channel.send(
                f'Invalid Role {raider[2]} for class {raider[1]}, must be one of: '
                f'{", ".join(CLASS_ROLES.get(raider[1].lower()))}')
            return
        
        # Checking that the raider is not already added
        with open(f'{raider[3].upper()}.txt', 'r') as f:
            for line in f:
                parts = line.split(',')
                if parts[0] == raider[0]:
                    await channel.send(f'Raider {self.message.author.mention} already on the roster!')
                    return
        # Writing to a text file (this is our db...)
        with open(f'{raider[3].upper()}.txt', 'a+') as f:
            f.write(f'{",".join([r for r in raider[:-1]])}\n')
            await channel.send(f'{self.message.author.mention} added to the raid roster!')
            
    async def remove_signup(self):
        """
        Removes raider from signup file
        :return: 
        """
        message_parts = self.get_message_parts()
        channel = self.message.channel
        raider_to_remove = self.get_raider_name()
        
        # Validating message format
        if len(message_parts) < 2:
            await channel.send(
                f'Invalid signup removal {self.message.content}. Must be in the format "!removesignup <raid>" '
                f'or "!removesignup <raid> <name>"')
            return
        
        # If a raider is specified, check that it is an officer removing the raider
        if len(message_parts) > 2:
            if 'Officer' in [role.name for role in self.message.author.roles]:
                raider_to_remove = message_parts[2]
            else:
                await channel.send('You do not have permission to clear the roster')
                
        # So... this essentially re-writes the entire raider file without the raider being removed
        new_roster = ''
        raider_removed = False
        if message_parts[1].upper() not in RAIDS:
            await channel.send(f'Invalid Raid {message_parts[1]}, must be one of: {", ".join(RAIDS)}')
            return
        with open(f'{message_parts[1].upper()}.txt', 'r') as f:
            for line in f:
                raider_parts = line.split(',')
                if raider_parts[0].lower() != raider_to_remove.lower():
                    new_roster += line
                else:
                    raider_removed = True
                    await channel.send(f'{raider_parts[0]} removed from roster')
                    
        # Raider was not found in the list, returning 
        if raider_removed is False:
            await channel.send(f'Could not find raider {raider_to_remove} in roster')
            return
        with open(f'{message_parts[1].upper()}.txt', 'w') as f:
            f.write(new_roster)
    
    async def clear_roster(self):
        """
        Clears the roster for the selected raid
        :return: 
        """
        message_parts = self.get_message_parts()
        channel = self.message.channel
        if len(message_parts) != 2:
            await channel.send(
                f'Invalid roster clear {self.message.content}. Must be in the format "!clearroster <raid>"')
            return
        if message_parts[1].upper() not in RAIDS:
            await channel.send(f'Invalid Raid {message_parts[1]}, must be one of: {", ".join(RAIDS)}')
            return
        
        # Checks permission, then writes over the file blank
        if 'Officer' in [role.name for role in self.message.author.roles]:
            open(f'{message_parts[1].upper()}.txt', 'w').close()
            await channel.send('Roster cleared!')
        else:
            await channel.send('You do not have permission to clear the roster')
            
    async def get_roster(self):
        """
        Gets and returns the selected raid
        :return: 
        """
        message_parts = self.get_message_parts()
        channel = self.message.channel
        if len(message_parts) != 2:
            await channel.send(
                f'Invalid roster query {self.message.content}. Must be in the format "!raidroster <raid>"')
            return

        if message_parts[1].upper() not in RAIDS:
            await channel.send(f'Invalid Raid {message_parts[1]}, must be one of: {", ".join(RAIDS)}')
            return

        # Create table to render in the discord message
        table = BeautifulTable()
        table.column_headers = ['Name', 'Class', 'Role']
        dps = 0
        tank = 0
        heals = 0
        class_count = {}
        msg = f'''
        ==================================
        Roster for {message_parts[1].upper()}
        ==================================

                '''
        # Making sure that all signup duplicates are removed
        signups = set()
        with open(f'{message_parts[1].upper()}.txt', 'r') as f:
            raiders = f.readlines()
            for raider in raiders:
                raider = raider.strip('\n').lower()
                signups.add(raider)

        # Adding in permanent raiders
        with open(f'PERMANENT.txt', 'r') as f:
            raiders = f.readlines()
            for raider in raiders:
                raider = raider.strip('\n').lower()
                signups.add(raider)

        # Creating raider report
        for raider in signups:
            raider_parts = raider.split(',')
            if class_count.get(raider_parts[1].lower()) is not None:
                class_count[raider_parts[1].lower()] += 1
            else:
                class_count[raider_parts[1].lower()] = 1
            if raider_parts[2].lower() == 'dps':
                dps += 1
            elif raider_parts[2].lower() == 'heals':
                heals += 1
            elif raider_parts[2].lower() == 'tank':
                tank += 1
            table.append_row(raider_parts)
        msg += str(table)
        msg += f'\n\n ROLE TOTALS: DPS: {dps} HEALS:{heals} TANKS:{tank}'
        msg += f'\n\n CLASS TOTALS: '
        for class_name, class_amount in class_count.items():
            msg += f'{class_name.lower()}: {class_amount} '

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
        

async def raid_roster_commands(message):
    """
    Route raid roster commands based on operation
    :param message: 
    :return: 
    """
    raid_roster_bot = RaidRoster(message)
    if message.content.startswith('!signup'):
        await raid_roster_bot.raid_signup()
    elif message.content.startswith('!help'):
        await raid_roster_bot.help()
    elif message.content.startswith('!removesignup'):
        await raid_roster_bot.remove_signup()

    elif message.content.startswith('!clearroster'):
        await raid_roster_bot.clear_roster()
       
    elif message.content.startswith('!raidroster'):
        await raid_roster_bot.get_roster()
