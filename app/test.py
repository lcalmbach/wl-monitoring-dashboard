import panel as pn

pn.extension()

app = pn.Column('hello world v2')

# Serveable entrypoint
app.servable()