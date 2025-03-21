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
#import dash_core_components as dcc
#import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import math
import gdown
import os

# Daten laden
df_grouped = pd.read_csv('/content/drive/MyDrive/DIIHK/Data/Render_Data_Sets/df_grouped.csv')

# Einzigartige Länder alphabetisch sortieren
länder_options = sorted(df_grouped['Land'].unique())

# Dash-App erstellen
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Deutschlands Export- und Importwachstum mit anderen Ländern"),

    dcc.Dropdown(
        id='land_dropdown_growth',
        options=[{'label': land, 'value': land} for land in länder_options],
        value='Islamische Republik Iran',  # Standardwert
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='wachstums_graph'),
])

@app.callback(
    Output('wachstums_graph', 'figure'),
    Input('land_dropdown_growth', 'value')
)
def update_graph(selected_country):
    df_country = df_grouped[(df_grouped['Land'] == selected_country) &
                            (df_grouped['Jahr'] >= 2008) &
                            (df_grouped['Jahr'] <= 2024)]

    fig = go.Figure()

    for col, name, color in zip(
        ['export_wachstum', 'import_wachstum'],
        ['Exportwachstum', 'Importwachstum'],
        ['#1f77b4', '#ff7f0e']
    ):
        fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Wachstum: %{{y:.2f}} %<extra></extra>'
        ))

    # Maximale & Minimale Werte bestimmen
    max_value = df_country[['export_wachstum', 'import_wachstum']].max().max()
    min_value = df_country[['export_wachstum', 'import_wachstum']].min().min()

    # **Neue Logik für eine bessere Y-Achsen-Skalierung**

    # 1. Finde den größten absoluten Wert für symmetrische Achsen
    abs_max = max(abs(max_value), abs(min_value))

    # 2. Runde den Maximalwert auf die nächste sinnvolle Zehnerpotenz auf
    exponent = math.floor(math.log10(abs_max))  # Finde Zehnerpotenz
    base_step = 10 ** exponent  # Basisschrittweite

    # Falls der Maximalwert nicht sauber in die Basisschrittweite passt, erhöhe sie
    if abs_max / base_step > 5:
        base_step *= 2
    elif abs_max / base_step > 2:
        base_step *= 1.5

    # 3. Setze den neuen maximalen Wert als Vielfaches des Schrittwertes
    new_max = math.ceil(abs_max / base_step) * base_step
    new_min = -new_max  # Symmetrisch zur positiven Achse

    # 4. Erstelle Tick-Werte von 0 ausgehend
    tickvals = np.arange(new_min, new_max + base_step, base_step)

    # Achsen und Layout
    fig.update_layout(
        title=f'Export- und Importwachstum zwischen Deutschland und {selected_country} (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wachstum (%)',
        yaxis=dict(
            tickvals=tickvals,
            range=[new_min, new_max]  # Setzt die symmetrische Skala
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)

