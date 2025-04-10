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

# Werte umrechnen (Tausenderwerte auf Originalwerte)
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0) * 1000

# Handelsvolumen berechnen
df["Handelsvolumen"] = df["Ausfuhr: Wert"] + df["Einfuhr: Wert"]

# Funktion zur Bestimmung der optimalen Schrittgröße für die Y-Achse
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Formatter-Funktion für Achsenticks
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

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

        # Y-Achsen-Skalierung individuell berechnen
        def generate_ticks(max_val):
            step = determine_step_size(max_val)
            upper = math.ceil(max_val / step) * step
            tickvals = np.arange(0, upper + 1, step)
            ticktext = [formatter(v) for v in tickvals]
            return tickvals, ticktext

        # EXPORT
        max_exp = top_export['Ausfuhr: Wert'].max()
        tickvals_exp, ticktext_exp = generate_ticks(max_exp)

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
            yaxis=dict(tickvals=tickvals_exp, ticktext=ticktext_exp, rangemode="tozero")
        )

        # IMPORT
        max_imp = top_import['Einfuhr: Wert'].max()
        tickvals_imp, ticktext_imp = generate_ticks(max_imp)

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
            yaxis=dict(tickvals=tickvals_imp, ticktext=ticktext_imp, rangemode="tozero")
        )

        # HANDELSVOLUMEN
        max_hv = top_handelsvolumen['Handelsvolumen'].max()
        tickvals_hv, ticktext_hv = generate_ticks(max_hv)

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
            yaxis=dict(tickvals=tickvals_hv, ticktext=ticktext_hv, rangemode="tozero")
        )

        return fig_export, fig_import, fig_handelsvolumen
