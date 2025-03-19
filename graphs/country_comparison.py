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
        dcc.Graph(id='trade_volume_graph'),
    ])

# Callback für die Aktualisierung der Graphen
@callback(
    Output('export_graph', 'figure'),
    Output('import_graph', 'figure'),
    Output('trade_volume_graph', 'figure'),
    Input('land_dropdown', 'value')
)
def update_graphs(selected_countries):
    if not selected_countries:
        return go.Figure(), go.Figure(), go.Figure()  # Leere Diagramme, falls keine Auswahl

    figures = []
    categories = [
        ('export_wert', 'Exportvolumen', '#1f77b4'),
        ('import_wert', 'Importvolumen', '#ff7f0e'),
        ('handelsvolumen_wert', 'Gesamthandelsvolumen', '#2ca02c')
    ]

    for col, name, color in categories:
        fig = go.Figure()

        for country in selected_countries:
            df_country = df_grouped[
                (df_grouped['Land'] == country) &
                (df_grouped['Jahr'] >= 2008) &
                (df_grouped['Jahr'] <= 2024)
            ]

            fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country[col],
                mode='lines+markers',
                name=f"{name} ({country})",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name} ({country})</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Maximale Werte bestimmen
        max_value = df_grouped[df_grouped['Land'].isin(selected_countries)][col].max()

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

        rounded_max = math.ceil(max_value / step) * step

        tickvals = np.arange(0, rounded_max + step, step)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'{name} mit Deutschland (2008-2024)',
            xaxis_title='Jahr',
            yaxis_title='Wert in €',
            yaxis=dict(
                tickvals=tickvals,
                ticktext=ticktext
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        figures.append(fig)

    return figures[0], figures[1], figures[2]

# Callback-Registrierung
def register_callbacks(app):
    app.callback(
        Output('export_graph', 'figure'),
        Output('import_graph', 'figure'),
        Output('trade_volume_graph', 'figure'),
        Input('land_dropdown', 'value')
    )(update_graphs)
