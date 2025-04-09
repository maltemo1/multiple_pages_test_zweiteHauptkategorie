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
    "#4b0082", "#ffa500", "#00ff00", "#800080", "#ff4500"
]

# Funktion zur Bestimmung der optimalen Schrittgröße für die Y-Achse
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Y-Achsen-Formatter
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
        html.H1("Deutschlands Top 5 Export- und Importländer einer ausgewählten Ware (2008–2024)"),

        dcc.Dropdown(
            id='top5_spec_good_dropdown_goods',
            options=[{'label': good, 'value': good} for good in sorted(df['Label'].dropna().unique())],
            value='Kraftfahrzeuge, Landfahrzeuge',
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Graph(id='top5_spec_good_export_graph'),
        dcc.Graph(id='top5_spec_good_import_graph')
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('top5_spec_good_export_graph', 'figure'),
         dash.Output('top5_spec_good_import_graph', 'figure')],
        [dash.Input('top5_spec_good_dropdown_goods', 'value')]
    )
    def update_graphs(selected_good):
        df_filtered = df[df['Label'] == selected_good]

        if df_filtered.empty:
            return go.Figure(), go.Figure()

        # Gruppieren nach Jahr & Land
        export_agg = df_filtered.groupby(['Jahr', 'Land'], as_index=False)['Ausfuhr: Wert'].sum()
        import_agg = df_filtered.groupby(['Jahr', 'Land'], as_index=False)['Einfuhr: Wert'].sum()

        # Top 5 Länder insgesamt
        top5_export_countries = export_agg.groupby('Land')['Ausfuhr: Wert'].sum().nlargest(5).index
        top5_import_countries = import_agg.groupby('Land')['Einfuhr: Wert'].sum().nlargest(5).index

        export_df = export_agg[export_agg['Land'].isin(top5_export_countries)]
        import_df = import_agg[import_agg['Land'].isin(top5_import_countries)]

        # Max-Werte für Skalierung
        max_export = export_df['Ausfuhr: Wert'].max()
        max_import = import_df['Einfuhr: Wert'].max()

        # EXPORT-GRAPH
        fig_export = go.Figure()
        for i, country in enumerate(top5_export_countries):
            country_df = export_df[export_df['Land'] == country]
            fig_export.add_trace(go.Scatter(
                x=country_df['Jahr'],
                y=country_df['Ausfuhr: Wert'],
                mode='lines+markers',
                name=country,
                line=dict(width=2, color=colors[i % len(colors)]),
                hovertemplate=f"<b>{country} – {selected_good}</b><br>Jahr: %{{x}}<br>Export: %{{y:,.0f}} €<extra></extra>"
            ))

        step_export = determine_step_size(max_export)
        rounded_max_export = math.ceil(max_export / step_export) * step_export
        tickvals_export = np.arange(0, rounded_max_export + 1, step_export)
        ticktext_export = [formatter(val) for val in tickvals_export]

        fig_export.update_layout(
            title=f"Top 5 Exportländer für {selected_good}",
            xaxis_title="Jahr",
            yaxis_title="Exportwert in €",
            xaxis=dict(tickmode='array', tickvals=sorted(export_df['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_export, ticktext=ticktext_export),
            legend=dict(title="Länder")
        )

        # IMPORT-GRAPH
        fig_import = go.Figure()
        for i, country in enumerate(top5_import_countries):
            country_df = import_df[import_df['Land'] == country]
            fig_import.add_trace(go.Scatter(
                x=country_df['Jahr'],
                y=country_df['Einfuhr: Wert'],
                mode='lines+markers',
                name=country,
                line=dict(width=2, color=colors[i % len(colors)]),
                hovertemplate=f"<b>{country} – {selected_good}</b><br>Jahr: %{{x}}<br>Import: %{{y:,.0f}} €<extra></extra>"
            ))

        step_import = determine_step_size(max_import)
        rounded_max_import = math.ceil(max_import / step_import) * step_import
        tickvals_import = np.arange(0, rounded_max_import + 1, step_import)
        ticktext_import = [formatter(val) for val in tickvals_import]

        fig_import.update_layout(
            title=f"Top 5 Importländer für {selected_good}",
            xaxis_title="Jahr",
            yaxis_title="Importwert in €",
            xaxis=dict(tickmode='array', tickvals=sorted(import_df['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_import, ticktext=ticktext_import),
            legend=dict(title="Länder")
        )

        return fig_export, fig_import
