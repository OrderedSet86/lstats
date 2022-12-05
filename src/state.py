
import json
import math
import os
from pathlib import Path

import pandas as pd
import pendulum
import yaml
from termcolor import colored, cprint



class AppDataHandler:
    # Load in all relevant data into df
    # Also, handle waiting for API data

    def __init__(self,
            game_map='summoners_rift',
            role='CARRY',
        ):
        with open('data/private.yaml', 'r') as f:
            user_data = yaml.safe_load(f)
        self.puuid = user_data['puuid']

        self.game_map = game_map
        self.role = role

        self.match_summary_df = None


    def loadSummonersRiftData(self):
        base_summoners_data_path = Path('data/historical/summoners_rift')
        summary_data_path = base_summoners_data_path / 'summary'
        timeline_data_path = base_summoners_data_path / 'timeline'

        match_summary_files = os.listdir(summary_data_path)
        match_timeline_files = os.listdir(timeline_data_path)
        both_exist = set(match_summary_files) & set(match_timeline_files)
        cprint(f'Found {len(both_exist)} files with summary + timeline data', 'green')
        both_exist = list(both_exist)
        both_exist.sort() # Now sorted oldest -> newest

        cols = [
            'game_index',
            'negative_day_index',
            'length',
            'cs',
            'gold',
            'champion',
            'vision_score',
            'lane',
            'dmg_champions',
            'kills',
            'deaths',
            'assists',
            'total_team_kills',
            'total_team_dmg_champions',
            'gd15',
            'csdiff15',
        ]
        self.match_summary_df = pd.DataFrame(columns=cols)

        now = pendulum.now()
        floor_date = pendulum.datetime(year=now.year, month=now.month, day=now.day, tz=now.tz)
        game_index = 0
        for file in both_exist: # Most recent games = biggest ID
            with open(summary_data_path / file, 'r') as f:
                match_summary_data = json.load(f)
            with open(timeline_data_path / file, 'r') as f:
                match_timeline_data = json.load(f)

            queueId = match_summary_data['info']['queueId']
            _queueIdToMap = { # Modified from https://static.developer.riotgames.com/docs/lol/queues.json
                400: 'summoners_rift', # draft
                420: 'summoners_rift', # ranked
                430: 'summoners_rift', # blind pick
                440: 'summoners_rift', # ranked flex
                450: 'howling_abyss', # aram
                700: 'summoners_rift', # clash
            }
            if queueId not in _queueIdToMap:
                continue
            else:
                if _queueIdToMap[queueId] != self.game_map:
                    continue

            # Get data of user
            target_idx = match_summary_data['metadata']['participants'].index(self.puuid)
            participant_data = match_summary_data['info']['participants'][target_idx]

            if self.role is not None:
                game_role = participant_data['role'] 
                if game_role != self.role:
                    continue
            
            to_write = []

            # Index of row
            index = file[:-5]

            # game_index
            to_write.append(game_index)
            game_index += 1

            # negative_day_index
            # aka, how many days ago was the game
            start_ts = match_summary_data['info']['gameStartTimestamp']
            start_unix_ts = start_ts//1000
            negative_days = math.ceil((pendulum.from_timestamp(start_unix_ts) - floor_date) / pendulum.duration(days=1)) - 1
            to_write.append(negative_days)

            # length
            length_played_in_s = participant_data['timePlayed'] # Note - this excludes DCs
            to_write.append(length_played_in_s)

            # cs
            cs = participant_data["totalMinionsKilled"]
            to_write.append(cs)

            # gold
            gold = participant_data["goldEarned"]
            to_write.append(gold)

            # champion
            champion = participant_data['championName']
            to_write.append(champion)

            # vision score per game
            vision_score = participant_data['visionScore']
            to_write.append(vision_score)

            # lane
            lane = participant_data['lane']
            to_write.append(lane)

            # total damage to champions
            dmg_champions = (
                participant_data['physicalDamageDealtToChampions'] +
                participant_data['magicDamageDealtToChampions'] +
                participant_data['trueDamageDealtToChampions']
            )
            to_write.append(dmg_champions)

            # kda stats
            kills = participant_data['kills']
            deaths = participant_data['deaths']
            assists = participant_data['assists']
            to_write.extend([kills, deaths, assists])

            # Anything involving other players
            own_team = participant_data['teamId']
            total_team_kills = 0
            total_team_damage = 0
            all_participant_data = match_summary_data['info']['participants']
            for player_data in all_participant_data:
                if player_data['teamId'] == own_team:
                    # total team kills
                    total_team_kills += player_data['kills']

                    # total team damage to champions
                    total_team_damage += (
                        player_data['physicalDamageDealtToChampions'] +
                        player_data['magicDamageDealtToChampions'] +
                        player_data['trueDamageDealtToChampions']
                    )

            to_write.extend([total_team_kills, total_team_damage])
                
            # lane difference @ 15
            if len(match_timeline_data['info']['frames']) >= 16:
                rival_id = [i for i, x in enumerate(all_participant_data) if (
                    x['role'] == self.role
                    and x['lane'] == participant_data['lane']
                    and i != target_idx
                )]
                if len(rival_id) != 1:
                    to_write.extend([None, None])

                else:
                    rival_id = rival_id[0]
                    fifteen_frame = match_timeline_data['info']['frames'][15]

                    # gold diff @ 15
                    own_gold = fifteen_frame['participantFrames'][str(target_idx)]['totalGold']
                    rival_gold = fifteen_frame['participantFrames'][str(rival_id)]['totalGold']
                    gd15 = own_gold - rival_gold
                    to_write.append(gd15)

                    # cs diff @ 15
                    own_cs = fifteen_frame['participantFrames'][str(target_idx)]['minionsKilled']
                    rival_cs = fifteen_frame['participantFrames'][str(rival_id)]['minionsKilled']
                    csdiff15 = own_cs - rival_cs
                    to_write.append(csdiff15)
            else:
                print('Game shorter than 15m')
                to_write.extend([None, None])

            self.match_summary_df.loc[index] = to_write



if __name__ == '__main__':
    adh = AppDataHandler()
    print(adh.df)
