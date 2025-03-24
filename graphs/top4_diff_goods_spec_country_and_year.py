from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import os

# CSV-Datei einlesen
csv_path = os.path.join(os.path.dirname(__file__), '../data/top10_goods_spec_country_and_year.csv')
df = pd.read_csv(csv_path)

# Werte umwandeln (Tausender in Originalwerte)
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0) * 1000

# Layout der Seite
def create_layout():
    return html.Div([
        html.H1("Top 4 Waren nach Differenz zum Vorjahr"),
        dcc.Dropdown(
            id='land_dropdown_top10_goods_year',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].unique())],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Dropdown(
            id='jahr_dropdown_top10_goods_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
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
        df_current = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)]
        df_previous = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year - 1)]

        if df_current.empty or df_previous.empty:
            return (
                go.Figure(layout={"title": f"Keine Daten für {selected_year}"}),
                go.Figure(layout={"title": f"Keine Daten für {selected_year}"})
            )

        df_current = df_current.groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})
        df_previous = df_previous.groupby('Label', as_index=False).agg({'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'})

        df_diff = pd.merge(df_current, df_previous, on="Label", suffixes=('_current', '_previous'), how='outer').fillna(0)
        df_diff['export_differenz'] = df_diff['Ausfuhr: Wert_current'] - df_diff['Ausfuhr: Wert_previous']
        df_diff['import_differenz'] = df_diff['Einfuhr: Wert_current'] - df_diff['Einfuhr: Wert_previous']

        # Top & Bottom 4 für Export
        top_4_export_diff = df_diff.nlargest(4, 'export_differenz')
        bottom_4_export_diff = df_diff.nsmallest(4, 'export_differenz')

        # Top & Bottom 4 für Import
        top_4_import_diff = df_diff.nlargest(4, 'import_differenz')
        bottom_4_import_diff = df_diff.nsmallest(4, 'import_differenz')

        # Export-Diagramm
        export_fig = go.Figure([
            go.Bar(y=top_4_export_diff['Label'], x=top_4_export_diff['export_differenz'], orientation='h', name='Top 4 Zuwächse', marker_color='green'),
            go.Bar(y=bottom_4_export_diff['Label'], x=bottom_4_export_diff['export_differenz'], orientation='h', name='Top 4 Rückgänge', marker_color='red')
        ])
        export_fig.update_layout(title=f'Exportdifferenzen ({selected_country}, {selected_year} vs. {selected_year - 1})')

        # Import-Diagramm
        import_fig = go.Figure([
            go.Bar(y=top_4_import_diff['Label'], x=top_4_import_diff['import_differenz'], orientation='h', name='Top 4 Zuwächse', marker_color='green'),
            go.Bar(y=bottom_4_import_diff['Label'], x=bottom_4_import_diff['import_differenz'], orientation='h', name='Top 4 Rückgänge', marker_color='red')
        ])
        import_fig.update_layout(title=f'Importdifferenzen ({selected_country}, {selected_year} vs. {selected_year - 1})')

        return export_fig, import_fig
