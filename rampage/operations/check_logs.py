from beautifultable import BeautifulTable
from datetime import datetime
from discord.message import Message
import requests

from rampage.utils import chunk_message
from rampage.settings import WC_LOG_API_KEY

CLASSIC_LOG_URL = 'https://classic.warcraftlogs.com/v1/'

WC_LOGS_USERS = ['VoldeSC']
MANUAL_RAIDS = ['jcXPk8NTvbz4C1LG', 'zaDtcW4xQ1YHGgvd', 'Yh3MqdTj1BG6fcAD', 'jcXPk8NTvbz4C1LG']
PHASES = {
    '1': datetime.utcfromtimestamp(1566777600),
    '2': datetime.utcfromtimestamp(1573516800),
    '3': datetime.utcfromtimestamp(1581465600),
    '4': datetime.utcfromtimestamp(1586908800),
    '5': datetime.utcfromtimestamp(1595894400),
    '6': datetime.utcfromtimestamp(1605139200),
}


def get_attendance_from_record(record_id: str, phase: str) -> list:
    wc_log_resp = requests.get(f'{CLASSIC_LOG_URL}report/fights/{record_id}?api_key={WC_LOG_API_KEY}')
    fight_data = wc_log_resp.json()
    fight_date = datetime.utcfromtimestamp(float(fight_data['start'])/1000)
    if PHASES[phase] <= fight_date < PHASES.get(str(int(phase) + 1), datetime.utcnow()):
        raiders = fight_data.get('friendlies', [])
        raider_names = [raider.get('name') for raider in raiders]
        return raider_names
    return []


async def generate_attendance_report(message: Message):
    await message.channel.send('Generating report, please wait (May take a few minutes)')

    message_parts = message.content.split(' ')
    for message_part in message_parts:
        if message_part == '':
            message_parts.remove(message_part)

    current_phase = "1"
    if len(message_parts) == 1:
        now = datetime.utcnow()
        for phase, start_date in PHASES.items():
            if start_date <= now:
                current_phase = phase
                continue
            break
    else:
        current_phase = message_parts[1]
        if current_phase not in PHASES.keys():
            await message.channel.send(f'Invalid Phase {current_phase}, must be one of {list(PHASES.keys())}')
            return

    user_attendance = {}
    total_raids = 0
    wc_log_resp = requests.get(f'{CLASSIC_LOG_URL}reports/guild/Rampage/Whitemane/US?api_key={WC_LOG_API_KEY}')
    raid_list = wc_log_resp.json()
    raid_list = [raid.get('id') for raid in raid_list]

    wc_log_resp = requests.get(f'{CLASSIC_LOG_URL}reports/user/VoldeSC?api_key={WC_LOG_API_KEY}')
    user_raid_list = wc_log_resp.json()
    user_raid_list = [raid.get('id') for raid in user_raid_list]
    raid_list.extend(user_raid_list)
    raid_list.extend(MANUAL_RAIDS)

    raid_list = reversed(raid_list)
    for raid in raid_list:
        total_raids += 1
        raid_attendance = get_attendance_from_record(raid, current_phase)
        if len(raid_attendance) > 0:
            for user in user_attendance.keys():
                user_attendance[user]['total'] += 1

            for attendance_record in raid_attendance:
                user_attendance.setdefault(attendance_record, {'attended': 0, 'total': 1})
                user_attendance[attendance_record]['attended'] += 1

    # Create table to render in the discord message
    table = BeautifulTable()
    table.column_headers = ['Name', 'Raids Attended', 'Attendance %']
    msg = f'''
==================================
Attendance Report Phase {current_phase}
==================================

'''
    user_tuple = user_attendance.items()
    user_tuple = sorted(user_tuple, key=lambda x: x[1]['attended'], reverse=True)
    min_percent = 30
    waitlist_records = read_waitlist_file()
    for raider, raids_attended in user_tuple:

        # Accounting for waitlisted raiders
        for waitlist_record in waitlist_records:
            if waitlist_record[0].lower() == raider.lower():
                raids_attended['total'] = raids_attended['total'] - int(waitlist_record[1])
        if raids_attended['total'] >= 1:
            percent = raids_attended['attended'] / raids_attended['total'] * 100
            if percent > min_percent and raids_attended['attended'] > 1:
                row = [raider, raids_attended['attended'], f'{int(percent)}%']
                table.append_row(row)

    msg += str(table)
    await chunk_message(message.channel, msg)


def read_waitlist_file():
    records = []
    with open('waitlist_records.csv', 'r') as wrf:
        for line in wrf:
            if not line.isspace():
                records.append(line.split(','))

    return records


async def waitlist(message: Message):
    message_parts = message.content.split(' ')
    for message_part in message_parts:
        if message_part == '':
            message_parts.remove(message_part)

    if len(message_parts) < 2:
        await message.channel.send(
            f'Invalid waitlist command {message.content}, must be in the format: !waitlist <raider>')
        return
    records = read_waitlist_file()
    waitlist_data = ''
    updated_record = False
    for record in records:
        if record[0].lower() == message_parts[1].lower():
            record[1] = str(int(record[1]) + 1) + "\n"
            updated_record = True
            await message.channel.send(f'Raider {message_parts[1]} waitlist count is now {record[1]}')
        waitlist_data += f'{",".join(record)}'
    if updated_record is False:
        waitlist_data += f'{message_parts[1]},1\n'
        await message.channel.send(f'Raider {message_parts[1]} waitlist count is now 1')

    with open('waitlist_records.csv', 'w+') as wrf:
        wrf.write(waitlist_data)


async def remove_waitlist(message: Message):
    message_parts = message.content.split(' ')
    for message_part in message_parts:
        if message_part == '':
            message_parts.remove(message_part)

    if len(message_parts) < 2:
        await message.channel.send(
            f'Invalid remove waitlist command {message.content}, must be in the format: !removewaitlist <raider>')
        return
    records = read_waitlist_file()
    with open('waitlist_records.csv', 'w+') as wrf:
        updated_record = False
        for record in records:
            if record[0].lower() == message_parts[1].lower():
                record[1] = str(int(record[1]) - 1) + '\n'
                updated_record = True
                await message.channel.send(f'Raider {message_parts[1]} waitlist count is now {record[1]}')
            wrf.write(f'{",".join(record)}')
        if updated_record is False:
            await message.channel.send(f'Raider {message_parts[1]} not found in waitlist records')


async def attendance(message: Message):
    if message.content.startswith('!attendance'):
        await generate_attendance_report(message)
    elif message.content.startswith('!waitlist'):
        await waitlist(message)
    elif message.content.startswith('!removewaitlist'):
        await remove_waitlist(message)
