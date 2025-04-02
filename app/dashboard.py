
import pandas as pd
import panel as pn
import altair as alt
from groundwater import Groundwater

pn.extension("vega", "tabulator", sizing_mode="stretch_width")


component1 = pn.pane.Markdown("# Welcome to Component 1")
component2 = pn.pane.Markdown("# Welcome to Component 2")
component3 = pn.pane.Markdown("# Welcome to test 2")

page = pn.template.FastGridTemplate(
    title="Grundwassermonitoring Basel-Stadt",
    sidebar=[component1, component2],
    main=[component3]
)
page.servable()