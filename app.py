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


def constructValueLineChart(value, y_axis, title):
    global dh
    fig = px.line(
        dh.match_summary_df,
        x='game_index',
        y=value,
        labels={
            'y': y_axis,
            'game_index': 'Game Number',
        },
        title=title,
        **standardTheming
    )
    fig.update_layout(yaxis_range=[0, 1.1*value.max()])
    return fig
    

# CS/Minute
cspm = dh.match_summary_df['cs'] / (dh.match_summary_df['length'] / 60)
fig_cspm = constructValueLineChart(
    cspm,
    'CS/Minute',
    'CS Per Game',
)
fig_cspm.update_layout(yaxis_range=[4, 10])

# Gold/Minute
gpm = dh.match_summary_df['gold'] / (dh.match_summary_df['length'] / 60)
fig_gpm = constructValueLineChart(
    gpm,
    'Gold/Minute',
    'Gold Per Game',
)

# Vision Score/Minute
vsm = dh.match_summary_df['vision_score'] / (dh.match_summary_df['length'] / 3600)
fig_vsm = constructValueLineChart(
    vsm,
    'Vision Score/Hour',
    'Vision Score Per Game',
)


# Following two functions were modified from https://stackoverflow.com/a/63602391/7247528
# Figure wrapper
def drawFigure(fig):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    figure=fig.update_layout(
                        template='plotly_dark',
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)',
                    ),
                    config={
                        'displayModeBar': False
                    }
                )
            ])
        ),  
    ])

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


# Build app
client_stats_tab = dbc.Card(
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                drawText('League Stats')
            ], width=3),
        ], align='center'), 
        html.Br(),
        dbc.Row([
            dbc.Col([
                drawFigure(fig_cspm)
            ], width=6),
            dbc.Col([
                drawFigure(fig_gpm)
            ], width=6),
        ], align='center'), 
        html.Br(),
        dbc.Row([
            dbc.Col([
                drawFigure(fig_vsm)
            ], width=6),
        ], align='center'),      
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
    app.run_server()