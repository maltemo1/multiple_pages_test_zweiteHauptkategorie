from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import math
import os



# Daten laden
df_grouped = pd.read_csv('data/df_grouped.csv')

# ✅ Unique country options sorted alphabetically
länder_options = sorted(df_grouped['Land'].unique())

# ✅ Create Layout function (REQUIRED for multi-page app)
def create_layout():
    return html.Div([
        html.H1("Deutschlands Export- und Importwachstum mit anderen Ländern"),

        dcc.Dropdown(
            id='land_dropdown_growth',
            options=[{'label': land, 'value': land} for land in länder_options],
            value='Islamische Republik Iran',  # Standardwert
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Graph(id='wachstums_graph'),
    ])

# ✅ Register callback function
def register_callbacks(app):
    @app.callback(
        Output('wachstums_graph', 'figure'),
        Input('land_dropdown_growth', 'value')
    )
    def update_graph(selected_country):
        df_country = df_grouped[(df_grouped['Land'] == selected_country) &
                                (df_grouped['Jahr'] >= 2008) &
                                (df_grouped['Jahr'] <= 2024)]

        fig = go.Figure()

        for col, name, color in zip(
            ['export_wachstum', 'import_wachstum'],
            ['Exportwachstum', 'Importwachstum'],
            ['#1f77b4', '#ff7f0e']
        ):
            fig.add_trace(go.Scatter(
                x=df_country['Jahr'],
                y=df_country[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Wachstum: %{{y:.2f}} %<extra></extra>'
            ))

        # ✅ Scale y-axis dynamically
        max_value = df_country[['export_wachstum', 'import_wachstum']].max().max()
        min_value = df_country[['export_wachstum', 'import_wachstum']].min().min()
        abs_max = max(abs(max_value), abs(min_value))
        exponent = math.floor(math.log10(abs_max))
        base_step = 10 ** exponent
        if abs_max / base_step > 5:
            base_step *= 2
        elif abs_max / base_step > 2:
            base_step *= 1.5
        new_max = math.ceil(abs_max / base_step) * base_step
        new_min = -new_max
        tickvals = list(range(int(new_min), int(new_max) + int(base_step), int(base_step)))

        fig.update_layout(
            title=f'Export- und Importwachstum zwischen Deutschland und {selected_country} (2008-2024)',
            xaxis_title='Jahr',
            yaxis_title='Wachstum (%)',
            yaxis=dict(tickvals=tickvals, range=[new_min, new_max]),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        return fig
