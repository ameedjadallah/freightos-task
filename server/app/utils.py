from datetime import datetime, timedelta
import pandas as pd
from server.app.database import get_db_connection
import numpy as np
import decimal
from sklearn.linear_model import LinearRegression


def convert_to_mysql_datetime(date_value):
    """Converts an Excel date string to MySQL DATETIME format."""
    if isinstance(date_value, str):
        return datetime.strptime(date_value.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
    elif isinstance(date_value, pd.Timestamp):
        return date_value.to_pydatetime()
    else:
        raise ValueError(f"Unexpected date format: {date_value}")


def import_market_rates(file_path: str):
    """Imports market rates from an Excel file into the database after clearing previous data."""
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        required_columns = {"date", "origin", "destination", "price"}

        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        df["date"] = df["date"].astype(str).apply(convert_to_mysql_datetime)

        conn = get_db_connection()
        if conn is None:
            print("❌ Database connection failed.")
            return

        cursor = conn.cursor()

        # Truncate the market_rates table to remove previous data
        cursor.execute("TRUNCATE TABLE market_rates")
        conn.commit()

        # Insert new market rates
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO market_rates (date, origin, destination, price)
                VALUES (%s, %s, %s, %s)
            """, (row["date"], row["origin"], row["destination"], row["price"]))

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Market rates imported successfully and table cleared before insertion.")

    except Exception as e:
        print(f"❌ Error importing market rates: {e}")


def calculate_aggregated_market_rates():
    """Calculates aggregated market rates after clearing previous data."""
    try:
        conn = get_db_connection()
        if conn is None:
            print("❌ Database connection failed.")
            return

        cursor = conn.cursor(dictionary=True)

        # Clear aggregated market rates table before recalculating
        cursor.execute("TRUNCATE TABLE aggregated_market_rates")
        conn.commit()

        cursor.execute("""
            SELECT date, origin, destination, price
            FROM market_rates
        """)
        market_data = cursor.fetchall()

        df = {}  # Grouping data by (date, origin, destination)
        for row in market_data:
            key = (row['date'], row['origin'], row['destination'])
            price = float(row['price']) if isinstance(row['price'], decimal.Decimal) else row[
                'price']  # Convert Decimal to float

            if key not in df:
                df[key] = []
            df[key].append(price)

        aggregated_results = []
        for (date, origin, destination), prices in df.items():
            prices = np.array(prices, dtype=float)  # Ensure NumPy array is float
            aggregated_results.append({
                "date": date,
                "origin": origin,
                "destination": destination,
                "min_price": float(np.min(prices)),
                "percentile_10_price": float(np.percentile(prices, 10)),
                "median_price": float(np.median(prices)),
                "percentile_90_price": float(np.percentile(prices, 90)),
                "max_price": float(np.max(prices)),
            })

        if aggregated_results:
            cursor.executemany("""
                INSERT INTO aggregated_market_rates
                (date, origin, destination, min_price, percentile_10_price, median_price, percentile_90_price, max_price)
                VALUES (%(date)s, %(origin)s, %(destination)s, %(min_price)s, %(percentile_10_price)s, %(median_price)s, %(percentile_90_price)s, %(max_price)s)
            """, aggregated_results)
            conn.commit()

        cursor.close()
        conn.close()

        print("✅ Aggregated market rates successfully calculated and stored.")

    except Exception as e:
        print(f"❌ Error calculating aggregated market rates: {e}")


def match_closest_percentile(user_price, market_prices):
    # Ensure all values are converted to float
    market_prices = [float(price) for price in market_prices]

    percentiles = {
        "percentile_10": np.percentile(market_prices, 10),
        "percentile_25": np.percentile(market_prices, 25),
        "percentile_50": np.percentile(market_prices, 50),
        "percentile_75": np.percentile(market_prices, 75),
        "percentile_90": np.percentile(market_prices, 90),
    }

    closest_percentile = min(percentiles, key=lambda p: abs(percentiles[p] - float(user_price)))

    return closest_percentile, percentiles[closest_percentile]


def load_market_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT date, origin, destination, min_price, percentile_10_price, median_price, percentile_90_price, max_price FROM aggregated_market_rates")
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data)


def load_user_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_email, origin, destination, effective_date, expiry_date, price, annual_volume FROM users_rates")
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data)


def match_percentile(user_df, market_df):
    results = []
    for _, user_row in user_df.iterrows():
        match = market_df[
            (market_df['origin'] == user_row['origin']) & (market_df['destination'] == user_row['destination'])]
        if not match.empty:
            market_prices = match.iloc[0]
            user_price = user_row['price']

            percentiles = {
                'min_price': market_prices['min_price'],
                'percentile_10_price': market_prices['percentile_10_price'],
                'median_price': market_prices['median_price'],
                'percentile_90_price': market_prices['percentile_90_price'],
                'max_price': market_prices['max_price']
            }

            closest_percentile = min(percentiles.keys(), key=lambda k: abs(percentiles[k] - user_price))

            results.append({
                'user_email': user_row['user_email'],
                'origin': user_row['origin'],
                'destination': user_row['destination'],
                'user_price': user_price,
                'closest_percentile': closest_percentile,
                'closest_price': percentiles[closest_percentile]
            })
    return pd.DataFrame(results)


def predict_future_prices(market_df):
    predictions = []
    market_df['date'] = pd.to_datetime(market_df['date'])
    market_df['timestamp'] = market_df['date'].map(datetime.toordinal)  # Fixed here

    for (origin, destination), group in market_df.groupby(['origin', 'destination']):
        X = group[['timestamp']].values
        y = group['median_price'].values
        if len(X) > 1:
            model = LinearRegression()
            model.fit(X, y)
            future_date = datetime.today() + timedelta(days=30)  # Fixed here
            future_timestamp = np.array([[future_date.toordinal()]])
            predicted_price = model.predict(future_timestamp)[0]
            predictions.append({
                'origin': origin,
                'destination': destination,
                'predicted_date': future_date.strftime('%Y-%m-%d'),
                'predicted_price': predicted_price
            })
    return pd.DataFrame(predictions)
