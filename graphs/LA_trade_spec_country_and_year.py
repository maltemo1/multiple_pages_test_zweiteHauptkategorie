import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# Relativer Pfad zur CSV-Datei
csv_path = os.path.join(os.path.dirname(__file__), "../data/trade_spec_country_and_year.csv")
csv_path_grouped = os.path.join(os.path.dirname(__file__), "../data/df_grouped.csv")

# Daten laden
df = pd.read_csv(csv_path)
df_grouped = pd.read_csv(csv_path_grouped)

# Falls die Daten nicht korrekt geladen wurden, abbrechen
if df.empty or df_grouped.empty:
    raise ValueError("CSV-Dateien konnten nicht geladen werden oder sind leer.")

# Werte mit 1000 multiplizieren, um die Originalwerte zu erhalten
#df[['export_wert', 'import_wert', 'handelsvolumen_wert']] = df[['export_wert', 'import_wert', 'handelsvolumen_wert']].fillna(0) * 1000

# Funktion zur Bestimmung der optimalen Schrittgröße für die Y-Achse
def determine_step_size(max_value):
    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9, 50e9, 100e9]
    steps = [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9, 2e9, 10e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 25e9

# Funktion zur Y-Achsen-Formatierung
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

# Funktion zur Erstellung des Layouts
def create_layout():
    return html.Div([
        html.H1("Monatlicher Handelsverlauf Deutschlands mit ausgewähltem Land"),

        dcc.Dropdown(
            id='la_trade_spec_country_dropdown_country',
            options=[{'label': country, 'value': country} for country in sorted(df['Land'].dropna().unique())],
            value='Islamische Republik Iran' if 'Islamische Republik Iran' in df['Land'].values else df['Land'].dropna().unique()[0],
            clearable=False,
            style={'width': '50%'}
        ),

        dcc.Dropdown(
            id='la_trade_spec_country_dropdown_year',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].dropna().unique())],
            value=df['Jahr'].dropna().max(),  # Standardmäßig das aktuellste Jahr
            clearable=False,
            style={'width': '50%'}
        ),

        html.Div(id='la_trade_spec_country_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='la_trade_spec_country_graph'),
    ])

# Callback für das Update des Graphen
def register_callbacks(app):
    @app.callback(
        [dash.Output('la_trade_spec_country_graph', 'figure'),
         dash.Output('la_trade_spec_country_info_text', 'children')],
        [dash.Input('la_trade_spec_country_dropdown_country', 'value'),
         dash.Input('la_trade_spec_country_dropdown_year', 'value')]
    )
    def update_graph(selected_country, selected_year):
        # Daten filtern für das ausgewählte Land und Jahr
        df_filtered = df[(df['Land'] == selected_country) & (df['Jahr'] == selected_year)]

        # Falls keine Daten vorhanden sind, leeren Graph zurückgeben
        if df_filtered.empty:
            return go.Figure(), "Keine Daten für dieses Land und Jahr verfügbar."

        fig = go.Figure()

        # Linien für Export, Import und Handelsvolumen
        for col, name, color in zip(
            ['export_wert', 'import_wert', 'handelsvolumen_wert'],
            ['Exportvolumen', 'Importvolumen', 'Gesamthandelsvolumen'],
            ['#1f77b4', '#ff7f0e', '#2ca02c']
        ):
            fig.add_trace(go.Scatter(
                x=df_filtered['Monat'],
                y=df_filtered[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Achsenskala berechnen
        max_value = df_filtered[['export_wert', 'import_wert', 'handelsvolumen_wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Monatlicher Export-, Import- und Handelsverlauf Deutschlands mit {selected_country} im Jahr {selected_year}',
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

        # Handelsbilanz-Info anzeigen
        df_selected = df_grouped[(df_grouped['Land'] == selected_country) & (df_grouped['Jahr'] == selected_year)]
        if not df_selected.empty:
            status = df_selected['handelsbilanz_status'].values[0]
            handelsbilanz = df_selected['handelsbilanz'].values[0]
            
            info_text = f"Deutschlands Handelsbilanzstatus mit {selected_country} im ausgewählten Jahr: {status} ({handelsbilanz} €)"
        else:
            info_text = "Keine Daten zur Handelsbilanz verfügbar."

        return fig, info_text
