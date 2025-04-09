# graphs/overview_trade_spec_good_in_spec_year.py

import dash
from dash import dcc, html
import pandas as pd
import os
import numpy as np
import math
import plotly.graph_objects as go

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/aggregated_df.csv")

# CSV laden
df = pd.read_csv(csv_path)

# Sicherstellen, dass Daten korrekt geladen wurden
if df.empty:
    raise ValueError("CSV-Datei konnte nicht geladen werden oder ist leer.")

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

# Dynamische Schrittweite für y-Achse
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Monatlicher Export- und Importverlauf einer Ware im ausgewählten Jahr"),

        dcc.Dropdown(
            id='overview_spec_good_dropdown_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].dropna().unique())],
            value=df['Jahr'].dropna().max(),
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='overview_spec_good_dropdown_good',
            options=[{'label': str(g), 'value': g} for g in sorted(df['Label'].dropna().unique())],
            value='Mineralische Brennstoffe usw.' if 'Mineralische Brennstoffe usw.' in df['Label'].values else df['Label'].dropna().iloc[0],
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='overview_spec_good_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='overview_spec_good_graph'),
    ])

# Callback-Registrierung
def register_callbacks(app):
    @app.callback(
        [dash.Output('overview_spec_good_graph', 'figure'),
         dash.Output('overview_spec_good_info_text', 'children')],
        [dash.Input('overview_spec_good_dropdown_year', 'value'),
         dash.Input('overview_spec_good_dropdown_good', 'value')]
    )
    def update_graph(selected_year, selected_good):
        # Daten filtern
        df_filtered = df[(df['Jahr'] == selected_year) & (df['Label'] == selected_good)]

        if df_filtered.empty:
            return go.Figure(), "Keine Daten für diese Kombination verfügbar."

        fig = go.Figure()

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

        # Y-Achse berechnen
        max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Monatlicher Export- und Importverlauf von "{selected_good}" im Jahr {selected_year}',
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

        # Ranking-Info berechnen
        df_year = df[df['Jahr'] == selected_year]
        export_ranking = df_year.groupby('Label')['Ausfuhr: Wert'].sum().sort_values(ascending=False).reset_index()
        import_ranking = df_year.groupby('Label')['Einfuhr: Wert'].sum().sort_values(ascending=False).reset_index()

        try:
            export_rank = export_ranking[export_ranking['Label'] == selected_good].index[0] + 1
            import_rank = import_ranking[import_ranking['Label'] == selected_good].index[0] + 1

            info_text = f'Platzierung der Ware "{selected_good}" im Jahr {selected_year}:\n'
            info_text += f'➤ Export: Platz {export_rank} von {len(export_ranking)}\n'
            info_text += f'➤ Import: Platz {import_rank} von {len(import_ranking)}'
        except:
            info_text = f'Keine Platzierungsdaten für die Ware "{selected_good}" verfügbar.'

        return fig, info_text
