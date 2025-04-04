
import pandas as pd
import panel as pn
import altair as alt
from groundwater import Groundwater

pn.extension("vega", "tabulator", sizing_mode="stretch_width")
image_path = 'app/header-trinkwasser_lange-erlen-grundwasserwerk_1280px.jpg'

ACCENT = "teal"
stylesheet = """
    .styled-table {
        border-collapse: collapse;
        width: 60%;
        font-family: Arial, sans-serif;
        font-size: 14px;
    }
    .styled-table td {
        border: 1px solid #ddd;
        padding: 8px;
        vertical-align: top;
    }
    .styled-table td:first-child {
        font-weight: bold;
        background-color: #f2f2f2;
        width: 30%;
        white-space: nowrap;
    }
    .styled-table tr:nth-child(even) { background-color: #fafafa; }
    .styled-table a {
        color: #007acc;
        text-decoration: none;
    }
    .styled-table td:nth-child(2) {
        width: 70%;
    }
    .styled-table a:hover {
        text-decoration: underline;
    }
"""

def format_well_info_table(df):
    def format_cell(val):
        if isinstance(val, str) and val.startswith("http"):
            return f'<a href="{val}" target="_blank">Link</a>'
        return val
    
    # Clean and drop irrelevant rows
    df = df.dropna(how='all').fillna('')
    col_name = df.columns[1]
    # Convert URLs to clickable links
    df[col_name] = df[col_name].apply(format_cell)
    # Create styled HTMLindex                                                          
    html_table = df.to_html(escape=False, index=False, header=False, classes="styled-table")
    return html_table


def update_year_options(event):
# Update year options when station changes
    station = event.new
    years = gw.get_years(station)
    year_range_slider.param.set_param(
        start=years[-1],
        end=years[0],
    )
    year_range_slider.param.set_param(
        value=(years[-1], years[0])
    )


def update_view(station, year_range):
    # Function to update both plot and table
    
    df = gw.get_plot_waterlevels_df(station, year_range)
    start_date = pd.to_datetime(df["date"].min())
    end_date = pd.to_datetime(df["date"].max())
    shared_xscale = alt.Scale(domain=[start_date, end_date])
    settings = {
        'x': 'date', 
        'y': 'value', 
        'color': 'stationnr',
        'title': f"Grundwasserstand {gw.get_station_name(station)} - {year_range[0]}-{year_range[1]}",
        'x_domain': shared_xscale
    }
    plot = gw.get_timeseries_chart(df, settings)
    # Precipitation
    df_prec = gw.get_precipitation_df(year_range)
    settings = {
        'x': 'date', 
        'y': 'precipitation', 
        'color': 'stationnr',
        'title': f"Niederschlag(mm) {year_range[0]}-{year_range[1]}",
        'x_domain': shared_xscale
    }
    plot_precipitation = gw.get_precipitation_chart(df_prec, settings) # gw.get_precipitation_chart(year_range)
    # Table
    table = pn.widgets.Tabulator(df, sizing_mode="stretch_both", name="Table")
    fmap = gw.get_map(station)
    map_panel = pn.pane.HTML(fmap._repr_html_(), sizing_mode="stretch_both")
    info_df = gw.get_bohrkaster_info_df(station)
    html = format_well_info_table(info_df)
    info_panel = pn.pane.HTML(html, sizing_mode="stretch_width", stylesheets=[stylesheet])
    styles = {
        "box-shadow": "rgba(50, 50, 93, 0.25) 0px 6px 12px -2px, rgba(0, 0, 0, 0.3) 0px 3px 7px -3px",
        "border-radius": "4px",
        "padding": "10px",
    }
    return pn.Tabs(
        ("📈 Plot", pn.Column(
            pn.pane.Vega(plot),
            pn.pane.Vega(plot_precipitation))
        ),
        ("📊 Tabelle", table),
        ("🗺️ Karte", map_panel),
        ("ℹ️ Details Bohrung", info_panel),
        styles=styles
    )


# Main app logic
gw = Groundwater()
selected_station = pn.widgets.Select(
    name="Stationen",
    value=gw.station_nrs[0],
    options=gw.stations,
    description="Wöhle eine Station",
)
years = gw.get_years(selected_station.value)

year_range_slider = pn.widgets.RangeSlider(
    name='Jahresintervall',
    start=years[-1],
    end=years[0],
    value=(years[2], years[0]),  # Default selected range
    step=1
)

selected_station.param.watch(update_year_options, "value")


# Bind dynamic content
tabs = pn.bind(update_view, selected_station, year_range_slider)
selected_station.margin = (20, 0, 30, 0)  # 10px bottom margin
year_range_slider.margin = (0, 0, 30, 0)  # no extra margin
card_styles = {
    'background': 'transparent',  # Transparent background
    'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)',  # Subtle shadow for outline effect
    'border-radius': '8px',  # Optional: rounded corners
    'padding': '20px'  # Optional: internal padding
}
filter_card = pn.Card(
    selected_station,
    year_range_slider,
    title='🔎 Filter',
    styles=card_styles,
    margin=(30, 10, 10, 10),  # 20px margin on all sides
    collapsible=False,

)
logo_with_link = pn.pane.HTML(f"""
<div style="text-align: center;">
  <img src="https://www.iwb.ch/dam/jcr:09981f98-e6eb-4136-8b3b-8f607ffb07c3/header-trinkwasser_lange-erlen-grundwasserwerk-16x9.jpg" width="350" style="margin-right: 10px;">
  <a href="https://www.iwb.ch/klimadreh/ratgeber/sauberes-trinkwasser/wie-funktioniert-die-trinkwasserversorgung-in-basel" 
     target="_blank" style="font-size: 0.8em;">
    Source
  </a>
</div>
""", width=200)

info_card = pn.pane.HTML("""
<br><br><div style="border:1px solid #ccc; border-radius:9px; padding:10px;">
  <strong>App: </strong>Grundwassermonitoring Basel-Stadt<br>
  <strong>Version: </strong>2025-04-04 / v0.2<br>
  <strong>Autor: </strong> <a href="mailto:lcalmbach@gmail.com" target="_blank">lcalmbach@gmail.com</a><br>
  <strong>Data Source:</strong> <a href="https://data.bs.ch" target="_blank">data.bs</a>
</div>
""", width=260)

sidebar = pn.Column(
    logo_with_link,
    filter_card,
    info_card,
    pn.Spacer(height=50),
    info_card,
    width=300,
)

page = pn.template.MaterialTemplate(
    title="⛲ Grundwassermonitoring Basel-Stadt",
    sidebar=sidebar,
    main=[tabs]
)
page.servable()