
import panel as pn
import pandas as pd
import altair as alt

pn.extension(sizing_mode="stretch_width")

component1 = pn.pane.Markdown("# Welcome to Component 1")
component2 = pn.pane.Markdown("# Welcome to Component 2")
component3 = pn.pane.Markdown("# Welcome to test 2")

page = pn.template.MaterialTemplate(
    title="Grundwassermonitoring Basel-Stadt",
    sidebar=[component1, component2],
    main=[component3]
)
page.servable()