import pandas as pd
from datetime import datetime, timedelta

def generate_ai_insights(dormant_customers, target_month, df, customer_col, date_col, amount_col, item_col=None, region_col=None):
    """
    Generate AI insights for dormant customers report.
    
    Parameters:
    - dormant_customers: Dictionary of dormant customers
    - target_month: The target month string
    - df: The full DataFrame of all transactions
    - customer_col: Column name for customer
    - date_col: Column name for date
    - amount_col: Column name for amount
    - item_col: Column name for item (optional)
    - region_col: Column name for region (optional)
    
    Returns:
    - Dictionary with insights and recommendations
    """
    insights = []
    recommendations = []
    actions = []
    
    # Basic count insight
    dormant_count = len(dormant_customers)
    if dormant_count > 0:
        total_value = sum(data['total_spent'] for data in dormant_customers.values())
        insights.append(f"You have {dormant_count} customers who haven't ordered since {target_month}.")
    else:
        insights.append("Great job! You don't have any dormant customers from the target month.")
        return {
            "observations": insights,
            "recommendations": ["Continue your excellent customer retention strategies."],
            "actions": ["Analyze what's working well in your customer engagement approach."]
        }
    
    # Segment customers by value
    high_value_customers = {k: v for k, v in dormant_customers.items() if v['total_spent'] >= 1000}
    mid_value_customers = {k: v for k, v in dormant_customers.items() if 500 <= v['total_spent'] < 1000}
    low_value_customers = {k: v for k, v in dormant_customers.items() if v['total_spent'] < 500}
    
    # Value-based insights
    high_value_count = len(high_value_customers)
    mid_value_count = len(mid_value_customers)
    if high_value_count > 0:
        high_value_total = sum(data['total_spent'] for data in high_value_customers.values())
        insights.append(f"There are {high_value_count} high-value dormant customers (${high_value_total:.2f} total lifetime value).")
        
        # Add top high-value customer insight
        if high_value_customers:
            top_customer = max(high_value_customers.items(), key=lambda x: x[1]['total_spent'])
            insights.append(f"Your highest value dormant customer is {top_customer[0]} with ${top_customer[1]['total_spent']:.2f} in lifetime purchases.")
    
    # Trend analysis (comparing to previous period if possible)
    try:
        # Get customer order dates to check for patterns
        customer_order_dates = {}
        for customer, data in dormant_customers.items():
            customer_df = df[df[customer_col] == customer]
            dates = sorted(customer_df[date_col].tolist())
            customer_order_dates[customer] = dates
        
        # Check for seasonal patterns
        months = [d.month for customer in customer_order_dates.values() for d in customer]
        month_counts = pd.Series(months).value_counts()
        if len(month_counts) > 0:
            peak_month = month_counts.idxmax()
            peak_month_name = datetime(2000, peak_month, 1).strftime('%B')
            peak_month_pct = month_counts[peak_month] / sum(month_counts) * 100
            if peak_month_pct > 30:  # If more than 30% of orders are in one month
                insights.append(f"Seasonal Pattern: {peak_month_pct:.1f}% of these dormant customers' previous orders were in {peak_month_name}, suggesting a seasonal purchasing pattern.")
    except Exception as e:
        print(f"Error in trend analysis: {e}")
    
    # Purchase frequency analysis
    try:
        regular_customers = 0
        for customer, dates in customer_order_dates.items():
            if len(dates) >= 3:  # At least 3 orders to detect a pattern
                intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval <= 45:  # Monthly-ish
                    regular_customers += 1
                    
        if regular_customers > 0:
            insights.append(f"Frequency Analysis: {regular_customers} dormant customers previously ordered regularly (avg. interval < 45 days), suggesting they may be ready to order again with the right incentive.")
    except Exception as e:
        print(f"Error in frequency analysis: {e}")
    
    # Product-based insights
    if item_col:
        try:
            # Find the most common last purchased items among dormant customers
            last_items = []
            for customer, data in dormant_customers.items():
                if 'last_order_items' in data and data['last_order_items']:
                    last_items.extend(data['last_order_items'])
            
            if last_items:
                item_counts = pd.Series(last_items).value_counts()
                top_item = item_counts.index[0] if len(item_counts) > 0 else None
                if top_item:
                    item_customers = sum(1 for data in dormant_customers.values() 
                                      if 'last_order_items' in data and 
                                         any(top_item in item for item in data['last_order_items']))
                    if item_customers >= 3:  # At least 3 customers bought this
                        insights.append(f"Product Insight: {item_customers} dormant customers last purchased {top_item}. Consider a targeted promotion for this product line.")
        except Exception as e:
            print(f"Error in product analysis: {e}")
    
    # Region-based insights (if region data available)
    if region_col and region_col in df.columns:
        try:
            regions = []
            for customer in dormant_customers:
                customer_regions = df[df[customer_col] == customer][region_col].unique()
                regions.extend(customer_regions)
            
            if regions:
                region_counts = pd.Series(regions).value_counts()
                top_region = region_counts.index[0] if len(region_counts) > 0 else None
                if top_region:
                    region_pct = region_counts[top_region] / sum(region_counts) * 100
                    if region_pct > 30:  # If more than 30% from one region
                        insights.append(f"Regional Insight: {region_pct:.1f}% of your dormant customers are from {top_region}. Consider a region-specific re-engagement campaign.")
        except Exception as e:
            print(f"Error in region analysis: {e}")
    
    # Generate recommendations based on insights
    if high_value_count > 0:
        recommendations.append(f"Consider a targeted re-engagement campaign for these dormant customers, particularly focusing on your high-value customers who spent over $1000 lifetime.")
        actions.append(f"Send a personalized email to high-value dormant customers (Lifetime Sales > $1000) with a special offer based on their purchase history")
    elif mid_value_count > 0:
        recommendations.append(f"Consider a targeted re-engagement campaign for these dormant customers, particularly focusing on your mid-tier customers who spent over $500 lifetime.")
        actions.append(f"Send a personalized email to mid-tier dormant customers (Lifetime Sales $500-$1000) with a special offer based on their purchase history")
    else:
        recommendations.append(f"Consider a targeted re-engagement campaign for these dormant customers with appropriate incentives based on their purchase history.")
    
    actions.append("Create a \"We miss you\" campaign with a time-limited discount for mid-tier customers ($500-$1000)")
    actions.append("Monitor which re-engagement strategies are most effective to refine future campaigns")
    
    # Recommendation for retention
    today = datetime.now()
    try:
        if dormant_customers:
            earliest_dormant_date = min(data['last_order_date'] for data in dormant_customers.values() if data['last_order_date'] is not None)
            dormant_period = (today - earliest_dormant_date).days
            if dormant_period <= 180:  # Less than 6 months
                recommendations.append(f"Your dormant customers are still within the 6-month reactivation window when they're most likely to return. Act quickly for best results.")
    except Exception as e:
        print(f"Error in retention analysis: {e}")
    
    return {
        "observations": insights,
        "recommendations": recommendations,
        "actions": actions
    }