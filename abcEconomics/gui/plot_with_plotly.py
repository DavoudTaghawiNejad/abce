from plotly.offline import plot
import pandas as pd
import cufflinks as cf
import dash
import dash_core_components as dcc
import dash_html_components as html

def dateparse(x):
    return pd.datetime.strptime(x, '%Y-%m-%d')


def gen(path):
    app = dash.Dash()

    infile = path + '/data.csv'
    df = pd.read_csv(infile, parse_dates={'datetime': ['round']}, date_parser=dateparse)
    df = df.set_index(df['datetime'])

    farms = df[df['group'] == 'farm']

    data = {}
    for col in farms.columns:
        if col not in ['round', 'name', 'datetime', 'group']:
            try:
                data[col] = farms.pivot_table(columns='name', values=col, index='datetime')
            except Exception as e:
                print(col, e)

    app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        '''),

        dcc.Graph(
            id='example-graph',
            figure=data['money'].figure(kind='scatter', theme='ggplot', asFigure=True))
    ])

    return app


def ppl(path):
    app = gen(path)
    app.run_server(debug=True, use_reloader=False)
