from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math
import os

# Sicherstellen, dass der richtige Dateipfad verwendet wird
csv_path = os.path.join(os.path.dirname(__file__), '../data/top10_goods_spec_country.csv')
top10_goods_spec_country = pd.read_csv(csv_path)

# Einzigartige Länder alphabetisch sortieren
länder_options = sorted(top10_goods_spec_country['Land'].unique())

# Formatierungsfunktion für Achsenbeschriftung
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.1f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.1f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.1f} K'
    else:
        return f'{int(value)}'

# Berechnung der Tick-Schritte für Achsen
def calculate_tick_step(max_value):
    if max_value < 5e6:
        return 1e6
    elif max_value < 10e6:
        return 2e6
    elif max_value < 50e6:
        return 5e6
    elif max_value < 100e6:
        return 10e6
    elif max_value < 250e6:
        return 20e6
    elif max_value < 500e6:
        return 50e6
    elif max_value < 1e9:
        return 100e6
    elif max_value < 5e9:
        return 200e6
    elif max_value < 10e9:
        return 500e6
    elif max_value < 50e9:
        return 5e9
    elif max_value < 100e9:
        return 10e9
    elif max_value < 250e9:
        return 20e9
    else:
        return 50e9

# Layout-Funktion für das Dash-Modul
def create_layout():
    return html.Div([
        html.H1("Top 10 Handelswaren zwischen Deutschland und einem ausgewählten Land (2008-2024)"),
        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': land, 'value': land} for land in länder_options],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Graph(id='export_graph'),
        dcc.Graph(id='import_graph'),
    ])

# Callback-Funktion für die Graphen-Updates
def register_callbacks(app):
    @app.callback(
        [Output('export_graph', 'figure'),
         Output('import_graph', 'figure')],
        Input('land_dropdown', 'value')
    )
    def update_graphs(selected_country):
        filtered_df = top10_goods_spec_country[top10_goods_spec_country['Land'] == selected_country]
        aggregated_country_df = filtered_df.groupby(['Code', 'Label'], as_index=False).agg(
            {'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'}
        )

        top_10_exports = aggregated_country_df.sort_values(by='Ausfuhr: Wert', ascending=False).head(10)
        max_export = top_10_exports['Ausfuhr: Wert'].max()
        export_step = calculate_tick_step(max_export)
        rounded_export_max = math.ceil(max_export / export_step) * export_step
        export_tick_vals = np.arange(0, rounded_export_max + 1, export_step)

        top_10_imports = aggregated_country_df.sort_values(by='Einfuhr: Wert', ascending=False).head(10)
        max_import = top_10_imports['Einfuhr: Wert'].max()
        import_step = calculate_tick_step(max_import)
        rounded_import_max = math.ceil(max_import / import_step) * import_step
        import_tick_vals = np.arange(0, rounded_import_max + 1, import_step)

        # Export-Plot
        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(
            x=top_10_exports['Ausfuhr: Wert'],
            y=top_10_exports['Label'],
            orientation='h',
            marker_color='blue',
            hovertemplate='Exportwert: %{x:,.0f} €<extra></extra>'
        ))
        export_fig.update_layout(
            title=f"Top 10 Exportprodukte aus Deutschland nach {selected_country} (2008-2024)",
            xaxis_title="Exportwert (Euro)",
            yaxis_title="Warenkategorie",
            xaxis=dict(tickmode='array', tickvals=export_tick_vals, ticktext=[formatter(val) for val in export_tick_vals]),
        )

        # Import-Plot
        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(
            x=top_10_imports['Einfuhr: Wert'],
            y=top_10_imports['Label'],
            orientation='h',
            marker_color='red',
            hovertemplate='Importwert: %{x:,.0f} €<extra></extra>'
        ))
        import_fig.update_layout(
            title=f"Top 10 Importprodukte aus {selected_country} nach Deutschland (2008-2024)",
            xaxis_title="Importwert (Euro)",
            yaxis_title="Warenkategorie",
            xaxis=dict(tickmode='array', tickvals=import_tick_vals, ticktext=[formatter(val) for val in import_tick_vals]),
        )

        return export_fig, import_fig
