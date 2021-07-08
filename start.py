from pyclickup import ClickUp
from secrets import api_token
import json
from typing import Union, overload
from requests.models import Response
from pathlib import Path
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import date


class ClickUpExt(ClickUp):
    def delete(
        self, path: str, raw: bool = False, **kwargs
    ) -> Union[list, dict, Response]:
        """makes a put request to the API"""
        request = self._req(path, method="delete", **kwargs)
        return request if raw else request.json()


clickup = ClickUpExt(api_token)
team_id = clickup.teams[0].id

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
    
    return list(map(lambda goal_rec: get_goal_from_id(goal_rec['id']), goal_list ))


def get_date_change():
    today = date.today()
    last_wed_offset = (today.weekday() - 2) % 7
    next_tues_offset = -(today.weekday() - 1) % 7
    last_wed = today - timedelta(days=last_wed_offset)
    next_tues = today + timedelta(days=next_tues_offset)

    return last_wed, next_tues


def determine_if_change():
    goals_list = get_all_goals(clickup)


def get_goal_from_search(goal_search):
    goals = get_all_goals()
    if type(goal_search) == str:
        return [goal_rec for goal_rec in goals if goal_rec['goal']['name'] == goal_search][0]

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


def archive_historical_goals():
    conf = get_conf()
    goal = get_goal_from_search(conf['Weekly goals update'])
    goal_id = goal['id']
    goal['archived'] = True
    clickup.put(f'https://api.clickup.com/api/v2/goal/{goal_id}', data=goal)

# print(clickup.headers)


"""
with (Path(__file__).parent / f'data/goals.json').open('w+') as file:
    file.write(json.dumps(clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/goal')))
"""

update_song_count()
