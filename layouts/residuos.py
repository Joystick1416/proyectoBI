"""Layout y callbacks — Dashboard 2: Residuos."""
import folium
from branca.colormap import LinearColormap
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from queries.q_residuos import (
    kpi_residuos, evolucion_tasa, top10_distritos_tasa,
    heatmap_region_anio, por_tipo_municipalidad,
    scatter_gpc_tasa, top10_mejora, treemap_generacion,
    mapa_generacion, get_geojson,
)
from queries.q_general import opciones_filtros

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

PLOTLY_LAYOUT = dict(
    font_family="Quicksand, sans-serif",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(t=30, b=30, l=20, r=20),
)


def _opts(vals):
    return [{"label": str(v), "value": v} for v in vals]


def layout():
    anios, regiones, deptos = opciones_filtros()
    tipos = ["ORGANICO", "INORGANICO"]
    tipos_mun = ["DISTRITAL", "PROVINCIAL"]

    filtros = html.Div(className="filtros-bar", children=[
        html.Div([
            html.Div("Años", className="filtro-label"),
            dcc.Dropdown(id="res-anios", options=_opts(anios),
                         value=anios, multi=True, style={"minWidth": "180px"}),
        ]),
        html.Div([
            html.Div("Región natural", className="filtro-label"),
            dcc.Dropdown(id="res-regiones", options=_opts(regiones),
                         multi=True, placeholder="Todas", style={"minWidth": "180px"}),
        ]),
        html.Div([
            html.Div("Departamento", className="filtro-label"),
            dcc.Dropdown(id="res-deptos", options=_opts(deptos),
                         multi=True, placeholder="Todos", style={"minWidth": "200px"}),
        ]),
        html.Div([
            html.Div("Tipo de residuo", className="filtro-label"),
            dcc.Dropdown(
                id="res-tipos",
                options=_opts(tipos),
                value=tipos,
                multi=True,
                style={"minWidth": "200px"},
            ),
        ]),
        html.Div([
            html.Div("Tipo municipalidad", className="filtro-label"),
            dcc.Dropdown(
                id="res-tipo-mun",
                options=_opts(tipos_mun),
                multi=True,
                placeholder="Todas",
                style={"minWidth": "180px"},
            ),
        ]),
    ])

    kpis = html.Div(id="res-kpis", className="kpi-row")

    charts = html.Div(className="charts-section", children=[
        # Fila 1: R1 + R2
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Evolución tasa de valorización", className="chart-titulo"),
                html.Div("Orgánico vs Inorgánico por año", className="chart-subtitulo"),
                dcc.Graph(id="res-r1", config={"displayModeBar": False}),
            ]), md=6),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Top 10 distritos con mayor tasa", className="chart-titulo"),
                html.Div("Tasa promedio en el período seleccionado", className="chart-subtitulo"),
                dcc.Graph(id="res-r2", config={"displayModeBar": False}),
            ]), md=6),
        ], className="mb-0"),
        # Fila 2: R3 + R4
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Tasa por región natural × año", className="chart-titulo"),
                html.Div("Heatmap de valorización (%)", className="chart-subtitulo"),
                dcc.Graph(id="res-r3", config={"displayModeBar": False}),
            ]), md=6),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Valorización por tipo de municipalidad", className="chart-titulo"),
                html.Div("Distrital vs Provincial", className="chart-subtitulo"),
                dcc.Graph(id="res-r4", config={"displayModeBar": False}),
            ]), md=6),
        ], className="mb-0"),
        # Fila 3: R5 full width
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Generación per cápita vs tasa de valorización", className="chart-titulo"),
                html.Div("Un punto por departamento · color = región natural", className="chart-subtitulo"),
                dcc.Graph(id="res-r5", config={"displayModeBar": False}),
            ]), md=12),
        ], className="mb-0"),
        # Fila 4: R6 + R7
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Top 10 distritos con mayor mejora", className="chart-titulo"),
                html.Div("Variación de tasa primer → último año disponible", className="chart-subtitulo"),
                dcc.Graph(id="res-r6", config={"displayModeBar": False}),
            ]), md=5),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Generación de residuos por departamento", className="chart-titulo"),
                html.Div("Miles de toneladas municipales · agrupado por región", className="chart-subtitulo"),
                dcc.Graph(id="res-r7", config={"displayModeBar": False}),
            ]), md=7),
        ]),
        # Fila 5: Mapa choropleth distrital
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("Generación de residuos por distrito", className="chart-titulo"),
                html.Div("Toneladas anuales · 1 832 distritos con cobertura", className="chart-subtitulo"),
                html.Div(id="res-mapa", style={"height": "520px", "width": "100%"}),
            ]), md=12),
        ]),
    ])

    return html.Div([filtros, kpis, charts])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(Output("res-kpis", "children"),
          Input("res-anios", "value"),
          Input("res-regiones", "value"),
          Input("res-deptos", "value"))
def update_kpis(anios, regiones, deptos):
    d = kpi_residuos(anios or None, regiones or None, deptos or None)
    return [
        html.Div(className="kpi-card", children=[
            html.Div(f"{d['generado_mt']:,.2f} M t", className="kpi-valor"),
            html.Div("Total generado", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-naranja", children=[
            html.Div(f"{d['valorizado_kt']:,.1f} kt", className="kpi-valor"),
            html.Div("Total valorizado", className="kpi-etiqueta"),
        ]),
        html.Div(className="kpi-card acento-marron", children=[
            html.Div(f"{d['gpc_municipal']:.4f}", className="kpi-valor"),
            html.Div("Generación per cápita (kg/hab/día)", className="kpi-etiqueta"),
        ]),
    ]


@callback(Output("res-r1", "figure"),
          Input("res-anios", "value"), Input("res-regiones", "value"),
          Input("res-deptos", "value"), Input("res-tipos", "value"))
def r1_evolucion(anios, regiones, deptos, tipos):
    df = evolucion_tasa(anios or None, regiones or None, deptos or None, tipos or None)
    fig = go.Figure()
    colores = {"ORGANICO": C["bambu"], "INORGANICO": C["naranja"]}
    nombres = {"ORGANICO": "Orgánico", "INORGANICO": "Inorgánico"}
    for tipo in df["tipo_residuo"].unique():
        sub = df[df["tipo_residuo"] == tipo]
        fig.add_trace(go.Scatter(
            x=sub["anio"], y=sub["tasa_pct"], name=nombres.get(tipo, tipo),
            mode="lines+markers",
            line=dict(color=colores.get(tipo, C["musgo"]), width=2.5),
            marker=dict(size=7),
        ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280,
                      xaxis=dict(tickmode="linear", dtick=1),
                      yaxis_title="Tasa (%)",
                      legend=dict(orientation="h", y=-0.25))
    return fig


@callback(Output("res-r2", "figure"),
          Input("res-anios", "value"), Input("res-regiones", "value"),
          Input("res-deptos", "value"), Input("res-tipos", "value"))
def r2_top10(anios, regiones, deptos, tipos):
    df = top10_distritos_tasa(anios or None, regiones or None, deptos or None, tipos or None)
    df = df.sort_values("tasa_pct")
    fig = go.Figure(go.Bar(
        x=df["tasa_pct"], y=df["lugar"], orientation="h",
        marker_color=C["bambu"],
        text=df["tasa_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280,
                      xaxis_title="Tasa promedio (%)",
                      yaxis=dict(tickfont=dict(size=10)))
    return fig


@callback(Output("res-r3", "figure"),
          Input("res-tipos", "value"), Input("res-deptos", "value"))
def r3_heatmap(tipos, deptos):
    df = heatmap_region_anio(tipos or None, deptos or None)
    pivot = df.pivot(index="region_natural", columns="anio", values="tasa_pct").fillna(0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, "#F5F2EE"], [0.5, C["hoja"]], [1, C["bambu"]]],
        text=[[f"{v:.2f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="Región: %{y}<br>Año: %{x}<br>Tasa: %{z:.2f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="Tasa (%)"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280)
    return fig


@callback(Output("res-r4", "figure"),
          Input("res-anios", "value"), Input("res-regiones", "value"),
          Input("res-deptos", "value"), Input("res-tipos", "value"))
def r4_municipalidad(anios, regiones, deptos, tipos):
    df = por_tipo_municipalidad(anios or None, regiones or None, deptos or None, tipos or None)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Valorizado (t)", x=df["tipo_municipalidad"], y=df["valorizado_t"],
        marker_color=C["bambu"], yaxis="y",
        text=df["valorizado_t"].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        name="Tasa prom. (%)", x=df["tipo_municipalidad"], y=df["tasa_promedio"],
        mode="lines+markers",
        line=dict(color=C["naranja"], width=2.5), marker=dict(size=10),
        yaxis="y2",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, height=280,
        yaxis=dict(title="Toneladas valorizadas"),
        yaxis2=dict(title="Tasa promedio (%)", overlaying="y",
                    side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


@callback(Output("res-r5", "figure"),
          Input("res-anios", "value"), Input("res-regiones", "value"),
          Input("res-tipos", "value"))
def r5_scatter(anios, regiones, tipos):
    df = scatter_gpc_tasa(anios or None, regiones or None, tipos or None)
    colores_region = {"COSTA": C["naranja"], "SIERRA": C["bambu"], "SELVA": C["hoja"]}
    fig = go.Figure()
    for region in df["region_natural"].unique():
        sub = df[df["region_natural"] == region]
        fig.add_trace(go.Scatter(
            x=sub["gpc"], y=sub["tasa_pct"],
            mode="markers+text",
            name=region,
            text=sub["departamento"],
            textposition="top center",
            marker=dict(size=10, color=colores_region.get(region, C["musgo"])),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "GPC: %{x:.4f} kg/hab/día<br>"
                "Tasa: %{y:.2f}%<extra></extra>"
            ),
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT, height=350,
        xaxis_title="Generación per cápita municipal (kg/hab/día)",
        yaxis_title="Tasa de valorización (%)",
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


@callback(Output("res-r6", "figure"),
          Input("res-regiones", "value"),
          Input("res-deptos", "value"),
          Input("res-tipos", "value"))
def r6_mejora(regiones, deptos, tipos):
    df = top10_mejora(regiones or None, deptos or None, tipos or None)
    df = df.sort_values("mejora")
    fig = go.Figure(go.Bar(
        x=df["mejora"], y=df["lugar"], orientation="h",
        marker_color=C["hoja"],
        text=df["mejora"].apply(lambda v: f"+{v:.1f} pp"),
        textposition="outside",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280,
                      xaxis_title="Mejora en puntos porcentuales",
                      yaxis=dict(tickfont=dict(size=9)))
    return fig


@callback(Output("res-r7", "figure"),
          Input("res-anios", "value"),
          Input("res-regiones", "value"),
          Input("res-deptos", "value"))
def r7_treemap(anios, regiones, deptos):
    df = treemap_generacion(anios or None, regiones or None, deptos or None)
    colores_region = {"COSTA": C["naranja"], "SIERRA": C["bambu"], "SELVA": C["hoja"]}
    fig = px.treemap(
        df,
        path=["region_natural", "departamento"],
        values="generado_kt",
        color="region_natural",
        color_discrete_map=colores_region,
        hover_data={"generado_kt": ":.1f"},
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:.0f} kt",
        hovertemplate="<b>%{label}</b><br>Generado: %{value:.1f} kt<extra></extra>",
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=280)
    return fig


@callback(Output("res-mapa", "children"),
          Input("res-anios", "value"),
          Input("res-regiones", "value"),
          Input("res-deptos", "value"))
def r_mapa(anios, regiones, deptos):
    df = mapa_generacion(anios or None, regiones or None, deptos or None)
    gj  = get_geojson()

    vmax = float(df["generado_t"].quantile(0.95)) if not df.empty else 1.0

    colormap = LinearColormap(
        colors=["#F5F2EE", C["musgo"], C["hoja"], C["bambu"], C["marron"]],
        index=[0, vmax * 0.15, vmax * 0.5, vmax * 0.8, vmax],
        vmin=0,
        vmax=vmax,
        caption="Generación de residuos (t)",
    )

    color_lookup = {
        row["ubigeo_str"]: colormap(row["generado_t"])
        for _, row in df.iterrows()
    }

    m = folium.Map(
        location=[-9.5, -75.0],
        zoom_start=5,
        tiles="CartoDB positron",
        width="100%",
        height="100%",
    )

    folium.GeoJson(
        gj,
        style_function=lambda feat: {
            "fillColor":   color_lookup.get(feat["properties"]["IDDIST"], "#F5F2EE"),
            "color":       "white",
            "weight":      0.3,
            "fillOpacity": 0.75 if feat["properties"]["IDDIST"] in color_lookup else 0.1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NOMBDIST", "NOMBDEP"],
            aliases=["Distrito:", "Departamento:"],
            sticky=False,
        ),
    ).add_to(m)

    colormap.add_to(m)

    return html.Iframe(
        srcDoc=m._repr_html_(),
        style={"width": "100%", "height": "520px", "border": "none"},
    )
