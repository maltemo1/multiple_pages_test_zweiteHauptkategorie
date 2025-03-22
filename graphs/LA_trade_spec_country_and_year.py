import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import math

# Daten laden
data_dir = os.path.join(os.path.dirname(__file__), '../data')
df = pd.read_csv(os.path.join(data_dir, 'trade_spec_country_and_year.csv'))
df_grouped = pd.read_csv(os.path.join(data_dir, 'df_grouped.csv'))

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Monatlicher Handelsverlauf Deutschlands mit ausgewähltem Land"),

        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': str(l), 'value': l} for l in sorted(df['Land'].unique())],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='jahr_dropdown',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='monatlicher_handel_graph'),
    ])

# Callback-Funktion registrieren
def register_callbacks(app):
    @app.callback(
        [Output('monatlicher_handel_graph', 'figure'),
         Output('info_text', 'children')],
        [Input('land_dropdown', 'value'),
         Input('jahr_dropdown', 'value')]
    )
    def update_graph(country, year_selected):
        df_country_monthly = df[(df['Land'] == country) & (df['Jahr'] == year_selected)]

        fig = go.Figure()
        for col, name, color in zip(
            ['export_wert', 'import_wert', 'handelsvolumen_wert'],
            ['Exportvolumen', 'Importvolumen', 'Gesamthandelsvolumen'],
            ['#1f77b4', '#ff7f0e', '#2ca02c']
        ):
            fig.add_trace(go.Scatter(
                x=df_country_monthly['Monat'],
                y=df_country_monthly[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        max_value = df_country_monthly[['export_wert', 'import_wert', 'handelsvolumen_wert']].values.max()
        step = next(s for s in [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9, 25e9] if max_value < s * 5)

        rounded_max = math.ceil(max_value / step) * step
        tickvals = np.arange(0, rounded_max + 1, step)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Monatlicher Export-, Import- und Handelsverlauf Deutschlands mit {country} im Jahr {year_selected}',
            xaxis_title='Monat',
            yaxis_title='Wert in €',
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(1, 13)),
                ticktext=['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            ),
            yaxis=dict(
                tickvals=tickvals,
                ticktext=ticktext
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        df_selected = df_grouped[(df_grouped['Land'] == country) & (df_grouped['Jahr'] == year_selected)]

        if not df_selected.empty:
            status = df_selected['handelsbilanz_status'].values[0]
            handelsbilanz = df_selected['handelsbilanz'].values[0] / 1e9
            export_ranking = int(df_selected['export_ranking'].values[0])
            import_ranking = int(df_selected['import_ranking'].values[0])
            handelsvolumen_ranking = int(df_selected['handelsvolumen_ranking'].values[0])

            info_text = (f"{country}: Deutschland weist ein Handelsbilanz-{status} im Wert von {handelsbilanz:.2f} Mrd € "
                         f"mit diesem Land im Jahr {year_selected} auf.\n"
                         f"Unter allen deutschen Handelspartnern belegt {country} im Jahr {year_selected} den {export_ranking}. Platz "
                         f"gemessen am Exportvolumen, den {import_ranking}. Platz gemessen am Importvolumen "
                         f"und den {handelsvolumen_ranking}. Platz gemessen am gesamten Handelsvolumen.")
        else:
            info_text = f"Keine Daten für {country} im Jahr {year_selected} verfügbar."

        return fig, info_text
