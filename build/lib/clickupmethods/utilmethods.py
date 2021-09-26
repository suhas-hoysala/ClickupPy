from __future__ import annotations
import datetime
from dateutil import parser
from clickupmethods.confobject import *
from datetime import datetime as dt, timezone, timedelta
from togglmethods.start import *
from clickupmethods.clickupext import ClickUpExt

class Common():
    def utc_dt_to_local(utc_dt: datetime.datetime) -> datetime.datetime:
        if not utc_dt:
            utc_dt = datetime.datetime.utcnow()
        return utc_dt.replace(
            tzinfo=datetime.timezone.utc).astimezone(tz=None)


class PointsUpdate():
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
                    return_value = PointsUpdate.time_completed_to_points(goal_finish_time)
                    return return_value
        return 0.0

    def get_last_time_points(data, proj_list,  task_names):
        last_entry = None
        for proj in proj_list:
            if not proj in data or not data[proj]:
                continue
            rel_tasks = [rec for rec in data[proj] if not task_names or any(
                [name in rec['description'] for name in task_names])]
            final_proj_entry = rel_tasks[-1]
            if not last_entry or parser.parse(
                    final_proj_entry['stop']) > parser.parse(last_entry['stop']):
                last_entry = final_proj_entry
        if not last_entry:
            return 0.0

        goal_finish_time = parser.parse(last_entry['stop'])
        goal_finish_time = goal_finish_time.replace(
            tzinfo=timezone.utc).astimezone(tz=None)
        return PointsUpdate.time_completed_to_points(goal_finish_time)

class GoalDataUpdate():
    def update_key_result(dt: datetime.datetime = None):
        pass


class ConfData():
    def __init__(self):

        pass

class TimeExport():
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
    def get_time_tracking_data(clickup: ClickUpExt, start_time: dt, end_time: dt):
        team_id = clickup.teams[0].id
        start_time_ms = str(int(start_time.timestamp()*1000))
        end_time_ms = str(int(end_time.timestamp()*1000))
        return clickup.get(f'https://api.clickup.com/api/v2/team/{team_id}/time_entries?start_date={start_time_ms}&end_date={end_time_ms}')

    def get_day_time_tracking_data(clickup: ClickUpExt, day: dt = dt.now()):
        dt_of_day = dt(day.year, day.month, day.day).replace(tzinfo=None).astimezone(tz=timezone.utc)
        return TimeExport.get_time_tracking_data(clickup, dt_of_day, dt_of_day + timedelta(days=1))

    def export_time_tracking_data(clickup: ClickUpExt, day: dt = dt.now()):
        clickup_time_data = TimeExport.get_day_time_tracking_data(clickup, day)
        if not 'data' in clickup_time_data:
            return
        for rec in clickup_time_data['data']:
            name = rec['task']['name']
            start = dt.fromtimestamp(int(rec['start'])/1000)
            duration = int(int(rec['duration'])/1000)
            tags = [str(rec['id']), str(rec['task']['id'])]
            if not TimeExport.validate_task(rec) and duration > 0:
                print(create_time_entry(name, start, duration, tags=tags))

co = ConfObject('', [], '', [
                datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now()])
