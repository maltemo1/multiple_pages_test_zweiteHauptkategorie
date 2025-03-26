import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/top10_goods_spec_country_and_year.csv")

# Daten laden
df = pd.read_csv(csv_path)

# Falls die Daten nicht korrekt geladen wurden, abbrechen
if df.empty:
    raise ValueError("CSV-Datei konnte nicht geladen werden oder ist leer.")

# Werte umrechnen (Tausenderwerte auf Originalwerte)
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0) * 1000

# Funktion zur Bestimmung der optimalen Schrittgröße für die Y-Achse
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Funktion zur Y-Achsen-Formatierung
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

# Funktion zur Erstellung des Layouts
def create_layout():
    return html.Div([
        html.H1("Jährlicher Export- und Importverlauf einer Ware mit Deutschland"),

        dcc.Dropdown(
            id='overview_trade_spec_good_dropdown_country',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].dropna().unique())],
            value='Islamische Republik Iran' if 'Islamische Republik Iran' in df['Land'].values else df['Land'].dropna().unique()[0],
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='overview_trade_spec_good_dropdown_good',
            options=[{'label': good, 'value': good} for good in sorted(df['Label'].dropna().unique())],
            value="Pharmazeutische Erzeugnisse",  # Standardmäßig erste Ware
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='overview_trade_spec_good_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='overview_trade_spec_good_graph'),
    ])

# Callback für das Update des Graphen
def register_callbacks(app):
    @app.callback(
        [dash.Output('overview_trade_spec_good_graph', 'figure'),
         dash.Output('overview_trade_spec_good_info_text', 'children')],
        [dash.Input('overview_trade_spec_good_dropdown_country', 'value'),
         dash.Input('overview_trade_spec_good_dropdown_good', 'value')]
    )
    def update_graph(selected_country, selected_good):
        # Daten filtern für das ausgewählte Land und die ausgewählte Ware
        df_filtered = df[(df['Land'] == selected_country) & (df['Label'] == selected_good)]

        # Falls keine Daten vorhanden sind, leeren Graph zurückgeben
        if df_filtered.empty:
            return go.Figure(), f"Keine Daten für {selected_good} in {selected_country} verfügbar."

        fig = go.Figure()

        # Linien für Export und Import
        for col, name, color in zip(
            ['Ausfuhr: Wert', 'Einfuhr: Wert'],
            ['Exportwert', 'Importwert'],
            ['#1f77b4', '#ff7f0e']
        ):
            fig.add_trace(go.Scatter(
                x=df_filtered['Jahr'],
                y=df_filtered[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Achsenskala berechnen
        max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Jährlicher Export- und Importverlauf von {selected_good} mit {selected_country}',
            xaxis_title='Jahr',
            yaxis_title='Wert in €',
            xaxis=dict(
                tickmode='array',
                tickvals=sorted(df_filtered['Jahr'].unique()),
            ),
            yaxis=dict(
                tickvals=tickvals,
                ticktext=ticktext
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        # Handelsbilanz-Info berechnen
        total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
        total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9
        handelsbilanz = total_export - total_import
        status = "Handelsüberschuss" if handelsbilanz > 0 else "Handelsdefizit" if handelsbilanz < 0 else "Ausgeglichene Handelsbilanz"

        info_text = f"Gesamter Export: {total_export:.2f} Mrd €, Gesamter Import: {total_import:.2f} Mrd € → {status}: {handelsbilanz:.2f} Mrd € (für {selected_good} mit {selected_country} im Zeitraum von 2008-2024)"

        return fig, info_text
