import io
import chardet
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from server.app.database import get_db_connection

router = APIRouter()


@router.post("/upload-rates/")
def upload_user_rates(file: UploadFile = File(...)):
    """Uploads and saves user rates from CSV/XLSX to the database."""
    try:
        contents = file.file.read()
        file.file.seek(0)  # Reset file pointer

        if file.filename.endswith('.csv'):
            detected_encoding = chardet.detect(contents)['encoding'] or 'utf-8'
            df = pd.read_csv(io.BytesIO(contents), encoding=detected_encoding)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")

        required_columns = {"origin", "destination", "effective_date", "expiry_date", "price", "annual_volume"}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_cols}")

        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed.")

        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO users_rates (user_email, origin, destination, effective_date, expiry_date, price, annual_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('ameed', row["origin"], row["destination"], row["effective_date"], row["expiry_date"], row["price"],
                  row["annual_volume"]))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "File uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
