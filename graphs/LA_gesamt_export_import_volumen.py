from dash import dcc, html, callback
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math

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

# Layout für die Multi-Page-App
layout = html.Div([
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

# Callback für die Aktualisierung des Graphen
@callback(
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
        step = 5e6
    elif max_value < 50e6:
        step = 10e6
    elif max_value < 100e6:
        step = 25e6
    elif max_value < 250e6:
        step = 50e6
    elif max_value < 500e6:
        step = 100e6
    elif max_value < 1e9:
        step = 250e6
    elif max_value < 5e9:
        step = 500e6
    elif max_value < 10e9:
        step = 1e9
    elif max_value < 50e9:
        step = 5e9
    elif max_value < 100e9:
        step = 10e9
    else:
        step = 25e9

    # Maximale Achsenskala aufrunden
    rounded_max = math.ceil(max_value / step) * step

    # Y-Achsen-Ticks setzen (ohne doppelte Werte)
    tickvals = np.arange(0, rounded_max + step, step)
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
