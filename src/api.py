import json
import os

import pendulum
import requests
import yaml
from ratelimit import limits, sleep_and_retry


# Add more from here: https://developer.riotgames.com/apis

# Singlethreaded for now - throughput is unlikely to be a problem and rate limit is pretty low anyway
class ApiHandler:

    def __init__(self):
        self.api_key = None

        with open('data/private.yaml', 'r') as f:
            private_data = yaml.safe_load(f)
        self.api_key = private_data['personal-api-key']
        self.standardHeader = {
            'X-Riot-Token': self.api_key
        }
    
    @sleep_and_retry
    @limits(calls=95, period=60*2) # Only really need to worry about this one when singlethreaded
    def sendQuery(self, url):
        print(url)

        response = requests.get(url, headers=self.standardHeader)
        status = response.status_code
        print(status)

        if status == 200:
            res_json = json.loads(response.text)
            return (status, res_json)
        else:
            # FIXME: Doing this for now to avoid errors
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
            start_idx = 0,
            max_games = 50,
            # type = 'normal', # This prefers to ranked/non-ranked and I mostly won't be using it
            queue = None,
        ):

        rq_url = f'{self.standardPrefix}/match/v5/matches/by-puuid/{self.puuid}/ids?'

        args = [
            f'count={max_games}',
        ]
        if queue is not None:
            args.append(f'queue={queue}',)
        if start_date is not None:
            start_timestamp = int(start_date.timestamp())
            args.append(f'startTime={start_timestamp}')
        if start_idx is not None:
            args.append(f'start={start_idx}')

        args = '&'.join(args)
        rq_url += args

        res = self.apiHandler.sendQuery(rq_url)
        return res
    
    def getMatchData(self, match_id):
        rq_url = f'{self.standardPrefix}/match/v5/matches/{match_id}'
        
        res = self.apiHandler.sendQuery(rq_url)
        return res
    
    def getTimelineData(self, match_id):
        rq_url = f'{self.standardPrefix}/match/v5/matches/{match_id}/timeline'
        
        res = self.apiHandler.sendQuery(rq_url)
        return res



if __name__ == '__main__':
    rd = RiotDataHandler()

    existing_data = [x[:-5] for x in os.listdir('data/historical/summoners_rift/summary')]

    status, rj = rd.getMatchHistory()
    if status == 200:
        for match in rj:
            if match in existing_data:
                continue

            match_status, md = rd.getMatchData(match)
            print(match_status)
            if match_status == 200:
                with open(f'data/historical/summary/summoners_rift/{match}.json', 'w') as f:
                    json.dump(md, f)
