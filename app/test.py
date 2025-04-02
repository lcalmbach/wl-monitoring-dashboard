import panel as pn

pn.extension()

app = pn.Column('hello world')

# Serveable entrypoint
app.servable()