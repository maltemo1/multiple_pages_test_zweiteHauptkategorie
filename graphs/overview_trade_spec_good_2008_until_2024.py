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
df = pd.read_csv('/content/drive/MyDrive/DIIHK/Data/Render_Data_Sets/aggregated_df.csv')

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
    html.H1("Jährlicher Export- und Importverlauf einer Ware mit Deutschland"),

    dcc.Dropdown(
        id='ware_dropdown',
        options=[{'label': str(w), 'value': w} for w in sorted(df_yearly['Label'].unique())],
        value='Mineralische Brennstoffe usw.',
        clearable=False,
        style={'width': '50%'}
    ),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='jahresverlauf_graph'),
])

@app.callback(
    [Output('jahresverlauf_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('ware_dropdown', 'value')]
)
def update_graph(selected_label):
    df_filtered = df_yearly[df_yearly['Label'] == selected_label]

    if df_filtered.empty:
        return go.Figure(), f"Keine Daten für {selected_label} verfügbar."

    fig = go.Figure()

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

    max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()

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

    fig.update_layout(
        title=f'Deutschlands jährlicher Export- und Importverlauf von {selected_label}',
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

    total_export = df_filtered['Ausfuhr: Wert'].sum() / 1e9
    total_import = df_filtered['Einfuhr: Wert'].sum() / 1e9

    info_text = (f"Für {selected_label} zwischen Deutschland und der Welt beträgt "
                 f"der gesamte Exportwert {total_export:.0f} Mrd € und "
                 f"der gesamte Importwert {total_import:.0f} Mrd € von 2008 bis 2024.")

    return fig, info_text

if __name__ == '__main__':
    app.run(debug=True)
