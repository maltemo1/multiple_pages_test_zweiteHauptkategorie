import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/aggregated_df.csv")

# Daten laden
df = pd.read_csv(csv_path)

# Monatliche Werte in jährliche Werte aggregieren
df_yearly = df.groupby(['Jahr', 'Label'], as_index=False).agg({
    'Ausfuhr: Wert': 'sum',
    'Einfuhr: Wert': 'sum'
})

# Werte auf Originalniveau bringen, falls nötig
df_yearly[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df_yearly[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0)

# Funktion zur optimalen Y-Achsen-Schrittweite
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Formatierung der Y-Achse
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
        html.H1("Gesamtüberblick: Ex- und Importe einer Ware (2008–2024)"),

        dcc.Dropdown(
            id='overview_trade_spec_good_dropdown_good_only',
            options=[{'label': good, 'value': good} for good in sorted(df_yearly['Label'].dropna().unique())],
            value='Mineralische Brennstoffe usw.' if 'Mineralische Brennstoffe usw.' in df_yearly['Label'].values else df_yearly['Label'].dropna().unique()[0],
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='overview_trade_spec_good_info_text_good_only', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='overview_trade_spec_good_graph_good_only'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('overview_trade_spec_good_graph_good_only', 'figure'),
         dash.Output('overview_trade_spec_good_info_text_good_only', 'children')],
        [dash.Input('overview_trade_spec_good_dropdown_good_only', 'value')]
    )
    def update_graph(selected_good):
        df_filtered = df_yearly[df_yearly['Label'] == selected_good]

        if df_filtered.empty:
            return go.Figure(), f"Keine Daten für {selected_good} verfügbar."

        fig = go.Figure()

        # Linienplot für Export & Import
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

        # Y-Achse skalieren
        max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Export- und Importverlauf von {selected_good} weltweit (2008–2024)',
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

        # Info-Text
        total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
        total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9

        info_text = (
            f"Gesamter Export: {total_export:.2f} Mrd €, Gesamter Import: {total_import:.2f} Mrd € "
            f"→ Zeitraum: 2008–2024 für {selected_good} zwischen Deutschland und der Welt."
        )

        return fig, info_text
