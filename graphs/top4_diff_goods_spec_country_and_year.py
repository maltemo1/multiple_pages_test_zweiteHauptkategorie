import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Daten laden
df = pd.read_csv('data/top10_goods_spec_country_and_year.csv')

# Werte umwandeln (von Tausendern in Originalwerte)
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = (df[['Ausfuhr: Wert', 'Einfuhr: Wert']] * 1000).astype(int)

# Funktion zur Skalierung der x-Achse (Tsd, Mio, Mrd)
def formatter(value):
    if abs(value) >= 1e9:
        return f'{value / 1e9:.2f} Mrd'
    elif abs(value) >= 1e6:
        return f'{value / 1e6:.1f} Mio'
    elif abs(value) >= 1e3:
        return f'{value / 1e3:.0f} Tsd'
    else:
        return f'{int(value)}'

# Funktion zur Bestimmung der Schrittgröße
def determine_step_size(max_value):
    thresholds = [1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9, 5e9, 10e9, 50e9]
    steps = [100000, 500000, 1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9, 5e9, 10e9]
    for threshold, step in zip(thresholds, steps):
        if max_value < threshold:
            return step
    return 10e9

# Layout für das Dash-Dashboard
def create_layout():
    return html.Div([
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

# Callback-Funktion für Dash
def register_callbacks(app):
    @app.callback(
        [Output('export_diff_graph', 'figure'),
         Output('import_diff_graph', 'figure')],
        [Input('country_dropdown', 'value'),
         Input('year_dropdown', 'value')]
    )
    def update_graphs(selected_country, selected_year):
        df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
        df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
        df_diff['export_differenz'] = df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']
        df_diff['import_differenz'] = df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']

        # Top & Bottom 4 für Export
        top_4_export_diff = df_diff.nlargest(4, 'export_differenz')
        bottom_4_export_diff = df_diff.nsmallest(4, 'export_differenz')
        export_diff_min = min(bottom_4_export_diff['export_differenz'].min(), 0)
        export_diff_max = max(top_4_export_diff['export_differenz'].max(), 0)

        # Top & Bottom 4 für Import
        top_4_import_diff = df_diff.nlargest(4, 'import_differenz')
        bottom_4_import_diff = df_diff.nsmallest(4, 'import_differenz')
        import_diff_min = min(bottom_4_import_diff['import_differenz'].min(), 0)
        import_diff_max = max(top_4_import_diff['import_differenz'].max(), 0)

        # Schrittgrößen bestimmen
        export_step = determine_step_size(max(abs(export_diff_min), abs(export_diff_max)))
        import_step = determine_step_size(max(abs(import_diff_min), abs(import_diff_max)))

        export_ticks = np.arange(math.floor(export_diff_min / export_step) * export_step,
                                 math.ceil(export_diff_max / export_step) * export_step + export_step, export_step)

        import_ticks = np.arange(math.floor(import_diff_min / import_step) * import_step,
                                 math.ceil(import_diff_max / import_step) * import_step + import_step, import_step)

        # Export-Diagramm
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
            xaxis=dict(tickvals=export_ticks, ticktext=[formatter(val) for val in export_ticks]),
            yaxis_title='Warengruppe'
        )

        # Import-Diagramm
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
            xaxis=dict(tickvals=import_ticks, ticktext=[formatter(val) for val in import_ticks]),
            yaxis_title='Warengruppe'
        )

        return export_fig, import_fig
