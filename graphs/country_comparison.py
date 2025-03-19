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
def create_layout():
    return html.Div([
        html.H1("Vergleich der Handelsverläufe mehrerer Länder mit Deutschland"),

        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': land, 'value': land} for land in länder_options],
            value=['Islamische Republik Iran'],  # Standardwert
            multi=True,  # Mehrfachauswahl aktivieren
            clearable=False,
            style={'width': '60%'}
        ),

        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
        dcc.Graph(id='trade_volume_graph')
    ])

# Funktion zur Erstellung von Graphen
def create_graph(selected_countries, column, title, color):
    if not selected_countries:
        return go.Figure()

    fig = go.Figure()

    for country in selected_countries:
        df_country = df_grouped[
            (df_grouped['Land'] == country) &
            (df_grouped['Jahr'] >= 2008) &
            (df_grouped['Jahr'] <= 2024)
        ]

        fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country[column],
            mode='lines+markers',
            name=f"{title} ({country})",
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{title} ({country})</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Dynamische Skalierung der Y-Achse
    max_value = df_grouped[df_grouped['Land'].isin(selected_countries)][column].max()

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

    rounded_max = math.ceil(max_value / step) * step

    tickvals = np.arange(0, rounded_max + step, step)
    ticktext = [formatter(val) for val in tickvals]

    fig.update_layout(
        title=title,
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    return fig

# Callbacks für die drei separaten Graphen
@callback(
    Output('export_graph', 'figure'),
    Input('land_dropdown', 'value')
)
def update_export_graph(selected_countries):
    return create_graph(selected_countries, 'export_wert', 'Exportvolumen', '#1f77b4')

@callback(
    Output('import_graph', 'figure'),
    Input('land_dropdown', 'value')
)
def update_import_graph(selected_countries):
    return create_graph(selected_countries, 'import_wert', 'Importvolumen', '#ff7f0e')

@callback(
    Output('trade_volume_graph', 'figure'),
    Input('land_dropdown', 'value')
)
def update_trade_volume_graph(selected_countries):
    return create_graph(selected_countries, 'handelsvolumen_wert', 'Gesamthandelsvolumen', '#2ca02c')

# Callback-Registrierung
def register_callbacks(app):
    app.callback(
        Output('export_graph', 'figure'),
        Input('land_dropdown', 'value')
    )(update_export_graph)

    app.callback(
        Output('import_graph', 'figure'),
        Input('land_dropdown', 'value')
    )(update_import_graph)

    app.callback(
        Output('trade_volume_graph', 'figure'),
        Input('land_dropdown', 'value')
    )(update_trade_volume_graph)

