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
    html.H1("Deutschlands Handelsbeziehungen mit anderen Ländern (im Vergleich)"),

    dcc.Dropdown(
        id='land_dropdown',
        options=[{'label': land, 'value': land} for land in länder_options],
        value=['Islamische Republik Iran', 'Irak', 'Katar'],  # Default Auswahl
        multi=True,  # Mehrere Länder können ausgewählt werden
        clearable=False,
        style={'width': '50%'}
    ),

    html.Div([
        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
        dcc.Graph(id='handelsvolumen_graph')
    ])
])

@app.callback(
    [Output('export_graph', 'figure'),
     Output('import_graph', 'figure'),
     Output('handelsvolumen_graph', 'figure')],
    Input('land_dropdown', 'value')
)
def update_graph(selected_countries):
    # Farben für die Linien (damit jede Linie eine eigene Farbe bekommt)
    farben = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    export_fig = go.Figure()
    import_fig = go.Figure()
    handelsvolumen_fig = go.Figure()

    # Gehe durch jedes ausgewählte Land und füge die Linien zu den Graphen hinzu
    for i, country in enumerate(selected_countries):
        df_country = df_grouped[(df_grouped['Land'] == country) &
                                (df_grouped['Jahr'] >= 2008) &
                                (df_grouped['Jahr'] <= 2024)]

        # Exportwert Graph
        export_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['export_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Exportvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

        # Importwert Graph
        import_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['import_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Importvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

        # Handelsvolumenwert Graph
        handelsvolumen_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['handelsvolumen_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Gesamthandelsvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Maximale Werte für Y-Achse bestimmen und Dynamik hinzufügen
    max_export = df_grouped[['export_wert']].max().values[0]
    max_import = df_grouped[['import_wert']].max().values[0]
    max_handelsvolumen = df_grouped[['handelsvolumen_wert']].max().values[0]

    def get_dynamic_ticks(max_value):
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
        rounded_max = math.ceil(max_value / step) * step
        tickvals = np.arange(0, rounded_max + step, step)
        ticktext = [formatter(val) for val in tickvals]
        return tickvals, ticktext

    # Dynamische Y-Achse für jeden Graphen
    export_ticks, export_ticktext = get_dynamic_ticks(max_export)
    import_ticks, import_ticktext = get_dynamic_ticks(max_import)
    handelsvolumen_ticks, handelsvolumen_ticktext = get_dynamic_ticks(max_handelsvolumen)

    # Layout für die Graphen
    export_fig.update_layout(
        title='Exporte (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=export_ticks, ticktext=export_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    import_fig.update_layout(
        title='Importe (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=import_ticks, ticktext=import_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    handelsvolumen_fig.update_layout(
        title='Handelsvolumen (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=handelsvolumen_ticks, ticktext=handelsvolumen_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    return export_fig, import_fig, handelsvolumen_fig

if __name__ == '__main__':
    app.run_server(debug=True)
