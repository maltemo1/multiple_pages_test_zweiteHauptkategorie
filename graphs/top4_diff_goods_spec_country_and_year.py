import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/top10_goods_spec_country_and_year.csv")

# Daten laden
df = pd.read_csv(csv_path)

# Werte mit 1000 multiplizieren, um die Originalwerte zu erhalten
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)

# Funktion zur Formatierung der Achsenbeschriftungen
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

# Funktion zur Erstellung des Layouts
def create_layout():
    return html.Div([
        html.H1("Handelsdifferenzen nach Warengruppe für ein ausgewähltes Land und Jahr"),

        dcc.Dropdown(
            id='top4_diff_goods_country_year_dropdown_country',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].unique())],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='top4_diff_goods_country_year_dropdown_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Graph(id='top4_diff_goods_country_year_export_graph'),
        dcc.Graph(id='top4_diff_goods_country_year_import_graph'),
    ])

# Callback für das Update der Graphen
def register_callbacks(app):
    @app.callback(
        [dash.Output('top4_diff_goods_country_year_export_graph', 'figure'),
         dash.Output('top4_diff_goods_country_year_import_graph', 'figure')],
        [dash.Input('top4_diff_goods_country_year_dropdown_country', 'value'),
         dash.Input('top4_diff_goods_country_year_dropdown_year', 'value')]
    )
    def update_graphs(selected_country, selected_year):
        # Daten filtern für das ausgewählte Jahr und Land
        df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
        df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        # Handelsdifferenzen berechnen
        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
        df_diff['export_differenz'] = df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']
        df_diff['import_differenz'] = df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']

        # Top-4 und Bottom-4 Veränderungen berechnen
        top_4_export_diff = df_diff.nlargest(4, 'export_differenz')
        bottom_4_export_diff = df_diff.nsmallest(4, 'export_differenz')

        top_4_import_diff = df_diff.nlargest(4, 'import_differenz')
        bottom_4_import_diff = df_diff.nsmallest(4, 'import_differenz')

        # Achsengrenzen berechnen
        export_diff_min = min(bottom_4_export_diff['export_differenz'].min(), 0)
        export_diff_max = max(top_4_export_diff['export_differenz'].max(), 0)
        import_diff_min = min(bottom_4_import_diff['import_differenz'].min(), 0)
        import_diff_max = max(top_4_import_diff['import_differenz'].max(), 0)

        # Schrittgrößen bestimmen
        export_step = determine_step_size(max(abs(export_diff_min), abs(export_diff_max)))
        import_step = determine_step_size(max(abs(import_diff_min), abs(import_diff_max)))

        # Achsen-Ticks generieren
        export_ticks = np.arange(math.floor(export_diff_min / export_step) * export_step,
                                 math.ceil(export_diff_max / export_step) * export_step + export_step, export_step)

        import_ticks = np.arange(math.floor(import_diff_min / import_step) * import_step,
                                 math.ceil(import_diff_max / import_step) * import_step + import_step, import_step)

        # Export-Differenzen-Graph
        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(y=top_4_export_diff['Label'], x=top_4_export_diff['export_differenz'], 
                                    orientation='h', marker_color='green', name='Top 4 Export'))
        export_fig.add_trace(go.Bar(y=bottom_4_export_diff['Label'], x=bottom_4_export_diff['export_differenz'], 
                                    orientation='h', marker_color='red', name='Bottom 4 Export'))
        export_fig.update_layout(
            title=f'Exportdifferenzen ({selected_country}, {selected_year})',
            xaxis=dict(tickvals=export_ticks, ticktext=[formatter(val) for val in export_ticks])
        )

        # Import-Differenzen-Graph
        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(y=top_4_import_diff['Label'], x=top_4_import_diff['import_differenz'], 
                                    orientation='h', marker_color='green', name='Top 4 Import'))
        import_fig.add_trace(go.Bar(y=bottom_4_import_diff['Label'], x=bottom_4_import_diff['import_differenz'], 
                                    orientation='h', marker_color='red', name='Bottom 4 Import'))
        import_fig.update_layout(
            title=f'Importdifferenzen ({selected_country}, {selected_year})',
            xaxis=dict(tickvals=import_ticks, ticktext=[formatter(val) for val in import_ticks])
        )

        return export_fig, import_fig
