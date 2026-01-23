import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- INITIALIZE APP ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Marketing Insights Dashboard"

# --- DATA LOADER ---
def load_data():
    try:
        df = pd.read_csv("marketing_data_shocks.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except:
        pass
        
    try:
        df = pd.read_csv("marketing_data.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        print(f"Generating fallback data (Starting Q4 2022)...")
        dates = pd.date_range(start="2022-10-01", end="2023-12-31")
        rows = []
        channels = ["Paid Search", "Paid Social", "Programmatic", "Organic"]
        sources = ["Google Ads", "Facebook", "LinkedIn Ads", "Amazon Ad Server", "StackAdapt"]
        
        for d in dates:
            for ch in channels:
                imp = np.random.randint(20000, 80000)
                clicks = int(imp * np.random.uniform(0.08, 0.12))
                spend = imp * np.random.uniform(1.5, 3.5) if ch != "Organic" else 0
                conversions = int(clicks * np.random.uniform(0.05, 0.08))
                revenue = conversions * np.random.uniform(50, 200)
                
                rows.append({
                    "Date": d,
                    "Channel": ch,
                    "Source": np.random.choice(sources),
                    "Campaign": "Campaign " + str(np.random.randint(1, 5)),
                    "Impressions": imp,
                    "Clicks": clicks,
                    "Spend": spend,
                    "Conversions": conversions,
                    "Revenue": revenue
                })
        return pd.DataFrame(rows)

df = load_data()
if 'VideoViews' not in df.columns:
    df['VideoViews'] = df['Clicks'] * 0.7

# --- CONSTANTS ---
CHANNEL_ORDER = ["Programmatic", "Paid Search", "Paid Social", "Organic"]

# --- HELPER FUNCTIONS ---
def format_number(val):
    if val >= 1e6: return f"{val/1e6:.1f}M"
    elif val >= 1e3: return f"{val/1e3:.1f}K"
    else: return f"{val:.0f}"

def format_currency(val):
    if val >= 1e6: return f"${val/1e6:.2f}M"
    elif val >= 1e3: return f"${val/1e3:.0f}K"
    else: return f"${val:.0f}"

def format_percent(val):
    return f"{val:.2f}%"

def create_metric_card(title, value, delta, delta_value, sparkline_data=None):
    delta_color = '#10b981' if delta_value >= 0 else '#ef4444'
    
    sparkline = None
    if sparkline_data is not None and len(sparkline_data) > 0:
        sparkline = dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(
                    y=sparkline_data,
                    mode='lines',
                    line=dict(color='#8b5cf6', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(139, 92, 246, 0.1)',
                    hoverinfo='skip'
                )],
                layout=go.Layout(
                    height=30,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
            ),
            config={'displayModeBar': False, 'staticPlot': True, 'responsive': True},
            style={'height': '30px', 'width': '100%', 'marginTop': 'auto'}
        )
    
    return html.Div([
        html.Div([
            html.Div(title, style={
                'fontSize': 'clamp(11px, 0.8vw, 13px)', 
                'color': '#64748b', 
                'fontWeight': '600', 
                'marginBottom': '4px'
            }),
            html.Div(value, style={
                'fontSize': 'clamp(20px, 1.8vw, 28px)', 
                'fontWeight': '800', 
                'color': '#1e293b', 
                'marginBottom': '2px',
                'lineHeight': '1.1'
            }),
            html.Div([html.Span(f"{delta}", style={'color': delta_color, 'fontSize': 'clamp(10px, 0.7vw, 12px)', 'fontWeight': '600'})]) if delta else None,
        ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
        sparkline
    ], style={
        'background': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.04)',
        'border': '1px solid #e2e8f0',
        'height': '120px', 
        'padding': '12px 8px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'space-between',
        'textAlign': 'center',
        'overflow': 'hidden'
    })

def generate_heatmap_styles(df, col_name):
    if df.empty or col_name not in df.columns: return []
    min_val, max_val = df[col_name].min(), df[col_name].max()
    if max_val == min_val: return []
    
    styles = []
    steps = 5
    for i in range(steps):
        low = min_val + (i * (max_val - min_val) / steps)
        high = min_val + ((i + 1) * (max_val - min_val) / steps)
        alpha = 0.15 + (i * 0.35 / (steps - 1))
        r, g, b = 168, 85, 247 # Purple
        styles.append({
            'if': {'filter_query': f'{{{col_name}}} >= {low} && {{{col_name}}} <= {high}', 'column_id': col_name},
            'backgroundColor': f'rgba({r}, {g}, {b}, {alpha})',
            'color': '#1e293b',
            'fontWeight': '600'
        })
    return styles

def create_table_header(title):
    return html.Div([
        html.Div(title, style={'fontSize': '15px', 'color': '#1e293b', 'fontWeight': '700', 'flex': '1'}),
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'})

# --- LAYOUT ---
app.layout = html.Div([
    # Sidebar
    html.Div([
        html.Div([
            html.Button('«', id='sidebar-toggle', n_clicks=0, style={
                'background': 'rgba(255,255,255,0.1)', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 
                'width': '30px', 'height': '30px', 'cursor': 'pointer', 'fontSize': '18px', 'lineHeight': '30px', 'padding': '0'
            })
        ], style={'padding': '10px', 'textAlign': 'right'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('IM', style={'background': '#ff4081', 'borderRadius': '8px', 'padding': '4px 8px', 'display': 'inline-block', 'marginRight': '8px', 'fontWeight': 'bold', 'fontSize': '12px'}),
                    html.Span('IMPROVADO', style={'fontSize': '18px', 'fontWeight': '700', 'letterSpacing': '1px'})
                ], style={'marginBottom': '20px', 'color': 'white', 'display': 'flex', 'alignItems': 'center', 'whiteSpace': 'nowrap', 'overflow': 'hidden'}),
                
                html.Div('MARKETING INSIGHTS', style={'fontSize': '11px', 'color': '#b8a9d1', 'marginBottom': '10px', 'fontWeight': '600', 'letterSpacing': '0.5px', 'whiteSpace': 'nowrap'}),
                
                html.Div([
                    html.Div('Cross Channel', className='nav-item'),
                    html.Div('Executive Summary', className='nav-item nav-item-active'),
                    html.Div('Channel Performance', className='nav-item'),
                    html.Div('Channel Segments', className='nav-item'),
                    html.Div('', style={'height': '10px'}),
                    html.Div('Paid Ads x GA', className='nav-item'),
                    html.Div('Paid Search', className='nav-item'),
                    html.Div('Paid Social', className='nav-item'),
                    html.Div('SEO', className='nav-item'),
                    html.Div('Organic Social', className='nav-item'),
                    html.Div('Programmatic', className='nav-item'),
                    html.Div('eCommerce', className='nav-item'),
                ]),
                
                html.Div([
                    html.Div('HELP & SUPPORT', style={'fontSize': '11px', 'marginBottom': '10px', 'color': '#b8a9d1', 'fontWeight': '600', 'whiteSpace': 'nowrap'}),
                    html.Div('Contact', className='nav-item-small'),
                    html.Div('Dictionary', className='nav-item-small'),
                    html.Div('MCDM Dict', className='nav-item-small'),
                    html.Div('Ask AI', className='nav-item-small'),
                ], style={'marginTop': '20px'})
            ], style={'padding': '0 20px 20px 20px', 'width': '240px'})
        ], id='sidebar-content', style={'opacity': 1, 'transition': 'opacity 0.2s'})
    ], id='sidebar', style={
        'position': 'fixed', 'left': 0, 'top': 0, 'bottom': 0, 'width': '240px', 
        'background': '#2d1b4e', 'overflowX': 'hidden', 'overflowY': 'auto', 'zIndex': 1000, 'transition': 'width 0.3s ease'
    }),
    
    # Main Content
    html.Div([
        # Top Utility Bar
        html.Div([
            # Date Filter "Pill" inside the bar
            html.Div([
                dcc.DatePickerRange(
                    id='date-picker',
                    start_date='2023-01-01',
                    end_date='2023-03-31',
                    display_format='MMM D, YYYY',
                    style={'backgroundColor': 'transparent', 'border': 'none', 'color': 'white'}
                )
            ], style={
                'display': 'flex', 'alignItems': 'center', 'border': '1px solid rgba(255,255,255,0.4)', 
                'borderRadius': '20px', 'padding': '2px 12px', 'backgroundColor': 'rgba(255,255,255,0.1)'
            })
        ], style={
            'height': '60px', 'backgroundColor': '#2d1b4e', 'display': 'flex', 'alignItems': 'center', 
            'justifyContent': 'flex-end', 'padding': '0 30px', 'marginBottom': '25px',
            'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'
        }),
        
        # Responsive Layout Container
        html.Div([
            # Left Column (55%)
            html.Div([
                # Metrics Container
                html.Div(id='metrics-container', style={'marginBottom': '20px'}),
                
                # Chart
                html.Div([
                    html.Div([
                        html.Div([
                            # Dynamic Title ID
                            html.H3(id='graph-title', children='Channel Trends', style={'fontSize': '15px', 'fontWeight': '700', 'color': '#1e293b', 'margin': 0}),
                        ], style={'flex': 1}),
                        
                        html.Div([
                            # Aggregation
                            dcc.Dropdown(
                                id='aggregation-level',
                                options=[{'label': 'Daily', 'value': 'daily'}, {'label': 'Monthly', 'value': 'monthly'}],
                                value='monthly',
                                clearable=False,
                                style={'width': '85px', 'fontSize': '12px', 'marginRight': '5px'}
                            ),
                            
                            # Graph Date Picker (Text-like Button)
                            html.Div([
                                dcc.DatePickerRange(
                                    id='graph-date-picker',
                                    start_date='2023-01-01', end_date='2023-12-31',
                                    display_format='MMM D, YYYY',
                                    className='graph-date-picker-custom' 
                                )
                            ], style={'marginRight': '5px'}),
                            
                            dcc.RadioItems(
                                id='chart-view-mode',
                                options=[{'label': 'Compare', 'value': 'compare'}, {'label': 'Total', 'value': 'total'}],
                                value='compare',
                                labelStyle={'display': 'inline-block', 'marginLeft': '6px', 'fontSize': '12px'},
                                inputStyle={'marginRight': '2px'},
                                style={'marginRight': '5px', 'whiteSpace': 'nowrap'}
                            ),
                            dcc.Dropdown(
                                id='chart-metric',
                                options=[{'label': m, 'value': m} for m in ['Spend', 'Impressions', 'Clicks', 'Conversions', 'VideoViews', 'CTR', 'CPC', 'CPM', 'ConvRate']],
                                value='Spend',
                                clearable=False,
                                style={'width': '100px', 'fontSize': '12px'}
                            )
                        ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'justifyContent': 'flex-end'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'paddingBottom': '10px', 'borderBottom': '1px solid #f1f5f9', 'flexWrap': 'wrap'}),
                    
                    html.Div(
                        dcc.Graph(
                            id='main-chart', 
                            config={'displayModeBar': False, 'responsive': True}, 
                            style={'height': '400px', 'width': '100%'}
                        ),
                        style={'minWidth': '0', 'flex': '1', 'overflow': 'hidden', 'height': '400px'}
                    )
                ], style={'background': 'white', 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.04)', 'border': '1px solid #e2e8f0'})
            ], className='left-column'),
            
            # Right Column (45%)
            html.Div([
                # Channel Table
                html.Div([
                    create_table_header('Channel Performance'),
                    html.Div(id='channel-table')
                ], style={'background': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.04)', 'border': '1px solid #e2e8f0', 'marginBottom': '15px'}),
                
                # Source Table
                html.Div([
                    create_table_header('Data Source Performance'),
                    html.Div(id='source-table')
                ], style={'background': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.04)', 'border': '1px solid #e2e8f0', 'marginBottom': '15px'}),
                
                # Campaign Table
                html.Div([
                    create_table_header('Campaign Performance'),
                    html.Div(id='campaign-table')
                ], style={'background': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.04)', 'border': '1px solid #e2e8f0'})
            ], className='right-column')
            
        ], className='responsive-container', style={'display': 'flex', 'marginBottom': '30px', 'gap': '20px', 'flexWrap': 'wrap', 'alignItems': 'flex-start', 'padding': '0 30px'})
        
    ], id='main-content', style={'marginLeft': '240px', 'padding': '0', 'background': '#f8f9fc', 'minHeight': '100vh', 'transition': 'margin-left 0.3s ease'}),
    
], style={'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'})

# --- CALLBACKS ---

@app.callback(
    [Output('sidebar', 'style'), Output('main-content', 'style'), Output('sidebar-content', 'style'), Output('sidebar-toggle', 'children')],
    Input('sidebar-toggle', 'n_clicks'), prevent_initial_call=True
)
def toggle_sidebar(n_clicks):
    is_collapsed = n_clicks % 2 == 1
    width, margin = ('50px', '50px') if is_collapsed else ('240px', '240px')
    content_style = {'opacity': 0 if is_collapsed else 1, 'transition': 'opacity 0.2s', 'pointerEvents': 'none' if is_collapsed else 'auto'}
    arrow = '»' if is_collapsed else '«'
    
    sidebar_style = {'position': 'fixed', 'left': 0, 'top': 0, 'bottom': 0, 'width': width, 'background': '#2d1b4e', 'overflowX': 'hidden', 'overflowY': 'auto', 'zIndex': 1000, 'transition': 'width 0.3s ease'}
    main_style = {'marginLeft': margin, 'padding': '0', 'background': '#f8f9fc', 'minHeight': '100vh', 'transition': 'margin-left 0.3s ease'}
    return sidebar_style, main_style, content_style, arrow

@app.callback(
    [Output('metrics-container', 'children'), Output('channel-table', 'children'), Output('source-table', 'children'), Output('campaign-table', 'children')],
    [Input('date-picker', 'start_date'), Input('date-picker', 'end_date')]
)
def update_metrics(start_date, end_date):
    start, end = pd.to_datetime(start_date), pd.to_datetime(end_date)
    df_cur = df[(df['Date'] >= start) & (df['Date'] <= end)].copy()
    
    prev_start = start - timedelta(days=(end - start).days + 1)
    df_prev = df[(df['Date'] >= prev_start) & (df['Date'] <= start - timedelta(days=1))].copy()
    
    def calc_metrics(d):
        imps, clicks, spend, conv = d['Impressions'].sum(), d['Clicks'].sum(), d['Spend'].sum(), d['Conversions'].sum()
        return {'Spend': spend, 'Impressions': imps, 'Conversions': conv, 'Clicks': clicks, 'VideoViews': clicks*0.7,
                'CPM': (spend/imps*1000) if imps else 0, 'CTR': (clicks/imps*100) if imps else 0,
                'CPC': (spend/clicks) if clicks else 0, 'ConvRate': (conv/clicks*100) if clicks else 0}
    
    curr, prev = calc_metrics(df_cur), calc_metrics(df_prev)
    changes = {k: ((curr[k]-prev[k])/prev[k]*100) if prev[k] else 0 for k in curr}
    
    daily_stats = df_cur.groupby('Date').agg({'Spend': 'sum', 'Impressions': 'sum', 'Clicks': 'sum', 'Conversions': 'sum'}).reset_index()
    daily_stats['VideoViews'] = daily_stats['Clicks'] * 0.7
    daily_stats['CPM'] = (daily_stats['Spend'] / daily_stats['Impressions'] * 1000).fillna(0)
    daily_stats['CTR'] = (daily_stats['Clicks'] / daily_stats['Impressions'] * 100).fillna(0)
    daily_stats['CPC'] = (daily_stats['Spend'] / daily_stats['Clicks']).fillna(0)
    daily_stats['ConvRate'] = (daily_stats['Conversions'] / daily_stats['Clicks'] * 100).fillna(0)
    
    def get_spark(metric): return daily_stats[metric].tolist() if metric in daily_stats.columns else []
    
    metrics = html.Div([
        html.Div([create_metric_card(k, (format_currency(curr[k]) if k in ['Spend','CPM','CPC'] else (format_percent(curr[k]) if k in ['CTR','ConvRate'] else format_number(curr[k]))), f"{changes[k]:+.1f}%", changes[k], get_spark(k))]) for k in ['Spend','CPM','CTR','CPC','VideoViews','Impressions','Conversions','ConvRate']
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'})
    
    # Tables
    def make_table(group, limit=None):
        stats = df_cur.groupby(group).agg({'Impressions':'sum','Clicks':'sum','Spend':'sum'}).reset_index()
        stats_prev = df_prev.groupby(group).agg({'Impressions':'sum','Clicks':'sum'}).reset_index()
        stats['CTR'] = (stats['Clicks']/stats['Impressions']*100).round(2)
        stats['% Δ'] = (stats['Impressions']/stats['Impressions'].sum()*100).round(1)
        
        stats_prev['CTR_prev'] = (stats_prev['Clicks']/stats_prev['Impressions']*100)
        stats = stats.merge(stats_prev[[group, 'CTR_prev']], on=group, how='left')
        stats['CTR_delta'] = stats.apply(lambda x: ((x['CTR']-x['CTR_prev'])/x['CTR_prev']*100) if pd.notna(x['CTR_prev']) and x['CTR_prev'] else 0, axis=1).round(1)
        
        if group == 'Channel': 
            stats['Channel'] = pd.Categorical(stats['Channel'], categories=CHANNEL_ORDER, ordered=True)
            stats = stats.sort_values('Channel')
        else:
            stats = stats.sort_values('Impressions', ascending=False)
        
        if limit: stats = stats.head(limit)
        
        cols = [{'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.0f' if c=='Impressions' else '.1f'}} for c in [group, 'Impressions', '% Δ', 'CTR', 'CTR Δ']]
        cols[-1]['id'] = 'CTR_delta'
        
        return dash_table.DataTable(
            data=stats.to_dict('records'), columns=cols,
            sort_action='native',
            sort_mode='single',
            cell_selectable=False,
            style_table={'overflowX': 'auto', 'width': '100%'},
            style_cell={'textAlign': 'left', 'padding': '5px 10px', 'fontSize': '12px', 'fontFamily': 'inherit', 'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal', 'borderBottom': '1px solid #f1f5f9'},
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold', 'color': '#1e293b', 'borderBottom': '2px solid #e2e8f0', 'fontSize': '12px'},
            style_data={'backgroundColor': 'white', 'color': '#475569', 'border': 'none', 'borderBottom': '1px solid #f1f5f9'},
            style_data_conditional=[
                *generate_heatmap_styles(stats, 'Impressions'),
                *generate_heatmap_styles(stats, 'CTR'),
                {'if': {'filter_query': '{CTR_delta} > 0', 'column_id': 'CTR_delta'}, 'color': '#10b981', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{CTR_delta} < 0', 'column_id': 'CTR_delta'}, 'color': '#ef4444', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{% Δ} > 0', 'column_id': '% Δ'}, 'color': '#10b981', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{% Δ} < 0', 'column_id': '% Δ'}, 'color': '#ef4444', 'fontWeight': 'bold'}
            ]
        )

    return metrics, make_table('Channel'), make_table('Source', 8), make_table('Campaign', 10)

@app.callback(
    [Output('main-chart', 'figure'), Output('graph-title', 'children')],
    [Input('graph-date-picker', 'start_date'), Input('graph-date-picker', 'end_date'), Input('aggregation-level', 'value'), Input('chart-metric', 'value'), Input('chart-view-mode', 'value')]
)
def update_chart(start_date, end_date, agg, metric, mode):
    start, end = pd.to_datetime(start_date), pd.to_datetime(end_date)
    d = df[(df['Date'] >= start) & (df['Date'] <= end)].copy()
    
    if agg == 'monthly': d['Date'] = d['Date'].dt.to_period('M').dt.to_timestamp()
    
    grp = ['Date', 'Channel'] if mode == 'compare' else ['Date']
    data = d.groupby(grp).agg({'Spend':'sum','Impressions':'sum','Clicks':'sum','Conversions':'sum'}).reset_index()
    
    data['CPM'] = data['Spend']/(data['Impressions']+1e-9)*1000
    data['CTR'] = data['Clicks']/(data['Impressions']+1e-9)*100
    data['CPC'] = data['Spend']/(data['Clicks']+1e-9)
    data['ConvRate'] = data['Conversions']/(data['Clicks']+1e-9)*100
    data['VideoViews'] = data['Clicks']*0.7
    
    fig = go.Figure()
    colors = {'Paid Search': '#ec4899', 'Paid Social': '#3b82f6', 'Programmatic': '#8b5cf6', 'Organic': '#f97316'}
    
    if mode == 'compare':
        for ch in CHANNEL_ORDER:
            cd = data[data['Channel'] == ch]
            if not cd.empty:
                fig.add_trace(go.Scatter(x=cd['Date'], y=cd[metric], name=ch, mode='lines', line=dict(width=2.5, color=colors.get(ch,'#333'))))
        title = "Channel Trends"
    else:
        fig.add_trace(go.Scatter(x=data['Date'], y=data[metric], name='Total', mode='lines', line=dict(width=3, color='#0f172a'), fill='tozeroy', fillcolor='rgba(15, 23, 42, 0.05)'))
        title = "Total Trends"
        
    fig.update_layout(
        height=400, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center')
    )
    return fig, title

# --- CSS INJECTION ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { margin: 0; padding: 0; background-color: #f8f9fc; }
            
            /* Sidebar styling */
            .nav-item { padding: 8px 15px; color: #b8a9d1; cursor: pointer; border-radius: 6px; margin-bottom: 2px; font-size: 13px; transition: all 0.2s; }
            .nav-item:hover { background: rgba(255, 255, 255, 0.1); color: white; }
            .nav-item-active { background: rgba(255, 255, 255, 0.15); color: white; font-weight: 600; }
            .nav-item-small { padding: 6px 15px; color: #b8a9d1; cursor: pointer; font-size: 12px; margin-bottom: 2px; }
            .nav-item-small:hover { color: white; }
            
            /* Columns Layout - Flexbox Gap Logic */
            .responsive-container { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start; }
            
            /* Calculate width considering gap. 55% of (100% - 20px gap) */
            .left-column { flex: 1 1 calc(55% - 10px); min-width: 400px; }
            .right-column { flex: 1 1 calc(45% - 10px); min-width: 350px; }
            
            @media (max-width: 1000px) {
                .left-column, .right-column { flex: 1 1 100%; }
            }
            
            /* Top Date Picker (Pill Style) */
            .DateInput { background-color: transparent !important; width: 90px; }
            .DateInput_input { background-color: transparent !important; color: white !important; border-bottom: none !important; font-size: 13px !important; font-weight: 600; padding: 0 !important; text-align: center; }
            .DateRangePickerInput { background-color: transparent !important; border: none !important; }
            
            /* Graph Date Picker Override (Text Button Style) */
            .graph-date-picker-custom .DateInput { width: 100px; }
            .graph-date-picker-custom .DateInput_input { color: #475569 !important; font-size: 12px !important; font-weight: 600; text-align: center; background-color: #f1f5f9 !important; border-radius: 4px; padding: 4px 0 !important; }
            .graph-date-picker-custom .DateRangePickerInput_arrow_svg { display: none; } /* Hide arrow svg */
            .graph-date-picker-custom .DateRangePickerInput_arrow { display: inline-block; padding: 0 5px; color: #475569; font-weight: bold; }
            .graph-date-picker-custom .DateRangePickerInput_arrow:after { content: "-"; } /* Replace with hyphen */
            
            .DateRangePickerInput_clearDates { display: none; }
        </style>
        <script>
            window.addEventListener('load', function() {
                setTimeout(function() {
                    window.dispatchEvent(new Event('resize'));
                }, 150);
            });
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, port=8050)
    
