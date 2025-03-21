from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Load data (Ensure the correct path!)
df_grouped = pd.read_csv('data/df_grouped.csv')

# Unique sorted country list
länder_options = sorted(df_grouped['Land'].unique())

# Define layout function
def create_layout():
    return html.Div([
        html.H1("Platzierung im Export- und Importranking Deutschlands (2008-2024)"),
        dcc.Dropdown(
            id='land_dropdown_ranking',
            options=[{'label': land, 'value': land} for land in länder_options],
            value='Islamische Republik Iran',  # Default value
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Graph(id='ranking_graph'),
    ])

# Register callback function
def register_callbacks(app):
    @app.callback(
        Output('ranking_graph', 'figure'),
        Input('land_dropdown_ranking', 'value')
    )
    def update_ranking_graph(selected_country):
        df_country = df_grouped[(df_grouped['Land'] == selected_country) &
                                (df_grouped['Jahr'] >= 2008) &
                                (df_grouped['Jahr'] <= 2024)]

        #df_country['export_ranking'] = df_country['export_ranking'].astype(int)
        #df_country['import_ranking'] = df_country['import_ranking'].astype(int)
        #df_country['handelsvolumen_ranking'] = df_country['handelsvolumen_ranking'].astype(int)

        df_country.loc[:, 'export_ranking'] = df_country['export_ranking'].astype(int)
        df_country.loc[:, 'import_ranking'] = df_country['import_ranking'].astype(int)
        df_country.loc[:, 'handelsvolumen_ranking'] = df_country['handelsvolumen_ranking'].astype(int)


        fig = go.Figure()

        for col, name, color in zip(
            ['export_ranking', 'import_ranking', 'handelsvolumen_ranking'],
            ['Export-Ranking', 'Import-Ranking', 'Handelsvolumen-Ranking'],
            ['#1f77b4', '#2ca02c', '#ff7f0e']
        ):
            fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Platzierung: %{{y}}<extra></extra>'
            ))

        min_ranking = df_country[['export_ranking', 'import_ranking', 'handelsvolumen_ranking']].min().min()
        max_ranking = df_country[['export_ranking', 'import_ranking', 'handelsvolumen_ranking']].max().max()

        step_size = max(1, (max_ranking - min_ranking) // 10)
        tickvals = np.arange(min_ranking, max_ranking + step_size, step_size)

        fig.update_layout(
            title=f'Platzierung von {selected_country} im Export- und Importranking (2008-2024)',
            xaxis_title='Jahr',
            yaxis_title='Ranking (niedriger = besser)',
            yaxis=dict(
                tickvals=tickvals,
                range=[max_ranking + 2, min_ranking - 2],
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        return fig
