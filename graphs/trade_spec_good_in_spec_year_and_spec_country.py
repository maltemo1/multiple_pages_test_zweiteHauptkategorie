import dash
from dash import dcc, html
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import math

# Daten aus allen Jahresdateien laden
jahre = list(range(2014, 2025))
daten_liste = []

# Pfad korrekt setzen
base_path = os.path.join(os.path.dirname(__file__), "../data")

for jahr in jahre:
    pfad = os.path.join(base_path, f"Handelsdaten_{jahr}.csv")
    try:
        df_jahr = pd.read_csv(pfad, encoding='utf-8')
        daten_liste.append(df_jahr)
    except FileNotFoundError:
        print(f"⚠️ Datei für {jahr} nicht gefunden!")

# Alle Daten zusammenfügen
df = pd.concat(daten_liste, ignore_index=True)

# Monatsnamen zuweisen
monatsnamen = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez"
}
df['Monat_Name'] = df['Monat'].map(monatsnamen)

# Tausenderwerte umrechnen
df[['Ausfuhr: Wert', 'Einfuhr: Wert']] = df[['Ausfuhr: Wert', 'Einfuhr: Wert']].fillna(0) * 1000

# Formatierer für Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} Tsd €'
    else:
        return f'{value:,.0f} €'

# Layout-Funktion
def create_layout():
    return html.Div([
        html.H1("Monatlicher Export- und Importverlauf einer Ware mit einem ausgewählten Land in einem Jahr"),

        html.Div([
            dcc.Dropdown(
                id='trade_spec_good_year_dropdown',
                options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].dropna().unique())],
                value=2024,
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

        html.Div([
            dcc.Dropdown(
                id='trade_spec_good_good_dropdown',
                options=[{'label': g, 'value': g} for g in sorted(df['Label'].dropna().unique())],
                value='Pharmazeutische Erzeugnisse',
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

        html.Div([
            dcc.Dropdown(
                id='trade_spec_good_country_dropdown',
                options=[{'label': l, 'value': l} for l in sorted(df['Land'].dropna().unique())],
                value='Islamische Republik Iran',
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

        html.Div(id='trade_spec_good_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='trade_spec_good_graph')
    ])

# Callback-Funktion
def register_callbacks(app):
    @app.callback(
        [dash.Output('trade_spec_good_graph', 'figure'),
         dash.Output('trade_spec_good_info_text', 'children')],
        [dash.Input('trade_spec_good_year_dropdown', 'value'),
         dash.Input('trade_spec_good_good_dropdown', 'value'),
         dash.Input('trade_spec_good_country_dropdown', 'value')]
    )
    def update_graph(year_selected, good_selected, country_selected):
        df_filtered = df[(df['Jahr'] == year_selected) & (df['Label'] == good_selected)]
        df_monatlich = df_filtered[df_filtered['Land'] == country_selected]

        # Falls keine Daten vorhanden sind
        if df_monatlich.empty:
            return go.Figure(), f"Keine Daten für {good_selected} mit {country_selected} im Jahr {year_selected} vorhanden."

        fig = go.Figure()

        for col, name, color in zip(
            ['Ausfuhr: Wert', 'Einfuhr: Wert'],
            ['Exportwert', 'Importwert'],
            ['#1f77b4', '#ff7f0e']
        ):
            fig.add_trace(go.Scatter(
                x=df_monatlich['Monat_Name'],
                y=df_monatlich[col],
                mode='lines+markers',
                name=name,
                line=dict(width=2, color=color),
                hovertemplate=f"<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>"
            ))

        # Y-Achsenformatierung
        max_value = df_monatlich[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step = max_value / 5 if max_value > 0 else 1
        tickvals = np.arange(0, max_value + step, step)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            title=f'Monatlicher Handelsverlauf: {good_selected} mit {country_selected} ({year_selected})',
            xaxis_title='Monat',
            yaxis_title='Wert in €',
            yaxis=dict(
                tickvals=tickvals,
                ticktext=ticktext
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)'),
            margin=dict(l=40, r=40, t=60, b=40)
        )

        # Ranking-Logik
        export_agg = df_filtered.groupby('Land')['Ausfuhr: Wert'].sum()
        import_agg = df_filtered.groupby('Land')['Einfuhr: Wert'].sum()

        total_export = export_agg.sum()
        total_import = import_agg.sum()

        export_value = export_agg.get(country_selected, 0)
        import_value = import_agg.get(country_selected, 0)

        export_rank = export_agg.sort_values(ascending=False).index.get_loc(country_selected) + 1 if country_selected in export_agg else "-"
        import_rank = import_agg.sort_values(ascending=False).index.get_loc(country_selected) + 1 if country_selected in import_agg else "-"

        export_percent = (export_value / total_export) * 100 if total_export > 0 else 0
        import_percent = (import_value / total_import) * 100 if total_import > 0 else 0

        info_text = (
            f"{country_selected} war im Jahr {year_selected} "
            f"Deutschlands <b>{export_rank}. größter Exportpartner</b> ({export_percent:.2f}% des Exports) "
            f"und <b>{import_rank}. größter Importpartner</b> ({import_percent:.2f}% des Imports) "
            f"für die Ware <b>{good_selected}</b>."
        )

        return fig, info_text
