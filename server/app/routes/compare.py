from fastapi import APIRouter, HTTPException
from server.app.database import get_db_connection
from server.app.utils import predict_future_prices, load_user_data, load_market_data, match_percentile

router = APIRouter()


# Example Usage:
# db_connection = create_db_connection()  # Replace with actual DB connection
# market_data = load_market_data(db_connection)
# user_data = load_user_data(db_connection)
# percentile_matches = match_percentile(user_data, market_data)
# future_prices = predict_future_prices(market_data)
# print(percentile_matches)
# print(future_prices)


@router.get("/predict-future-prices/")
def get_future_price_predictions():
    try:
        market_data = load_market_data()
        return predict_future_prices(market_data).to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}


@router.get("/percentile-matching/")
def get_percentile_matching():
    try:
        user_data = load_user_data()
        market_data = load_market_data()
        return match_percentile(user_data, market_data)
    except Exception as e:
        return {"error": str(e)}


@router.get("/compare-rates/")
def compare_user_rates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT u.effective_date AS date, u.origin, u.destination, u.price AS user_price, u.annual_volume,
                   a.min_price, a.percentile_10_price, a.median_price, a.percentile_90_price, a.max_price
            FROM users_rates u
            JOIN aggregated_market_rates a
            ON u.origin = a.origin AND u.destination = a.destination
            WHERE u.effective_date <= a.date AND u.expiry_date >= a.date
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                "date": row["date"],
                "origin": row["origin"],
                "destination": row["destination"],
                "user_price": row["user_price"],
                "min_price": row["min_price"],
                "percentile_10_price": row["percentile_10_price"],
                "median_price": row["median_price"],
                "percentile_90_price": row["percentile_90_price"],
                "max_price": row["max_price"],
                "potential_savings_min_price": (row["min_price"] - row["user_price"]) * row["annual_volume"],
                "potential_savings_percentile_10_price": (row["percentile_10_price"] - row["user_price"]) * row[
                    "annual_volume"],
                "potential_savings_median_price": (row["median_price"] - row["user_price"]) * row["annual_volume"],
                "potential_savings_percentile_90_price": (row["percentile_90_price"] - row["user_price"]) * row[
                    "annual_volume"],
                "potential_savings_max_price": (row["max_price"] - row["user_price"]) * row["annual_volume"]
            })

        cursor.close()
        conn.close()

        return results
    except Exception as e:
        return {"error": str(e)}
