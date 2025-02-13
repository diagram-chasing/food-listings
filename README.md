# Restaurant Menu Scraper

A Python script that extracts and processes restaurant menu data from Zomato.

## Features

- Extracts complete menu data including items, prices, categories, and tags
- Cleans and organizes data into a consistent format
- Combines multiple tag columns (dietary, service, etc.)
- Generates summary statistics
- Exports to CSV

## Example Usage

```bash
python data-scripts/scrape/scraper.py https://www.zomato.com/bangalore/watsons-ulsoor/order watsons.csv
```

## Sample Summary Statistics

```bash
Processed menu data saved to watsons.csv

Menu Summary:
Total items: 103

Items per category:
category
Main Course        46
Appetizers         45
Pasta               6
Burgers & Wraps     5
Desserts            1
Name: count, dtype: int64

Price range by category:
                 min  max    mean
category
Appetizers       155  465  322.33
Burgers & Wraps  265  475  365.00
Desserts         195  195  195.00
Main Course       40  525  259.11
Pasta            275  425  331.67
```
