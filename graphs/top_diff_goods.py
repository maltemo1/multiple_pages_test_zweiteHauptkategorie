from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math

# CSV-Datei einlesen
df_reduced = pd.read_csv('data/df_reduced.csv')

# Funktion zum Formatieren der x-Achse
def formatter(value):
    if abs(value) >= 1e9:
        return f'{int(value * 1e-9)} Mrd'
    elif abs(value) >= 1e6:
        return f'{int(value * 1e-6)} Mio'
    elif abs(value) >= 1e3:
        return f'{int(value * 1e-3)} Tsd'
    else:
        return f'{int(value)}'

# Layout-Funktion für das Dash-Layout
def create_layout():
    return html.Div([
        html.H1("Waren mit größten Handelsdifferenzen für Deutschland zum Vorjahr"),
        dcc.Dropdown(
            id='jahr_dropdown_goods',
            options=[{'label': str(j), 'value': j} for j in sorted(df_reduced['Jahr'].unique())],
            value=2024,  
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Graph(id='export_diff_graph_goods'),
        dcc.Graph(id='import_diff_graph_goods'),
    ])

# Callback-Funktion zur Aktualisierung der Diagramme
def register_callbacks(app):
    @app.callback(
        [Output('export_diff_graph_goods', 'figure'),
         Output('import_diff_graph_goods', 'figure')],
        Input('jahr_dropdown_goods', 'value')
    )
    def update_graphs(selected_year):
        df_current = df_reduced[df_reduced['Jahr'] == selected_year]
        df_previous = df_reduced[df_reduced['Jahr'] == selected_year - 1]
        
        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'))
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

        # Achsenticks generieren
        step_size = 2e9
        export_ticks = np.arange(math.floor(export_diff_min / step_size) * step_size,
                                math.ceil(export_diff_max / step_size) * step_size + step_size, step_size)

        import_ticks = np.arange(math.floor(import_diff_min / step_size) * step_size,
                                math.ceil(import_diff_max / step_size) * step_size + step_size, step_size)

        # Export-Diagramm
        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(
            y=top_4_export_diff['Label'], x=top_4_export_diff['export_differenz'],
            orientation='h', name='Top 4 Zuwächse', marker_color='green',
            hovertemplate='Exportzuwachs: %{x:,.0f} €<extra></extra>'
        ))
        export_fig.add_trace(go.Bar(
            y=bottom_4_export_diff['Label'], x=bottom_4_export_diff['export_differenz'],
            orientation='h', name='Top 4 Rückgänge', marker_color='red',
            hovertemplate='Exportrückgang: %{x:,.0f} €<extra></extra>'
        ))
        export_fig.update_layout(
            title=f'Exportdifferenzen nach Warengruppe ({selected_year} vs. {selected_year - 1})',
            xaxis_title='Exportdifferenz (EUR)',
            xaxis=dict(tickmode='array', tickvals=export_ticks, ticktext=[formatter(val) for val in export_ticks]),
            yaxis_title='Warengruppe',
            xaxis_range=[export_diff_min * 1.1, export_diff_max * 1.3],
        )

        # Import-Diagramm
        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(
            y=top_4_import_diff['Label'], x=top_4_import_diff['import_differenz'],
            orientation='h', name='Top 4 Zuwächse', marker_color='green',
            hovertemplate='Importzuwachs: %{x:,.0f} €<extra></extra>'
        ))
        import_fig.add_trace(go.Bar(
            y=bottom_4_import_diff['Label'], x=bottom_4_import_diff['import_differenz'],
            orientation='h', name='Top 4 Rückgänge', marker_color='red',
            hovertemplate='Importrückgang: %{x:,.0f} €<extra></extra>'
        ))
        import_fig.update_layout(
            title=f'Importdifferenzen nach Warengruppe ({selected_year} vs. {selected_year - 1})',
            xaxis_title='Importdifferenz (EUR)',
            xaxis=dict(tickmode='array', tickvals=import_ticks, ticktext=[formatter(val) for val in import_ticks]),
            yaxis_title='Warengruppe',
            xaxis_range=[import_diff_min * 1.1, import_diff_max * 1.3],
        )

        return export_fig, import_fig
