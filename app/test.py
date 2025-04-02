import panel as pn

pn.extension("vega", "tabulator")

pn.extension(sizing_mode="stretch_width", template="material")
pn.config.raw_css.append("body { background: yellow; }")

pn.extension()

app = pn.Column('hello world v4')

# Serveable entrypoint
app.servable()