from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# Sicherstellen, dass der richtige Dateipfad verwendet wird
csv_path = os.path.join(os.path.dirname(__file__), '../data/aggregated_df.csv')
aggregated_df = pd.read_csv(csv_path)

# Funktion zum Formatieren der x-Achse (Euro-Werte)
def formatter(value):
    if value >= 1e9:
        return f'{int(value * 1e-9)} Mrd'  # Ganze Zahl für Milliarden
    elif value >= 1e6:
        return f'{int(value * 1e-6)} Mio'  # Ganze Zahl für Millionen
    elif value >= 1e3:
        return f'{int(value * 1e-3)} K'  # Ganze Zahl für Tausend
    else:
        return f'{int(value)}'

# Layout-Funktion für das Dash-Modul
def create_layout():
    return html.Div([
        html.H1("Top 10 Export- und Importprodukte nach Jahr"),
        dcc.Dropdown(
            id='jahr_dropdown_top_10_trade_goods',
            options=[{'label': str(j), 'value': j} for j in sorted(aggregated_df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Graph(id='export_graph_top_10_trade_goods'),
        dcc.Graph(id='import_graph_top_10_trade_goods'),
    ])

# Callback-Funktion registrieren
def register_callbacks(app):
    @app.callback(
        [Output('export_graph_top_10_trade_goods', 'figure'),
         Output('import_graph_top_10_trade_goods', 'figure')],
        Input('jahr_dropdown_top_10_trade_goods', 'value')
    )
    def update_graphs(selected_year):
        filtered_df = aggregated_df[aggregated_df['Jahr'] == selected_year]
        aggregated_year_df = filtered_df.groupby(['Jahr', 'Code', 'Label'], as_index=False).agg(
            {'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'}
        )

        aggregated_year_df['Handelsvolumen'] = aggregated_year_df['Ausfuhr: Wert'] + aggregated_year_df['Einfuhr: Wert']
        top_10_exports = aggregated_year_df.sort_values(by='Ausfuhr: Wert', ascending=False).head(10)
        top_10_imports = aggregated_year_df.sort_values(by='Einfuhr: Wert', ascending=False).head(10)

        # Maximalen Wert für die Achse bestimmen
        max_export = top_10_exports['Ausfuhr: Wert'].max()
        max_import = top_10_imports['Einfuhr: Wert'].max()
        max_value = max(max_export, max_import)

        # Tick-Werte in 20-Mrd-Schritten
        tick_max = np.ceil(max_value / 2e10) * 2e10  # Aufrunden auf 20 Mrd
        tick_vals = np.arange(0, tick_max + 1, 2e10)  # Schrittweite 20 Mrd

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
            title=f"Top 10 Exportprodukte im Jahr {selected_year}",
            xaxis_title="Exportwert (Euro)",
            yaxis_title="Warenkategorie",
            xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=[formatter(val) for val in tick_vals]),
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
            title=f"Top 10 Importprodukte im Jahr {selected_year}",
            xaxis_title="Importwert (Euro)",
            yaxis_title="Warenkategorie",
            xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=[formatter(val) for val in tick_vals]),
        )

        return export_fig, import_fig
