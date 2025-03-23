from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# Sicherstellen, dass der richtige Dateipfad verwendet wird
csv_path = os.path.join(os.path.dirname(__file__), '../data/top10_goods_spec_country_and_year.csv')
df = pd.read_csv(csv_path)

# Einzigartige Länder und Jahre alphabetisch bzw. numerisch sortieren
länder_options = sorted(df['Land'].unique())
jahre_options = sorted(df['Jahr'].unique())

# Funktion zur Formatierung der x-Achsen-Werte
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.1f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.1f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.1f} K'
    else:
        return f'{int(value)}'

# Funktion zur Berechnung der Schrittweite der Achse
def calculate_tick_step(max_value):
    if max_value < 5e6:
        step = 1e6
    elif max_value < 10e6:
        step = 2e6
    elif max_value < 50e6:
        step = 5e6
    elif max_value < 100e6:
        step = 10e6
    elif max_value < 250e6:
        step = 20e6
    elif max_value < 500e6:
        step = 50e6
    elif max_value < 1e9:
        step = 100e6
    elif max_value < 5e9:
        step = 200e6
    elif max_value < 10e9:
        step = 500e6
    elif max_value < 50e9:
        step = 5e9
    elif max_value < 100e9:
        step = 10e9
    elif max_value < 250e9:
        step = 20e9
    else:
        step = 50e9
    return step

# Layout-Funktion für das Dash-Modul
def create_layout():
    return html.Div([
        html.H1("Top 10 Handelswaren zwischen Deutschland und einem ausgewählten Land in einem bestimmten Jahr"),

        dcc.Dropdown(
            id='land_dropdown_top10_goods_year',
            options=[{'label': land, 'value': land} for land in länder_options],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%', 'margin-bottom': '10px'}
        ),

        dcc.Dropdown(
            id='jahr_dropdown_top10_goods_year',
            options=[{'label': jahr, 'value': jahr} for jahr in jahre_options],
            value=2024,
            clearable=False,
            style={'width': '50%', 'margin-bottom': '20px'}
        ),

        dcc.Graph(id='export_graph_top10_goods_year'),
        dcc.Graph(id='import_graph_top10_goods_year'),
    ])

# Callback-Funktion registrieren
def register_callbacks(app):
    @app.callback(
        [Output('export_graph_top10_goods_year', 'figure'),
         Output('import_graph_top10_goods_year', 'figure')],
        [Input('land_dropdown_top10_goods_year', 'value'),
         Input('jahr_dropdown_top10_goods_year', 'value')]
    )
    def update_graphs(selected_country, selected_year):
        filtered_df = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)]
        aggregated_country_df = filtered_df.groupby(['Label'], as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        top_10_exports = aggregated_country_df.sort_values(by='Ausfuhr: Wert', ascending=False).head(10)
        max_export = top_10_exports['Ausfuhr: Wert'].max()
        export_step = calculate_tick_step(max_export)
        rounded_export_max = np.ceil(max_export / export_step) * export_step
        export_tick_vals = np.arange(0, rounded_export_max + 1, export_step)

        top_10_imports = aggregated_country_df.sort_values(by='Einfuhr: Wert', ascending=False).head(10)
        max_import = top_10_imports['Einfuhr: Wert'].max()
        import_step = calculate_tick_step(max_import)
        rounded_import_max = np.ceil(max_import / import_step) * import_step
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
            title=f"Top 10 Exportprodukte aus Deutschland nach {selected_country} ({selected_year})",
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
            title=f"Top 10 Importprodukte aus {selected_country} nach Deutschland ({selected_year})",
            xaxis_title="Importwert (Euro)",
            yaxis_title="Warenkategorie",
            xaxis=dict(tickmode='array', tickvals=import_tick_vals, ticktext=[formatter(val) for val in import_tick_vals]),
        )

        return export_fig, import_fig
