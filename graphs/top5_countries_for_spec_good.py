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
df = pd.read_csv('data/top10_goods_spec_country_and_year.csv')

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

# Dash-App erstellen
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Top 5 Handelspartner für eine ausgewählte Ware"),

    dcc.Dropdown(
        id='waren_dropdown',
        options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].unique())],
        value='Mineralische Brennstoffe usw.',
        multi=False,
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='export_graph'),
    dcc.Graph(id='import_graph'),
])

@app.callback(
    [Output('export_graph', 'figure'),
     Output('import_graph', 'figure')],
    [Input('waren_dropdown', 'value')]
)
def update_graphs(selected_label):
    df_filtered = df[df['Label'] == selected_label]

    if df_filtered.empty:
        return go.Figure(), go.Figure()

    # Aggregation nach Jahr und Land für Export und Import
    export_agg = df_filtered.groupby(['Jahr', 'Land'], as_index=False).agg({'Ausfuhr: Wert': 'sum'})
    import_agg = df_filtered.groupby(['Jahr', 'Land'], as_index=False).agg({'Einfuhr: Wert': 'sum'})

    # Gesamtwerte pro Jahr berechnen
    export_total_per_year = export_agg.groupby('Jahr')['Ausfuhr: Wert'].sum()
    import_total_per_year = import_agg.groupby('Jahr')['Einfuhr: Wert'].sum()

    # Top 5 Exportländer
    top5_exports = export_agg.groupby('Land')['Ausfuhr: Wert'].sum().nlargest(5).index
    top5_export_df = export_agg[export_agg['Land'].isin(top5_exports)]
    top5_export_df['Prozentanteil'] = top5_export_df.apply(
        lambda row: round((row['Ausfuhr: Wert'] / export_total_per_year[row['Jahr']]) * 100, 2), axis=1
    )

    # Top 5 Importländer
    top5_imports = import_agg.groupby('Land')['Einfuhr: Wert'].sum().nlargest(5).index
    top5_import_df = import_agg[import_agg['Land'].isin(top5_imports)]
    top5_import_df['Prozentanteil'] = top5_import_df.apply(
        lambda row: round((row['Einfuhr: Wert'] / import_total_per_year[row['Jahr']]) * 100, 2), axis=1
    )

    # Max-Werte für Y-Achsen-Skalierung getrennt berechnen
    max_export = top5_export_df['Ausfuhr: Wert'].max()
    max_import = top5_import_df['Einfuhr: Wert'].max()

    fig_export = go.Figure()
    fig_import = go.Figure()

    for country in top5_exports:
        df_country = top5_export_df[top5_export_df['Land'] == country]

        fig_export.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['Ausfuhr: Wert'],
            mode='lines+markers',
            name=f"{country} - Export",
            line=dict(width=2),
            marker=dict(symbol='circle', size=8),
            hovertemplate=(
                f'<b>{country} - {selected_label}</b><br>'
                'Jahr: %{x}<br>'
                'Wert: %{y:,.0f} €<br>'
                'Anteil: %{customdata} %<extra></extra>'
            ),
            customdata=df_country['Prozentanteil']
        ))

    for country in top5_imports:
        df_country = top5_import_df[top5_import_df['Land'] == country]

        fig_import.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['Einfuhr: Wert'],
            mode='lines+markers',
            name=f"{country} - Import",
            line=dict(width=2),
            marker=dict(symbol='x', size=8),
            hovertemplate=(
                f'<b>{country} - {selected_label}</b><br>'
                'Jahr: %{x}<br>'
                'Wert: %{y:,.0f} €<br>'
                'Anteil: %{customdata} %<extra></extra>'
            ),
            customdata=df_country['Prozentanteil']
        ))

    # Dynamische Schrittgröße für Y-Achse
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

    tickvals_export = np.arange(0, math.ceil(max_export / step_export) * step_export + 1, step_export)
    tickvals_import = np.arange(0, math.ceil(max_import / step_import) * step_import + 1, step_import)

    fig_export.update_layout(
        title='Top 5 Exportdestinationen Deutschlands',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=tickvals_export, ticktext=[formatter(val) for val in tickvals_export]),
        legend=dict(title='Exportländer', bgcolor='rgba(255,255,255,0.7)')
    )

    fig_import.update_layout(
        title='Top 5 Importländer Deutschlands',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=tickvals_import, ticktext=[formatter(val) for val in tickvals_import]),
        legend=dict(title='Importländer', bgcolor='rgba(255,255,255,0.7)')
    )

    return fig_export, fig_import

if __name__ == '__main__':
    app.run(debug=True)
