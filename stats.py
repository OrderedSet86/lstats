import json
import math
import os
from pathlib import Path

import pandas as pd
import pendulum
import plotly.express as px
import yaml
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

from src.state import AppDataHandler


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
)

dh = AppDataHandler()

### FIGURES

standardTheming = {
    'template': 'plotly_dark'
}


# CS/Minute
cspm = dh.match_summary_df['cs'] / (dh.match_summary_df['length'] / 60)
fig_cspm = px.scatter(
    dh.match_summary_df,
    x='negative_day_index',
    y=cspm,
    labels={
        'y': 'CS/minute',
        'negative_day_index': 'Days ago',
    },
    title='CS Per Game',
    **standardTheming
)
fig_cspm.update_layout(yaxis_range=[4, 10])
fig_cspm.update_layout(xaxis_range=[-7.5, 0.5])

# Gold/Minute
gpm = dh.match_summary_df['gold'] / (dh.match_summary_df['length'] / 60)
fig_gpm = px.scatter(
    dh.match_summary_df,
    x='negative_day_index',
    y=gpm,
    labels={
        'y': 'Gold/minute',
        'negative_day_index': 'Days ago',
    },
    title='Gold Per Game',
    **standardTheming
)
fig_gpm.update_layout(yaxis_range=[0, 1.1*gpm.max()])
fig_gpm.update_layout(xaxis_range=[-7.5, 0.5])

# Vision Score/Minute
vsm = dh.match_summary_df['vision_score'] / (dh.match_summary_df['length'] / 3600)
fig_vsm = px.scatter(
    dh.match_summary_df,
    x='negative_day_index',
    y=vsm,
    labels={
        'y': 'Vision Score/Hour',
        'negative_day_index': 'Days ago',
    },
    title='Vision Per Game',
    **standardTheming
)
fig_vsm.update_layout(yaxis_range=[0, 1.1*vsm.max()])
fig_vsm.update_layout(xaxis_range=[-7.5, 0.5])


# app.layout = html.Div([
#     html.H1(children='League Stats'),

#     # html.Div(children='''
#     #     Dash: A web application framework for your data.
#     # '''),

#     dbc.Row([
#         dbc.Col(
#             html.Div(
#                 dcc.Graph(
#                     id='cspm',
#                     figure=fig_cspm
#                 ),
#             )
#         ),
#         dbc.Col(
#             html.Div(
#                 dcc.Graph(
#                     id='gpm',
#                     figure=fig_gpm
#                 ),
#             )
#         )
#     ]),
#     dbc.Row(
#         dcc.Graph(
#             id='vsm',
#             figure=fig_vsm
#         ),
#     ),
# ])

# Iris bar figure
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

# Build App
app = Dash(external_stylesheets=[dbc.themes.SLATE])

app.layout = html.Div([
    dbc.Card(
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
                ], width=12),
            ], align='center'),      
        ]), color = 'dark'
    )
])

# Run app and display result inline in the notebook
app.run_server()
if __name__ == '__main__':
    app.run_server(debug=True)