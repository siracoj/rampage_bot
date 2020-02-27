from beautifultable import BeautifulTable
from discord.message import Message
import requests

from rampage.utils import chunk_message
from rampage.settings import WC_LOG_API_KEY

CLASSIC_LOG_URL = 'https://classic.warcraftlogs.com/v1/'

WC_LOGS_USERS = ['VoldeSC']
MANUAL_RAIDS = ['jcXPk8NTvbz4C1LG', 'zaDtcW4xQ1YHGgvd', 'Yh3MqdTj1BG6fcAD', 'jcXPk8NTvbz4C1LG']


def get_attendance_from_record(record_id: str) -> list:
    wc_log_resp = requests.get(f'{CLASSIC_LOG_URL}report/fights/{record_id}?api_key={WC_LOG_API_KEY}')
    fight_data = wc_log_resp.json()

    raiders = fight_data.get('friendlies', [])
    raider_names = [raider.get('name') for raider in raiders]
    return raider_names


async def generate_attendance_report(message: Message):
    await message.channel.send('Generating report, please wait')
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
        raid_attendance = get_attendance_from_record(raid)
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
Attendance Report
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
    with open('waitlist_records.csv', 'w+') as wrf:
        updated_record = False
        for record in records:
            if record[0].lower() == message_parts[1].lower():
                record[1] = str(int(record[1]) + 1)
                updated_record = True
                await message.channel.send(f'Raider {message_parts[1]} waitlist count is now {record[1]}')
            wrf.write(f'{",".join(record)}\n')
        if updated_record is False:
            wrf.write(f'{message_parts[1]},1')
            await message.channel.send(f'Raider {message_parts[1]} waitlist count is now 1')


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
                record[1] = str(int(record[1]) - 1)
                updated_record = True
                await message.channel.send(f'Raider {message_parts[1]} waitlist count is now {record[1]}')
            wrf.write(f'{",".join(record)}\n')
        if updated_record is False:
            await message.channel.send(f'Raider {message_parts[1]} not found in waitlist records')


async def attendance(message: Message):
    if message.content.startswith('!attendance'):
        await generate_attendance_report(message)
    elif message.content.startswith('!waitlist'):
        await waitlist(message)
    elif message.content.startswith('!removewaitlist'):
        await remove_waitlist(message)
