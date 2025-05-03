import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # Added seaborn for enhanced visualizations
from sqlalchemy import create_engine
import importlib.util
import sys
import urllib.parse  # For URL encoding database password
from datetime import datetime  # For timestamp formatting
import numpy as np  # For additional data transformations
from matplotlib.colors import LinearSegmentedColormap  # For custom colormaps

# =====================================
# CONFIGURATION AND SETUP
# =====================================

# Create output directory structure
os.makedirs('static/visualizations', exist_ok=True)  
os.makedirs('static/analytics_data', exist_ok=True)  

# Set visualization style globally
sns.set(style="whitegrid")  # Apply seaborn whitegrid style to all plots
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.titlesize': 16,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (12, 9)  # Larger default figure size
})

# Custom color palettes for visualizations
PALETTE_MAIN = ["#2C3E50", "#E74C3C", "#3498DB", "#2ECC71", "#F39C12"]
PALETTE_DIVERGING = ["#3498DB", "#ECF0F1", "#E74C3C"]  # Blue to white to red

# Database connection configuration 
user = 'sanjana'
raw_password = 'MyStrongP@ssword123'
password = urllib.parse.quote_plus(raw_password)  # Encode special characters like '@'
host = 'retail-database.mysql.database.azure.com'
port = 3306
database = 'retail_data_new'

# Create database connection string
db_connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'

# Create SQLAlchemy engine with connection pooling optimization
engine = create_engine(
    db_connection_string,
    echo=False,  # Set to True for debugging SQL queries
    pool_pre_ping=True,  # Verify connections before using from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={"connect_timeout": 30}  # Connection timeout in seconds
)

# =====================================
# UTILITY FUNCTIONS
# =====================================

def load_module_from_path(module_name, file_path):
    """
    Dynamically load a Python module from a file path
    
    Args:
        module_name (str): The name to assign to the loaded module
        file_path (str): Path to the Python file to load
        
    Returns:
        module: The loaded Python module
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def save_metrics(metrics_dict, filename):
    """
    Save analysis metrics to JSON file with timestamping
    
    Args:
        metrics_dict (dict): Dictionary containing metrics to save
        filename (str): Output filename
    """
    # Add timestamp to metrics
    metrics_dict['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Write metrics to file with pretty formatting
    with open(f'static/analytics_data/{filename}', 'w') as f:
        json.dump(metrics_dict, f, indent=4)

def apply_plot_styling(ax, title, xlabel, ylabel):
    """
    Apply consistent styling to matplotlib plots
    
    Args:
        ax (matplotlib.axes): The plot axes to style
        title (str): Plot title
        xlabel (str): X-axis label
        ylabel (str): Y-axis label
    """
    ax.set_title(title, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, linestyle='--', alpha=0.7)
    return ax

# =====================================
# BASKET ANALYSIS MODULE
# =====================================

def run_basket_analysis():
    """
    Analyze shopping basket patterns to identify purchasing behaviors
    
    Returns:
        dict: Key metrics from the basket analysis
    """
    print("➤ Running basket analysis...")
    engine = create_engine(db_connection_string)
    metrics = {}

    # Data acquisition
    transactions = pd.read_sql('SELECT * FROM transactions', engine)
    print(f"   ↳ Loaded {len(transactions)} transaction records")

    # Data cleansing and preprocessing
    transactions['spend'] = pd.to_numeric(transactions['spend'], errors='coerce')
    transactions['units'] = pd.to_numeric(transactions['units'], errors='coerce')
    cleaned_data = transactions.dropna(subset=['spend', 'units'])
    print(f"   ↳ Removed {len(transactions) - len(cleaned_data)} records with missing values")
    transactions = cleaned_data

    # Feature engineering and transformation
    transactions['spend_per_unit'] = transactions['spend'] / transactions['units'].replace(0, 1)
    transactions['high_purchase'] = (transactions['units'] > 3).astype(int)
    transactions['basket_size_category'] = pd.cut(
        transactions['units'], 
        bins=[0, 1, 3, 5, 10, float('inf')],
        labels=['Single', 'Small', 'Medium', 'Large', 'Bulk']
    )

    # Calculate business metrics
    metrics['avg_spend'] = f"${transactions['spend'].mean():.2f}"
    metrics['median_spend'] = f"${transactions['spend'].median():.2f}"  # Added median statistic
    metrics['high_purchase_rate'] = f"{(transactions['high_purchase'].mean() * 100):.1f}%"
    metrics['avg_basket_size'] = f"{transactions['units'].mean():.1f} units"  # New metric

    # Model preparation
    X = transactions[['spend', 'units']]
    y = transactions['high_purchase']

    # Train-Test Split with stratification
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   ↳ Training set: {X_train.shape[0]} records, Test set: {X_test.shape[0]} records")

    # Model training with hyperparameters
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1  # Use all available CPU cores
    )
    clf.fit(X_train, y_train)

    # Model evaluation with comprehensive metrics
    from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
    y_pred = clf.predict(X_test)
    train_accuracy = clf.score(X_train, y_train)
    test_accuracy = clf.score(X_test, y_test)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
    
    metrics['model_accuracy'] = f"{test_accuracy * 100:.1f}%"
    metrics['model_precision'] = f"{precision * 100:.1f}%"
    metrics['model_recall'] = f"{recall * 100:.1f}%"  # New metric
    metrics['model_f1'] = f"{f1 * 100:.1f}%"  # New metric

    # Create enhanced visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Scatter plot with decision boundaries
    h = 0.25  # Step size in the mesh
    x_min, x_max = X['spend'].min() - 1, X['spend'].max() + 1
    y_min, y_max = X['units'].min() - 1, X['units'].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    
    # Create custom colormap
    custom_cmap = LinearSegmentedColormap.from_list("custom", ["#3498DB", "#E74C3C"])
    
    # Plot the decision boundary
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    ax1.contourf(xx, yy, Z, alpha=0.25, cmap=custom_cmap)
    
    # Plot the data points
    scatter = ax1.scatter(
        transactions['spend'], 
        transactions['units'], 
        c=transactions['high_purchase'],
        edgecolor='k', 
        alpha=0.6, 
        cmap=custom_cmap,
        s=50
    )
    
    # Apply styling
    apply_plot_styling(
        ax1, 
        'Purchase Pattern Classification',
        'Customer Spending ($)', 
        'Units Purchased'
    )
    ax1.legend(*scatter.legend_elements(), title="High Volume Purchase")
    
    # Right plot: Distribution of basket sizes
    basket_counts = transactions['basket_size_category'].value_counts().sort_index()
    ax2.bar(
        range(len(basket_counts)),
        basket_counts.values,
        color=PALETTE_MAIN,
        edgecolor='black',
        alpha=0.7
    )
    ax2.set_xticks(range(len(basket_counts)))
    ax2.set_xticklabels(basket_counts.index)
    
    # Apply styling
    apply_plot_styling(
        ax2, 
        'Distribution of Basket Sizes',
        'Basket Size Category', 
        'Number of Transactions'
    )
    
    # Add text annotations on bars
    for i, v in enumerate(basket_counts.values):
        ax2.text(i, v + 10, str(v), ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('static/visualizations/basket_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save analysis artifacts
    save_metrics(metrics, 'basket_analysis_metrics.json')
    print("   ↳ Basket analysis completed successfully")

    return metrics

# =====================================
# CHURN PREDICTION MODULE
# =====================================

def run_churn_prediction():
    """
    Predict customer churn based on purchasing patterns over time
    
    Returns:
        dict: Key metrics from the churn prediction model
    """
    print("➤ Running churn prediction analysis...")
    engine = create_engine(db_connection_string)
    metrics = {}

    # Data acquisition
    transactions = pd.read_sql('SELECT * FROM transactions', engine)
    print(f"   ↳ Loaded {len(transactions)} transaction records for churn analysis")

    # Data preprocessing
    transactions['purchase_date'] = pd.to_datetime(transactions['purchase_date'], errors='coerce')
    transactions['spend'] = pd.to_numeric(transactions['spend'], errors='coerce')
    cleaned_data = transactions.dropna(subset=['purchase_date', 'spend', 'hshd_num'])
    print(f"   ↳ Removed {len(transactions) - len(cleaned_data)} records with missing values")
    transactions = cleaned_data

    # Advanced feature engineering
    # Extract time-based features
    transactions['month'] = transactions['purchase_date'].dt.month
    transactions['day_of_week'] = transactions['purchase_date'].dt.dayofweek
    transactions['week_of_month'] = (transactions['purchase_date'].dt.day - 1) // 7 + 1
    
    # Calculate monthly spending patterns
    monthly_spend = transactions.groupby(['hshd_num', 'month']).agg({
        'spend': 'sum',
        'purchase_date': 'count'  # Count of purchases as frequency
    }).rename(columns={'purchase_date': 'frequency'}).reset_index()
    
    # Pivot for time-series features
    pivot = monthly_spend.pivot(index='hshd_num', columns='month', values='spend').fillna(0)
    freq_pivot = monthly_spend.pivot(index='hshd_num', columns='month', values='frequency').fillna(0)
    
    # Rename columns for clarity
    for col in pivot.columns:
        pivot.rename(columns={col: f'spend_month_{col}'}, inplace=True)
    for col in freq_pivot.columns:
        freq_pivot.rename(columns={col: f'freq_month_{col}'}, inplace=True)
    
    # Merge spending and frequency features
    features = pivot.merge(freq_pivot, left_index=True, right_index=True)
    
    # Create churn definition with business logic
    # Churn defined as 50% or greater reduction in spending from month 7 to month 8
    features['prev_month_spend'] = features['spend_month_7']
    features['current_month_spend'] = features['spend_month_8']
    features['spend_decrease_pct'] = 1 - (features['current_month_spend'] / features['prev_month_spend'].replace(0, 1))
    features['churn_risk'] = (features['spend_decrease_pct'] >= 0.5).astype(int)
    
    # Handle edge cases where previous spending was zero
    features.loc[features['prev_month_spend'] == 0, 'churn_risk'] = 0
    
    # Calculate business metrics
    churn_count = features['churn_risk'].sum()
    total_customers = len(features)
    churn_rate = churn_count / total_customers
    
    metrics['churn_rate'] = f"{churn_rate * 100:.1f}%"
    metrics['at_risk_households'] = str(int(churn_count))
    metrics['total_households'] = str(int(total_customers))
    metrics['retention_rate'] = f"{(1 - churn_rate) * 100:.1f}%"  # New metric

    # Prepare model features - drop derived columns used for churn definition
    X = features.drop(['churn_risk', 'prev_month_spend', 'current_month_spend', 'spend_decrease_pct'], axis=1)
    y = features['churn_risk']

    # Train-Test Split with stratification for imbalanced data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"   ↳ Training set: {X_train.shape[0]} records, Test set: {X_test.shape[0]} records")

    # Model Training with balanced class weights
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=8,
        min_samples_leaf=5,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Model Evaluation
    from sklearn.metrics import (
        classification_report, confusion_matrix, precision_score, 
        recall_score, f1_score, roc_auc_score, precision_recall_curve
    )
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]  # Probability of churn
    
    # Calculate comprehensive metrics
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except:
        auc = 0  # Handle edge case if only one class is present
    
    metrics['model_precision'] = f"{precision * 100:.1f}%"
    metrics['model_recall'] = f"{recall * 100:.1f}%"
    metrics['model_f1'] = f"{f1 * 100:.1f}%"
    metrics['model_auc'] = f"{auc:.2f}"  # New metric

    # Feature importance analysis
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    top_features = feature_importance.head(5)['feature'].tolist()
    metrics['top_churn_indicators'] = ", ".join(top_features)

    # Create enhanced visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Churn distribution with percentages
    churn_counts = features['churn_risk'].value_counts()
    labels = ['Retained', 'Churned']
    sizes = [churn_counts.get(0, 0), churn_counts.get(1, 0)]
    percentages = [100 * s / sum(sizes) for s in sizes]
    
    ax1.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=90, 
        colors=['#2ECC71', '#E74C3C'],
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 14, 'fontweight': 'bold'},
        explode=(0, 0.1)  # Explode the churned slice
    )
    ax1.set_title('Customer Retention vs Churn Distribution', fontweight='bold', pad=20, fontsize=16)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

    # Right plot: Top 5 Features Importance  
    importance_data = feature_importance.head(10)
    bars = ax2.barh(
        range(len(importance_data)), 
        importance_data['importance'],
        color=sns.color_palette("viridis", len(importance_data)),
        alpha=0.8,
        edgecolor='black'
    )
    
    # Add feature names and importance values
    for i, (value, feature) in enumerate(zip(importance_data['importance'], importance_data['feature'])):
        feature_name = feature.replace('_', ' ').title()
        if len(feature_name) > 15:
            feature_name = feature_name[:12] + '...'
        ax2.text(value + 0.01, i, f"{feature_name} ({value:.3f})", va='center')
    
    # Apply styling    
    apply_plot_styling(
        ax2, 
        'Top Churn Prediction Factors',
        'Feature Importance', 
        'Features'
    )
    ax2.set_yticks([])  # Hide y-axis labels since we added them as text
    
    plt.tight_layout()
    plt.savefig('static/visualizations/churn_prediction.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save analysis artifacts
    save_metrics(metrics, 'churn_prediction_metrics.json')
    print("   ↳ Churn prediction analysis completed successfully")

    return metrics

# =====================================
# CUSTOMER LIFETIME VALUE MODULE
# =====================================

def run_clv_analysis():
    """
    Analyze and predict customer lifetime value based on transaction history
    
    Returns:
        dict: Key metrics from the CLV analysis
    """
    print("➤ Running customer lifetime value (CLV) analysis...")
    engine = create_engine(db_connection_string)
    metrics = {}

    # Data acquisition
    transactions = pd.read_sql('SELECT * FROM transactions', engine)
    print(f"   ↳ Loaded {len(transactions)} transaction records for CLV analysis")

    # Data preprocessing with robust error handling
    transactions['spend'] = pd.to_numeric(transactions['spend'], errors='coerce')
    transactions['units'] = pd.to_numeric(transactions['units'], errors='coerce')
    
    # Convert purchase_date to datetime
    transactions['purchase_date'] = pd.to_datetime(transactions['purchase_date'], errors='coerce')
    
    # Handle outliers using IQR method
    Q1_spend = transactions['spend'].quantile(0.25)
    Q3_spend = transactions['spend'].quantile(0.75)
    IQR_spend = Q3_spend - Q1_spend
    
    # Filter outliers and missing values
    cleaned_data = transactions[
        (transactions['spend'] >= Q1_spend - 1.5 * IQR_spend) & 
        (transactions['spend'] <= Q3_spend + 1.5 * IQR_spend)
    ].dropna(subset=['hshd_num', 'spend', 'units', 'purchase_date'])
    
    print(f"   ↳ Removed {len(transactions) - len(cleaned_data)} outliers and records with missing values")
    transactions = cleaned_data

    # Enhanced feature engineering
    # Aggregate customer-level data with multiple metrics
    data = transactions.groupby('hshd_num').agg({
        'spend': ['sum', 'mean', 'count'],
        'units': ['sum', 'mean'],
        'purchase_date': ['min', 'max']
    })
    
    # Flatten the column multi-index
    data.columns = ['_'.join(col).strip() for col in data.columns.values]
    data.reset_index(inplace=True)
    
    # Calculate additional features
    data['avg_spend_per_unit'] = data['spend_sum'] / data['units_sum']
    data['purchase_frequency'] = data['spend_count']
    
    # Calculate recency (days since first purchase)
    data['customer_tenure'] = (data['purchase_date_max'] - data['purchase_date_min']).dt.days
    
    # Replace infinite and NaN values
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    data.fillna({
        'avg_spend_per_unit': data['avg_spend_per_unit'].median(),
        'customer_tenure': data['customer_tenure'].median()
    }, inplace=True)
    
    # CLV can be approximated as: CLV = Annual Revenue × Customer Tenure (in years) × Profit Margin
    # For simplicity, we'll use total spend as CLV proxy
    data['clv'] = data['spend_sum']
    
    # Calculate business metrics
    metrics['avg_clv'] = f"${data['clv'].mean():.2f}"
    metrics['median_clv'] = f"${data['clv'].median():.2f}"
    metrics['max_clv'] = f"${data['clv'].max():.2f}"
    metrics['total_customer_value'] = f"${data['clv'].sum():,.2f}"

    # Segment customers by CLV
    q75, q25 = np.percentile(data['clv'], [75, 25])
    data['clv_segment'] = pd.cut(
        data['clv'], 
        bins=[0, q25, q75, float('inf')],
        labels=['Low Value', 'Medium Value', 'High Value']
    )
    
    segment_counts = data['clv_segment'].value_counts()
    metrics['high_value_customers'] = f"{segment_counts.get('High Value', 0)} ({segment_counts.get('High Value', 0)/len(data)*100:.1f}%)"

    # Prepare model features
    X = data[['units_sum', 'purchase_frequency', 'avg_spend_per_unit', 'customer_tenure']]
    y = data['clv']

    # Train-Test Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   ↳ Training set: {X_train.shape[0]} records, Test set: {X_test.shape[0]} records")

    # Model Training with optimized parameters
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=6,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Model Evaluation with comprehensive metrics
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    metrics['mse'] = f"{mse:.2f}"
    metrics['rmse'] = f"{rmse:.2f}"  # New metric
    metrics['mae'] = f"{mae:.2f}"  # New metric
    metrics['r2_score'] = f"{r2:.2f}"

    # Create feature importance data
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    # Create enhanced visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Actual vs Predicted with confidence intervals
    z = np.polyfit(y_test, y_pred, 1)
    p = np.poly1d(z)
    
    ax1.scatter(
        y_test, 
        y_pred, 
        alpha=0.5, 
        c=np.log1p(y_test),  # Color by actual value (log-scaled)
        cmap='viridis',
        s=50,
        edgecolor='k'
    )
    
    # Add trend line
    test_range = np.linspace(y_test.min(), y_test.max(), 100)
    ax1.plot(test_range, p(test_range), 'r--', linewidth=2)
    
    # Add perfect prediction line
    ax1.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
             'k-', linewidth=1, alpha=0.3)
    
    # Apply styling
    apply_plot_styling(
        ax1, 
        'Actual vs Predicted Customer Lifetime Value',
        'Actual CLV ($)', 
        'Predicted CLV ($)'
    )
    
    # Add metrics annotation
    ax1.text(
        0.05, 0.95, 
        f"R² = {r2:.2f}\nRMSE = {rmse:.2f}\nMAE = {mae:.2f}", 
        transform=ax1.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8),
        verticalalignment='top'
    )
    
    # Right plot: Customer Segments by CLV
    segment_data = data['clv_segment'].value_counts().sort_index()
    colors = ['#E74C3C', '#F39C12', '#2ECC71']  # Red, Orange, Green
    
    wedges, texts, autotexts = ax2.pie(
        segment_data, 
        labels=segment_data.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        textprops={'fontsize': 12, 'fontweight': 'bold'}
    )
    
    # Add segment values
    for i, segment in enumerate(segment_data.index):
        segment_value = data[data['clv_segment'] == segment]['clv'].mean()
        texts[i].set_text(f"{segment}\n(Avg: ${segment_value:.2f})")
    
    ax2.set_title('Customer Value Segmentation', fontweight='bold', pad=20, fontsize=16)
    ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    plt.tight_layout()
    plt.savefig('static/visualizations/clv_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save analysis artifacts
    save_metrics(metrics, 'clv_analysis_metrics.json')
    print("   ↳ Customer lifetime value analysis completed successfully")

    return metrics

# =====================================
# MAIN EXECUTION
# =====================================

if __name__ == "__main__":
    # Print execution header
    print("=" * 80)
    print("RETAIL ANALYTICS DASHBOARD GENERATOR")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all analyses sequentially with timing
    start_time = datetime.now()
    
    # Execute analysis modules
    basket_metrics = run_basket_analysis()
    churn_metrics = run_churn_prediction()
    clv_metrics = run_clv_analysis()
    
    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ All analyses completed in {execution_time:.2f} seconds")
    print(f"✓ Results saved to static/visualizations and static/analytics_data directories")