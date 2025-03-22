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
df = pd.read_csv("/content/drive/MyDrive/DIIHK/Data/Render_Data_Sets/top10_goods_spec_country_and_year.csv")

# Werte mal 1000 multiplizieren, um von Tausender-Werte zu den Originalwerten zu gelangen
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)



# Funktion zum Formatieren der x-Achse (Tsd, Mio, Mrd)
def formatter(value):
    if abs(value) >= 1e9:
        return f'{value / 1e9:.2f} Mrd'
    elif abs(value) >= 1e6:
        return f'{value / 1e6:.1f} Mio'
    elif abs(value) >= 1e3:
        return f'{value / 1e3:.0f} Tsd'
    else:
        return f'{int(value)}'


# Funktion zur Bestimmung der optimalen Schrittgröße
def determine_step_size(max_value):
    if max_value < 1e6:
        return 100000
    elif max_value < 5e6:
        return 500000
    elif max_value < 10e6:
        return 1e6
    elif max_value < 50e6:
        return 5e6
    elif max_value < 100e6:
        return 10e6
    elif max_value < 500e6:
        return 50e6
    elif max_value < 1e9:
        return 100e6
    elif max_value < 5e9:
        return 500e6
    elif max_value < 10e9:
        return 1e9
    elif max_value < 50e9:
        return 5e9
    else:
        return 10e9

# Dash-App erstellen
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Handelsdifferenzen nach Warengruppe für ein ausgewähltes Land und Jahr"),

    # Dropdown für Landesauswahl
    dcc.Dropdown(
        id='country_dropdown',
        options=[{'label': country, 'value': country} for country in sorted(df['Land'].unique())],
        value='Islamische Republik Iran',  # Standardland
        clearable=False,
        style={'width': '50%'}
    ),

    # Dropdown für Jahresauswahl
    dcc.Dropdown(
        id='year_dropdown',
        options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
        value=2024,  # Standardjahr
        clearable=False,
        style={'width': '50%'}
    ),

    # Balkendiagramme für Export- und Importdifferenzen
    dcc.Graph(id='export_diff_graph'),
    dcc.Graph(id='import_diff_graph'),
])

@app.callback(
    [dash.Output('export_diff_graph', 'figure'),
     dash.Output('import_diff_graph', 'figure')],
    [dash.Input('country_dropdown', 'value'),
     dash.Input('year_dropdown', 'value')]
)
def update_graphs(selected_country, selected_year):
    # Daten für das ausgewählte Land und Jahr filtern
    df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
    df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

    # Daten zusammenführen, um Differenzen zu berechnen
    df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
    df_diff['export_differenz'] = df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']
    df_diff['import_differenz'] = df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']

    # Top & Bottom 4 Export-Differenzen
    top_4_export_diff = df_diff.nlargest(4, 'export_differenz')
    bottom_4_export_diff = df_diff.nsmallest(4, 'export_differenz')
    export_diff_min = min(bottom_4_export_diff['export_differenz'].min(), 0)
    export_diff_max = max(top_4_export_diff['export_differenz'].max(), 0)

    # Top & Bottom 4 Import-Differenzen
    top_4_import_diff = df_diff.nlargest(4, 'import_differenz')
    bottom_4_import_diff = df_diff.nsmallest(4, 'import_differenz')
    import_diff_min = min(bottom_4_import_diff['import_differenz'].min(), 0)
    import_diff_max = max(top_4_import_diff['import_differenz'].max(), 0)

    # Schrittgrößen für Export und Import bestimmen
    export_max_value = max(abs(export_diff_min), abs(export_diff_max))
    import_max_value = max(abs(import_diff_min), abs(import_diff_max))

    export_step = determine_step_size(export_max_value)
    import_step = determine_step_size(import_max_value)

    # Generiere die X-Achsen-Ticks (Schrittgröße auf Basis der maximalen Werte)
    export_ticks = np.arange(math.floor(export_diff_min / export_step) * export_step,
                             math.ceil(export_diff_max / export_step) * export_step + export_step, export_step)

    import_ticks = np.arange(math.floor(import_diff_min / import_step) * import_step,
                             math.ceil(import_diff_max / import_step) * import_step + import_step, import_step)

    # Graph für Exportdifferenzen
    export_fig = go.Figure()

    export_fig.add_trace(go.Bar(
        y=top_4_export_diff['Label'],
        x=top_4_export_diff['export_differenz'],
        orientation='h',
        name='Top 4 Zuwächse',
        marker_color='green',
        hovertemplate='Exportzuwachs: %{x:,.0f} €<extra></extra>'
    ))

    export_fig.add_trace(go.Bar(
        y=bottom_4_export_diff['Label'],
        x=bottom_4_export_diff['export_differenz'],
        orientation='h',
        name='Top 4 Rückgänge',
        marker_color='red',
        hovertemplate='Exportrückgang: %{x:,.0f} €<extra></extra>'
    ))

    export_fig.update_layout(
        title=f'Exportdifferenzen nach Warengruppe ({selected_country}, {selected_year} vs. {selected_year - 1})',
        xaxis_title='Exportdifferenz (EUR)',
        xaxis=dict(tickmode='array', tickvals=export_ticks, ticktext=[formatter(val) for val in export_ticks]),
        yaxis_title='Warengruppe',
        xaxis_range=[export_diff_min * 1.1, export_diff_max * 1.3],
    )

    # Graph für Importdifferenzen
    import_fig = go.Figure()

    import_fig.add_trace(go.Bar(
        y=top_4_import_diff['Label'],
        x=top_4_import_diff['import_differenz'],
        orientation='h',
        name='Top 4 Zuwächse',
        marker_color='green',
        hovertemplate='Importzuwachs: %{x:,.0f} €<extra></extra>'
    ))

    import_fig.add_trace(go.Bar(
        y=bottom_4_import_diff['Label'],
        x=bottom_4_import_diff['import_differenz'],
        orientation='h',
        name='Top 4 Rückgänge',
        marker_color='red',
        hovertemplate='Importrückgang: %{x:,.0f} €<extra></extra>'
    ))

    import_fig.update_layout(
        title=f'Importdifferenzen nach Warengruppe ({selected_country}, {selected_year} vs. {selected_year - 1})',
        xaxis_title='Importdifferenz (EUR)',
        xaxis=dict(tickmode='array', tickvals=import_ticks, ticktext=[formatter(val) for val in import_ticks]),
        yaxis_title='Warengruppe',
        xaxis_range=[import_diff_min * 1.1, import_diff_max * 1.3],
    )

    return export_fig, import_fig

if __name__ == '__main__':
    app.run(debug=True)
