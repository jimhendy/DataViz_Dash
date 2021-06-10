import base64
import io
import os
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

app = dash.Dash()

SELECTOR_MARGIN = "0.7vh"
DF = None

app.layout = html.Div(
    id="main-div",
    children=[
        html.Div(
            id="selections-div",
            style={
                "width": "calc(20vw - 8px)",
                "height": "calc(100vh - 16px)",
                "display": "flex",
                "flex-direction": "column",
                "align-items": "center",
                "justify-content": "center",
                "text-align": "center",
            },
            children=[
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        id="file-name-div", children="Drag and Drop or Select Files"
                    ),
                    style={
                        "width": "100%",
                        "height": "3vh",
                        "textAlign": "center",
                        "display": "flex",
                        "align-items": "center",
                        "justify-content": "center",
                        "borderWidth": "0.1vh",
                        "borderStyle": "dashed",
                        "borderRadius": "0.6vh",
                        "borderColor": "blue",
                        "cursor": "pointer",
                        "margin": SELECTOR_MARGIN,
                    },
                    multiple=False,
                ),
                html.Button(
                    id="draw-button",
                    children="Draw",
                    style={"margin": SELECTOR_MARGIN},
                    disabled=True,
                ),
                dcc.Checklist(
                    id="log-y-checkbox",
                    options=[
                        {"label": "Log Y", "value": "log-y"},
                        {"label": "Log X", "value": "log-x"},
                    ],
                    style={"margin": SELECTOR_MARGIN},
                    labelStyle={
                        "display": "inline-block",
                        "margin-left": "2vw",
                        "margin-right": "2vw",
                    },
                ),
                dcc.Dropdown(
                    id="x-variable-dropdown",
                    options=[],
                    placeholder="Select the X variable",
                    multi=False,
                    searchable=True,
                    clearable=True,
                    disabled=True,
                    style={
                        "width": "90%",
                        "margin-left": "5%",
                        "margin-bottom": SELECTOR_MARGIN,
                    },
                ),
                dcc.Checklist(
                    id="y-variables-checklist",
                    options=[],
                    style={
                        "margin": SELECTOR_MARGIN,
                        "width": "100%",
                        "display": "flex",
                        "flex": "1 1 auto",
                        "flex-direction": "column",
                    },
                ),
            ],
        ),
        dcc.Graph(
            id="graph",
            style={
                "width": "calc(80vw - 8px)",
                "height": "calc(100vh - 16px)",
                "margin": "0px",
                "padding": "0px",
            },
        ),
    ],
    style={
        "width": "calc(100vw - 16px)",
        "height": "calc(100vh - 16px)",
        "display": "flex",
        "flex-direction": "row",
        "margin": "0px",
    },
)


@app.callback(
    [
        Output("x-variable-dropdown", "options"),
        Output("x-variable-dropdown", "value"),
        Output("x-variable-dropdown", "disabled"),
        Output("y-variables-checklist", "options"),
        Output("y-variables-checklist", "value"),
        Output("draw-button", "disabled"),
        Output("file-name-div", "children"),
    ],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
)
def load_new_file(contents_input, filename):
    global DF

    failed_returns = [[], None, True, [], [], True, "No File Loaded"]

    if any([i is None for i in [contents_input, filename]]):
        raise PreventUpdate

    _, file_type = os.path.splitext(filename)
    file_type = re.sub("^\.", "", file_type)

    if not hasattr(pd, f"read_{file_type}"):
        return failed_returns

    contents_string = contents_input.split(",")[1]
    decoded = base64.b64decode(contents_string)
    contents = io.StringIO(decoded.decode("utf-8"))

    DF = getattr(pd, f"read_{file_type}")(contents)

    columns = [{"label": c, "value": c} for c in DF.columns.tolist()]

    if not len(columns):
        return failed_returns
    else:
        return (columns, None, False, columns, [], False, filename)


@app.callback(
    Output("graph", "figure"),
    [Input("draw-button", "n_clicks")],
    [
        State("x-variable-dropdown", "value"),
        State("y-variables-checklist", "value"),
        State("log-y-checkbox", "value"),
    ],
)
def plot(click, x_var, y_vars, log_status):
    if any([i is None for i in (click, x_var, y_vars)]):
        raise PreventUpdate

    fig = go.Figure(
        data=[go.Scatter(x=DF[x_var], y=DF[y], name=y) for y in y_vars],
        layout=go.Layout(
            margin=go.layout.Margin(
                l=0,  # left margin
                r=0,  # right margin
                b=0,  # bottom margin
                t=0,  # top margin
            )
        ),
    )

    fig.update_yaxes(
        type="linear" if (log_status is None or "log-y" not in log_status) else "log"
    )
    fig.update_xaxes(
        type="linear" if (log_status is None or "log-x" not in log_status) else "log"
    )

    return fig


if __name__ == "__main__":
    app.run_server(host="localhost")
