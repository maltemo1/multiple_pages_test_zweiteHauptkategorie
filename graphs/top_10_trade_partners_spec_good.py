import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math
import os

# Datenpfad
df_path = os.path.join("data", "top10_goods_spec_country_and_year.csv")
df = pd.read_csv(df_path)

# Werte umrechnen
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0) * 1000

# Handelsvolumen berechnen
df['Handelsvolumen'] = df['Ausfuhr: Wert'] + df['Einfuhr: Wert']

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
        html.H1("Top 10 Handelspartner Deutschlands für ausgewählte Ware"),

        html.Div([
            dcc.Dropdown(
                id='jahr_dropdown',
                options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
                value=2024,
                clearable=False,
                style={'width': '48%', 'display': 'inline-block'}
            ),
            dcc.Dropdown(
                id='ware_dropdown',
                options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].unique())],
                value='Mineralische Brennstoffe, Schmiermittel und verwandte Erzeugnisse',
                clearable=False,
                style={'width': '48%', 'display': 'inline-block', 'float': 'right'}
            ),
        ], style={'margin-bottom': '20px'}),

        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
        dcc.Graph(id='handelsvolumen_graph'),
    ])

# Callback-Funktion
def register_callbacks(app):
    @app.callback(
        [Output('export_graph', 'figure'),
         Output('import_graph', 'figure'),
         Output('handelsvolumen_graph', 'figure')],
        [Input('jahr_dropdown', 'value'),
         Input('ware_dropdown', 'value')]
    )
    def update_graphs(year_selected, ware_selected):
        dff = df[(df['Jahr'] == year_selected) & (df['Label'] == ware_selected)]

        top_export = dff.sort_values(by='Ausfuhr: Wert', ascending=False).head(10)
        top_import = dff.sort_values(by='Einfuhr: Wert', ascending=False).head(10)
        top_handelsvolumen = dff.sort_values(by='Handelsvolumen', ascending=False).head(10)

        max_value = max(
            top_export['Ausfuhr: Wert'].max(),
            top_import['Einfuhr: Wert'].max(),
            top_handelsvolumen['Handelsvolumen'].max()
        )
        rounded_max = math.ceil(max_value / 50e9) * 50e9
        tickvals = np.arange(0, rounded_max + 1, 50e9)
        ticktext = [formatter(val) for val in tickvals]

        # Export
        fig_export = go.Figure([go.Bar(
            x=top_export['Land'],
            y=top_export['Ausfuhr: Wert'],
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br>Exportwert: %{y:,} €<extra></extra>'
        )])
        fig_export.update_layout(
            title=f'Top 10 Exportländer im Jahr {year_selected} ({ware_selected})',
            xaxis_title='Land',
            yaxis_title='Exportwert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Import
        fig_import = go.Figure([go.Bar(
            x=top_import['Land'],
            y=top_import['Einfuhr: Wert'],
            marker_color='green',
            hovertemplate='<b>%{x}</b><br>Importwert: %{y:,} €<extra></extra>'
        )])
        fig_import.update_layout(
            title=f'Top 10 Importländer im Jahr {year_selected} ({ware_selected})',
            xaxis_title='Land',
            yaxis_title='Importwert (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        # Handelsvolumen
        fig_handelsvolumen = go.Figure([go.Bar(
            x=top_handelsvolumen['Land'],
            y=top_handelsvolumen['Handelsvolumen'],
            marker_color='orange',
            hovertemplate='<b>%{x}</b><br>Handelsvolumen: %{y:,} €<extra></extra>'
        )])
        fig_handelsvolumen.update_layout(
            title=f'Top 10 Länder nach Handelsvolumen im Jahr {year_selected} ({ware_selected})',
            xaxis_title='Land',
            yaxis_title='Handelsvolumen (Euro)',
            yaxis=dict(tickvals=tickvals, ticktext=ticktext, rangemode="tozero")
        )

        return fig_export, fig_import, fig_handelsvolumen
