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

# Daten laden
df = pd.read_csv("data/top10_goods_spec_country_and_year.csv")

# Werte in Originalskala konvertieren
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)

# Dash-App erstellen
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Top 4 Waren nach Export- und Importwachstum"),

    # Dropdown-Menü für Land & Jahr
    dcc.Dropdown(
        id='land_dropdown',
        options=[{'label': land, 'value': land} for land in sorted(df['Land'].unique())],
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

    # Graphen für Export- und Importwachstum
    dcc.Graph(id='export_growth_graph'),
    dcc.Graph(id='import_growth_graph'),
])

@app.callback(
    [Output('export_growth_graph', 'figure'),
     Output('import_growth_graph', 'figure')],
    [Input('land_dropdown', 'value'),
     Input('jahr_dropdown', 'value')]
)
def update_graphs(selected_country, selected_year):
    df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)]
    df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)]

    df_current = df_current.groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
    df_previous = df_previous.groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

    df_growth = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous')).fillna(0)
    df_growth['export_wachstum'] = ((df_growth['Ausfuhr: Wert_current'] - df_growth['Ausfuhr: Wert_previous']) / df_growth['Ausfuhr: Wert_previous'].replace(0, float('nan'))) * 100
    df_growth['import_wachstum'] = ((df_growth['Einfuhr: Wert_current'] - df_growth['Einfuhr: Wert_previous']) / df_growth['Einfuhr: Wert_previous'].replace(0, float('nan'))) * 100
    df_growth = df_growth.dropna()

    # Top & Bottom 4 für Export und Import
    top_4_export = df_growth.nlargest(4, 'export_wachstum')
    bottom_4_export = df_growth.nsmallest(4, 'export_wachstum')
    top_4_import = df_growth.nlargest(4, 'import_wachstum')
    bottom_4_import = df_growth.nsmallest(4, 'import_wachstum')

    max_abs_export = max(abs(top_4_export['export_wachstum'].max()), abs(bottom_4_export['export_wachstum'].min()))
    max_abs_import = max(abs(top_4_import['import_wachstum'].max()), abs(bottom_4_import['import_wachstum'].min()))

    # Export-Wachstums-Graph
    export_fig = go.Figure()
    export_fig.add_trace(go.Bar(
        y=top_4_export['Label'],
        x=top_4_export['export_wachstum'],
        orientation='h',
        name='Top 4 Zuwächse',
        marker_color='green',
        hovertemplate='Wachstum: %{x:.1f}%<extra></extra>'
    ))
    export_fig.add_trace(go.Bar(
        y=bottom_4_export['Label'],
        x=bottom_4_export['export_wachstum'],
        orientation='h',
        name='Top 4 Rückgänge',
        marker_color='red',
        hovertemplate='Rückgang: %{x:.1f}%<extra></extra>'
    ))
    export_fig.update_layout(
        title=f'Exportwachstum ({selected_country}, {selected_year} vs. {selected_year - 1})',
        xaxis_title='Wachstum in %',
        xaxis=dict(range=[-max_abs_export * 1.2, max_abs_export * 1.2]),
        yaxis_title='Warengruppe'
    )

    # Import-Wachstums-Graph
    import_fig = go.Figure()
    import_fig.add_trace(go.Bar(
        y=top_4_import['Label'],
        x=top_4_import['import_wachstum'],
        orientation='h',
        name='Top 4 Zuwächse',
        marker_color='green',
        hovertemplate='Wachstum: %{x:.1f}%<extra></extra>'
    ))
    import_fig.add_trace(go.Bar(
        y=bottom_4_import['Label'],
        x=bottom_4_import['import_wachstum'],
        orientation='h',
        name='Top 4 Rückgänge',
        marker_color='red',
        hovertemplate='Rückgang: %{x:.1f}%<extra></extra>'
    ))
    import_fig.update_layout(
        title=f'Importwachstum ({selected_country}, {selected_year} vs. {selected_year - 1})',
        xaxis_title='Wachstum in %',
        xaxis=dict(range=[-max_abs_import * 1.2, max_abs_import * 1.2]),
        yaxis_title='Warengruppe'
    )

    return export_fig, import_fig

if __name__ == '__main__':
    app.run(debug=True)
