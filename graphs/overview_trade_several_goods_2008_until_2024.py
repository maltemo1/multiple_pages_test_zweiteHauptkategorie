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

# Sicherstellen, dass notwendige Spalten vorhanden sind
if df.empty or not {'Jahr', 'Label', 'Ausfuhr: Wert', 'Einfuhr: Wert'}.issubset(df.columns):
    raise ValueError("Die CSV-Datei konnte nicht korrekt geladen werden oder enthält nicht alle benötigten Spalten.")

# Daten aggregieren: monatliche Werte zu jährlichen Summen je Ware
df_yearly = df.groupby(['Jahr', 'Label'], as_index=False).agg({
    'Ausfuhr: Wert': 'sum',
    'Einfuhr: Wert': 'sum'
})

# Liste der Farben für Konsistenz
colors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#ff1493", "#00ffff", "#8b0000", "#32cd32", "#ffd700",
    "#4b0082", "#ffa500", "#00ff00", "#800080", "#ff4500",
    "#4682b4", "#dc143c", "#2e8b57", "#ff6347", "#6a5acd",
    "#20b2aa", "#ff69b4", "#b8860b", "#008080", "#adff2f"
]

# Farben Waren zuordnen
unique_labels = sorted(df_yearly['Label'].dropna().unique())
color_dict = {label: colors[i % len(colors)] for i, label in enumerate(unique_labels)}

# Hilfsfunktionen für Y-Achsen
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

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
        html.H1("Gesamter Export- und Importverlauf der Waren (jährliche Werte)"),

        dcc.Dropdown(
            id='overview_goods_dropdown',
            options=[{'label': label, 'value': label} for label in unique_labels],
            value=['Mineralische Brennstoffe usw.', 'Kraftfahrzeuge, Landfahrzeuge'],
            multi=True,
            clearable=False,
            style={'width': '60%'}
        ),

        html.Div(id='overview_goods_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='overview_goods_export_graph'),
        dcc.Graph(id='overview_goods_import_graph'),
    ])

# Callback-Funktion
def register_callbacks(app):
    @app.callback(
        [dash.Output('overview_goods_export_graph', 'figure'),
         dash.Output('overview_goods_import_graph', 'figure'),
         dash.Output('overview_goods_info_text', 'children')],
        [dash.Input('overview_goods_dropdown', 'value')]
    )
    def update_graphs(selected_goods):
        df_filtered = df_yearly[df_yearly['Label'].isin(selected_goods)]

        if df_filtered.empty:
            return go.Figure(), go.Figure(), "Keine Daten für die ausgewählten Waren verfügbar."

        # Graphen vorbereiten
        fig_export = go.Figure()
        fig_import = go.Figure()

        max_export = df_filtered['Ausfuhr: Wert'].max()
        max_import = df_filtered['Einfuhr: Wert'].max()

        for label in selected_goods:
            df_label = df_filtered[df_filtered['Label'] == label]
            color = color_dict.get(label, '#000000')

            fig_export.add_trace(go.Scatter(
                x=df_label['Jahr'],
                y=df_label['Ausfuhr: Wert'],
                mode='lines+markers',
                name=f"{label} - Export",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{label} - Export</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

            fig_import.add_trace(go.Scatter(
                x=df_label['Jahr'],
                y=df_label['Einfuhr: Wert'],
                mode='lines+markers',
                name=f"{label} - Import",
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{label} - Import</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Achsen formatieren
        step_size_export = determine_step_size(max_export)
        rounded_max_export = math.ceil(max_export / step_size_export) * step_size_export
        tickvals_export = np.arange(0, rounded_max_export + 1, step_size_export)
        ticktext_export = [formatter(val) for val in tickvals_export]

        step_size_import = determine_step_size(max_import)
        rounded_max_import = math.ceil(max_import / step_size_import) * step_size_import
        tickvals_import = np.arange(0, rounded_max_import + 1, step_size_import)
        ticktext_import = [formatter(val) for val in tickvals_import]

        fig_export.update_layout(
            title='Jährliche Exporte aus Deutschland (alle Länder)',
            xaxis_title='Jahr',
            yaxis_title='Exportwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_export, ticktext=ticktext_export),
            legend=dict(title='Waren')
        )

        fig_import.update_layout(
            title='Jährliche Importe nach Deutschland (aus allen Ländern)',
            xaxis_title='Jahr',
            yaxis_title='Importwert in €',
            xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
            yaxis=dict(tickvals=tickvals_import, ticktext=ticktext_import),
            legend=dict(title='Waren')
        )

        # Handelsbilanz-Berechnung
        total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
        total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9
        handelsbilanz = total_export - total_import
        status = "Handelsüberschuss" if handelsbilanz > 0 else "Handelsdefizit" if handelsbilanz < 0 else "Ausgeglichene Handelsbilanz"

        info_text = f"Gesamter Export: {total_export:.2f} Mrd €, Gesamter Import: {total_import:.2f} Mrd € → {status}: {handelsbilanz:.2f} Mrd € (für die ausgewählten Waren von 2008–2024)"

        return fig_export, fig_import, info_text
