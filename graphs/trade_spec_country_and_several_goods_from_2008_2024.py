import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from statistics import mean
import glob
from statsmodels.tsa.seasonal import seasonal_decompose
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.ticker import FuncFormatter
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import math
import gdown
import os


# CSV-Datei einlesen
df = pd.read_csv("data/top10_goods_spec_country_and_year.csv")

# Werte umrechnen (Tausenderwerte auf Originalwerte)
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# # Farbpalette für Waren
# colors = [
#     "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
#     "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
# ]

colors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#ff1493", "#00ffff", "#8b0000", "#32cd32", "#ffd700",
    "#4b0082", "#ffa500", "#00ff00", "#800080", "#ff4500",
    "#4682b4", "#dc143c", "#2e8b57", "#ff6347", "#6a5acd",
    "#20b2aa", "#ff69b4", "#b8860b", "#008080", "#adff2f",
    "#c71585", "#8b008b", "#556b2f", "#ff8c00", "#9932cc",
    "#808000", "#ffdab9", "#00bfff", "#cd5c5c", "#9400d3"
]


# Waren zu Farben zuordnen
unique_labels = sorted(df['Label'].unique())
color_dict = {label: colors[i % len(colors)] for i, label in enumerate(unique_labels)}

# Dash-App erstellen
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Jährlicher Export- und Importverlauf ausgewählter Waren mit Deutschland"),

    dcc.Dropdown(
        id='land_dropdown',
        options=[{'label': str(l), 'value': l} for l in sorted(df['Land'].unique())],
        value='Islamische Republik Iran',
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Dropdown(
        id='ware_dropdown',
        options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].unique())],
        value=['Pharmazeutische Erzeugnisse', 'Mineralische Brennstoffe usw.'],
        multi=True,
        clearable=False,
        style={'width': '50%'}
    ),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='export_graph'),
    dcc.Graph(id='import_graph'),
])

@app.callback(
    [Output('export_graph', 'figure'),
     Output('import_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('land_dropdown', 'value'),
     Input('ware_dropdown', 'value')]
)
def update_graphs(selected_land, selected_labels):
    df_filtered = df[(df['Land'] == selected_land) & (df['Label'].isin(selected_labels))]

    if df_filtered.empty:
        return go.Figure(), go.Figure(), f"Keine Daten für die ausgewählten Waren in {selected_land} verfügbar."

    # Max-Werte für Y-Achsen-Skalierung getrennt berechnen
    max_export = df_filtered['Ausfuhr: Wert'].max()
    max_import = df_filtered['Einfuhr: Wert'].max()

    fig_export = go.Figure()
    fig_import = go.Figure()

    for label in selected_labels:
        df_label = df_filtered[df_filtered['Label'] == label]
        color = color_dict[label]  # Gleiche Farbe für Export & Import

        # EXPORT-GRAPH
        fig_export.add_trace(go.Scatter(
            x=df_label['Jahr'],
            y=df_label['Ausfuhr: Wert'],
            mode='lines+markers',
            name=f"{label} - Export",
            line=dict(width=2, color=color),
            marker=dict(symbol='circle', size=8),
            hovertemplate=f'<b>{label} - Export</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

        # IMPORT-GRAPH
        fig_import.add_trace(go.Scatter(
            x=df_label['Jahr'],
            y=df_label['Einfuhr: Wert'],
            mode='lines+markers',
            name=f"{label} - Import",
            line=dict(width=2, color=color),
            marker=dict(symbol='x', size=8),
            hovertemplate=f'<b>{label} - Import</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Dynamische Schrittgröße für Export-Y-Achse
    def get_step_size(max_value):
        if max_value < 1e3: return 100
        elif max_value < 5e3: return 500
        elif max_value < 1e4: return 1e3
        elif max_value < 5e4: return 5e3
        elif max_value < 1e5: return 10e3
        elif max_value < 5e5: return 50e3
        elif max_value < 1e6: return 100e3
        elif max_value < 5e6: return 1e6
        elif max_value < 10e6: return 5e6
        elif max_value < 50e6: return 10e6
        elif max_value < 100e6: return 25e6
        elif max_value < 250e6: return 50e6
        elif max_value < 500e6: return 100e6
        elif max_value < 1e9: return 250e6
        elif max_value < 5e9: return 500e6
        elif max_value < 10e9: return 1e9
        elif max_value < 50e9: return 2e9
        elif max_value < 100e9: return 10e9
        else: return 25e9

    step_export = get_step_size(max_export)
    step_import = get_step_size(max_import)

    # Achsenwerte berechnen
    tickvals_export = np.arange(0, math.ceil(max_export / step_export) * step_export + 1, step_export)
    tickvals_import = np.arange(0, math.ceil(max_import / step_import) * step_import + 1, step_import)

    # EXPORT-GRAPH Layout
    fig_export.update_layout(
        title=f'Jährliche Exportwerte nach {selected_land}',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
        yaxis=dict(tickvals=tickvals_export, ticktext=[formatter(val) for val in tickvals_export]),
        legend=dict(title='Exportwaren', bgcolor='rgba(255,255,255,0.7)')
    )

    # IMPORT-GRAPH Layout
    fig_import.update_layout(
        title=f'Jährliche Importwerte aus {selected_land}',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        xaxis=dict(tickmode='array', tickvals=sorted(df_filtered['Jahr'].unique())),
        yaxis=dict(tickvals=tickvals_import, ticktext=[formatter(val) for val in tickvals_import]),
        legend=dict(title='Importwaren', bgcolor='rgba(255,255,255,0.7)')
    )

    total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
    total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9

    info_text = (f"Für die ausgewählten Waren zwischen Deutschland und {selected_land} beträgt "
                 f"der gesamte Exportwert {total_export:.2f} Mrd € und "
                 f"der gesamte Importwert {total_import:.2f} Mrd € von 2008 bis 2024.")

    return fig_export, fig_import, info_text

if __name__ == '__main__':
    app.run(debug=True)
