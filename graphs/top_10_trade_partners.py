import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math
import os

# Daten laden
df_path = os.path.join("data", "df_grouped.csv")
df_grouped = pd.read_csv(df_path)

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.0f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Top 10 Handelspartner Deutschlands"),
        
        dcc.Dropdown(
            id='jahr_dropdown',
            options=[{'label': str(j), 'value': j} for j in sorted(df_grouped['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
        dcc.Graph(id='handelsvolumen_graph'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [Output('export_graph', 'figure'),
         Output('import_graph', 'figure'),
         Output('handelsvolumen_graph', 'figure')],
        Input('jahr_dropdown', 'value')
    )
    def update_graphs(year_selected):
        top_10_export = df_grouped[(df_grouped['export_ranking'] <= 10) & (df_grouped['Jahr'] == year_selected)][["Land", "export_wert"]]
        top_10_import = df_grouped[(df_grouped['import_ranking'] <= 10) & (df_grouped['Jahr'] == year_selected)][["Land", "import_wert"]]
        top_10_handelsvolumen = df_grouped[(df_grouped['handelsvolumen_ranking'] <= 10) & (df_grouped['Jahr'] == year_selected)][["Land", "handelsvolumen_wert"]]

        top_10_export = top_10_export.sort_values(by="export_wert", ascending=False)
        top_10_import = top_10_import.sort_values(by="import_wert", ascending=False)
        top_10_handelsvolumen = top_10_handelsvolumen.sort_values(by="handelsvolumen_wert", ascending=False)

        # Maximale Werte für Skalierung
        max_export = top_10_export['export_wert'].max()
        max_import = top_10_import['import_wert'].max()
        max_handelsvolumen = top_10_handelsvolumen['handelsvolumen_wert'].max()

        # Die höchste Zahl für die Y-Achse ermitteln
        max_value = max(max_export, max_import, max_handelsvolumen)
        rounded_max = math.ceil(max_value / 50e9) * 50e9
        tickvals = np.arange(0, rounded_max + 1, 50e9)
        ticktext = [formatter(val) for val in tickvals]

        # Export Grafik
        fig_export = go.Figure([go.Bar(
            x=top_10_export['Land'],
            y=top_10_export['export_wert'],
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br>Wert: %{y:,} €<extra></extra>'
        )])
        fig_export.update_layout(
            title=f'Top 10 Exportländer im Jahr {year_selected}',
            xaxis_title='Land',
            yaxis_title='Export Wert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Import Grafik
        fig_import = go.Figure([go.Bar(
            x=top_10_import['Land'],
            y=top_10_import['import_wert'],
            marker_color='green',
            hovertemplate='<b>%{x}</b><br>Wert: %{y:,} €<extra></extra>'
        )])
        fig_import.update_layout(
            title=f'Top 10 Importländer im Jahr {year_selected}',
            xaxis_title='Land',
            yaxis_title='Import Wert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Handelsvolumen Grafik
        fig_handelsvolumen = go.Figure([go.Bar(
            x=top_10_handelsvolumen['Land'],
            y=top_10_handelsvolumen['handelsvolumen_wert'],
            marker_color='orange',
            hovertemplate='<b>%{x}</b><br>Wert: %{y:,} €<extra></extra>'
        )])
        fig_handelsvolumen.update_layout(
            title=f'Top 10 Handelsvolumenländer im Jahr {year_selected}',
            xaxis_title='Land',
            yaxis_title='Handelsvolumen Wert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        return fig_export, fig_import, fig_handelsvolumen
