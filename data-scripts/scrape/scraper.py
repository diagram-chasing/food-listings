import json
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
from typing import Dict, List

def clean_column_name(col: str) -> str:
    """Clean column names for better readability"""
    # Remove numeric suffixes from tag columns
    col = re.sub(r'_\d+$', '', col)
    # Remove unnecessary prefixes
    col = col.replace('item_', '')
    # Special handling for specific columns
    if col == 'name':
        return 'item_name'
    return col

def organize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Organize columns in a logical order"""
    # Priority columns that should appear first
    priority_cols = [
        'category', 'item_name', 'price', 'desc', 'dietary_slugs',
        'rating_value', 'rating_total_rating_text', 'item_state',
        'tag_slugs', 'service_slugs'
    ]
    
    # Get existing columns that are in priority list
    existing_priority_cols = [col for col in priority_cols if col in df.columns]
    
    # Get remaining columns
    other_cols = [col for col in df.columns if col not in existing_priority_cols]
    
    # Return reorganized dataframe
    return df[existing_priority_cols + other_cols]

def clean_tag_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Combine multiple tag columns into single columns with comma-separated values"""
    # Identify tag columns
    tag_patterns = {
        'tag_slugs': r'tag_slugs_\d+',
        'service_slugs': r'service_slugs_\d+',
        'dietary_slugs': r'dietary_slugs_\d+'
    }
    
    for new_col, pattern in tag_patterns.items():
        matching_cols = [col for col in df.columns if re.match(pattern, col)]
        if matching_cols:
            # Combine values from all matching columns
            df[new_col] = df[matching_cols].apply(
                lambda x: ', '.join(filter(None, x.dropna())), axis=1
            )
            # Drop original columns
            df.drop(columns=matching_cols, inplace=True)
            
    return df

def extract_menu_data(url: str) -> pd.DataFrame:
    """Extract menu data from the website"""
    # Fetch page content with headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find preloaded state script using string parameter
    script_tag = soup.find('script', string=lambda text: text and '__PRELOADED_STATE__' in text)
    if not script_tag:
        # Try alternative search method
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and '__PRELOADED_STATE__' in script.string:
                script_tag = script
                break
    
    if not script_tag:
        raise ValueError("Preloaded state not found")
    
    # Extract JSON with improved regex
    match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*JSON\.parse\((.*?)\);', script_tag.string)
    if not match:
        raise ValueError("Could not extract JSON data")
    
    json_str = match.group(1)
    preloaded_state = json.loads(json.loads(json_str))
    
    # Get restaurant data
    restaurant_data = preloaded_state['pages']['current']['restaurant']
    restaurant_id = list(restaurant_data.keys())[0]
    menu_data = restaurant_data[restaurant_id]['order']['menuList']['menus']
    
    # Extract items
    all_items = []
    for menu_section in menu_data:
        category_name = menu_section['menu']['name']
        
        for category in menu_section['menu']['categories']:
            for item_data in category['category']['items']:
                # Flatten the item structure
                flat_item = flatten_dict(item_data['item'])
                
                # Add category name
                flat_item['category'] = category_name
                all_items.append(flat_item)
    
    return pd.DataFrame(all_items)

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle list values by creating indexed keys
            for i, item in enumerate(v):
                if isinstance(item, (dict, list)):
                    # Skip complex nested structures in lists
                    continue
                items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, v))
    
    return dict(items)

def process_menu_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process and clean the menu dataframe"""
    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Convert numeric columns
    numeric_cols = ['price', 'rating_value', 'min_price', 'max_price', 'default_price', 'display_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
    
    # Clean up and combine tag columns
    df = clean_tag_columns(df)
    
    # Remove duplicate columns
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Organize columns
    df = organize_columns(df)
    
    # Drop redundant or unnecessary columns
    cols_to_drop = ['fb_slug', 'name_slug', 'item_metadata', 'tracking_dish_type',
                    'item_tag_image', 'tag_images', 'tag_texts', 'tag_objects']
    df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True)
    
    # Sort by category and price
    df = df.sort_values(['category', 'price'])
    
    return df

def save_menu(url: str, output_path: str):
    """Extract menu data, process it, and save to CSV"""
    try:
        # Extract raw data
        print("Extracting menu data...")
        df = extract_menu_data(url)
        
        # Process and clean data
        print("Processing and cleaning data...")
        df = process_menu_data(df)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"\nProcessed menu data saved to {output_path}")
        
        # Print summary statistics
        print("\nMenu Summary:")
        print(f"Total items: {len(df)}")
        print("\nItems per category:")
        print(df['category'].value_counts())
        print("\nPrice range by category:")
        print(df.groupby('category')['price'].agg(['min', 'max', 'mean']).round(2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python script.py <restaurant_url> <output_csv_path>")
        sys.exit(1)
        
    url = sys.argv[1]
    output_path = sys.argv[2]
    save_menu(url, output_path)