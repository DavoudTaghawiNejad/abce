import pandas as pd
import cufflinks  # extends pandas to work with plotly
import dash
import dash_core_components as dcc
import dash_html_components as html


def dateparse(x):
    return pd.datetime.strptime(x, '%Y-%m-%d')


def gen(path, datetime=False):


    infile = path + '/data.csv'
    df = pd.read_csv(infile)
    try:
        df['round'].apply(int)
    except ValueError:
        df['round'] = pd.to_datetime(df['round'])

    groups = set(df['group'])

    graphs = {}

    for group in groups:
        graphs[group] = []

        group_df = df[df['group'] == group]

        for col in group_df.columns:
            if col not in ['round', 'name', 'group']:
                table = group_df.pivot_table(columns='name', values=col, index='round')
                if len(table) > 0:
                    graphs[group].append(html.H3(children=group + ' - ' + col))
                    panel_graph = dcc.Graph(id=group + '_' + col,
                                            figure=table.figure(kind='scatter', asFigure=True))

                    if len(table.columns) == 1:
                        graphs[group].append(panel_graph)
                    elif len(table.columns) > 1:
                        sum_graph = dcc.Graph(id=group + '_' + col + '_mean',
                                              figure=table.sum(1).figure(kind='scatter', asFigure=True))
                        mean_graph = dcc.Graph(id=group + '_' + col + '_mean',
                                               figure=table.mean(1).figure(kind='scatter', asFigure=True))
                        tabs = dcc.Tabs(id=group + '_' + col + '_tab', children=
                                        [dcc.Tab(label='panel', children=panel_graph),
                                         dcc.Tab(label='sum', children=sum_graph),
                                         dcc.Tab(label='mean', children=mean_graph)])
                        graphs[group].append(tabs)



    layout = html.Div(children=[
        html.H1(children='abcEconomics')] +
        [dcc.Tabs(id='graphs', children=[dcc.Tab(label=group, children=graphs[group]) for group in groups])])

    return layout


def ppl(path):
    app = dash.Dash()

    app.layout = gen(path)
    app.run_server(debug=True, use_reloader=False)
