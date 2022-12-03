
import json
import math
import os
from pathlib import Path

import pandas as pd
import pendulum
import yaml



class AppDataHandler:
    # Load in all relevant data into df
    # Also, handle waiting for API data

    def __init__(self):
        with open('data/private.yaml', 'r') as f:
            user_data = yaml.safe_load(f)
        self.puuid = user_data['puuid']

        self.match_summary_df = None
        self._loadHistoricalData()


    def _loadHistoricalData(self):
        data_path = Path('data/historical/proto')
        match_summary_files = os.listdir(data_path)
        match_summary_files.sort() # Now sorted oldest -> newest

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
        ]
        self.match_summary_df = pd.DataFrame(columns=cols)

        now = pendulum.now()
        floor_date = pendulum.datetime(year=now.year, month=now.month, day=now.day, tz=now.tz)
        game_index = -len(match_summary_files) + 1
        for file in match_summary_files: # Most recent games = biggest ID
            with open(data_path / file, 'r') as f:
                match_summary_data = json.load(f)

            # Get data of user
            target_idx = match_summary_data['metadata']['participants'].index(self.puuid)
            participant_data = match_summary_data['info']['participants'][target_idx]
            
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

            # kda
            kills = participant_data['kills']
            deaths = participant_data['deaths']
            assists = participant_data['assists']
            to_write.extend([kills, deaths, assists])

            # Anything involving other players
            own_team = participant_data['teamId']
            total_team_kills = 0
            total_team_damage = 0
            for player_data in match_summary_data['info']['participants']:
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

            self.match_summary_df.loc[index] = to_write



if __name__ == '__main__':
    adh = AppDataHandler()
    print(adh.df)
