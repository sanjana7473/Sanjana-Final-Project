import dash
from dash import dcc, html
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import urllib.parse  # for URL encoding the password

# Database connection configuration
user = 'sanjana'
raw_password = 'MyStrongP@ssword123'
password = urllib.parse.quote_plus(raw_password)  # Encode special characters like '@'
host = 'retail-database.mysql.database.azure.com'
port = 3306
database = 'retail_data_new'

# Create database connection
db_connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
engine = create_engine(db_connection_string)

# Read transactions data
df = pd.read_sql("""
    SELECT 
        DATE(purchase_date) as date,
        SUM(spend) as total_spend,
        COUNT(DISTINCT hshd_num) as unique_customers,
        COUNT(*) as transaction_count
    FROM transactions 
    GROUP BY DATE(purchase_date)
    ORDER BY date
""", engine)

# Create Dash app with custom styles
app = dash.Dash(
    __name__,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
    ]
)

# Custom colors
colors = {
    'primary': '#4f46e5',
    'secondary': '#64748b',
    'background': '#f8fafc',
    'text': '#1e293b'
}

# Custom graph layout
graph_layout = {
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'font': {
        'family': 'Inter, sans-serif',
        'color': colors['text']
    },
    'title': {
        'font': {
            'size': 20,
            'color': colors['text'],
            'family': 'Inter, sans-serif'
        }
    },
    'xaxis': {
        'gridcolor': '#f1f5f9',
        'tickfont': {'size': 12}
    },
    'yaxis': {
        'gridcolor': '#f1f5f9',
        'tickfont': {'size': 12}
    }
}

# Calculate key metrics
total_revenue = df['total_spend'].sum()
total_customers = df['unique_customers'].sum()
avg_transaction = df['total_spend'].mean() / df['transaction_count'].mean()

app.layout = html.Div([
    # Navigation bar
    html.Nav(
        html.Div(
            html.H1('Retail Analytics Dashboard',
                    style={'color': colors['text'], 'margin': '0'}),
            style={
                'padding': '1rem',
                'background': 'white',
                'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
                'marginBottom': '2rem'
            }
        )
    ),

    # Main container
    html.Div([
        # Stats cards
        html.Div([
            html.Div([
                html.H3('Total Revenue'),
                html.Div(f'${total_revenue:,.2f}', className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.H3('Total Customers'),
                html.Div(f'{total_customers:,}', className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.H3('Avg Transaction'),
                html.Div(f'${avg_transaction:.2f}', className='stat-value')
            ], className='stat-card')
        ], className='dashboard-grid'),

        # Graphs
        html.Div([
            # Daily Revenue Trend
            html.Div([
                dcc.Graph(
                    figure={
                        'data': [{
                            'x': df['date'],
                            'y': df['total_spend'],
                            'type': 'scatter',
                            'mode': 'lines',
                            'name': 'Revenue',
                            'line': {'color': colors['primary']}
                        }],
                        'layout': {
                            **graph_layout,
                            'title': 'Daily Revenue Trend',
                            'xaxis': {'title': 'Date'},
                            'yaxis': {'title': 'Revenue ($)'}
                        }
                    }
                )
            ], className='card'),

            # Customer Activity
            html.Div([
                dcc.Graph(
                    figure={
                        'data': [{
                            'x': df['date'],
                            'y': df['unique_customers'],
                            'type': 'bar',
                            'name': 'Active Customers',
                            'marker': {'color': colors['primary']}
                        }],
                        'layout': {
                            **graph_layout,
                            'title': 'Daily Active Customers',
                            'xaxis': {'title': 'Date'},
                            'yaxis': {'title': 'Number of Customers'}
                        }
                    }
                )
            ], className='card')
        ], style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
            'gap': '1.5rem',
            'marginTop': '1.5rem'
        })
    ], style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '0 1rem'
    })
], style={'backgroundColor': colors['background'], 'minHeight': '100vh'})

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
