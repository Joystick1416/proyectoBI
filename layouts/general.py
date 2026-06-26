"""Layout y callbacks — Dashboard 1: General."""
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from queries.q_general import (
    kpi_general, evolucion_tasa_nacional, top10_deptos_valorizado,
    sin_valorizacion_por_region, generacion_por_anio,
    resumen_por_region, opciones_filtros,
)

# ── Paleta ────────────────────────────────────────────────────────────────────
C = {
    "bambu":   "#5C8A66",
    "hoja":    "#7EA479",
    "marron":  "#665044",
    "musgo":   "#8C9980",
    "rojo":    "#A62B2B",
    "naranja": "#D36E36",
    "mostaza": "#DCA134",
    "purpura": "#522D5B",
}
SEQ = [C["bambu"], C["naranja"], C["musgo"], C["mostaza"],
       C["hoja"], C["marron"], C["purpura"], C["rojo"]]

PLOTLY_LAYOUT = dict(
    font_family="Lato, sans-serif",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(t=30, b=30, l=20, r=20),
)


def _opts(vals):
    return [{"label": str(v), "value": v} for v in vals]


# ── Layout ────────────────────────────────────────────────────────────────────

def layout():
    anios, regiones, deptos = opciones_filtros()

    filtros = html.Div(className="filtros-bar", children=[
        html.Div([
            html.Div("Años", className="filtro-label"),
            dcc.Dropdown(
                id="gen-anios", options=_opts(anios),
                value=anios, multi=True, placeholder="Todos los años",
                style={"minWidth": "200px"},
            ),
        ]),
        html.Div([
            html.Div("Región natural", className="filtro-label"),
            dcc.Dropdown(
                id="gen-regiones", options=_opts(regiones),
                multi=True, placeholder="Todas las regiones",
                style={"minWidth": "200px"},
            ),
        ]),
        html.Div([
            html.Div("Departamento", className="filtro-label"),
            dcc.Dropdown(
                id="gen-deptos", options=_opts(deptos),
                multi=True, placeholder="Todos los departamentos",
                style={"minWidth": "220px"},
            ),
        ]),
    ])

    kpis = html.Div(id="gen-kpis", className="kpi-row")

    charts = html.Div(className="charts-section", children=[
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Evolución de la tasa de valorización nacional", className="chart-titulo"),
                html.Div("Orgánico vs Inorgánico · 2019–2024", className="chart-subtitulo"),
                dcc.Graph(id="gen-g1", config={"displayModeBar": False}),
            ]), md=7),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Top 10 departamentos por residuos valorizados", className="chart-titulo"),
                html.Div("Toneladas acumuladas en el período", className="chart-subtitulo"),
                dcc.Graph(id="gen-g2", config={"displayModeBar": False}),
            ]), md=5),
        ], className="mb-0"),
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Distritos sin ninguna valorización", className="chart-titulo"),
                html.Div("Distribución por región natural", className="chart-subtitulo"),
                dcc.Graph(id="gen-g3", config={"displayModeBar": False}),
            ]), md=4),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Generación de residuos por año", className="chart-titulo"),
                html.Div("Millones de toneladas municipales", className="chart-subtitulo"),
                dcc.Graph(id="gen-g4", config={"displayModeBar": False}),
            ]), md=4),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Resumen por región natural", className="chart-titulo"),
                html.Div("Generación, valorización y GPC", className="chart-subtitulo"),
                dcc.Graph(id="gen-g5", config={"displayModeBar": False}),
            ]), md=4),
        ]),
    ])

    return html.Div([filtros, kpis, charts])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("gen-kpis", "children"),
    Input("gen-anios", "value"),
    Input("gen-regiones", "value"),
    Input("gen-deptos", "value"),
)
def update_kpis(anios, regiones, deptos):
    d = kpi_general(anios or None, regiones or None, deptos or None)
    return [
        html.Div(className="kpi-card", children=[
            html.Div(f"{d['total_generado_mt']:,.2f} M t", className="kpi-valor"),
            html.Div("Residuos generados", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-naranja", children=[
            html.Div(f"{d['tasa_valorizacion_pct']:.2f} %", className="kpi-valor"),
            html.Div("Tasa de valorización", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-marron", children=[
            html.Div(f"{d['valorizado_miles_t']:,.1f} K t", className="kpi-valor"),
            html.Div("Residuos valorizados", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-purpura", children=[
            html.Div(str(d['municipios_con_reporte']), className="kpi-valor"),
            html.Div("Municipios con reporte", className="kpi-etiqueta"),
        ]),
    ]


@callback(Output("gen-g1", "figure"),
          Input("gen-anios", "value"),
          Input("gen-regiones", "value"),
          Input("gen-deptos", "value"))
def g1_evolucion(anios, regiones, deptos):
    df = evolucion_tasa_nacional(anios or None, regiones or None, deptos or None)
    fig = go.Figure()
    colores = {"ORGANICO": C["bambu"], "INORGANICO": C["naranja"]}
    nombres = {"ORGANICO": "Orgánico", "INORGANICO": "Inorgánico"}
    for tipo in ["ORGANICO", "INORGANICO"]:
        sub = df[df["tipo_residuo"] == tipo]
        fig.add_trace(go.Scatter(
            x=sub["anio"], y=sub["tasa_pct"],
            name=nombres[tipo],
            mode="lines+markers",
            line=dict(color=colores[tipo], width=2.5),
            marker=dict(size=7),
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(tickmode="linear", dtick=1, title="Año"),
        yaxis=dict(title="Tasa valorización (%)"),
        legend=dict(orientation="h", y=-0.2),
        height=300,
    )
    return fig


@callback(Output("gen-g2", "figure"),
          Input("gen-anios", "value"),
          Input("gen-regiones", "value"),
          Input("gen-deptos", "value"))
def g2_top10(anios, regiones, deptos):
    df = top10_deptos_valorizado(anios or None, regiones or None, deptos or None)
    df = df.sort_values("valorizado_t")
    fig = go.Figure(go.Bar(
        x=df["valorizado_t"], y=df["departamento"],
        orientation="h",
        marker_color=C["bambu"],
        text=df["valorizado_t"].apply(lambda v: f"{v:,.0f} t"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Toneladas", height=300,
                      yaxis=dict(tickfont=dict(size=11)))
    return fig


@callback(Output("gen-g3", "figure"),
          Input("gen-anios", "value"),
          Input("gen-deptos", "value"))
def g3_sin_val(anios, deptos):
    df = sin_valorizacion_por_region(anios or None, deptos or None)
    colores_region = {"COSTA": C["naranja"], "SIERRA": C["bambu"], "SELVA": C["hoja"]}
    fig = go.Figure(go.Pie(
        labels=df["region_natural"],
        values=df["sin_valorizacion"],
        marker_colors=[colores_region.get(r, C["musgo"]) for r in df["region_natural"]],
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} distritos<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300,
                      showlegend=False,
                      annotations=[dict(text="Sin val.", x=0.5, y=0.5,
                                        font_size=11, showarrow=False)])
    return fig


@callback(Output("gen-g4", "figure"),
          Input("gen-anios", "value"),
          Input("gen-regiones", "value"),
          Input("gen-deptos", "value"))
def g4_generacion(anios, regiones, deptos):
    df = generacion_por_anio(anios or None, regiones or None, deptos or None)
    fig = go.Figure(go.Bar(
        x=df["anio"], y=df["generado_mt"],
        marker_color=C["musgo"],
        text=df["generado_mt"].apply(lambda v: f"{v:.2f}"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300,
                      xaxis=dict(tickmode="linear", dtick=1),
                      yaxis_title="Millones de toneladas")
    return fig


@callback(Output("gen-g5", "figure"),
          Input("gen-anios", "value"),
          Input("gen-deptos", "value"))
def g5_resumen_region(anios, deptos):
    df = resumen_por_region(anios or None, deptos or None)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Generado (M t)", x=df["region_natural"], y=df["generado_mt"],
        marker_color=C["bambu"], yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        name="Tasa val. (%)", x=df["region_natural"], y=df["tasa_valorizacion_pct"],
        mode="lines+markers", line=dict(color=C["naranja"], width=2.5),
        marker=dict(size=8), yaxis="y2",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300,
        yaxis=dict(title="Millones de toneladas"),
        yaxis2=dict(title="Tasa valorización (%)",
                    overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.25),
        barmode="group",
    )
    return fig
