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
df = pd.read_csv('data/aggregated_df.csv')

# Monatliche Werte in jährliche Werte aggregieren
df_yearly = df.groupby(['Jahr', 'Label'], as_index=False).agg({
    'Ausfuhr: Wert': 'sum',
    'Einfuhr: Wert': 'sum'
})

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

# Dash-App erstellen
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Jährlicher Export- und Importverlauf mehrerer Waren mit Deutschland"),

    dcc.Dropdown(
        id='ware_dropdown',
        options=[{'label': str(w), 'value': w} for w in sorted(df_yearly['Label'].unique())],
        value=['Mineralische Brennstoffe usw.', "Kraftfahrzeuge, Landfahrzeuge"],
        multi=True,
        clearable=False,
        style={'width': '60%'}
    ),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='export_graph'),
    dcc.Graph(id='import_graph'),
])

@app.callback(
    [Output('export_graph', 'figure'),
     Output('import_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('ware_dropdown', 'value')]
)
def update_graph(selected_labels):
    df_filtered = df_yearly[df_yearly['Label'].isin(selected_labels)]

    if df_filtered.empty:
        return go.Figure(), go.Figure(), "Keine Daten verfügbar."

    export_fig = go.Figure()
    import_fig = go.Figure()

    for label in selected_labels:
        subset = df_filtered[df_filtered['Label'] == label]

        # Export Graph
        export_fig.add_trace(go.Scatter(
            x=subset['Jahr'],
            y=subset['Ausfuhr: Wert'],
            mode='lines+markers',
            name=f'{label} (Export)',
            line=dict(width=2),
            hovertemplate=f'<b>{label}</b><br>Jahr: %{{x}}<br>Exportwert: %{{y:,.0f}} €<extra></extra>'
        ))

        # Import Graph
        import_fig.add_trace(go.Scatter(
            x=subset['Jahr'],
            y=subset['Einfuhr: Wert'],
            mode='lines+markers',
            name=f'{label} (Import)',
            line=dict(width=2),
            hovertemplate=f'<b>{label}</b><br>Jahr: %{{x}}<br>Importwert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Maximale Werte für dynamische Skalierung der y-Achse bestimmen
    max_export_value = df_filtered['Ausfuhr: Wert'].max()
    max_import_value = df_filtered['Einfuhr: Wert'].max()
    max_value = max(max_export_value, max_import_value)

    # Dynamische Schrittgröße für die y-Achse
    if max_value < 1e3:
        step = 100
    elif max_value < 5e3:
        step = 500
    elif max_value < 1e4:
        step = 1e3
    elif max_value < 5e4:
        step = 5e3
    elif max_value < 1e5:
        step = 10e3
    elif max_value < 5e5:
        step = 50e3
    elif max_value < 1e6:
        step = 100e3
    elif max_value < 5e6:
        step = 1e6
    elif max_value < 10e6:
        step = 5e6
    elif max_value < 50e6:
        step = 10e6
    elif max_value < 100e6:
        step = 25e6
    elif max_value < 250e6:
        step = 50e6
    elif max_value < 500e6:
        step = 100e6
    elif max_value < 1e9:
        step = 250e6
    elif max_value < 5e9:
        step = 500e6
    elif max_value < 10e9:
        step = 1e9
    elif max_value < 50e9:
        step = 2e9
    elif max_value < 100e9:
        step = 10e9
    else:
        step = 25e9

    rounded_max = math.ceil(max_value / step) * step
    tickvals = np.arange(0, rounded_max + 1, step)
    ticktext = [formatter(val) for val in tickvals]

    # Layout-Einstellungen für Export-Graph
    export_fig.update_layout(
        title="Jährlicher Exportverlauf ausgewählter Waren",
        xaxis_title="Jahr",
        yaxis_title="Wert in €",
        xaxis=dict(tickmode="array", tickvals=sorted(df_filtered['Jahr'].unique())),
        yaxis=dict(tickvals=tickvals, ticktext=ticktext),
        legend=dict(title="Waren", bgcolor="rgba(255,255,255,0.7)")
    )

    # Layout-Einstellungen für Import-Graph
    import_fig.update_layout(
        title="Jährlicher Importverlauf ausgewählter Waren",
        xaxis_title="Jahr",
        yaxis_title="Wert in €",
        xaxis=dict(tickmode="array", tickvals=sorted(df_filtered['Jahr'].unique())),
        yaxis=dict(tickvals=tickvals, ticktext=ticktext),
        legend=dict(title="Waren", bgcolor="rgba(255,255,255,0.7)")
    )

    # Infotext für Summen
    total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
    total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9

    info_text = (f"Für die ausgewählten Waren beträgt der gesamte Exportwert {total_export:.0f} Mrd € und "
                 f"der gesamte Importwert {total_import:.0f} Mrd € von 2008 bis 2024.")

    return export_fig, import_fig, info_text

if __name__ == '__main__':
    app.run(debug=True)
