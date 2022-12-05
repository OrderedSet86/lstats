import json
import os
from collections import defaultdict
from pathlib import Path

import pendulum
from termcolor import colored, cprint

from src.api import RiotDataHandler

# Run API to get historical data



class UserDataInterface:


    def __init__(self):
        self._rd = RiotDataHandler()
        self._queueIdToMap = { # Modified from https://static.developer.riotgames.com/docs/lol/queues.json
            400: 'summoners_rift', # draft
            420: 'summoners_rift', # ranked
            430: 'summoners_rift', # blind pick
            440: 'summoners_rift', # ranked flex
            450: 'howling_abyss', # aram
            700: 'summoners_rift', # clash
        }
        self._known_game_maps = set(self._queueIdToMap.values())
        self._doHaveData = None


    def run(self):
        range_selection = self.getUserParams()
        self._constructDoHaveData()

        if range_selection == 1:
            status, match_list = self._rd.getMatchHistory() # Defaults to now minus 2 days
            if status == 200:
                self._getDataFromMatchList(match_list)

        elif range_selection == 2:
            # Go back to Jan 1st 2022
            tooOld = False
            start_idx = 0
            nonzero_status = []
            while not tooOld:
                status, match_list = self._rd.getMatchHistory(
                    start_date = None,
                    start_idx = start_idx,
                    max_games = 100
                )
                if status == 200:
                    tooOld = self._getDataFromMatchList(match_list)
                    start_idx += 100
                else:
                    nonzero_status.append(status)
                    if len(nonzero_status) >= 3:
                        print(nonzero_status)
                        break

    
    def _constructDoHaveData(self):
        # Construct dict "doHaveData", which does game_id: [summary_bool, timeline_bool]
        doHaveData = defaultdict(lambda: [False, False]) # Default is that no data is stored
        for game_map in self._known_game_maps:
            base_dir = Path('data/historical') / f'{game_map}'
            summary_dir = base_dir / 'summary'
            timeline_dir = base_dir / 'timeline'

            os.makedirs(summary_dir, exist_ok=True)
            os.makedirs(timeline_dir, exist_ok=True)

            existing_summary_ids = {x[:-5] for x in os.listdir(summary_dir)}
            existing_timeline_ids = {x[:-5] for x in os.listdir(timeline_dir)}

            for game_id in existing_summary_ids:
                doHaveData[game_id][0] = True
            for game_id in existing_timeline_ids:
                doHaveData[game_id][1] = True
        
        self._doHaveData = doHaveData


    def getUserParams(self):
        cprint('Select an option:', 'green')
        cprint('\n'.join([
            '1. Update recent games (last 50 games)',
            '2. Gather historical data (iterates back to Jan 1st 2022)',
            '',
        ]), 'green')
        range_selection = input(colored('> '))
        range_selection = int(range_selection)

        return range_selection


    def _getDataFromMatchList(self, match_list):
        # Return value is True if too old, False if not
        # "too old" is defined as pre 2022/01/01

        for match in match_list:
            summaryCached, timelineCached = self._doHaveData[match]

            if not summaryCached:
                match_status, md = self._rd.getMatchData(match)
                if match_status == 200:
                    match_queue_id = md['info']['queueId']
                    if match_queue_id not in self._queueIdToMap:
                        # Unrecognized mode - ignore (prob a special game mode)
                        cprint(f'Ignoring unrecognized gamemode: {match_queue_id}', 'yellow')
                        continue

                    match_date = pendulum.from_timestamp(md['info']['gameStartTimestamp'] // 1000)
                    if match_date < pendulum.datetime(year=2022, month=1, day=1):
                        cprint(f'Found too old match: {match_date}', 'green')
                        return True

                    match_map = self._queueIdToMap[match_queue_id]
                    cprint(f'Writing summary data to file!', 'green')
                    with open(f'data/historical/{match_map}/summary/{match}.json', 'w') as f:
                        json.dump(md, f)
                    self._doHaveData[match][0] = True
            
            if not timelineCached:
                timeline_status, td = self._rd.getTimelineData(match)
                if timeline_status == 200:
                    # Map data is not in timeline status - need to look at match summary
                    if not self._doHaveData[match][0]:
                        cprint(f'Missing data! No summary for {match}', 'red')
                    else:
                        for game_map in self._known_game_maps:
                            base_dir = Path('data/historical') / f'{game_map}'
                            summary_dir = base_dir / 'summary'
                            existing_summary_ids = {x[:-5] for x in os.listdir(summary_dir)}
                            if match in existing_summary_ids:
                                break
                        else:
                            raise RuntimeError('doHaveData contains false info about which data is available :(')

                        # Now we know the game_map, so store timeline in same spot
                        cprint(f'Writing timeline data to file!', 'green')
                        with open(f'data/historical/{game_map}/timeline/{match}.json', 'w') as f:
                            json.dump(td, f)
                        self._doHaveData[match][1] = True
        
        return False



if __name__ == '__main__':
    udi = UserDataInterface()
    udi.run()