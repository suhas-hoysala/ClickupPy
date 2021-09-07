
import random
from typing import List
from multipledispatch.core import dispatch
import datetime
from dateutil import parser
class ConfObject():
    def __init__(self, goal_title: str,  goal_names: list = [], color: str or int = None,
                 date_intervals: List[datetime.datetime] = [], time_intervals: List[datetime.datetime] = [], goal_records: List[dict] = []) -> None:
        if not color:
            color = "%06x" % random.randint(0, 0xFFFFFF)
        self.goal_title = goal_title
        self.color = str(color)
        self.goal_names = goal_names
        self.date_intervals = date_intervals
        self.time_intervals = TimeInterval.from_list(time_intervals)
        self.goal_records = GoalRecord.from_list(goal_records)
    

class TimeInterval():
    def __init__(self, start_time: datetime.datetime, end_time: datetime.datetime) -> None:
        self.start_time = start_time
        self.end_time = end_time

    def from_list(time_intervals: List[datetime.datetime]) -> List[TimeInterval]:
        return_list = []
        for i in range(int(len(time_intervals)/2)):
            start_time = time_intervals[2*i]
            end_time = time_intervals[2*i+1]
            return_list.append(
                TimeInterval(start_time, end_time))
        return return_list
    
    def to_list(time_intervals: List[TimeInterval]):
        return_list = []
        for interval in time_intervals:
            return_list.append([interval.start_time.timestamp(), interval.end_time.timestamp()])
        
        return return_list
    
class GoalRecord():
    def to_timestamp(date: str or float) -> float:
        ts = None
        if(str(date).isnumeric()):
            try:
                ts = datetime.datetime.fromtimestamp(float(date))
            except(OSError):
                ts = datetime.datetime.fromtimestamp(float(date)/1000)
        else:
            ts = parser.parse(date).timestamp()
        return ts

    def __init__(self, pts_achieved: float, pts_total: float, completed: bool, start_date: str or float, due_date: str or int):
        self.pts_achieved = pts_achieved
        self.pts_total = pts_total
        self.completed = completed
        self.start_date = self.to_timestamp(start_date)
        self.end_date = self.to_timestamp(due_date)
    
    def from_list(goal_records_list: List[dict]) -> List[GoalRecord]:
        return_list = []
        for goal_record in goal_records_list:
            return_list.append(ConfObject.GoalRecord(**goal_record))

        return return_list
    
    def to_list(goal_records_list: List[GoalRecord]) -> List[dict]:
        return list(map(vars, goal_records_list))
            
