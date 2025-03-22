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


# CSV-Dateien einlesen
df = pd.read_csv('/content/drive/MyDrive/DIIHK/Data/Render_Data_Sets/trade_spec_country_and_year.csv')
df_grouped = pd.read_csv('/content/drive/MyDrive/DIIHK/Data/Render_Data_Sets/df_grouped.csv')

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
    html.H1("Monatlicher Handelsverlauf Deutschlands mit ausgewähltem Land"),

    dcc.Dropdown(
        id='land_dropdown',
        options=[{'label': str(l), 'value': l} for l in sorted(df['Land'].unique())],
        value='Islamische Republik Iran',
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Dropdown(
        id='jahr_dropdown',
        options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
        value=2024,
        clearable=False,
        style={'width': '50%'}
    ),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='monatlicher_handel_graph'),
])

@app.callback(
    [Output('monatlicher_handel_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('land_dropdown', 'value'),
     Input('jahr_dropdown', 'value')]
)
def update_graph(country, year_selected):
    df_country_monthly = df[(df['Land'] == country) & (df['Jahr'] == year_selected)]

    fig = go.Figure()

    for col, name, color in zip(
        ['export_wert', 'import_wert', 'handelsvolumen_wert'],
        ['Exportvolumen', 'Importvolumen', 'Gesamthandelsvolumen'],
        ['#1f77b4', '#ff7f0e', '#2ca02c']
    ):
        fig.add_trace(go.Scatter(
            x=df_country_monthly['Monat'],
            y=df_country_monthly[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    max_value = df_country_monthly[['export_wert', 'import_wert', 'handelsvolumen_wert']].values.max()

    if max_value < 5e6:
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
        title=f'Monatlicher Export-, Import- und Handelsverlauf Deutschlands mit {country} im Jahr {year_selected}',
        xaxis_title='Monat',
        yaxis_title='Wert in €',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        ),
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    df_selected = df_grouped[(df_grouped['Land'] == country) & (df_grouped['Jahr'] == year_selected)]

    if not df_selected.empty:
        status = df_selected['handelsbilanz_status'].values[0]
        handelsbilanz = df_selected['handelsbilanz'].values[0] / 1e9
        export_ranking = int(df_selected['export_ranking'].values[0])
        import_ranking = int(df_selected['import_ranking'].values[0])
        handelsvolumen_ranking = int(df_selected['handelsvolumen_ranking'].values[0])

        info_text = (f"{country}: Deutschland weist ein Handelsbilanz-{status} im Wert von {handelsbilanz:.2f} Mrd € "
                     f"mit diesem Land im Jahr {year_selected} auf.\n"
                     f"Unter allen deutschen Handelspartnern belegt {country} im Jahr {year_selected} den {export_ranking}. Platz "
                     f"gemessen am Exportvolumen, den {import_ranking}. Platz gemessen am Importvolumen "
                     f"und den {handelsvolumen_ranking}. Platz gemessen am gesamten Handelsvolumen.")
    else:
        info_text = f"Keine Daten für {country} im Jahr {year_selected} verfügbar."

    return fig, info_text

if __name__ == '__main__':
    app.run(debug=True)
