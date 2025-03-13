from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go

# Daten laden
df_grouped = pd.read_csv('data/df_grouped.csv')

# Layout-Funktion für das Dashboard
def create_layout():
    return html.Div([
        html.H1("Handelswachstum nach Jahr"),
        
        # Dropdown-Menü für Jahrsauswahl
        dcc.Dropdown(
            id='jahr_dropdown_wachstum',
            options=[{'label': str(j), 'value': j} for j in sorted(df_grouped['Jahr'].unique())],
            value=2024,  # Standardjahr
            clearable=False,
            style={'width': '50%'}
        ),
        
        # Graphen für Export-, Import- und Handelsvolumen-Wachstum
        dcc.Graph(id='export_wachstum_graph'),
        dcc.Graph(id='import_wachstum_graph'),
        dcc.Graph(id='handelsvolumen_wachstum_graph'),
    ])

# Callbacks registrieren
def register_callbacks(app):
    @app.callback(
        [Output('export_wachstum_graph', 'figure'),
         Output('import_wachstum_graph', 'figure'),
         Output('handelsvolumen_wachstum_graph', 'figure')],
        Input('jahr_dropdown_wachstum', 'value')
    )
    def update_graphs(year_selected):
        # Filtern der relevanten Länder
        df_filtered = df_grouped[(df_grouped['Jahr'] == year_selected) & 
                                 ((df_grouped['export_wert'] >= 100_000_000) | 
                                  (df_grouped['import_wert'] >= 100_000_000))]
        df_filtered = df_filtered[~df_filtered['Land'].isin(['Nicht ermittelte Länder und Gebiete', 'Schiffs- und Luftfahrzeugbedarf'])]

        # 1. Export-Wachstum: Top 4 & Bottom 4
        top_4_export = df_filtered.nlargest(4, 'export_wachstum')
        bottom_4_export = df_filtered.nsmallest(4, 'export_wachstum')
        export_min = min(bottom_4_export['export_wachstum'].min(), 0)
        export_max = max(top_4_export['export_wachstum'].max(), 0)

        # 2. Import-Wachstum: Top 4 & Bottom 4
        top_4_import = df_filtered.nlargest(4, 'import_wachstum')
        bottom_4_import = df_filtered.nsmallest(4, 'import_wachstum')
        import_min = min(bottom_4_import['import_wachstum'].min(), 0)
        import_max = max(top_4_import['import_wachstum'].max(), 0)

        # 3. Handelsvolumen-Wachstum: Top 4 & Bottom 4
        top_4_handelsvolumen = df_filtered.nlargest(4, 'handelsvolumen_wachstum')
        bottom_4_handelsvolumen = df_filtered.nsmallest(4, 'handelsvolumen_wachstum')
        handelsvolumen_min = min(bottom_4_handelsvolumen['handelsvolumen_wachstum'].min(), 0)
        handelsvolumen_max = max(top_4_handelsvolumen['handelsvolumen_wachstum'].max(), 0)

        # Funktion zum Erstellen der Graphen
        def create_bar_chart(top_df, bottom_df, x_col, title, x_min, x_max):
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=top_df['Land'],
                x=top_df[x_col],
                orientation='h',
                name='Top 4 Wachstum',
                marker_color='green',
                hovertemplate='Wachstum: %{x:.2f}%<extra></extra>'
            ))
            fig.add_trace(go.Bar(
                y=bottom_df['Land'],
                x=bottom_df[x_col],
                orientation='h',
                name='Top 4 Negativwachstum',
                marker_color='red',
                hovertemplate='Rückgang: %{x:.2f}%<extra></extra>'
            ))
            fig.update_layout(
                title=f'{title} für {year_selected}',
                xaxis_title='Wachstumsrate (%)',
                yaxis_title='Land',
                xaxis=dict(range=[x_min * 1.5, x_max * 1.1]),
                barmode='relative',
            )
            return fig

        return (
            create_bar_chart(top_4_export, bottom_4_export, 'export_wachstum', 'Exportwachstum', export_min, export_max),
            create_bar_chart(top_4_import, bottom_4_import, 'import_wachstum', 'Importwachstum', import_min, import_max),
            create_bar_chart(top_4_handelsvolumen, bottom_4_handelsvolumen, 'handelsvolumen_wachstum', 'Handelsvolumenwachstum', handelsvolumen_min, handelsvolumen_max),
        )
