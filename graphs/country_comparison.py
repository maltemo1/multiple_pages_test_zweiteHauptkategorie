import os
from dash import dcc, html, callback
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math

# Absoluter Pfad zur CSV-Datei sicherstellen
csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'df_grouped.csv')

# Prüfen, ob die Datei existiert
if os.path.exists(csv_path):
    df_grouped = pd.read_csv(csv_path)
else:
    df_grouped = None
    print(f"Fehler: Datei {csv_path} nicht gefunden!")

# Falls die Datei erfolgreich geladen wurde, Länderoptionen extrahieren
länder_options = sorted(df_grouped['Land'].unique()) if df_grouped is not None else []

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
            value=['Islamische Republik Iran'] if 'Islamische Republik Iran' in länder_options else None,  
            multi=True,  
            clearable=False,
            style={'width': '60%'}
        ),

        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
        dcc.Graph(id='trade_volume_graph')
    ])

# Funktion zur Erstellung von Graphen
def create_graph(selected_countries, column, title, color):
    if not selected_countries or df_grouped is None:
        return go.Figure()

    fig = go.Figure()

    for country in selected_countries:
        df_country = df_grouped[(df_grouped['Land'] == country) & (df_grouped['Jahr'].between(2008, 2024))]

        if df_country.empty:
            continue  # Falls das Land keine Daten hat, überspringen

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

    if pd.isna(max_value) or max_value == 0:
        return go.Figure()  # Falls keine Daten vorhanden sind, leere Graphen zurückgeben

    step_values = [5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 25e9]
    step = next((s for s in step_values if max_value < s * 2), 50e6)

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

# Funktion zur Registrierung von Callbacks
def register_callbacks(app):
    app.callback(Output('export_graph', 'figure'), Input('land_dropdown', 'value'))(update_export_graph)
    app.callback(Output('import_graph', 'figure'), Input('land_dropdown', 'value'))(update_import_graph)
    app.callback(Output('trade_volume_graph', 'figure'), Input('land_dropdown', 'value'))(update_trade_volume_graph)
