import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# Daten einlesen
jahre = list(range(2014, 2025))
daten_liste = []

for jahr in jahre:
    pfad = f'data/Handelsdaten_{jahr}.csv'
    try:
        df_jahr = pd.read_csv(pfad, encoding='utf-8')
        daten_liste.append(df_jahr)
    except FileNotFoundError:
        print(f"⚠️ Datei für {jahr} nicht gefunden!")

df = pd.concat(daten_liste, ignore_index=True)

# Monatsnamen zuweisen
monatsnamen = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez"
}
df['Monat_Name'] = df['Monat'].map(monatsnamen)

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

# App erstellen
app = dash.Dash(__name__)
app.title = "Monatlicher Handelsverlauf"

app.layout = html.Div([
    html.H1("Monatlicher Handelsverlauf für ausgewählte Waren, Länder und Jahre"),

    html.Div([
        html.Label("Jahr auswählen:"),
        dcc.Dropdown(
            id='jahr_dropdown',
            options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
            value=2024,
            clearable=False,
            style={'width': '100%'}
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

    html.Div([
        html.Label("Ware auswählen:"),
        dcc.Dropdown(
            id='ware_dropdown',
            options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].unique())],
            value='Pharmazeutische Erzeugnisse',
            clearable=False,
            style={'width': '100%'}
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

    html.Div([
        html.Label("Land auswählen:"),
        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': str(l), 'value': l} for l in sorted(df['Land'].unique())],
            value='Islamische Republik Iran',
            clearable=False,
            style={'width': '100%'}
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'padding': '0 10px'}),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='monatlicher_warenhandel_graph')
])

@app.callback(
    [Output('monatlicher_warenhandel_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('jahr_dropdown', 'value'),
     Input('ware_dropdown', 'value'),
     Input('land_dropdown', 'value')]
)
def update_graph(year_selected, ware_selected, land_selected):
    # Daten filtern
    df_filtered = df[(df['Jahr'] == year_selected) & (df['Label'] == ware_selected)]
    df_monatlich = df_filtered[df_filtered['Land'] == land_selected]

    # Ranking berechnen
    export_agg = df_filtered.groupby('Land')['Ausfuhr: Wert'].sum()
    import_agg = df_filtered.groupby('Land')['Einfuhr: Wert'].sum()

    total_export = export_agg.sum()
    total_import = import_agg.sum()

    export_rank = export_agg.sort_values(ascending=False).index.get_loc(land_selected) + 1 if land_selected in export_agg else None
    export_value = export_agg.get(land_selected, 0)
    export_percentage = (export_value / total_export) * 100 if total_export > 0 else 0

    import_rank = import_agg.sort_values(ascending=False).index.get_loc(land_selected) + 1 if land_selected in import_agg else None
    import_value = import_agg.get(land_selected, 0)
    import_percentage = (import_value / total_import) * 100 if total_import > 0 else 0

    info_text = (
        f"📊 Bedeutung von {land_selected} für '{ware_selected}' im Jahr {year_selected}: "
        f"➡️ Export-Rang: {export_rank}, Wert: {export_value:,.0f} € ({export_percentage:.2f} %) | "
        f"➡️ Import-Rang: {import_rank}, Wert: {import_value:,.0f} € ({import_percentage:.2f} %)"
    )

    # Monatsdaten plotten
    fig = go.Figure()
    for col, name, color in zip(['Ausfuhr: Wert', 'Einfuhr: Wert'],
                                ['Exportvolumen', 'Importvolumen'],
                                ['#1f77b4', '#ff7f0e']):
        fig.add_trace(go.Scatter(
            x=df_monatlich['Monat_Name'],
            y=df_monatlich[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    max_value = df_monatlich[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()
    rounded_max = math.ceil(max_value * 1.1)

    # Dynamische Schrittweite (kleiner & angepasst)
    steps = [1e3, 5e3, 1e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7,
             2e7, 5e7, 1e8, 2e8, 5e8, 1e9, 2e9, 5e9, 1e10, 2e10, 5e10]
    step = next((s for s in steps if rounded_max / s <= 10), steps[-1])
    tickvals = np.arange(0, rounded_max + step, step)
    ticktext = [formatter(val) for val in tickvals]

    fig.update_layout(
        title=f'Monatlicher Verlauf – {ware_selected} ({year_selected}) – {land_selected}',
        xaxis_title='Monat',
        yaxis_title='Wert in Euro',
        xaxis=dict(tickmode='array', tickvals=list(monatsnamen.values())),
        yaxis=dict(tickvals=tickvals, ticktext=ticktext),
        legend=dict(x=0, y=1.15, orientation='h'),
        margin=dict(l=60, r=20, t=80, b=50),
        height=600
    )

    return fig, info_text

if __name__ == '__main__':
    app.run(debug=True)
