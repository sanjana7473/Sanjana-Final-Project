# Import only necessary libraries
import pandas as pd

# Load your data (ensure paths are correct)
transactions_df = pd.read_csv('400_transactions.csv', nrows=10000)
products_df = pd.read_csv('400_products.csv')
household_df = pd.read_csv('400_households.csv')

# Step 1: Clean the column names by stripping extra spaces
transactions_df.columns = transactions_df.columns.str.strip()
products_df.columns = products_df.columns.str.strip()
household_df.columns = household_df.columns.str.strip()

# Step 2: Rename columns for consistency and clarity
transactions_df.rename(columns={
    'BASKET_NUM                      ': 'BASKET_NUM',
    'HSHD_NUM        ': 'HSHD_NUM',
    'PURCHASE_': 'PURCHASE_DATE',
    'PRODUCT_NUM                     ': 'PRODUCT_NUM',
    '     SPEND': 'SPEND',
    '     UNITS': 'UNITS',
    'STORE_R': 'STORE_REGION',
    '  WEEK_NUM': 'WEEK_NUM',
    'YEAR': 'YEAR'
}, inplace=True)

products_df.rename(columns={
    'PRODUCT_NUM                     ': 'PRODUCT_NUM',
    'DEPARTMENT                ': 'DEPARTMENT',
    'COMMODITY                 ': 'COMMODITY',
    'BRAND_TY': 'BRAND_TYPE',
    'NATURAL_ORGANIC_FLAG': 'NATURAL_ORGANIC_FLAG'
}, inplace=True)

household_df.rename(columns={
    'HSHD_NUM        ': 'HSHD_NUM',
    'L': 'IS_LOYAL',
    'AGE_RANGE                                                                                                                                                                                               ': 'AGE_RANGE',
    'MARITAL': 'MARITAL_STATUS',
    'INCOME_RANGE                                                                                                                                                                                            ': 'INCOME_RANGE',
    'HOMEOWNER': 'HOMEOWNER_STATUS',
    'HSHD_COMPOSITION ': 'HOUSEHOLD_COMPOSITION',
    'HH_SIZE                                                                                                                                                                                                 ': 'HH_SIZE',
    'CHILDREN': 'NUMBER_OF_CHILDREN'
}, inplace=True)

# Step 3: Merge dataframes (transactions with products and households)
transactions_products_df = pd.merge(transactions_df, products_df, on='PRODUCT_NUM', how='left')
transactions_household_df = pd.merge(transactions_products_df, household_df, on='HSHD_NUM', how='left')

# Drop rows with missing values
transactions_household_df.dropna(inplace=True)
products_df.dropna(inplace=True)
household_df.dropna(inplace=True)

# Step 4: Clean and convert 'HH_SIZE' and 'NUMBER_OF_CHILDREN'
transactions_household_df['HH_SIZE'] = transactions_household_df['HH_SIZE'].replace(r'\+', '', regex=True).astype(float)
transactions_household_df['NUMBER_OF_CHILDREN'] = transactions_household_df['NUMBER_OF_CHILDREN'].replace(r'\+', '', regex=True).astype(float)

# Remove rows where 'HH_SIZE' or 'NUMBER_OF_CHILDREN' are missing after conversion
transactions_household_df = transactions_household_df[transactions_household_df['HH_SIZE'].notna()]
transactions_household_df = transactions_household_df[transactions_household_df['NUMBER_OF_CHILDREN'].notna()]

# Save the cleaned datasets to new CSV files
transactions_household_df.to_csv('cleaned_transactions_households.csv', index=False)
products_df.to_csv('cleaned_products.csv', index=False)
household_df.to_csv('cleaned_households.csv', index=False)
