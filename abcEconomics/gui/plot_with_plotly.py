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

    groups = set(df['group'])

    graphs = {}

    for group in groups:
        graphs[group] = []

        group_df = df[df['group'] == group]

        for col in group_df.columns:
            if col not in ['round', 'name', 'datetime', 'group']:
                table = group_df.pivot_table(columns='name', values=col, index='datetime')

                if len(table) > 0:
                    graphs[group].append(html.H3(children=group + ' - ' + col))
                    graphs[group].append(dcc.Graph(id=group + '_' + col,
                                         figure=table.figure(kind='scatter', asFigure=True)))

    app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        ''')] +
        [dcc.Tabs(id='graphs', children=[dcc.Tab(label=group, children=graphs[group]) for group in groups])])

    return app


def ppl(path):
    app = gen(path)
    app.run_server(debug=True, use_reloader=False)
