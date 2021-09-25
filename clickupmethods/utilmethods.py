from __future__ import annotations
import datetime
from dateutil import parser
from clickupmethods.confobject import ConfObject

class Common():
    def utc_dt_to_local(utc_dt: datetime.datetime) -> datetime.datetime:
        if not utc_dt:
            utc_dt = datetime.datetime.utcnow()
        return utc_dt.replace(
            tzinfo=datetime.timezone.utc).astimezone(tz=None)


class PointsUpdate():
    def time_completed_to_points(dt: datetime.datetime):
        dt_reg = dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
        return (24 - dt_reg.hour) - dt_reg.minute/60 - dt_reg.second/3600

    def get_time_limit_points(conf, goal_duration, data, proj_list, task_names):
        total_duration = 0.0
        for proj in proj_list:
            if not proj in data:
                continue
            rel_tasks = [rec for rec in data[proj] if not task_names or any(
                [name in rec['description'] for name in task_names])]
            for entry in rel_tasks:
                total_duration += entry['duration']/60.0
                if total_duration >= goal_duration:
                    extra = total_duration - goal_duration
                    goal_finish_time = parser.parse(
                        entry['stop']) - datetime.timedelta(minutes=extra)
                    goal_finish_time = goal_finish_time.replace(
                        tzinfo=datetime.timezone.utc).astimezone(tz=None)
                    return PointsUpdate.time_completed_to_points(goal_finish_time)
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
            tzinfo=datetime.timezone.utc).astimezone(tz=None)
        return PointsUpdate.time_completed_to_points(goal_finish_time)


class GoalDataUpdate():
    def update_key_result(dt: datetime.datetime = None):
        pass


class ConfData():
    def __init__(self):

        pass


co = ConfObject(ConfObject.GoalType.DAILY, [], '', [
                datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now()])
