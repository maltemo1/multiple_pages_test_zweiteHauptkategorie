from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math
import os

# Daten laden (Pfad für Render anpassen)
data_path = os.path.join("data", "df_grouped.csv")
df_grouped = pd.read_csv(data_path)

# Funktion zum Formatieren der x-Achse (Mrd)
def formatter(x, pos):
    return f'{int(x * 1e-9)} Mrd' if abs(x) >= 1e9 else f'{int(x)}'

# Funktion zum Berechnen der Achsen-Ticks (nur Mrd)
def generate_ticks(min_value, max_value, step_size):
    min_tick = math.floor(min_value / step_size) * step_size
    max_tick = math.ceil(max_value / step_size) * step_size
    return np.arange(min_tick, max_tick + step_size, step_size)

# Layout für das Diagramm
def create_layout():
    return html.Div([
        html.H1("Länder mit größten Handelsdifferenzen pro Jahr"),

        # Dropdown-Menü für Jahrsauswahl
        dcc.Dropdown(
            id='jahr_dropdown_2',
            options=[{'label': str(j), 'value': j} for j in sorted(df_grouped['Jahr'].unique())],
            value=2024,  # Standardwert
            clearable=False,
            style={'width': '50%'}
        ),

        # Graphen für Export-, Import- und Handelsvolumen-Differenzen
        dcc.Graph(id='export_diff_graph'),
        dcc.Graph(id='import_diff_graph'),
        dcc.Graph(id='handelsvolumen_diff_graph'),
    ])

# Callbacks registrieren
def register_callbacks(app):
    @app.callback(
        [Output('export_diff_graph', 'figure'),
         Output('import_diff_graph', 'figure'),
         Output('handelsvolumen_diff_graph', 'figure')],
        Input('jahr_dropdown_2', 'value')
    )
    def update_graphs(year_selected):
        df_filtered = df_grouped[df_grouped['Jahr'] == year_selected]
        df_filtered = df_filtered[~df_filtered['Land'].isin(['Nicht ermittelte Länder und Gebiete', 'Schiffs- und Luftfahrzeugbedarf'])]

        # Export-Differenzen: Top 4 und Bottom 4
        top_4_export_diff = df_filtered.nlargest(4, 'export_differenz')
        bottom_4_export_diff = df_filtered.nsmallest(4, 'export_differenz')
        export_diff_min = min(bottom_4_export_diff['export_differenz'].min(), 0)
        export_diff_max = max(top_4_export_diff['export_differenz'].max(), 0)

        # Import-Differenzen: Top 4 und Bottom 4
        top_4_import_diff = df_filtered.nlargest(4, 'import_differenz')
        bottom_4_import_diff = df_filtered.nsmallest(4, 'import_differenz')
        import_diff_min = min(bottom_4_import_diff['import_differenz'].min(), 0)
        import_diff_max = max(top_4_import_diff['import_differenz'].max(), 0)

        # Handelsvolumen-Differenzen: Top 4 und Bottom 4
        top_4_handelsvolumen_diff = df_filtered.nlargest(4, 'handelsvolumen_differenz')
        bottom_4_handelsvolumen_diff = df_filtered.nsmallest(4, 'handelsvolumen_differenz')
        handelsvolumen_diff_min = min(bottom_4_handelsvolumen_diff['handelsvolumen_differenz'].min(), 0)
        handelsvolumen_diff_max = max(top_4_handelsvolumen_diff['handelsvolumen_differenz'].max(), 0)

        # Achsen-Ticks berechnen
        step_size = 1e9  # Schrittwert immer 1 Mrd
        export_ticks = generate_ticks(export_diff_min, export_diff_max, step_size)
        import_ticks = generate_ticks(import_diff_min, import_diff_max, step_size)
        handelsvolumen_ticks = generate_ticks(handelsvolumen_diff_min, handelsvolumen_diff_max, step_size)

        # Diagramm: Exportdifferenzen
        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(
            y=top_4_export_diff['Land'],
            x=top_4_export_diff['export_differenz'],
            orientation='h',
            name='Top 4 Zuwächse',
            marker_color='green',
            hovertemplate='Höhe des Exportzuwachses: %{x:,.0f} €<extra></extra>'
        ))
        export_fig.add_trace(go.Bar(
            y=bottom_4_export_diff['Land'],
            x=bottom_4_export_diff['export_differenz'],
            orientation='h',
            name='Top 4 Rückgänge',
            marker_color='red',
            hovertemplate='Höhe des Exportrückgangs: %{x:,.0f} €<extra></extra>'
        ))
        export_fig.update_layout(
            title=f'Exportdifferenzen für {year_selected}',
            xaxis=dict(tickmode='array', tickvals=export_ticks, ticktext=[formatter(val, 0) for val in export_ticks])
        )

        # Diagramm: Importdifferenzen
        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(
            y=top_4_import_diff['Land'],
            x=top_4_import_diff['import_differenz'],
            orientation='h',
            name='Top 4 Zuwächse',
            marker_color='green',
            hovertemplate='Höhe des Importzuwachses: %{x:,.0f} €<extra></extra>'
        ))
        import_fig.add_trace(go.Bar(
            y=bottom_4_import_diff['Land'],
            x=bottom_4_import_diff['import_differenz'],
            orientation='h',
            name='Top 4 Rückgänge',
            marker_color='red',
            hovertemplate='Höhe des Importrückgangs: %{x:,.0f} €<extra></extra>'
        ))
        import_fig.update_layout(
            title=f'Importdifferenzen für {year_selected}',
            xaxis=dict(tickmode='array', tickvals=import_ticks, ticktext=[formatter(val, 0) for val in import_ticks])
        )

        # Diagramm: Handelsvolumendifferenzen
        handelsvolumen_fig = go.Figure()
        handelsvolumen_fig.add_trace(go.Bar(
            y=top_4_handelsvolumen_diff['Land'],
            x=top_4_handelsvolumen_diff['handelsvolumen_differenz'],
            orientation='h',
            name='Top 4 Zuwächse',
            marker_color='green',
            hovertemplate='Höhe des Handelszuwachses: %{x:,.0f} €<extra></extra>'
        ))
        handelsvolumen_fig.add_trace(go.Bar(
            y=bottom_4_handelsvolumen_diff['Land'],
            x=bottom_4_handelsvolumen_diff['handelsvolumen_differenz'],
            orientation='h',
            name='Top 4 Rückgänge',
            marker_color='red',
            hovertemplate='Höhe des Handelsrückgangs: %{x:,.0f} €<extra></extra>'
        ))
        handelsvolumen_fig.update_layout(
            title=f'Handelsvolumendifferenzen für {year_selected}',
            xaxis=dict(tickmode='array', tickvals=handelsvolumen_ticks, ticktext=[formatter(val, 0) for val in handelsvolumen_ticks])
        )

        return export_fig, import_fig, handelsvolumen_fig
