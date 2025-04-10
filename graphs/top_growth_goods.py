from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go

# Daten einlesen
df_reduced = pd.read_csv('data/df_reduced.csv')

# Layout-Funktion für das Graph-Modul
def create_layout():
    return html.Div([
        html.H1("Waren mit größtem Handelswachstum bzw. -rückgang für Deutschland zum Vorjahr"),
        
        # Dropdown-Menü für Jahrsauswahl
        dcc.Dropdown(
            id='jahr_dropdown_growth_goods',
            options=[{'label': str(j), 'value': j} for j in sorted(df_reduced['Jahr'].unique())],
            value=2024,  # Standardjahr
            clearable=False,
            style={'width': '50%'}
        ),

        # Graphen für relative Export- und Import-Differenzen
        dcc.Graph(id='export_rel_diff_graph'),
        dcc.Graph(id='import_rel_diff_graph'),
    ])

# Callback-Funktion registrieren
def register_callbacks(app):
    @app.callback(
        [Output('export_rel_diff_graph', 'figure'),
         Output('import_rel_diff_graph', 'figure')],
        Input('jahr_dropdown_growth_goods', 'value')
    )
    def update_graphs(selected_year):
        df_current = df_reduced[df_reduced['Jahr'] == selected_year]
        df_previous = df_reduced[df_reduced['Jahr'] == selected_year - 1]

        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'))

        # Berechnung der relativen Veränderungen in Prozent
        df_diff['export_rel_diff'] = (df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']) / df_diff['Ausfuhr: Wert_previous'] * 100
        df_diff['import_rel_diff'] = (df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']) / df_diff['Einfuhr: Wert_previous'] * 100

        # Top & Bottom 4 relative Export-Differenzen
        top_4_export_rel_diff = df_diff.nlargest(4, 'export_rel_diff')
        bottom_4_export_rel_diff = df_diff.nsmallest(4, 'export_rel_diff')
        export_rel_min = min(bottom_4_export_rel_diff['export_rel_diff'].min(), 0)
        export_rel_max = max(top_4_export_rel_diff['export_rel_diff'].max(), 0)

        # Top & Bottom 4 relative Import-Differenzen
        top_4_import_rel_diff = df_diff.nlargest(4, 'import_rel_diff')
        bottom_4_import_rel_diff = df_diff.nsmallest(4, 'import_rel_diff')
        import_rel_min = min(bottom_4_import_rel_diff['import_rel_diff'].min(), 0)
        import_rel_max = max(top_4_import_rel_diff['import_rel_diff'].max(), 0)

        # Graph für relative Export-Differenzen
        export_fig = go.Figure()

        export_fig.add_trace(go.Bar(
            y=top_4_export_rel_diff['Label'],
            x=top_4_export_rel_diff['export_rel_diff'],
            orientation='h',
            name='Top 4 Zuwächse',
            marker_color='green',
            hovertemplate='Relative Exportveränderung: %{x:.1f}%<extra></extra>'
        ))

        export_fig.add_trace(go.Bar(
            y=bottom_4_export_rel_diff['Label'],
            x=bottom_4_export_rel_diff['export_rel_diff'],
            orientation='h',
            name='Top 4 Rückgänge',
            marker_color='red',
            hovertemplate='Relative Exportrückgang: %{x:.1f}%<extra></extra>'
        ))

        export_fig.update_layout(
            title=f'Relative Exportdifferenzen nach Warengruppe ({selected_year} vs. {selected_year - 1})',
            xaxis_title='Veränderung in %',
            xaxis=dict(tickformat=".1f", tickmode='auto'),
            yaxis_title='Warengruppe',
            xaxis_range=[export_rel_min * 1.2, export_rel_max * 1.2],
        )

        # Graph für relative Import-Differenzen
        import_fig = go.Figure()

        import_fig.add_trace(go.Bar(
            y=top_4_import_rel_diff['Label'],
            x=top_4_import_rel_diff['import_rel_diff'],
            orientation='h',
            name='Top 4 Zuwächse',
            marker_color='green',
            hovertemplate='Relative Importveränderung: %{x:.1f}%<extra></extra>'
        ))

        import_fig.add_trace(go.Bar(
            y=bottom_4_import_rel_diff['Label'],
            x=bottom_4_import_rel_diff['import_rel_diff'],
            orientation='h',
            name='Top 4 Rückgänge',
            marker_color='red',
            hovertemplate='Relative Importrückgang: %{x:.1f}%<extra></extra>'
        ))

        import_fig.update_layout(
            title=f'Relative Importdifferenzen nach Warengruppe ({selected_year} vs. {selected_year - 1})',
            xaxis_title='Veränderung in %',
            xaxis=dict(tickformat=".1f", tickmode='auto'),
            yaxis_title='Warengruppe',
            xaxis_range=[import_rel_min * 1.2, import_rel_max * 1.2],
        )

        return export_fig, import_fig
