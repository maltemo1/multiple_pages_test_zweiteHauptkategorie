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

# Liste der Farben für Konsistenz
colors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#ff1493", "#00ffff", "#8b0000", "#32cd32", "#ffd700",
    "#4b0082", "#ffa500", "#00ff00", "#800080", "#ff4500",
    "#4682b4", "#dc143c", "#2e8b57", "#ff6347", "#6a5acd"
]

# Farben Ländern zuordnen
unique_countries = sorted(df['Land'].dropna().unique())
color_dict = {country: colors[i % len(colors)] for i, country in enumerate(unique_countries)}

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

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Gesamter Export- und Importverlauf einer Ware mit verschiedenen Ländern von 2008 bis 2024"),

        dcc.Dropdown(
            id='trade_spec_good_dropdown_goods',
            options=[{'label': good, 'value': good} for good in sorted(df['Label'].dropna().unique())],
            value="Kraftfahrzeuge, Landfahrzeuge",  # Standardwert
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='trade_spec_good_dropdown_countries',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].dropna().unique())],
            value=['Islamische Republik Iran', 'Irak', 'Katar'],  # Standardwerte
            multi=True,
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='trade_spec_good_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='trade_spec_good_export_graph'),
        dcc.Graph(id='trade_spec_good_import_graph'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('trade_spec_good_export_graph', 'figure'),
         dash.Output('trade_spec_good_import_graph', 'figure'),
         dash.Output('trade_spec_good_info_text', 'children')],
        [dash.Input('trade_spec_good_dropdown_goods', 'value'),
         dash.Input('trade_spec_good_dropdown_countries', 'value')]
    )
    def update_graphs(selected_good, selected_countries):
        df_filtered = df[(df['Label'] == selected_good) & (df['Land'].isin(selected_countries))]

        # Falls keine Daten vorhanden sind, leere Graphen zurückgeben
        if df_filtered.empty:
            return go.Figure(), go.Figure(), f"Keine Daten für {selected_good} in den ausgewählten Ländern verfügbar."

        # Export- und Import-Graphen
        fig_export = go.Figure()
        fig_import = go.Figure()

        # Daten für Y-Achsen-Skalierung sammeln
        max_export = df_filtered['Ausfuhr: Wert'].max()
        max_import = df_filtered['Einfuhr: Wert'].max()

        for country in selected_countries:
            df_country = df_filtered[df_filtered['Land'] == country]
            color = color_dict.get(country, '#000000')  # Fallback-Farbe falls nicht gefunden

            # EXPORT-GRAPH
            fig_export.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country['Ausfuhr: Wert'],
                mode='lines+markers',
                name=f"{country} - Export",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{country} - Export</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

            # IMPORT-GRAPH
            fig_import.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country['Einfuhr: Wert'],
                mode='lines+markers',
                name=f"{country} - Import",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{country} - Import</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Achsenskala berechnen
        step_size_export = determine_step_size(max_export)
        rounded_max_export = math.ceil(max_export / step_size_export) * step_size_export
        tickvals_export = np.arange(0, rounded_max_export + 1, step_size_export)
        ticktext_export = [formatter(val) for val in tickvals_export]

        step_size_import = determine_step_size(max_import)
        rounded_max_import = math.ceil(max_import / step_size_import) * step_size_import
        tickvals_import = np.arange(0, rounded_max_import + 1, step_size_import)
        ticktext_import = [formatter(val) for val in tickvals_import]

        fig_export.update_layout(
            title=f'Jährliche Exporte von {selected_good} aus Deutschland in die ausgewählten Länder',
            xaxis_title='Jahr',
            yaxis_title='Exportwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_export, ticktext=ticktext_export),
            legend=dict(title='Länder')
        )

        fig_import.update_layout(
            title=f'Jährliche Importe von {selected_good} aus den ausgewählten Ländern nach Deutschland',
            xaxis_title='Jahr',
            yaxis_title='Importwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_import, ticktext=ticktext_import),
            legend=dict(title='Länder')
        )

        return fig_export, fig_import, f"Export- und Importverlauf von {selected_good} mit den ausgewählten Ländern."

