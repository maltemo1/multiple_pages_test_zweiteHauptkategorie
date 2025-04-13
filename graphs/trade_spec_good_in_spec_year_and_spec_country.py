import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np
import math

# ----------- CSVs aus Ordner "data" laden -----------------
jahre = list(range(2014, 2025))
daten_liste = []

for jahr in jahre:
    pfad = os.path.join(os.path.dirname(__file__), f"../data/Handelsdaten_{jahr}.csv")
    if os.path.exists(pfad):
        df_jahr = pd.read_csv(pfad, encoding='utf-8')
        daten_liste.append(df_jahr)

if not daten_liste:
    raise ValueError("Keine gültigen Handelsdaten-Dateien gefunden.")

df = pd.concat(daten_liste, ignore_index=True)

# Monatsnamen hinzufügen
monatsnamen = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez"
}
df['Monat_Name'] = df['Monat'].map(monatsnamen)

# ---------------- Hilfsfunktionen ------------------

#def determine_step_size(max_value):
#    thresholds = [5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9]
 #   steps =       [1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9]
  #  for i, threshold in enumerate(thresholds):
   #     if max_value < threshold:
    #        return steps[i]
    #return 2e9


def determine_step_size(max_value):
    thresholds = [2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 10e6, 50e6, 100e6, 250e6, 500e6, 1e9, 5e9, 10e9]
    steps =       [5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 5e6, 10e6, 25e6, 50e6, 100e6, 250e6, 500e6, 1e9]
    for i, threshold in enumerate(thresholds):
        if max_value < threshold:
            return steps[i]
    return 2e9


def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd €'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio €'
    else:
        return f'{value:,.0f} €'

# ---------------- Layout-Funktion ------------------

def create_layout():
    return html.Div([
        html.H1("Monatlicher Export- und Importverlauf einer Ware mit einem Land im ausgewählten Jahr"),

        dcc.Dropdown(
            id='16729_dropdown_jahr',
            options=[{'label': str(jahr), 'value': jahr} for jahr in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '40%'}
        ),

        dcc.Dropdown(
            id='16729_dropdown_ware',
            options=[{'label': ware, 'value': ware} for ware in sorted(df['Label'].dropna().unique())],
            value="Pharmazeutische Erzeugnisse",
            clearable=False,
            style={'width': '60%'}
        ),

        dcc.Dropdown(
            id='16729_dropdown_land',
            options=[{'label': land, 'value': land} for land in sorted(df['Land'].dropna().unique())],
            value="Islamische Republik Iran",
            clearable=False,
            style={'width': '60%'}
        ),

        html.Div(id='16729_info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

        dcc.Graph(id='16729_graph'),
    ])

# ---------------- Callback-Funktion ------------------

def register_callbacks(app):
    @app.callback(
        [dash.Output('16729_graph', 'figure'),
         dash.Output('16729_info_text', 'children')],
        [dash.Input('16729_dropdown_jahr', 'value'),
         dash.Input('16729_dropdown_ware', 'value'),
         dash.Input('16729_dropdown_land', 'value')]
    )
    def update_graph(selected_year, selected_ware, selected_country):
        df_year = df[(df['Jahr'] == selected_year) & (df['Label'] == selected_ware)]

        if df_year.empty:
            return go.Figure(), f"Keine Daten für {selected_ware} im Jahr {selected_year} verfügbar."

        df_selected = df_year[df_year['Land'] == selected_country]

        if df_selected.empty:
            return go.Figure(), f"Keine Daten für {selected_ware} mit {selected_country} im Jahr {selected_year} verfügbar."

        fig = go.Figure()

        for col, name, color in zip(
            ['Ausfuhr: Wert', 'Einfuhr: Wert'],
            ['Exportwert', 'Importwert'],
            ['#1f77b4', '#ff7f0e']
        ):
            fig.add_trace(go.Bar(
                x=df_selected['Monat_Name'],
                y=df_selected[col],
                name=name,
                marker=dict(color=color),
                hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
            ))

        # Achsenskalierung
        max_value = df_selected[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
        step_size = determine_step_size(max_value)
        rounded_max = math.ceil(max_value / step_size) * step_size
        tickvals = np.arange(0, rounded_max + 1, step_size)
        ticktext = [formatter(val) for val in tickvals]

        fig.update_layout(
            barmode='group',
            title=f'Monatlicher Export- und Importverlauf von {selected_ware} mit {selected_country} ({selected_year})',
            xaxis_title='Monat',
            yaxis_title='Wert in €',
            yaxis=dict(
                tickvals=tickvals,
                ticktext=ticktext
            ),
            legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
        )

        # Handelsbilanz-Analyse und Ranking
        export_agg = df_year.groupby('Land')['Ausfuhr: Wert'].sum()
        import_agg = df_year.groupby('Land')['Einfuhr: Wert'].sum()

        total_export = export_agg.sum()
        total_import = import_agg.sum()

        export_rank = export_agg.sort_values(ascending=False).index.get_loc(selected_country) + 1 if selected_country in export_agg else None
        import_rank = import_agg.sort_values(ascending=False).index.get_loc(selected_country) + 1 if selected_country in import_agg else None

        export_value = export_agg.get(selected_country, 0)
        import_value = import_agg.get(selected_country, 0)

        export_percent = (export_value * 1e9 / total_export) * 100 if total_export > 0 else 0
        import_percent = (import_value * 1e9 / total_import) * 100 if total_import > 0 else 0

        
        # old:
        #info_text = (f"Export-Rang: {export_rank} ({export_value:.2f} Mrd €, {export_percent:.2f}%) | "
        #             f"Import-Rang: {import_rank} ({import_value:.2f} Mrd €, {import_percent:.2f}%) "
        #             f"→ Jahr: {selected_year}, Ware: {selected_ware}, Land: {selected_country}")

        
        # new:
        info_text = (
            f"{selected_country} war im Jahr {selected_year} "
            f"Deutschlands {export_rank}. größter Exportpartner (mit {export_value:,.0f} €) "
            f"und {import_rank}. größter Importpartner (mit {import_value:,.0f} €) "
            f"für die Ware {selected_ware}."
        )

        
        #
        # Ranking-Logik
        #export_percent = (export_value / total_export) * 100 if total_export > 0 else 0
        #import_percent = (import_value / total_import) * 100 if total_import > 0 else 0

        #info_text = (
        #    f"{country_selected} war im Jahr {year_selected} "
        #    f"Deutschlands <b>{export_rank}. größter Exportpartner</b> "
        #    f"und <b>{import_rank}. größter Importpartner</b> "
        #    f"für die Ware <b>{good_selected}</b>."
        #)
        #


        return fig, info_text
