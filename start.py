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


def update_song_count():
    deduped_song_file = get_data_from_project(
        'Spotipy', 'deduped_songs_list.json')
    deduped_songs = json.load(deduped_song_file)
    deduped_songs_len = len(deduped_songs)

    conf = get_conf()
    song_count_goal = get_goal_from_search(conf['song_habit']['name'])
    key_result_habit = get_key_result_from_goal(
        song_count_goal, conf['song_habit']['key_result_count'])
    key_result_habit_id = key_result_habit['id']

    note = datetime.strftime(datetime.now(), '%m-%d-%y')
    key_result_habit['steps_current'] = deduped_songs_len
    key_result_habit['note'] = note
    clickup.put(
        f'https://api.clickup.com/api/v2/key_result/{key_result_habit_id}', data=key_result_habit)


def archive_goal(goal_rec):
    goal_id = goal_rec['goal']['id']
    goal_rec['goal']['archived'] = True
    clickup.put(
        f'https://api.clickup.com/api/v2/goal/{goal_id}', data=goal_rec)


def create_goal(goal_name, start_date, due_date, color="%06x" % random.randint(0, 0xFFFFFF), description=''):
    parent_dir = get_parent_dir()
    goal = json.load(open(f'{parent_dir}/data/goals.json'))['goals'][0]
    goal['name'] = goal_name
    goal['due_date'] = str(parser.parse(due_date).timestamp())
    goal['team_id'] = team_id
    goal['description'] = description
    goal['owners'] = [user['user']]
    goal['multiple_owners'] = False
    goal['color'] = color.lower()
    goal['team_id'] = team_id
    goal['creator'] = int(user['user']['id'])
    goal['start_date'] = str(parser.parse(start_date).timestamp())
    goal['private'] = False
    goal['archived'] = False
    goal['multiple_owners'] = True
    goal['folder_id'] = None
    goal['members'] = []
    goal['key_results'] = []
    goal['percent_completed'] = 0.0
    goal['history'] = []
    goal['id'] = str(uuid.uuid1())
    goal["pretty_id"] = str(random.randint(20, 100))
    goal["pretty_url"] = f"https://app.clickup.com/8609598/goals/{goal['pretty_id']}"

    goal.pop('editor_token')
    goal.pop('pinned')
    goal.pop('date_updated')
    goal.pop('owner')
    goal.pop('key_result_count')
    goal.pop('last_update')

    trial = """
    {
  "goals": [
    {
      "id": "e53a033c-900e-462d-a849-4a216b06d930",
      "name": "Updated Goal Name",
      "team_id": "%d",
      "date_created": "1568044355026",
      "start_date": null,
      "due_date": "1568036964079",
      "description": "Updated Goal Description",
      "private": false,
      "archived": false,
      "creator": "%d",
      "color": "#32a852",
      "pretty_id": "621",
      "multiple_owners": true,
      "folder_id": null,
      "members": [],
      "owners": [
      ],
      "key_results": [],
      "percent_completed": 0,
      "history": [],
      "pretty_url": "https://app.clickup.com/512/goals/21"
    }
  ],
  "folders": [
  ]
}
    """%(int(team_id), int(user['user']['id']))

    new_goal = {'goal': goal}
    print(json.dumps(new_goal, indent=4))
    print(len(goal))
    print(clickup.post(
        f'https://api.clickup.com/api/v2/team/{team_id}/goal', data=json.loads(trial)))


def create_weekly_goal(goal_name, start_date, end_date):
    due_date = f'{end_date} 11:59 pm'
    conf = get_conf()
    color = conf['Weekly goals update'][goal_name]['color']
    description = f'{start_date} - {end_date}'
    create_goal(goal_name, start_date, due_date, color, description)


def update_weekly_goal():
    conf = get_conf()
    for goal_name in conf['Weekly goals update']:
        goal_rec = get_goal_from_search(goal_name)
        if not goal_rec:
            new_start_date, new_end_date = get_date_change()
            create_weekly_goal(goal_name, new_start_date, new_end_date)
            continue

        date_pat = r'[0-9]*-[0-9]*-[0-9]*'
        range_pat = rf'{date_pat} - {date_pat}'
        description = goal_rec['goal']['description']
        date_range_str = re.search(range_pat, description).group()
        start_date_str, end_date_str = re.findall(date_pat, date_range_str)
        if not (datetime.now() >= datetime.strptime(start_date_str, '%m-%d-%y') and datetime.now() <= datetime.strptime(end_date_str, '%m-%d-%y')):
            archive_goal(goal_rec)
            new_start_date, new_end_date = get_date_change()
            create_weekly_goal(goal_name, new_start_date, new_end_date)


def archive_historical_goals():
    conf = get_conf()
    goal_list = get_goal_from_search(conf['Weekly goals update'])
    for goal in goal_list:
        archive_goal(goal)

"""
with (Path(__file__).parent / f'data/goals.json').open('w+') as file:
    file.write(json.dumps(clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/goal')))
"""

update_weekly_goal()
