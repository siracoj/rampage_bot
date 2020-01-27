from beautifultable import BeautifulTable
from discord.message import Message
import requests

from rampage.utils import chunk_message
from rampage.settings import WC_LOG_API_KEY

CLASSIC_LOG_URL = 'https://classic.warcraftlogs.com/v1/'

WC_LOGS_USERS = ['VoldeSC']
MANUAL_RAIDS = ['jcXPk8NTvbz4C1LG', 'zaDtcW4xQ1YHGgvd', 'Dvwqd9K6WPLFgzMG', 'Yh3MqdTj1BG6fcAD', 'jcXPk8NTvbz4C1LG']

def get_attendance_from_record(record_id: str) -> list:
    wc_log_resp = requests.get(f'{CLASSIC_LOG_URL}report/fights/{record_id}?api_key={WC_LOG_API_KEY}')
    fight_data = wc_log_resp.json()

    raiders = fight_data.get('friendlies', [])
    raider_names = [raider.get('name') for raider in raiders]
    return raider_names


async def generate_attendance_report(message: Message):
    if message.content.startswith('!attendance'):
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
        rows = 0
        for raider, raids_attended in user_tuple:
            rows += 1
            percent = raids_attended['attended'] / raids_attended['total'] * 100
            if percent > min_percent and raids_attended['attended'] > 1:
                row = [raider, raids_attended['attended'], f'{int(percent)}%']
                table.append_row(row)

        msg += str(table)
        await chunk_message(message.channel, msg)
