from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine, text
import pandas as pd
import dash
from dash import dcc, html
import urllib.parse
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'bhdbfdbsfuhe8yryr7t47ry7y2984yrg'  

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

# Integrate Dash into Flask
external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap',
    {'href': '/static/css/styles.css', 'rel': 'stylesheet'}
]

dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/', external_stylesheets=external_stylesheets)

@app.route('/household-data')
def household_data():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    sort_column = request.args.get('sort', 'hshd_num')
    sort_order = request.args.get('order', 'asc')
    
    # Build the SQL query with sorting
    query = """
        SELECT t.hshd_num, t.basket_num, t.purchase_date, t.product_num, 
               p.department, p.commodity
        FROM transactions t
        JOIN products p ON t.product_num = p.product_num
        ORDER BY {} {}
    """.format(sort_column, sort_order.upper())
    
    try:
        data = pd.read_sql(query, engine).to_dict('records')
        return render_template('household_data.html', data=data)
    except Exception as e:
        flash('Error loading household data: ' + str(e))
        return redirect(url_for('dashboard'))

# Load data for dashboard
def serve_layout():
    try:
        # Get aggregated transaction data
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

        # Calculate key metrics
        total_revenue = df['total_spend'].sum()
        total_customers = df['unique_customers'].sum()
        avg_transaction = df['total_spend'].mean() / df['transaction_count'].mean()

        if not df.empty:
            return html.Div([
                # Navigation bar
                html.Nav(
                    html.Div([
                        # Left side - Title
                        html.H1('Retail Analytics Dashboard', 
                               style={'color': 'var(--text)', 'margin': '0'}),
                        # Right side - Navigation Links
                        html.Div([
                            html.A('Dashboard', href='/dashboard/', className='nav-link active'),
                            html.A('Upload Data', href='/upload', className='nav-link'),
                            html.A('Search', href='/search', className='nav-link'),
                            html.A('Household Data', href='/household-data', className='nav-link'),
                            html.A('ML Analysis', href='/ml-analysis', className='nav-link'),
                            html.A('Logout', href='/logout', className='nav-link')
                        ], style={
                            'display': 'flex',
                            'gap': '1.5rem',
                            'alignItems': 'center'
                        })
                    ], style={
                        'display': 'flex',
                        'justifyContent': 'space-between',
                        'alignItems': 'center',
                        'padding': '1rem',
                        'background': 'white',
                        'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
                        'marginBottom': '2rem'
                    })
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
                                        'line': {'color': 'var(--primary)'}
                                    }],
                                    'layout': {
                                        'plot_bgcolor': 'white',
                                        'paper_bgcolor': 'white',
                                        'font': {
                                            'family': 'Inter, sans-serif',
                                            'color': 'var(--text)'
                                        },
                                        'title': {
                                            'text': 'Daily Revenue Trend',
                                            'font': {
                                                'size': 20,
                                                'color': 'var(--text)',
                                                'family': 'Inter, sans-serif'
                                            }
                                        },
                                        'xaxis': {
                                            'title': 'Date',
                                            'gridcolor': '#f1f5f9',
                                            'tickfont': {'size': 12}
                                        },
                                        'yaxis': {
                                            'title': 'Revenue ($)',
                                            'gridcolor': '#f1f5f9',
                                            'tickfont': {'size': 12}
                                        }
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
                                        'marker': {'color': 'var(--primary)'}
                                    }],
                                    'layout': {
                                        'plot_bgcolor': 'white',
                                        'paper_bgcolor': 'white',
                                        'font': {
                                            'family': 'Inter, sans-serif',
                                            'color': 'var(--text)'
                                        },
                                        'title': {
                                            'text': 'Daily Active Customers',
                                            'font': {
                                                'size': 20,
                                                'color': 'var(--text)',
                                                'family': 'Inter, sans-serif'
                                            }
                                        },
                                        'xaxis': {
                                            'title': 'Date',
                                            'gridcolor': '#f1f5f9',
                                            'tickfont': {'size': 12}
                                        },
                                        'yaxis': {
                                            'title': 'Number of Customers',
                                            'gridcolor': '#f1f5f9',
                                            'tickfont': {'size': 12}
                                        }
                                    }
                                }
                            )
                        ], className='card')
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
                        'gap': '1.5rem',
                        'marginTop': '1.5rem'
                    }),

                    # End of main container
                ], style={
                    'maxWidth': '1200px',
                    'margin': '0 auto',
                    'padding': '0 1rem'
                })
            ], style={'backgroundColor': 'var(--background)', 'minHeight': '100vh'})
        else:
            return html.Div([
                html.H1('No transaction data available. Please upload transactions first.'),
                html.Br(),
                html.A('Upload New Data', href='/upload'),
                html.Br(),
                html.A('Search Household', href='/search'),
                html.Br(),
                html.A('Logout', href='/logout')
            ])
    except Exception as e:
        return html.Div([
            html.H1('Error loading dashboard!'),
            html.P(str(e))
        ])

dash_app.layout = serve_layout

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        insert_query = text("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)")
        with engine.connect() as connection:
            connection.execute(insert_query, {"username": username, "password": password, "email": email})
            connection.commit()

        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = text("SELECT * FROM users WHERE username=:username AND password=:password")
        with engine.connect() as connection:
            result = connection.execute(query, {"username": username, "password": password})
            user = result.fetchone()

        if user:
            session['username'] = username
            return redirect('/dashboard/')
        else:
            return "Invalid username or password."

    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        table_name = request.form['table_name']
        df_upload = pd.read_csv(file)
        df_upload.columns = df_upload.columns.str.strip().str.lower()  # STRIP SPACES here
         # If transactions table, limit to 10k rows
        if table_name.lower() == 'transactions':
            df_upload = df_upload.head(10000)
        df_upload.to_sql(table_name, engine, if_exists='replace', index=False)
        return f"Table {table_name} uploaded successfully!"

    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        hshd_num = request.form['hshd_num']
        query = text("""
            SELECT *
            FROM households h
            JOIN transactions t ON h.hshd_num = t.hshd_num
            JOIN products p ON t.product_num = p.product_num
            WHERE h.hshd_num = :hshd_num
            ORDER BY h.hshd_num, t.basket_num, t.purchase_date, p.product_num
        """)
        result = pd.read_sql(query, engine, params={"hshd_num": hshd_num})
        return result.to_html()

    return render_template('search.html')

@app.route('/ml-analysis')
def ml_analysis():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Load metrics from JSON files
    try:
        # Check if metrics files exist
        basket_metrics_path = 'static/analytics_data/basket_analysis_metrics.json'
        churn_metrics_path = 'static/analytics_data/churn_prediction_metrics.json'
        clv_metrics_path = 'static/analytics_data/clv_analysis_metrics.json'
        
        # Initialize with default values
        basket_metrics = {}
        churn_metrics = {}
        clv_metrics = {}
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Load metrics if files exist
        if os.path.exists(basket_metrics_path):
            with open(basket_metrics_path, 'r') as f:
                basket_metrics = json.load(f)
                generated_at = basket_metrics.get('generated_at', generated_at)
        
        if os.path.exists(churn_metrics_path):
            with open(churn_metrics_path, 'r') as f:
                churn_metrics = json.load(f)
        
        if os.path.exists(clv_metrics_path):
            with open(clv_metrics_path, 'r') as f:
                clv_metrics = json.load(f)
        
        return render_template('ml_analysis.html', 
                               basket_metrics=basket_metrics, 
                               churn_metrics=churn_metrics, 
                               clv_metrics=clv_metrics,
                               generated_at=generated_at)
    except Exception as e:
        return f"Error loading ML analysis data: {str(e)}"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
