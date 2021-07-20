from pyclickup import ClickUp
from secrets import api_token
import json
from typing import Union, overload
from requests.models import Response
from pathlib import Path
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import date
from dateutil import parser
import re
import random
import uuid
import os
from arrow import Arrow


def get_parent_dir():
    return os.path.dirname(os.path.realpath(__file__))


class ClickUpExt(ClickUp):
    def delete(
        self, path: str, raw: bool = False, **kwargs
    ) -> Union[list, dict, Response]:
        """makes a put request to the API"""
        request = self._req(path, method="delete", **kwargs)
        return request if raw else request.json()


clickup = ClickUpExt(api_token)
team_id = clickup.teams[0].id
user = clickup.get('https://api.clickup.com/api/v2/user')


def reference(clickup):
    main_team = clickup.teams[0]
    main_space = main_team.spaces[0]
    #members = main_space.members

    main_project = main_space.projects[0]
    print(main_space.projects)
    main_list = main_project.lists[0]
    print(main_project.lists)

    tasks = main_list.get_all_tasks(include_closed=True)
    print(str(tasks))


def get_data_from_project(project, file_name):
    proj_data_file = Path(__file__).parent / \
        f"../{project}/data/{file_name}"
    return proj_data_file.open()


def get_conf():
    conf_file = Path(__file__).parent / \
        f"./data/conf.json"
    return json.load(conf_file.open())

def update_conf(conf):
    conf_file = Path(__file__).parent / \
        f"./data/conf.json"
    json.dump(conf, conf_file.open('w+'))
    return get_conf()


def get_goal_from_id(goal_id):
    return clickup.get(f'https://api.clickup.com/api/v2/goal/{goal_id}')


def get_all_goals():
    goal_list = clickup.get(
        f'https://api.clickup.com/api/v2/team/{team_id}/goal')['goals']

    return list(map(lambda goal_rec: get_goal_from_id(goal_rec['id']), goal_list))


def get_date_change():
    today = date.today()
    last_wed_offset = (today.weekday() - 2) % 7
    next_tues_offset = -(today.weekday() - 1) % 7
    last_wed = today - timedelta(days=last_wed_offset)
    next_tues = today + timedelta(days=next_tues_offset)

    return f'{last_wed.month}-{last_wed.day}-{last_wed.year}', f'{next_tues.month}-{next_tues.day}-{next_tues.year}'


def determine_if_change():
    goals_list = get_all_goals(clickup)

def get_goal_from_id(goal_id):
    return clickup.get(f'https://api.clickup.com/api/v2/goal/{goal_id}')

def get_goal_from_search(goal_search):
    goals = get_all_goals()
    if type(goal_search) == str:
        search_list = [
            goal_rec for goal_rec in goals if goal_rec['goal']['name'] == goal_search]
        return search_list[0] if search_list else None

    elif type(goal_search) == list:
        return [goal_rec for goal_rec in goals if goal_rec['goal']['name'] in goal_search]


def get_key_result_from_goal(goal_rec, key_result_search):
    key_results = goal_rec['goal']['key_results']

    if type(key_result_search) == str:
        return [goal_rec for goal_rec in key_results if goal_rec['name'] == key_result_search][0]

    elif type(key_result_search) == list:
        return [goal_rec for goal_rec in key_results if goal_rec['name'] in key_result_search]


def time_completed_to_points(dt: datetime):
    dt_reg = Arrow.fromdatetime(dt, 'America/New_York').datetime
    return (24 - dt_reg.hour) - dt_reg.minute/60 - dt_reg.second/3600


def get_time_limit_points(conf, goal_name, data, proj_list):
    for proj in proj_list:
        total_duration = 0
        goal_duration = conf['Weekly goals update'][goal_name]['toggl_config']['duration']
        for entry in data[proj]:
            total_duration += entry['duration']
            if total_duration >= goal_duration:
                extra = total_duration - goal_duration
                goal_finish_time = parser.parse(
                    entry['stop']) - timedelta(minutes=extra)
                return time_completed_to_points(goal_finish_time)
    return 0.0


def get_last_time_points(conf, goal_name, data, proj_list):
    last_entry = None
    for proj in proj_list:
        total_duration = 0
        final_proj_entry = data[proj][-1]
        if not last_entry or parser.parse(
                final_proj_entry['stop']) > parser.parse(last_entry['stop']):
            last_entry = final_proj_entry
    if not last_entry:
        return 0.0

    goal_finish_time = parser.parse(last_entry['stop'])
    return time_completed_to_points(goal_finish_time)

def update_weekly_key_result(goal_name, key_result_name, steps_current, note):
    goal_rec = get_goal_from_search(goal_name)

    key_result_habit = get_key_result_from_goal(
    goal_rec, key_result_name)

    key_result_habit_id = key_result_habit['id']

    key_result_habit['steps_current'] = steps_current
    key_result_habit['note'] = note
    clickup.put(
    f'https://api.clickup.com/api/v2/key_result/{key_result_habit_id}', data=key_result_habit)

def check_for_extra(goal_name, key_result_name, date: str):
    goal_rec = get_goal_from_search(goal_name)
    key_result = get_key_result_from_goal(goal_rec, key_result_name)
    net_change = 0.0
    for hist_rec in goal_rec['goal']['history']:
        if hist_rec['key_result_id'] == key_result['id'] and hist_rec[
            'note'] == date:
            net_change += hist_rec['steps_taken']
    if not net_change == 0.0:
        return update_weekly_key_result(goal_name, key_result_name, net_change, date)
    
    return 0
def update_time_goal(date=None):
    if not date:
        date = datetime.strftime(datetime.now(), '%m-%d-%y')
    conf = get_conf()
    for goal_name, goal_conf in conf['Weekly goals update']['goals'].items():
        data = get_data_from_project(
            'Toggl', f'{date}_{goal_conf["toggl_config"]["toggl_keyword"]}.json')
        goal_duration = goal_conf['toggl_config']['duration']
        proj_list = conf[goal_conf['toggl_config']['projects']]
        if goal_duration > 0:
            pts = get_time_limit_points(conf, goal_name, data, proj_list)
        else:
            pts = get_last_time_points(conf, goal_name, data, proj_list)
        
        check_for_extra(goal_name, 'Hour Points', date)
        note = datetime.strftime(datetime.now(), '%m-%d-%y')
        key_result_created = update_weekly_key_result(goal_name, 'Hour Points', pts, note)
        if 'err' in key_result_created:
            print(f'Key result of {goal_name} not generated.')


def update_song_count():
    deduped_song_file = get_data_from_project(
        'Spotipy', 'deduped_songs_list.json')
    deduped_songs = json.load(deduped_song_file)
    deduped_songs_len = len(deduped_songs)

    conf = get_conf()
    note = datetime.strftime(datetime.now(), '%m-%d-%y')
    check_for_extra(conf['Weekly goals update']['song_habit']['name'],
        conf['song_habit']['key_result_count'],
        note)
    return update_weekly_key_result(conf['Weekly goals update']['song_habit']['name'],
     conf['song_habit']['key_result_count'],
        deduped_songs_len, note)

def archive_goal(goal_rec):
    goal_id = goal_rec['goal']['id']
    goal_update = {
        'archived': True
    }
    return clickup.put(
        f'https://api.clickup.com/api/v2/goal/{goal_id}', json=goal_update)


def create_goal(goal_name, due_date: str, color=None, description=''):
    if not color:
        color = "%06x" % random.randint(0, 0xFFFFFF)
    due_date_ts = parser.parse(due_date).timestamp() * 1000
    goal = {
    "name": goal_name,
    "due_date": int(due_date_ts),
    "description": description,
    "multiple_owners": True,
    "owners": [
        user['user']['id']
    ],
    "color": f'#{color.lower()}'
    }

    return clickup.post(
        f'https://api.clickup.com/api/v2/team/{team_id}/goal',json=goal)

def create_key_result(goal_id, name, steps_start, steps_end, unit):
    key_result = {
        "name": name,
        "owners": [
            user['user']['id']
        ],
        "type": "number",
        "steps_start": steps_start,
        "steps_end": steps_end,
        "unit": unit,
        "task_ids": [],
        "list_ids": []
    }

    return clickup.post(
        f'https://api.clickup.com/api/v2/goal/{goal_id}/key_result',json=key_result)

def create_weekly_goal(goal_name, goal_conf, start_date, end_date):
    due_date = f'{end_date} 11:59 pm'
    color = goal_conf['clickup_config']['color']
    description = f'{start_date} - {end_date}'
    goal_created =  create_goal(goal_name, due_date, color, description)
    if not 'err' in goal_created:
        create_weekly_key_result(goal_name, goal_created)
        return get_goal_from_id(goal_created['goal']['id'])

    return goal_created

def create_weekly_key_result(goal_name, goal_rec):
    return create_key_result(goal_rec['goal']['id'], 'Hour Points', 0, 
    calculate_points(goal_name), 'pts')

def calculate_points(goal_name):
    conf = get_conf()
    goal_records = conf['Weekly goals update']['goals'][goal_name]['goal_records']
    sorted_goal_recs = goal_records.sort(key=lambda item: parser.parse(item['end_date']))
    if not sorted_goal_recs:
        return 1
    pts_list = [item['pts_achieved'] for item in sorted_goal_recs[-5:]]
    return sum(pts_list)/len(pts_list)
    
def update_weekly_goals():
    conf = get_conf()
    parent_dir = get_parent_dir()
    try:
        curr_goals = json.load(open(f'{parent_dir}\\curr_goals.json'))
    except:
        curr_goals = []
    for goal_name, goal_conf in conf['Weekly goals update']['goals'].items():
        goal_rec = get_goal_from_search(goal_name)
        if not goal_rec:
            new_start_date, new_end_date = get_date_change()
            create_weekly_goal(goal_name, goal_conf, new_start_date, new_end_date)
            continue

        date_pat = r'[0-9]*-[0-9]*-[0-9]*'
        range_pat = rf'{date_pat} - {date_pat}'
        description = goal_rec['goal']['description']
        date_range_str = re.search(range_pat, description).group()
        start_date_str, end_date_str = re.findall(date_pat, date_range_str)
        if not (datetime.now() >= parser.parse(start_date_str) and datetime.now() <= parser.parse(end_date_str)):
            new_start_date, new_end_date = get_date_change()
            archive_goal(goal_rec)
            create_weekly_goal(goal_name, goal_conf, new_start_date, new_end_date)
        
        update_time_goal()


def archive_historical_goals():
    conf = get_conf()
    goal_list = get_goal_from_search(conf['Weekly goals update'])
    for goal in goal_list:
        archive_goal(goal)


"""
with (Path(__file__).parent / f'data/goals.json').open('w+') as file:
    file.write(json.dumps(clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/goal')))
"""

update_weekly_goals()
