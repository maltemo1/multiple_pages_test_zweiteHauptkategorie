import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/aggregated_df.csv")

# Daten laden
df = pd.read_csv(csv_path)

# Falls die Daten nicht korrekt geladen wurden, abbrechen
if df.empty:
    raise ValueError("CSV-Datei konnte nicht geladen werden oder ist leer.")

# Funktion zur Bestimmung der optimalen Schrittgröße für die Y-Achse
def determine_step_size(max_value):
    thresholds = [1e6, 5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9, 50e9]
    steps = [100e3, 500e3, 1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 1e9, 2e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 5e9

# Funktion zur Y-Achsen-Formatierung
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Monatlicher Handelsverlauf für ausgewählte Waren"),

        dcc.Dropdown(
            id='overview_trade_spec_good_in_spec_year_dropdown_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].dropna().unique())],
            value=df['Jahr'].dropna().max(),  # Aktuellstes Jahr
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='overview_trade_spec_good_in_spec_year_dropdown_good',
            options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].dropna().unique())],
            value='Mineralische Brennstoffe usw.' if 'Mineralische Brennstoffe usw.' in df['Label'].values else df['Label'].dropna().unique()[0],
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='overview_trade_spec_good_in_spec_year_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='overview_trade_spec_good_in_spec_year_graph'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('overview_trade_spec_good_in_spec_year_graph', 'figure'),
         dash.Output('overview_trade_spec_good_in_spec_year_info_text', 'children')],
        [dash.Input('overview_trade_spec_good_in_spec_year_dropdown_year', 'value'),
         dash.Input('overview_trade_spec_good_in_spec_year_dropdown_good', 'value')]
    )
    def update_graph(selected_year, selected_good):
        # Daten filtern
        df_filtered = df[(df['Jahr'] == selected_year) & (df['Label'] == selected_good)]

        if df_filtered.empty:
            return go.Figure(), "Keine Daten für diese Auswahl verfügbar."

        fig = go.Figure()

        # Export / Import Linien hinzufügen
        for col, name, color in zip(
            ['Ausfuhr: Wert', 'Einfuhr: Wert'],
            ['Exportvolumen', 'Importvolumen'],
            ['#1f77b4', '#ff7f0e']
        ):
            fig.add_trace(go.Scatter(
                x=df_filtered['Monat'],
                y=df_filtered[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Y-Achsen-Skalierung
        max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        # Achsen und Layout
        fig.update_layout(
            title=f'Monatlicher Export- und Importverlauf der Ware "{selected_good}" im Jahr {selected_year}',
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

        # Info-Text
        info_text = f"Darstellung des monatlichen Export- und Importverlaufs der Ware '{selected_good}' im Jahr {selected_year}."

        return fig, info_text
