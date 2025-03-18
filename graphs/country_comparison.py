from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go

# Daten laden
df_grouped = pd.read_csv('data/df_grouped.csv')

# Einzigartige Länder alphabetisch sortieren
länder_options = sorted(df_grouped['Land'].unique())

def create_layout():
    return html.Div([
        html.H1("Deutschlands Handelsbeziehungen mit anderen Ländern (im Vergleich)"),

        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': land, 'value': land} for land in länder_options],
            value=['Islamische Republik Iran', 'Irak', 'Katar'],  # Standardauswahl
            multi=True,  # Mehrfachauswahl ermöglichen
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div([
            dcc.Graph(id='export_graph'),
            dcc.Graph(id='import_graph'),
            dcc.Graph(id='handelsvolumen_graph')
        ])
    ])

def register_callbacks(app):
    @app.callback(
        [Output('export_graph', 'figure'),
         Output('import_graph', 'figure'),
         Output('handelsvolumen_graph', 'figure')],
        Input('land_dropdown', 'value')
    )
    def update_graph(selected_countries):
        # Farben für die Linien
        farben = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        export_fig = go.Figure()
        import_fig = go.Figure()
        handelsvolumen_fig = go.Figure()

        # Gehe durch jedes ausgewählte Land
        for i, country in enumerate(selected_countries):
            df_country = df_grouped[(df_grouped['Land'] == country) &
                                    (df_grouped['Jahr'] >= 2008) &
                                    (df_grouped['Jahr'] <= 2024)]

            export_fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country['export_wert'],
                mode='lines+markers',
                name=country,
                line=dict(width=2, color=farben[i % len(farben)]),
                hovertemplate=f'<b>Exportvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

            import_fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country['import_wert'],
                mode='lines+markers',
                name=country,
                line=dict(width=2, color=farben[i % len(farben)]),
                hovertemplate=f'<b>Importvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

            handelsvolumen_fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country['handelsvolumen_wert'],
                mode='lines+markers',
                name=country,
                line=dict(width=2, color=farben[i % len(farben)]),
                hovertemplate=f'<b>Gesamthandelsvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        return export_fig, import_fig, handelsvolumen_fig
