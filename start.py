from pyclickup import ClickUp
from secrets import api_token
import json
from typing import Union
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

def get_goals_list():
    return clickup.get(
    f'https://api.clickup.com/api/v2/team/{team_id}/goal')['goals']

def get_date_change():
    today = date.today()
    last_wed_offset = (today.weekday() - 2) % 7
    next_tues_offset = -(today.weekday() - 1) % 7
    last_wed = today - timedelta(days=last_wed_offset)
    next_tues = today + timedelta(days=next_tues_offset)
    
    return last_wed, next_tues

def determine_if_change():
    goals_list = get_goals_list(clickup)
    


team_id = clickup.teams[0].id
# print(clickup.headers)

"""
with (Path(__file__).parent / f'data/goals.json').open('w+') as file:
    file.write(json.dumps(clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/goal')))
"""

for goal_rec in goals:
    if 'Finish 1 hour of work per day after lunch' in goal_rec['name']:
        goal_id = goal_rec['id']
        goal = goal_rec
        break
goal['archived'] = True
clickup.put(f'https://api.clickup.com/api/v2/goal/{goal_id}', data=goal)
