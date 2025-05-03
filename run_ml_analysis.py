import os
import sys
from ml_analysis import run_basket_analysis, run_churn_prediction, run_clv_analysis
from datetime import datetime

# Print execution header
print("=" * 80)
print("RETAIL ANALYTICS DASHBOARD GENERATOR")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Create output directories if they don't exist
os.makedirs('static/visualizations', exist_ok=True)
os.makedirs('static/analytics_data', exist_ok=True)

# Run all analyses sequentially with timing
start_time = datetime.now()

try:
    # Execute analysis modules
    print("Running basket analysis...")
    basket_metrics = run_basket_analysis()
    
    print("Running churn prediction...")
    churn_metrics = run_churn_prediction()
    
    print("Running CLV analysis...")
    clv_metrics = run_clv_analysis()
    
    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    print(f"✓ All analyses completed in {execution_time:.2f} seconds")
    print(f"✓ Results saved to static/visualizations and static/analytics_data directories")
    print("\nYou can now view the results in the web application at /ml-analysis")
    
except Exception as e:
    print(f"Error running ML analysis: {str(e)}")
    sys.exit(1)