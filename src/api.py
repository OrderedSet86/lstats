import json
import os
from collections import deque
from time import sleep

import pendulum
import requests
import yaml


# Add more from here: https://developer.riotgames.com/apis

# Singlethreaded for now - throughput is unlikely to be a problem and rate limit is pretty low anyway
class ApiHandler:

    def __init__(self):
        self.requestCache = deque()
        self.receiveTimesCache = []
        self.api_key = None

        with open('data/private.yaml', 'r') as f:
            private_data = yaml.safe_load(f)
        self.api_key = private_data['personal-api-key']
        self.standardHeader = {
            'X-Riot-Token': self.api_key
        }

    def _okToSend(self):
        now = pendulum.now()
        last_second_count = 0
        last_two_minutes_count = 0

        cache_pointer = 0
        time_cache_size = len(self.receiveTimesCache)

        while cache_pointer < time_cache_size - 1:
            cache_time = self.receiveTimesCache[cache_pointer]

            diff = now - cache_time
            if diff <= pendulum.duration(seconds=1):
                last_second_count += 1
                last_two_minutes_count += 1
            elif diff <= pendulum.duration(minutes=2):
                last_two_minutes_count += 1
            else:
                self.receiveTimesCache.popleft()
                cache_pointer -= 1
                time_cache_size -= 1
            
            cache_pointer += 1
        
        if last_second_count < 20 and last_two_minutes_count < 100:
            return True
        return False
    
    def sendQuery(self, url):
        print(url)

        notified_of_sleep = False
        while not self._okToSend():
            if not notified_of_sleep:
                print('Waiting for rate limits...')
                notified_of_sleep = True
            sleep(1)

        response = requests.get(url, headers=self.standardHeader)
        status = response.status_code

        if status == 200:
            res_json = json.loads(response.text)
            self.receiveTimesCache.append(pendulum.now())
            return (status, res_json)
        else:
            # FIXME: Doing this now to avoid errors
            return (status, {})


class RiotDataHandler:

    def __init__(self):
        self.apiHandler = ApiHandler()
        self.standardPrefix = 'https://americas.api.riotgames.com/lol'

        with open('data/private.yaml', 'r') as f:
            private_data = yaml.safe_load(f)
        self.puuid = private_data['puuid']
    
    def getMatchHistory(self,
            start_date = pendulum.now() - pendulum.duration(days=2), 
            max_games = 50,
            # type = 'normal', # This prefers to ranked/non-ranked and I mostly won't be using it
            queue = 400, # draft games TODO: figure out others
        ):

        start_timestamp = int(start_date.timestamp())

        rq_url = f'{self.standardPrefix}/match/v5/matches/by-puuid/{self.puuid}/ids?'
        args = '&'.join([
            f'startTime={start_timestamp}',
            f'start=0',
            f'count={max_games}',
            f'queue={queue}',
        ])
        rq_url += args

        res = self.apiHandler.sendQuery(rq_url)
        return res
    
    def getMatchData(self, match_id):
        rq_url = f'{self.standardPrefix}/match/v5/matches/{match_id}'
        
        res = self.apiHandler.sendQuery(rq_url)
        return res


if __name__ == '__main__':
    rd = RiotDataHandler()

    existing_data = [x[:-5] for x in os.listdir('data/historical/proto')]

    status, rj = rd.getMatchHistory()
    if status == 200:
        for match in rj:
            if match in existing_data:
                continue

            match_status, md = rd.getMatchData(match)
            print(match_status)
            if match_status == 200:
                with open(f'data/historical/proto/{match}.json', 'w') as f:
                    json.dump(md, f)
