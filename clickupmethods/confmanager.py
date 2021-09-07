from pathlib import Path
import json
from clickupmethods.confobject import *
class ConfManager:
    def __init__(self):
        conf_file = Path(__file__).parent / \
            '.data/conf.json'
        if not conf_file.exists():
            self.conf = {

            }
        else:
            self.conf = json.load(conf_file.open())
    def create_goal(**kwargs):
        pass