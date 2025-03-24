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

# Funktion zur Bestimmung der optimalen Schrittgröße
def determine_step_size(max_value):
    thresholds = [10, 50, 100, 500, 1000, 5000, 10000, 50000]
    steps = [1, 5, 10, 50, 100, 500, 1000, 5000]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 10000

# Funktion zur Erstellung des Layouts
def create_layout():
    return html.Div([
        html.H1("Top 4 Waren nach Export- und Importwachstum"),
        
        dcc.Dropdown(
            id='top4_growth_goods_country_year_dropdown_country',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].unique())],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='top4_growth_goods_country_year_dropdown_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Graph(id='top4_growth_goods_country_year_export_graph'),
        dcc.Graph(id='top4_growth_goods_country_year_import_graph'),
    ])

# Callback für das Update der Graphen
def register_callbacks(app):
    @app.callback(
        [dash.Output('top4_growth_goods_country_year_export_graph', 'figure'),
         dash.Output('top4_growth_goods_country_year_import_graph', 'figure')],
        [dash.Input('top4_growth_goods_country_year_dropdown_country', 'value'),
         dash.Input('top4_growth_goods_country_year_dropdown_year', 'value')]
    )
    def update_graphs(selected_country, selected_year):
        # Daten filtern für das ausgewählte Jahr und das Vorjahr
        df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
        df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)].groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        # Prozentuales Wachstum berechnen
        df_growth = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
        df_growth['export_wachstum'] = ((df_growth['Ausfuhr: Wert_current'] - df_growth['Ausfuhr: Wert_previous']) / df_growth['Ausfuhr: Wert_previous'].replace(0, np.nan)) * 100
        df_growth['import_wachstum'] = ((df_growth['Einfuhr: Wert_current'] - df_growth['Einfuhr: Wert_previous']) / df_growth['Einfuhr: Wert_previous'].replace(0, np.nan)) * 100
        df_growth = df_growth.dropna()

        # Top-4 und Bottom-4 Wachstum berechnen
        top_4_export = df_growth.nlargest(4, 'export_wachstum')
        bottom_4_export = df_growth.nsmallest(4, 'export_wachstum')

        top_4_import = df_growth.nlargest(4, 'import_wachstum')
        bottom_4_import = df_growth.nsmallest(4, 'import_wachstum')

        # Achsengrenzen berechnen
        export_min = min(bottom_4_export['export_wachstum'].min(), 0)
        export_max = max(top_4_export['export_wachstum'].max(), 0)
        import_min = min(bottom_4_import['import_wachstum'].min(), 0)
        import_max = max(top_4_import['import_wachstum'].max(), 0)

        # Schrittgrößen bestimmen
        export_step = determine_step_size(max(abs(export_min), abs(export_max)))
        import_step = determine_step_size(max(abs(import_min), abs(import_max)))

        # Achsen-Ticks generieren
        export_ticks = np.arange(math.floor(export_min / export_step) * export_step,
                                 math.ceil(export_max / export_step) * export_step + export_step, export_step)

        import_ticks = np.arange(math.floor(import_min / import_step) * import_step,
                                 math.ceil(import_max / import_step) * import_step + import_step, import_step)

        # Export-Wachstums-Graph
        export_fig = go.Figure()
        export_fig.add_trace(go.Bar(
            y=top_4_export['Label'],
            x=top_4_export['export_wachstum'], 
            orientation='h', 
            marker_color='green', 
            name='Top 4 Zuwächse',
            hovertemplate='Wachstum: %{x:.1f}%<extra></extra>'
        ))
        export_fig.add_trace(go.Bar(
            y=bottom_4_export['Label'],
            x=bottom_4_export['export_wachstum'], 
            orientation='h', 
            marker_color='red', 
            name='Top 4 Rückgänge',
            hovertemplate='Rückgang: %{x:.1f}%<extra></extra>'
        ))
        export_fig.update_layout(
            title=f'Exportwachstum nach Warengruppe ({selected_country}, {selected_year} vs. {selected_year - 1})',
            xaxis_title='Exportwachstum (%)',
            xaxis=dict(tickvals=export_ticks),
            yaxis_title='Warengruppe'
        )

        # Import-Wachstums-Graph
        import_fig = go.Figure()
        import_fig.add_trace(go.Bar(
            y=top_4_import['Label'],
            x=top_4_import['import_wachstum'], 
            orientation='h', 
            marker_color='green', 
            name='Top 4 Zuwächse',
            hovertemplate='Wachstum: %{x:.1f}%<extra></extra>'
        ))
        import_fig.add_trace(go.Bar(
            y=bottom_4_import['Label'],
            x=bottom_4_import['import_wachstum'], 
            orientation='h', 
            marker_color='red', 
            name='Top 4 Rückgänge',
            hovertemplate='Rückgang: %{x:.1f}%<extra></extra>'
        ))
        import_fig.update_layout(
            title=f'Importwachstum nach Warengruppe ({selected_country}, {selected_year} vs. {selected_year - 1})',
            xaxis_title='Importwachstum (%)',
            xaxis=dict(tickvals=import_ticks),
            yaxis_title='Warengruppe'
        )

        return export_fig, import_fig
