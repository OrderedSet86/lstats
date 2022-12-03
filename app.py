import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

from src.state import AppDataHandler


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.SLATE]
)

dh = AppDataHandler()

### FIGURES

standardTheming = {
    'template': 'plotly_dark'
}


def constructValueLineChart(value, y_axis, title, challenger_stat=None, silver_stat=None):
    global dh
    fig = px.line(
        dh.match_summary_df,
        x='game_index',
        y=value,
        labels={
            'y': y_axis,
            'game_index': 'Games Ago',
        },
        title=title,
        **standardTheming
    )

    if challenger_stat is not None:
        maxval = max(value.max(), challenger_stat)    
    else:
        maxval = value.max()

    if silver_stat is not None:
        minval = min(value.min(), silver_stat)
    else:
        minval = value.min()
    

    fig.update_layout(yaxis_range=[0.9*minval, 1.1*maxval])

    if challenger_stat is not None:
        fig.add_hline(challenger_stat, line_color='yellow')
    if silver_stat is not None:
        fig.add_hline(silver_stat, line_color='silver')

    return fig


# CS/Minute
cspm = dh.match_summary_df['cs'] / (dh.match_summary_df['length'] / 60)
fig_cspm = constructValueLineChart(
    cspm,
    'CS/Minute',
    'CS Per Minute',
    challenger_stat=7.1,
    silver_stat=5.5,
)
fig_cspm.update_layout(yaxis_range=[4.5, 8])

# Gold/Minute
gpm = dh.match_summary_df['gold'] / (dh.match_summary_df['length'] / 60)
fig_gpm = constructValueLineChart(
    gpm,
    'Gold/Minute',
    'Gold Per Minute',
)

# Vision Score/Minute
vsm = dh.match_summary_df['vision_score'] / (dh.match_summary_df['length'] / 3600)
fig_vsm = constructValueLineChart(
    vsm,
    'Vision Score/Hour',
    'Vision Score Per Game',
    challenger_stat=44.8,
    silver_stat=35.2,
)

# Damage/Gold
dpg = dh.match_summary_df['dmg_champions'] / dh.match_summary_df['gold']
fig_dpg = constructValueLineChart(
    dpg,
    'Damage/Gold',
    'Damage Per Gold',
    challenger_stat=1.74,
    silver_stat=1.77,
)

# KDA Ratio
kda = (dh.match_summary_df['kills'] + dh.match_summary_df['assists']) / dh.match_summary_df['deaths']
fig_kda = constructValueLineChart(
    kda,
    'KDA',
    'KDA Ratio',
    challenger_stat=2.55,
    silver_stat=2.57,
)

# Kill Participation
kp = (dh.match_summary_df['kills'] + dh.match_summary_df['assists']) / dh.match_summary_df['total_team_kills'] * 100
fig_kp = constructValueLineChart(
    kp,
    'Kill Participation %',
    'Kill Participation',
    challenger_stat=48.1,
    silver_stat=46.2,
)

# Damage Per Death
dpd = dh.match_summary_df['dmg_champions'] / dh.match_summary_df['deaths']
fig_dpd = constructValueLineChart(
    dpd,
    'Damage/Death',
    'Damage Per Death',
    challenger_stat=3863,
    silver_stat=3693,
)

# Damage Share
dsh = dh.match_summary_df['dmg_champions'] / dh.match_summary_df['total_team_dmg_champions'] * 100
fig_dsh = constructValueLineChart(
    dsh,
    'Damage Share %',
    'Damage Share',
    challenger_stat=22.8,
    silver_stat=21.0,
)


# Following two functions were modified from https://stackoverflow.com/a/63602391/7247528
# Figure wrapper
def drawFigure(fig, height=300):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    figure=fig.update_layout(
                        template='plotly_dark',
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)',
                        height=height,
                    ),
                    config={
                        'displayModeBar': False
                    },
                )
            ])
        ),  
    ])

cardBodyWrapper = lambda *args: dbc.Card(dbc.CardBody([*args]))

# Text field
def drawText(text):
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H2(text),
                ], style={'textAlign': 'center'}) 
            ])
        ),
    ])

combat_stats_tab = cardBodyWrapper(
    dbc.Row([
        dbc.Col([
            drawText('Placeholder')
        ], width=3),
        dbc.Col([
            drawFigure(fig_kda)
        ], width=3),
        dbc.Col([
            drawFigure(fig_kp)
        ], width=3),
    ], align='center'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            drawText('Utility Score')
        ], width=3),
        dbc.Col([
            drawFigure(fig_dpd)
        ], width=3),
        dbc.Col([
            drawFigure(fig_dsh)
        ], width=3),
    ], align='center'),
)

income_stats_tab = cardBodyWrapper(
    dbc.Row([
        dbc.Col([
            drawFigure(fig_dpg)
        ], width=3),
        dbc.Col([
            drawFigure(fig_cspm)
        ], width=3),
        dbc.Col([
            drawFigure(fig_gpm)
        ], width=3),
    ], align='center'), 
    # html.Br(),
    # dbc.Row([
    #     dbc.Col([
    #         drawFigure(fig_vsm)
    #     ], width=3),
    # ], align='center'),
)

map_control_stats_tab = cardBodyWrapper(
    dbc.Row([
        dbc.Col([
            drawFigure(fig_vsm)
        ], width=3),
    ], align='center'),
)


# Build app
client_stats_tab = dbc.Card(
    dbc.CardBody([
        # dbc.Row([
        #     dbc.Col([
        #         drawText('Client Stats')
        #     ], width=3),
        # ], align='center'), 
        # html.Br(),
        dbc.Tabs([
            dbc.Tab(combat_stats_tab, label='Combat'),
            dbc.Tab(income_stats_tab, label='Income'),
            dbc.Tab(map_control_stats_tab, label='Map Control'),
        ]),
    ]), color = 'dark'
)

app.layout = html.Div([
    dbc.Tabs([
        dbc.Tab(client_stats_tab, label='Client Stats'),
        dbc.Tab(html.Div(), label='ARAM Stats', disabled=True),
    ])
])


# Run app
if __name__ == '__main__':
    app.run_server(debug=True)