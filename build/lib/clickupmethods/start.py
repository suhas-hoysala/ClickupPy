import json
from pathlib import Path
import datetime
from datetime import date
from dateutil import parser
import random
import os
from togglmethods.drivers import *
import decimal
import spotifymethods
from clickupmethods.clickupext import ClickUpExt
from clickupmethods.utilmethods import *

methods_map = {
    "morning": morning_time_entries,
    "evening": evening_time_entries,
    "full_day": full_day_time_entries,
    "afternoon": afternoon_time_entries,
    "weekly": weekly_time_entries
}

def get_parent_dir():
    return os.path.dirname(os.path.realpath(__file__))


def get_conf():
    conf_file = Path(__file__).parent / \
        f"./data/conf.json"
    return json.load(conf_file.open())


api_token = get_conf()['api_token']
headers = {
    "Accept": "*/*",
    "AcceptEncoding": "gzip, deflate",
    "Authorization": api_token,
    "Connection": "keep-alive",
}

clickup = ClickUpExt(api_token)
user = clickup.get('https://api.clickup.com/api/v2/user')
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


def get_time_tracking_data(start_time: dt, end_time: dt):
    start_time_ms = str(int(start_time.timestamp()*1000))
    end_time_ms = str(int(end_time.timestamp()*1000))
    return clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/time_entries?start_date={start_time_ms}&end_date={end_time_ms}')

def get_day_time_tracking_data(day: dt = dt.now()):
    dt_of_day = dt(day.year, day.month, day.day).replace(tzinfo=None).astimezone(tz=timezone.utc)
    return get_time_tracking_data(dt_of_day, dt_of_day + timedelta(days=1))

def export_time_tracking_data(day: dt = dt.now()):
    clickup_time_data = get_day_time_tracking_data(day)
    if not 'data' in clickup_time_data:
        return
    for rec in clickup_time_data['data']:
        name = rec['task']['name']
        start = dt.fromtimestamp(int(rec['start'])/1000)
        duration = int(int(rec['duration'])/1000)
        tags = [str(rec['id']), str(rec['task']['id'])]
        if not validate_task(rec) and duration > 0:
            print(create_time_entry(name, start, duration, tags=tags))
    pass

def validate_task(task_rec):
    start = dt.fromtimestamp(int(task_rec['start'])/1000)
    end =  dt.fromtimestamp(int(task_rec['end'])/1000)
    all_times = time_entries_in_range(start, end)
    if not all_times:
        return False
    for entry in all_times:
        if not 'tags' in entry:
            continue
        if any([str(task_rec['id']) in entry['tags']]):
            return True

def update_conf(conf):
    conf_file = Path(__file__).parent / \
        f"./data/conf.json"
    json.dump(conf, conf_file.open('w+'))
    return get_conf()


def resolve_data_file(file_name):
    write_file = Path(__file__).parent / \
        f'./data/{file_name}'.replace(':', '').replace(' ', '_')

    write_file.parent.mkdir(parents=True, exist_ok=True)
    return write_file


def get_goal_from_id(goal_id):
    return clickup.get(f'https://api.clickup.com/api/v2/goal/{goal_id}')


def get_all_goals():
    date = dt.strftime(dt.now(), '%m-%d-%y')
    file_name = f'{date}_all_goals.json'
    file_data = resolve_data_file(file_name)
    goal_dict = clickup.get(
        f'https://api.clickup.com/api/v2/team/{team_id}/goal')
    goal_list = goal_dict['goals']

    goal_list = list(
        map(lambda goal_rec: get_goal_from_id(goal_rec['id']), goal_list))
    json.dump(goal_list, file_data.open('w+'))
    return goal_list


def get_date_change(day: str = None, start_day: str = 'Wed'):
    if not day:
        day = date.today()
    else:
        day = parser.parse(day)

    start_day = parser.parse(start_day).weekday()

    start_day_offset = (day.weekday() - start_day) % 7
    end_day_offset = -(day.weekday() - (start_day-1)) % 7
    start_day_date = day - datetime.timedelta(days=start_day_offset)
    end_day_date = day + datetime.timedelta(days=end_day_offset)

    return f'{start_day_date.month}-{start_day_date.day}-{start_day_date.year}', f'{end_day_date.month}-{end_day_date.day}-{end_day_date.year}'


def determine_if_change():
    goals_list = get_all_goals(clickup)


def get_goal_from_id(goal_id):
    return clickup.get(f'https://api.clickup.com/api/v2/goal/{goal_id}')


def get_goal_from_search(goal_search, description=None):
    goals = get_all_goals()
    if type(goal_search) == str:
        search_list = [
            goal_rec for goal_rec in goals if goal_rec['goal']['name'] == goal_search
            and (not description or str(goal_rec['goal']['description']).strip() == description)
        ]
        return search_list[0] if search_list else None

    elif type(goal_search) == list:
        return [goal_rec for goal_rec in goals if goal_rec['goal']['name'] in goal_search]


def get_key_result_from_goal(goal_rec, key_result_search):
    key_results = goal_rec['goal']['key_results']

    if type(key_result_search) == str:
        key_result_list = [goal_rec for goal_rec in key_results if goal_rec['name'] == key_result_search]
        return key_result_list[0] if key_result_list else None

    elif type(key_result_search) == list:
        return [goal_rec for goal_rec in key_results if goal_rec['name'] in key_result_search]


def time_completed_to_points(dt: dt):
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
    return (24 - dt.hour) - dt.minute/60 - dt.second/3600


def get_time_limit_points(conf, goal_duration, toggl_data, proj_list, task_names):
    total_duration = 0.0
    for proj in proj_list:
        if not proj in toggl_data:
            continue
        rel_tasks = [rec for rec in toggl_data[proj] if not task_names or any([name in rec['description'] for name in task_names])]
        rel_tasks.sort(key=lambda item: item['start'])
        for entry in rel_tasks:
            total_duration += entry['duration']/60.0
            if total_duration >= goal_duration:
                extra = total_duration - goal_duration
                goal_finish_time = parser.parse(
                    entry['stop']) - timedelta(minutes=extra)
                goal_finish_time = goal_finish_time.replace(
                    tzinfo=timezone.utc).astimezone(tz=None)
                return_value = time_completed_to_points(goal_finish_time)
                return return_value
    return 0.0


def get_last_time_points(data, proj_list,  task_names):
    last_entry = None
    for proj in proj_list:
        if not proj in data or not data[proj]:
            continue
        rel_tasks = [rec for rec in data[proj] if not task_names or any([name in rec['description'] for name in task_names])]
        final_proj_entry = rel_tasks[-1]
        if not last_entry or parser.parse(
                final_proj_entry['stop']) > parser.parse(last_entry['stop']):
            last_entry = final_proj_entry
    if not last_entry:
        return 0.0

    goal_finish_time = parser.parse(last_entry['stop'])
    goal_finish_time = goal_finish_time.replace(
        tzinfo=timezone.utc).astimezone(tz=None)
    return time_completed_to_points(goal_finish_time)

def update_key_result(key_result_id, steps_current, note):
    key_result_habit_new = {
        'steps_current': steps_current,
        'note': note
    }

    return clickup.put(
        f'https://api.clickup.com/api/v2/key_result/{key_result_id}', json=key_result_habit_new)

def update_weekly_key_result(goal_name, key_result_name, steps_current, note):
    goal_rec = get_goal_from_search(goal_name)
    if not goal_rec:
        return {}

    key_result_habit = get_key_result_from_goal(
        goal_rec, key_result_name)

    if not key_result_habit:
        key_result_habit = create_key_result(goal_rec['goal']['id'], key_result_name, 0.0, 1.0, 'pts')

    key_result_habit_id = key_result_habit['id']

    key_result_habit_new = {
        'steps_current': steps_current,
        'note': note
    }

    return clickup.put(
        f'https://api.clickup.com/api/v2/key_result/{key_result_habit_id}', json=key_result_habit_new)


def update_control_key_result(goal_name, note):
    goal_rec = get_goal_from_search(goal_name)
    key_result = get_key_result_from_goal(goal_rec, 'Hour Points')
    if not key_result:
        key_result = create_key_result(goal_rec['goal']['id'], 'Hour Points', 0,
                              calculate_hour_points(goal_name), 'pts')['key_result']

    percent_completed = key_result['percent_completed']
    decimal.getcontext().rounding = decimal.ROUND_DOWN
    new_percent_completed_dec = decimal.Decimal(percent_completed)
    new_percent_completed = float(round(new_percent_completed_dec, 2))

    if new_percent_completed > 0.99:
        new_percent_completed = 0.99

    return update_weekly_key_result(goal_name, 'Control Points',
                                    new_percent_completed, note)


def get_current_pts(goal_name):
    goal_rec = get_goal_from_search(goal_name)
    key_result = get_key_result_from_goal(goal_rec, 'Hour Points')
    if not key_result:
        key_result = create_key_result(goal_rec['goal']['id'], 'Hour Points', 0,
                              calculate_hour_points(goal_name), 'pts')['key_result']
    return key_result['steps_current']


def check_for_extra(goal_name, key_result_name, date: str):
    goal_rec = get_goal_from_search(goal_name)
    key_result = get_key_result_from_goal(goal_rec, key_result_name)
    if not key_result:
        key_result = create_key_result(goal_rec['goal']['id'], 'Hour Points', 0,
                              calculate_hour_points(goal_name), 'pts')['key_result']
    net_change = 0.0
    no_entry = True
    for hist_rec in goal_rec['goal']['history']:
        if hist_rec['key_result_id'] == key_result['id'] and hist_rec[
                'note'] == date:
            no_entry = False
            net_change += hist_rec['steps_taken']
    if no_entry:
        return 'No entry'
    return net_change

def get_toggl_data(date, toggl_keyword: str):
    if toggl_keyword in methods_map:
        return methods_map[toggl_keyword](date)
    time1, time2 = toggl_keyword.split(' - ')
    return by_times(date, date, time1, time2)


def update_time_goal(date=None):
    if not date:
        date = dt.strftime(dt.now(), '%m-%d-%y')

    conf = get_conf()
    for goal_name, goal_conf in conf['Weekly goals update']['goals'].items():
        toggl_keyword = goal_conf["toggl_config"]["toggl_keyword"]
        toggl_data = get_toggl_data(date, toggl_keyword)
        goal_duration = goal_conf['toggl_config']['duration']
        proj_list = conf['Weekly goals update'][goal_conf['toggl_config']['projects']]
        task_names = goal_conf['toggl_config']['names']
        if goal_duration > 0:
            pts = get_time_limit_points(conf, goal_duration, toggl_data, proj_list, task_names)
        else:
            pts = get_last_time_points(toggl_data, proj_list, task_names)

        extra_pts = check_for_extra(goal_name, 'Hour Points', date)
        curr_pts = get_current_pts(goal_name)
        if extra_pts != 'No entry' and extra_pts > 0.001 and abs(extra_pts - pts) > 0.001:
            update_weekly_key_result(
                goal_name, 'Hour Points',
                curr_pts - extra_pts, date
            )
            curr_pts -= extra_pts
        if (extra_pts != 'No entry' and abs(
            extra_pts - pts) > 0.001) or extra_pts == 'No entry':
            key_result_created = update_weekly_key_result(
                goal_name, 'Hour Points', curr_pts + pts, date)
            if 'err' in key_result_created:
                print(f'Key result of {goal_name} not generated.')
            else:
                update_control_key_result(goal_name, date)
            


def update_song_count():
    deduped_songs = spotifymethods.TodoSpotify.SongCountUpdater.get_deduped_songs_list()
    deduped_songs_len = len(deduped_songs)

    conf = get_conf()
    note = dt.strftime(dt.now(), '%m-%d-%y')
    
    return update_weekly_key_result(conf['Weekly goals update']['song_habit']['name'],
                                    conf['Weekly goals update']['song_habit']['key_result_count'],
                                    deduped_songs_len, note)

def update_song_artists_count():
    conf = get_conf()
    target = 30
    target_artists_count = spotifymethods.TodoSpotify.SongCountUpdater.get_target_artists_count()
    goal_rec = get_goal_from_search(conf['Weekly goals update']['song_habit']['name'])
    key_result_dict = {
        key_result['name']: key_result for key_result in goal_rec['goal']['key_results']
        if str(key_result['name']).endswith('song count')
    }
    date = dt.strftime(dt.now(), '%m-%d-%y')
    for artist_name, artist_count in target_artists_count.items():
        key_result_name = f'{artist_name} song count'
        if not key_result_name in key_result_dict:
            key_result = create_key_result(goal_rec['goal']['id'], key_result_name, 0, target, 'songs')
            update_key_result(key_result['key_result']['id'], artist_count, date)
        else:
            key_result = key_result_dict[key_result_name]
            update_key_result(key_result['id'], artist_count, date)
            key_result_dict.pop(key_result_name)
    
    for remaining_artist_name, remaining_key_result in key_result_dict.items():
        key_result_id = remaining_key_result['id']
        clickup.delete(f'https://api.clickup.com/api/v2/key_result/{key_result_id}')


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
        f'https://api.clickup.com/api/v2/team/{team_id}/goal', json=goal)


def create_key_result(goal_id, name, steps_start, steps_end, unit):
    if get_key_result_from_goal(get_goal_from_id(goal_id), name):
        return {}
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
        f'https://api.clickup.com/api/v2/goal/{goal_id}/key_result', json=key_result)


def create_weekly_goal(goal_name, goal_conf, start_date, end_date):
    due_date = f'{end_date} 11:59 pm'
    color = goal_conf['clickup_config']['color']
    description = f'{start_date} - {end_date}'
    goal_created = create_goal(goal_name, due_date, color, description)
    if not 'err' in goal_created:
        create_weekly_key_results(goal_name, goal_created)
        return get_goal_from_id(goal_created['goal']['id'])

    return goal_created


def create_weekly_key_results(goal_name, goal_rec):
    return [create_key_result(goal_rec['goal']['id'], 'Hour Points', 0,
                              calculate_hour_points(goal_name), 'pts'),
            create_key_result(goal_rec['goal']['id'], 'Control Points', 0,
                              1.0, 'pts')
            ]


def calculate_hour_points(goal_name):
    conf = get_conf()
    goal_records = conf['Weekly goals update']['goals'][goal_name]['goal_records']

    goal_records.sort(key=lambda item: dt.fromtimestamp(
        int(item['due_date'])/1000))
    if not goal_records:
        return 1
    pts_list = [item['pts_achieved'] for item in goal_records[-5:]]
    avg = sum(pts_list)/len(pts_list)
    return avg if avg > 0 else 1


def update_goal_hist(existing_goal_rec):
    if not existing_goal_rec:
        return None

    goal_name = existing_goal_rec['goal']['name']
    due_date = existing_goal_rec['goal']['due_date']
    key_result = get_key_result_from_goal(existing_goal_rec, 'Hour Points')
    if not key_result:
        key_result = create_key_result(existing_goal_rec['goal']['id'], 'Hour Points', 0,
                              calculate_hour_points(goal_name), 'pts')
    pts_achieved = key_result['steps_current']
    completed = key_result['completed']
    conf = get_conf()
    conf['Weekly goals update']['goals'][goal_name]['goal_records'].append(
        {
            'pts_achieved': pts_achieved,
            'completed': completed,
            'due_date': due_date
        }
    )
    update_conf(conf)


def update_weekly_goals(day: str = None):
    conf = get_conf()

    if not day:
        day = dt.strftime(dt.today(), '%m-%d-%y')
    for goal_name, goal_conf in conf['Weekly goals update']['goals'].items():
        start_date, end_date = get_date_change(day)
        goal_rec = get_goal_from_search(
            goal_name, description=f'{start_date} - {end_date}')
        if not goal_rec:
            existing_goal_rec = get_goal_from_search(goal_name)
            existing_goal_rec = archive_goal(
                existing_goal_rec) if existing_goal_rec else None
            update_goal_hist(existing_goal_rec)

            create_weekly_goal(goal_name, goal_conf,
                               start_date, end_date)

    dates_of_week = [parser.parse(start_date) + datetime.timedelta(days=x)
                     for x in range(0, (parser.parse(day)-parser.parse(start_date)).days+1)]

    for date in dates_of_week:
        update_time_goal(dt.strftime(date, '%m-%d-%y'))


def archive_historical_goals():
    conf = get_conf()
    goal_list = get_goal_from_search(conf['Weekly goals update'])
    for goal in goal_list:
        archive_goal(goal)

def export_weekly_time_tracking_data(day=None):
    if not day:
        day = dt.strftime(dt.today(), '%m-%d-%y')
    start_date, end_date = get_date_change(day)
    dates_of_week = [parser.parse(start_date) + datetime.timedelta(days=x)
                     for x in range(0, (parser.parse(day)-parser.parse(start_date)).days+1)]
    for date in dates_of_week:
        export_time_tracking_data(date)

"""
with (Path(__file__).parent / f'data/goals.json').open('w+') as file:
    file.write(json.dumps(requests.get(f'https://api.clickup.com/api/v2/team/{team_id}/goal')))
"""
def do(day=None):
    if not day:
        day = dt.strftime(dt.today(), '%m-%d-%y')

    export_weekly_time_tracking_data(day)
    
    input("Press enter when you are finished.")
    update_weekly_goals()