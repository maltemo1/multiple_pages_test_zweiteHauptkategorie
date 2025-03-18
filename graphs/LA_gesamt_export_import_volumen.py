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
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import math
import gdown
import os


# Daten laden
df_grouped = pd.read_csv('data/df_grouped.csv')

# Einzigartige Länder alphabetisch sortieren
länder_options = sorted(df_grouped['Land'].unique())

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.1f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# Dash-App erstellen
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Deutschlands Handelsbeziehungen mit anderen Ländern"),

    dcc.Dropdown(
        id='land_dropdown',
        options=[{'label': land, 'value': land} for land in länder_options],
        value='Islamische Republik Iran',  # Standardwert
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='handel_graph'),
])

@app.callback(
    Output('handel_graph', 'figure'),
    Input('land_dropdown', 'value')
)
def update_graph(selected_country):
    df_country = df_grouped[(df_grouped['Land'] == selected_country) &
                            (df_grouped['Jahr'] >= 2008) &
                            (df_grouped['Jahr'] <= 2024)]

    fig = go.Figure()

    for col, name, color in zip(
        ['export_wert', 'import_wert', 'handelsvolumen_wert'],
        ['Exportvolumen', 'Importvolumen', 'Gesamthandelsvolumen'],
        ['#1f77b4', '#ff7f0e', '#2ca02c']
    ):
        fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Maximale Werte bestimmen
    max_value = df_country[['export_wert', 'import_wert', 'handelsvolumen_wert']].values.max()

    # Dynamische Skalierung der Y-Achse
    if max_value < 10e6:
        step = 5e6   # < 10 Mio → 5 Mio Schritte
    elif max_value < 50e6:
        step = 10e6  # 10 Mio - 50 Mio → 10 Mio Schritte
    elif max_value < 100e6:
        step = 25e6  # 50 Mio - 100 Mio → 25 Mio Schritte
    elif max_value < 250e6:
        step = 50e6  # 100 Mio - 250 Mio → 50 Mio Schritte
    elif max_value < 500e6:
        step = 100e6  # 250 Mio - 500 Mio → 100 Mio Schritte
    elif max_value < 1e9:
        step = 250e6  # 500 Mio - 1 Mrd → 250 Mio Schritte
    elif max_value < 5e9:
        step = 500e6  # 1 Mrd - 5 Mrd → 500 Mio Schritte
    elif max_value < 10e9:
        step = 1e9  # 5 Mrd - 10 Mrd → 1 Mrd Schritte
    elif max_value < 50e9:
        step = 5e9  # 10 Mrd - 50 Mrd → 5 Mrd Schritte
    elif max_value < 100e9:
        step = 10e9  # 50 Mrd - 100 Mrd → 10 Mrd Schritte
    else:
        step = 25e9  # > 100 Mrd → 25 Mrd Schritte

    # Maximale Achsenskala aufrunden
    rounded_max = math.ceil(max_value / step) * step

    # Y-Achsen-Ticks setzen (ohne doppelte Werte)
    tickvals = np.arange(0, rounded_max + step, step)

    # Falls doppelte Werte auftreten, verbessere die Verteilung
    if len(set(tickvals)) != len(tickvals):
        tickvals = np.linspace(0, rounded_max, num=len(tickvals))

    ticktext = [formatter(val) for val in tickvals]

    # Achsen und Layout
    fig.update_layout(
        title=f'Handelsverlauf zwischen Deutschland und {selected_country} (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
