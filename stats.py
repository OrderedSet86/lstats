import json
import os
from pathlib import Path

import yaml
import pandas as pd
import plotly.express as px


with open('data/private.yaml', 'r') as f:
    user_data = yaml.safe_load(f)
puuid = user_data['puuid']


cspm_all = []
gpm_all = []
base_dir = Path('data/historical/proto')
for match in os.listdir(base_dir):
    with open(base_dir / match, 'r') as f:
        data = json.load(f)

    target_idx = data['metadata']['participants'].index(puuid)
    participant_data = data['info']['participants'][target_idx]

    iprint = lambda x: print('    ', x)

    # Game data
    length_played_in_s = participant_data['timePlayed'] # Note - this excludes DCs
    length_played_in_m = length_played_in_s/60

    print(match[:-5])

    iprint(f'{participant_data["championName"]}')

    kills = participant_data["kills"]
    deaths = participant_data["deaths"]
    assists = participant_data["assists"]
    iprint(''.join([
        'KDA: ',
        f'{kills}/'
        f'{deaths}/'
        f'{assists} '
        f'({round((kills + assists)/deaths, 2)})'
    ]))

    cspm = participant_data["totalMinionsKilled"]/(length_played_in_m)
    cspm_all.append(cspm)
    iprint(''.join([
        'CS/minute: ',
        f'{round(cspm, 1)}'
    ]))

    gpm = participant_data["goldEarned"]/(length_played_in_m)
    gpm_all.append(gpm)
    iprint(''.join([
        'Gold/minute: ',
        f'{int(round(gpm, 0))}'
    ]))

dt = {
    'game_index': list(range(len(cspm_all))),
    'cspm': cspm_all,
    'gpm': gpm_all,
}
df = pd.DataFrame(dt)
fig = px.line(
    df,
    x='game_index',
    y='cspm',
    title='CS Improvements',
)
fig.update_layout(yaxis_range=[4, 10])
fig.show()
