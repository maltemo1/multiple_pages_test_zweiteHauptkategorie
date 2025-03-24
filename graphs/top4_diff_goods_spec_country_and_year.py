import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math




# Sicherstellen, dass der richtige Dateipfad verwendet wird
csv_path = os.path.join(os.path.dirname(__file__), '../data/top10_goods_spec_country_and_year.csv')
df = pd.read_csv(csv_path)

# Werte mal 1000 multiplizieren, um zu Originalwerten zu gelangen
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)

# Einzigartige Länder und Jahre alphabetisch bzw. numerisch sortieren
länder_options = sorted(df['Land'].unique())
jahre_options = sorted(df['Jahr'].unique())


# Funktion zum Formatieren der x-Achse
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
    thresholds = [1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9, 5e9, 10e9, 50e9]
    steps = [100000, 500000, 1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9, 5e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 10e9

# Layout für das Dashboard (damit es in die Haupt-App integriert werden kann)
layout = html.Div([
    html.H1("Handelsdifferenzen nach Warengruppe für ein ausgewähltes Land und Jahr"),

    dcc.Dropdown(
        id='country_dropdown',
        options=[{'label': country, 'value': country} for country in sorted(df['Land'].unique())],
        value='Islamische Republik Iran',
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Dropdown(
        id='year_dropdown',
        options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
        value=2024,
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='export_diff_graph'),
    dcc.Graph(id='import_diff_graph'),
])

# Callback für das Update der Graphen
def register_callbacks(app):
    @app.callback(
        [dash.Output('export_diff_graph', 'figure'),
         dash.Output('import_diff_graph', 'figure')],
        [dash.Input('country_dropdown', 'value'),
         dash.Input('year_dropdown', 'value')]
    )
    def update_graphs(selected_country, selected_year):
        df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
        df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
        df_diff['export_differenz'] = df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']
        df_diff['import_differenz'] = df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']

        top_4_export_diff = df_diff.nlargest(4, 'export_differenz')
        bottom_4_export_diff = df_diff.nsmallest(4, 'export_differenz')

        top_4_import_diff = df_diff.nlargest(4, 'import_differenz')
        bottom_4_import_diff = df_diff.nsmallest(4, 'import_differenz')

        export_diff_min = min(bottom_4_export_diff['export_differenz'].min(), 0)
        export_diff_max = max(top_4_export_diff['export_differenz'].max(), 0)
        import_diff_min = min(bottom_4_import_diff['import_differenz'].min(), 0)
        import_diff_max = max(top_4_import_diff['import_differenz'].max(), 0)

        export_step = determine_step_size(max(abs(export_diff_min), abs(export_diff_max)))
        import_step = determine_step_size(max(abs(import_diff_min), abs(import_diff_max)))

        export_ticks = np.arange(math.floor(export_diff_min / export_step) * export_step,
                                 math.ceil(export_diff_max / export_step) * export_step + export_step, export_step)

        import_ticks = np.arange(math.floor(import_diff_min / import_step) * import_step,
                                 math.ceil(import_diff_max / import_step) * import_step + import_step, import_step)

        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(y=top_4_export_diff['Label'], x=top_4_export_diff['export_differenz'], orientation='h', marker_color='green'))
        export_fig.add_trace(go.Bar(y=bottom_4_export_diff['Label'], x=bottom_4_export_diff['export_differenz'], orientation='h', marker_color='red'))
        export_fig.update_layout(title=f'Exportdifferenzen ({selected_country}, {selected_year})',
                                 xaxis=dict(tickvals=export_ticks, ticktext=[formatter(val) for val in export_ticks]))

        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(y=top_4_import_diff['Label'], x=top_4_import_diff['import_differenz'], orientation='h', marker_color='green'))
        import_fig.add_trace(go.Bar(y=bottom_4_import_diff['Label'], x=bottom_4_import_diff['import_differenz'], orientation='h', marker_color='red'))
        import_fig.update_layout(title=f'Importdifferenzen ({selected_country}, {selected_year})',
                                 xaxis=dict(tickvals=import_ticks, ticktext=[formatter(val) for val in import_ticks]))

        return export_fig, import_fig
