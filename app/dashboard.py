import hvplot.pandas
import pandas as pd
import panel as pn
import altair as alt
import folium
from groundwater import Groundwater

pn.extension("vega", "tabulator")

pn.extension(sizing_mode="stretch_width", template="material")
pn.config.raw_css.append("body { background: yellow; }")

alt.themes.enable("default")  # fallback

ACCENT = "teal"
styles = {
    "box-shadow": "rgba(50, 50, 93, 0.25) 0px 6px 12px -2px, rgba(0, 0, 0, 0.3) 0px 3px 7px -3px",
    "border-radius": "4px",
    "padding": "10px",
}

gw = Groundwater()

# Widgets
selected_station = pn.widgets.Select(
    name="Stations",
    value=gw.stations[0],
    options=sorted(gw.stations),
    description="Select a station",
)
years = gw.get_years(selected_station.value)
selected_year = pn.widgets.Select(
    name="Year", 
    options=years, 
    value=years[0],
    description="Select a monitoring year",
)

# Update year options when station changes
def update_year_options(event):
    station = event.new
    years = gw.get_years(station)
    selected_year.options = sorted(years, reverse=True)
    selected_year.value = years[-1] if gw.max_year not in years else gw.max_year

selected_station.param.watch(update_year_options, "value")

# Function to update both plot and table
def update_view(station, year):
    df = gw.get_plot_waterlevels_df(station, [year])
    
    # Altair plot
    min_y = df["value"].min()
    max_y = df["value"].max()
    plot = alt.Chart(df.reset_index()).mark_line().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("value:Q", title="Water Level", scale=alt.Scale(domain=[min_y - 0.5, max_y + 0.5])),
        tooltip=["date:T", "value:Q"],
    ).properties(
        title=f"{gw.get_station_name(station)} - {year}",
        width="container",
    ).interactive()

    # Table
    table = pn.widgets.Tabulator(df, sizing_mode="stretch_both", name="Table")
    fmap = gw.get_map(station)
    map_panel = pn.pane.HTML(fmap._repr_html_(), sizing_mode="stretch_both", height=400)
    return pn.Tabs(
        ("📈 Plot", pn.pane.Vega(plot, sizing_mode="stretch_both")),
        ("📊 Table", table),
        ("🗺️ Map", map_panel),
        styles=styles,
        sizing_mode="stretch_both",
    )

# Bind dynamic content
tabs = pn.bind(update_view, selected_station, selected_year)

# Template
pn.template.MaterialTemplate(
    title="Grundwassermonitoring Basel-Stadt",
    sidebar=[selected_station, selected_year],
    main=[tabs]
).servable()
