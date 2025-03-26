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
    "#ff1493", "#00ffff", "#8b0000", "#32cd32", "#ffd700"
]

# Farben Waren zuordnen
unique_labels = sorted(df['Label'].dropna().unique())
color_dict = {label: colors[i % len(colors)] for i, label in enumerate(unique_labels)}

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
        html.H1("Gesamter Export- und Importverlauf verschiedener Waren mit Deutschland"),

        dcc.Dropdown(
            id='trade_several_goods_dropdown_country',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].dropna().unique())],
            value='Islamische Republik Iran' if 'Islamische Republik Iran' in df['Land'].values else df['Land'].dropna().unique()[0],
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='trade_several_goods_dropdown_goods',
            options=[{'label': good, 'value': good} for good in sorted(df['Label'].dropna().unique())],
            value=["Pharmazeutische Erzeugnisse", "Mineralische Brennstoffe usw."],  # Standardwerte
            multi=True,
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='trade_several_goods_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='trade_several_goods_export_graph'),
        dcc.Graph(id='trade_several_goods_import_graph'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('trade_several_goods_export_graph', 'figure'),
         dash.Output('trade_several_goods_import_graph', 'figure'),
         dash.Output('trade_several_goods_info_text', 'children')],
        [dash.Input('trade_several_goods_dropdown_country', 'value'),
         dash.Input('trade_several_goods_dropdown_goods', 'value')]
    )
    def update_graphs(selected_country, selected_goods):
        df_filtered = df[(df['Land'] == selected_country) & (df['Label'].isin(selected_goods))]

        # Falls keine Daten vorhanden sind, leere Graphen zurückgeben
        if df_filtered.empty:
            return go.Figure(), go.Figure(), f"Keine Daten für die ausgewählten Waren in {selected_country} verfügbar."

        # Export- und Import-Graphen
        fig_export = go.Figure()
        fig_import = go.Figure()

        # Daten für Y-Achsen-Skalierung sammeln
        max_export = df_filtered['Ausfuhr: Wert'].max()
        max_import = df_filtered['Einfuhr: Wert'].max()

        for good in selected_goods:
            df_good = df_filtered[df_filtered['Label'] == good]
            color = color_dict.get(good, '#000000')  # Fallback-Farbe falls nicht gefunden

            # EXPORT-GRAPH
            fig_export.add_trace(go.Scatter(
                x=df_good['Jahr'],
                y=df_good['Ausfuhr: Wert'],
                mode='lines+markers',
                name=f"{good} - Export",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{good} - Export</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

            # IMPORT-GRAPH
            fig_import.add_trace(go.Scatter(
                x=df_good['Jahr'],
                y=df_good['Einfuhr: Wert'],
                mode='lines+markers',
                name=f"{good} - Import",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{good} - Import</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
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
            title=f'Exportverlauf für {selected_country}',
            xaxis_title='Jahr',
            yaxis_title='Exportwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_export, ticktext=ticktext_export),
            legend=dict(title='Waren')
        )

        fig_import.update_layout(
            title=f'Importverlauf für {selected_country}',
            xaxis_title='Jahr',
            yaxis_title='Importwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_import, ticktext=ticktext_import),
            legend=dict(title='Waren')
        )

        return fig_export, fig_import, f"Handelsverlauf von {selected_country} für die ausgewählten Waren (2008-2024)."

