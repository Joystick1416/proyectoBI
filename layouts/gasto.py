"""Layout y callbacks — Dashboard 3: Gasto Presupuestal."""
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from queries.q_gasto import (
    opciones_gasto, kpi_gasto, evolucion_anual, top_deptos,
    gasto_por_funcion, gasto_por_fuente, gasto_por_nivel, heatmap_mensual,
)

C = {
    "bambu":   "#5C8A66",
    "hoja":    "#7EA479",
    "marron":  "#665044",
    "musgo":   "#8C9980",
    "naranja": "#D36E36",
    "mostaza": "#DCA134",
    "purpura": "#522D5B",
}

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

PLOTLY_LAYOUT = dict(
    font_family="Lato, sans-serif",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(t=30, b=30, l=20, r=20),
)


def _opts(vals):
    return [{"label": str(v), "value": v} for v in vals]


def layout():
    anios, niveles, deptos, funcs, progs = opciones_gasto()

    filtros = html.Div(className="filtros-bar", children=[
        html.Div([
            html.Div("Años", className="filtro-label"),
            dcc.Dropdown(id="gas-anios", options=_opts(anios),
                         value=anios, multi=True, style={"minWidth": "180px"}),
        ]),
        html.Div([
            html.Div("Nivel de gobierno", className="filtro-label"),
            dcc.Dropdown(id="gas-niveles", options=_opts(niveles),
                         multi=True, placeholder="Todos", style={"minWidth": "200px"}),
        ]),
        html.Div([
            html.Div("Departamento", className="filtro-label"),
            dcc.Dropdown(id="gas-deptos", options=_opts(deptos),
                         multi=True, placeholder="Todos", style={"minWidth": "200px"}),
        ]),
        html.Div([
            html.Div("Función", className="filtro-label"),
            dcc.Dropdown(id="gas-funciones", options=_opts(funcs),
                         multi=True, placeholder="Todas", style={"minWidth": "220px"}),
        ]),
        html.Div([
            html.Div("Programa presupuestal", className="filtro-label"),
            dcc.Dropdown(id="gas-programas", options=_opts(progs),
                         multi=True, placeholder="Todos",
                         style={"minWidth": "260px"},
                         optionHeight=50),
        ]),
    ])

    kpis = html.Div(id="gas-kpis", className="kpi-row")

    charts = html.Div(className="charts-section", children=[
        # Fila 1: evolución anual full width
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Evolución anual del presupuesto", className="chart-titulo"),
                html.Div("PIM vs Devengado en miles de millones S/", className="chart-subtitulo"),
                dcc.Graph(id="gas-g1", config={"displayModeBar": False}),
            ]), md=12),
        ], className="mb-0"),
        # Fila 2: top deptos + nivel gobierno
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Top 15 departamentos por devengado", className="chart-titulo"),
                html.Div("Miles de millones S/ ejecutados", className="chart-subtitulo"),
                dcc.Graph(id="gas-g2", config={"displayModeBar": False}),
            ]), md=7),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Ejecución por nivel de gobierno", className="chart-titulo"),
                html.Div("PIM vs Devengado (miles de millones S/)", className="chart-subtitulo"),
                dcc.Graph(id="gas-g3", config={"displayModeBar": False}),
            ]), md=5),
        ], className="mb-0"),
        # Fila 3: fuente financiamiento + tasa ejecución por depto
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Devengado por fuente de financiamiento", className="chart-titulo"),
                html.Div("Miles de millones S/", className="chart-subtitulo"),
                dcc.Graph(id="gas-g4", config={"displayModeBar": False}),
            ]), md=5),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Tasa de ejecución por departamento", className="chart-titulo"),
                html.Div("Devengado / PIM × 100 — top 15", className="chart-subtitulo"),
                dcc.Graph(id="gas-g5", config={"displayModeBar": False}),
            ]), md=7),
        ], className="mb-0"),
        # Fila 4: funciones full width
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Devengado por función", className="chart-titulo"),
                html.Div("Top 12 funciones presupuestales · miles de millones S/", className="chart-subtitulo"),
                dcc.Graph(id="gas-g6", config={"displayModeBar": False}),
            ]), md=12),
        ], className="mb-0"),
        # Fila 5: heatmap mensual full width
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Estacionalidad del gasto", className="chart-titulo"),
                html.Div("Devengado mensual en millones S/ por año", className="chart-subtitulo"),
                dcc.Graph(id="gas-g7", config={"displayModeBar": False}),
            ]), md=12),
        ]),
    ])

    return html.Div([filtros, kpis, charts])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(Output("gas-kpis", "children"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def update_kpis(anios, niveles, deptos, funciones, programas):
    d = kpi_gasto(anios or None, niveles or None, deptos or None,
                  funciones or None, programas or None)
    return [
        html.Div(className="kpi-card", children=[
            html.Div(f"S/ {d['pim']:,.2f} MM", className="kpi-valor"),
            html.Div("Presupuesto modificado (PIM)", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-naranja", children=[
            html.Div(f"S/ {d['girado']:,.2f} MM", className="kpi-valor"),
            html.Div("Monto girado (pagado)", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-marron", children=[
            html.Div(str(d['deptos']), className="kpi-valor"),
            html.Div("Departamentos con registro", className="kpi-etiqueta"),
        ]),
    ]


@callback(Output("gas-g1", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g1_evolucion(anios, niveles, deptos, funciones, programas):
    df = evolucion_anual(anios or None, niveles or None, deptos or None,
                         funciones or None, programas or None)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="PIM", x=df["anio"], y=df["pim"],
        marker_color=C["musgo"],
        text=df["pim"].apply(lambda v: f"S/{v:.1f}MM"),
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Devengado", x=df["anio"], y=df["devengado"],
        marker_color=C["bambu"],
        text=df["devengado"].apply(lambda v: f"S/{v:.1f}MM"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300, barmode="group",
                      xaxis=dict(tickmode="linear", dtick=1),
                      yaxis_title="Miles de millones S/",
                      legend=dict(orientation="h", y=-0.25))
    return fig


@callback(Output("gas-g2", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g2_deptos(anios, niveles, deptos, funciones, programas):
    df = top_deptos(anios or None, niveles or None, deptos or None,
                    funciones or None, programas or None)
    df = df.sort_values("devengado")
    fig = go.Figure(go.Bar(
        x=df["devengado"], y=df["departamento"], orientation="h",
        marker_color=C["bambu"],
        text=df["devengado"].apply(lambda v: f"S/{v:.2f}MM"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=380,
                      xaxis_title="Miles de millones S/",
                      yaxis=dict(tickfont=dict(size=10)))
    return fig


@callback(Output("gas-g3", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g3_nivel(anios, deptos, funciones, programas):
    df = gasto_por_nivel(anios or None, deptos or None,
                         funciones or None, programas or None)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="PIM", x=df["nivel_gobierno"], y=df["pim"],
        marker_color=C["musgo"],
    ))
    fig.add_trace(go.Bar(
        name="Devengado", x=df["nivel_gobierno"], y=df["devengado"],
        marker_color=C["naranja"],
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=380, barmode="group",
                      yaxis_title="Miles de millones S/",
                      xaxis=dict(tickfont=dict(size=10)),
                      legend=dict(orientation="h", y=-0.2))
    return fig


@callback(Output("gas-g4", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g4_fuente(anios, niveles, deptos, funciones, programas):
    df = gasto_por_fuente(anios or None, niveles or None, deptos or None,
                          funciones or None, programas or None)
    colores = [C["bambu"], C["naranja"], C["musgo"], C["mostaza"], C["marron"]]
    fig = go.Figure(go.Pie(
        labels=df["fuente_financiamiento"],
        values=df["devengado"],
        marker_colors=colores[:len(df)],
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>S/ %{value:.2f} MM<br>%{percent}<extra></extra>",
        hole=0.35,
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False)
    return fig


@callback(Output("gas-g5", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g5_tasa_depto(anios, niveles, deptos, funciones, programas):
    df = top_deptos(anios or None, niveles or None, deptos or None,
                    funciones or None, programas or None)
    df = df.sort_values("tasa_ejec")

    def color_tasa(v):
        if v >= 90:
            return C["bambu"]
        if v >= 75:
            return C["mostaza"]
        return C["naranja"]

    colores = [color_tasa(v) for v in df["tasa_ejec"]]
    fig = go.Figure(go.Bar(
        x=df["tasa_ejec"], y=df["departamento"], orientation="h",
        marker_color=colores,
        text=df["tasa_ejec"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=380,
                      xaxis=dict(title="Tasa de ejecución (%)", range=[0, 115]),
                      yaxis=dict(tickfont=dict(size=10)))
    return fig


@callback(Output("gas-g6", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g6_funcion(anios, niveles, deptos, funciones, programas):
    df = gasto_por_funcion(anios or None, niveles or None, deptos or None,
                           funciones or None, programas or None)
    df = df.sort_values("devengado")
    fig = go.Figure(go.Bar(
        x=df["devengado"], y=df["funcion"], orientation="h",
        marker_color=C["hoja"],
        text=df["devengado"].apply(lambda v: f"S/{v:.2f}MM"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=360,
                      xaxis_title="Miles de millones S/",
                      yaxis=dict(tickfont=dict(size=10)))
    return fig


@callback(Output("gas-g7", "figure"),
          Input("gas-anios",     "value"),
          Input("gas-niveles",   "value"),
          Input("gas-deptos",    "value"),
          Input("gas-funciones", "value"),
          Input("gas-programas", "value"))
def g7_heatmap(anios, niveles, deptos, funciones, programas):
    df = heatmap_mensual(anios or None, niveles or None, deptos or None,
                         funciones or None, programas or None)
    pivot = df.pivot(index="anio", columns="mes", values="devengado_mill").fillna(0)
    pivot.columns = [MESES[c - 1] for c in pivot.columns]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=[str(a) for a in pivot.index.tolist()],
        colorscale=[[0, "#F5F2EE"], [0.5, C["hoja"]], [1, C["bambu"]]],
        text=[[f"S/{v:,.0f}M" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="Año: %{y}<br>Mes: %{x}<br>Devengado: S/%{z:,.0f}M<extra></extra>",
        showscale=True,
        colorbar=dict(title="Millones S/"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280)
    return fig
