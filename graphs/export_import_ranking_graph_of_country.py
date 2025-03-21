import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from statistics import mean
import glob
from statsmodels.tsa.seasonal import seasonal_decompose
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.ticker import FuncFormatter
#import dash_core_components as dcc
#import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import math
import gdown
import os

# Daten laden
df_grouped = pd.read_csv('data/df_grouped.csv')

# Einzigartige Länder alphabetisch sortieren
länder_options = sorted(df_grouped['Land'].unique())

# Dash-App erstellen
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Platzierung im Export- und Importranking Deutschlands (2008-2024)"),

    dcc.Dropdown(
        id='land_dropdown_ranking',
        options=[{'label': land, 'value': land} for land in länder_options],
        value='Islamische Republik Iran',  # Standardwert
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='ranking_graph'),
])

@app.callback(
    Output('ranking_graph', 'figure'),
    Input('land_dropdown_ranking', 'value')
)
def update_ranking_graph(selected_country):
    df_country = df_grouped[(df_grouped['Land'] == selected_country) &
                            (df_grouped['Jahr'] >= 2008) &
                            (df_grouped['Jahr'] <= 2024)]

    # Stelle sicher, dass die Rankings Integer sind
    df_country['export_ranking'] = df_country['export_ranking'].astype(int)
    df_country['import_ranking'] = df_country['import_ranking'].astype(int)
    df_country['handelsvolumen_ranking'] = df_country['handelsvolumen_ranking'].astype(int)

    fig = go.Figure()

    for col, name, color in zip(
        ['export_ranking', 'import_ranking', 'handelsvolumen_ranking'],
        ['Export-Ranking', 'Import-Ranking', 'Handelsvolumen-Ranking'],
        ['#1f77b4', '#2ca02c', '#ff7f0e']
    ):
        fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Platzierung: %{{y}}<extra></extra>'
        ))

    # Min & Max Ranking bestimmen
    min_ranking = df_country[['export_ranking', 'import_ranking', 'handelsvolumen_ranking']].min().min()
    max_ranking = df_country[['export_ranking', 'import_ranking', 'handelsvolumen_ranking']].max().max()

    # Dynamische Achsenskalierung
    step_size = max(1, (max_ranking - min_ranking) // 10)
    tickvals = np.arange(min_ranking, max_ranking + step_size, step_size)

    # Achsen und Layout
    fig.update_layout(
        title=f'Platzierung von {selected_country} im Export- und Importranking (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Ranking (niedriger = besser)',
        yaxis=dict(
            tickvals=tickvals,
            range=[max_ranking +2 , min_ranking -2],  # Invertierte Achse (1 = beste Platzierung)
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)
