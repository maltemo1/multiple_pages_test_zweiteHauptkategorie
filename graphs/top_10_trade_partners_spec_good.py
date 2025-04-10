import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math
import os

# Datenpfad definieren
csv_path = os.path.join("data", "top10_goods_spec_country_and_year.csv")

# CSV einlesen
df = pd.read_csv(csv_path)

# Handelsvolumen berechnen
df["Handelsvolumen"] = df["Ausfuhr: Wert"] + df["Einfuhr: Wert"]

# Formatter-Funktion für Achsenticks
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
        html.H1("Top 10 Handelspartner für ausgewählte Ware und Jahr"),
        
        html.Div([
            dcc.Dropdown(
                id='top10_ware_dropdown_unique',
                options=[{'label': ware, 'value': ware} for ware in sorted(df['Label'].unique())],
                value='Mineralische Brennstoffe usw.',
                clearable=False,
                style={'width': '80%', 'marginBottom': '20px'}
            ),
            dcc.Dropdown(
                id='top10_jahr_dropdown_unique',
                options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
                value=2024,
                clearable=False,
                style={'width': '50%'}
            ),
        ]),

        dcc.Graph(id='top10_export_graph_unique'),
        dcc.Graph(id='top10_import_graph_unique'),
        dcc.Graph(id='top10_handelsvolumen_graph_unique'),
    ])

# Callback-Funktion
def register_callbacks(app):
    @app.callback(
        [Output('top10_export_graph_unique', 'figure'),
         Output('top10_import_graph_unique', 'figure'),
         Output('top10_handelsvolumen_graph_unique', 'figure')],
        [Input('top10_ware_dropdown_unique', 'value'),
         Input('top10_jahr_dropdown_unique', 'value')]
    )
    def update_graphs(selected_ware, selected_year):
        dff = df[(df['Jahr'] == selected_year) & (df['Label'] == selected_ware)]

        # Sortierung & Auswahl Top 10
        top_export = dff.sort_values(by='Ausfuhr: Wert', ascending=False).head(10)
        top_import = dff.sort_values(by='Einfuhr: Wert', ascending=False).head(10)
        top_handelsvolumen = dff.sort_values(by='Handelsvolumen', ascending=False).head(10)

        # Y-Achsen-Skalierung einheitlich setzen
        max_value = max(
            top_export['Ausfuhr: Wert'].max(),
            top_import['Einfuhr: Wert'].max(),
            top_handelsvolumen['Handelsvolumen'].max()
        )
        rounded_max = math.ceil(max_value / 50e9) * 50e9
        tickvals = np.arange(0, rounded_max + 1, 50e9)
        ticktext = [formatter(val) for val in tickvals]

        # Export-Graph
        fig_export = go.Figure([go.Bar(
            x=top_export['Land'],
            y=top_export['Ausfuhr: Wert'],
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br>Exportwert: %{y:,} €<extra></extra>'
        )])
        fig_export.update_layout(
            title=f'Top 10 Exportländer für "{selected_ware}" ({selected_year})',
            xaxis_title='Land',
            yaxis_title='Export Wert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Import-Graph
        fig_import = go.Figure([go.Bar(
            x=top_import['Land'],
            y=top_import['Einfuhr: Wert'],
            marker_color='green',
            hovertemplate='<b>%{x}</b><br>Importwert: %{y:,} €<extra></extra>'
        )])
        fig_import.update_layout(
            title=f'Top 10 Importländer für "{selected_ware}" ({selected_year})',
            xaxis_title='Land',
            yaxis_title='Import Wert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Handelsvolumen-Graph
        fig_handelsvolumen = go.Figure([go.Bar(
            x=top_handelsvolumen['Land'],
            y=top_handelsvolumen['Handelsvolumen'],
            marker_color='orange',
            hovertemplate='<b>%{x}</b><br>Handelsvolumen: %{y:,} €<extra></extra>'
        )])
        fig_handelsvolumen.update_layout(
            title=f'Top 10 Länder nach Handelsvolumen für "{selected_ware}" ({selected_year})',
            xaxis_title='Land',
            yaxis_title='Handelsvolumen (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        return fig_export, fig_import, fig_handelsvolumen
