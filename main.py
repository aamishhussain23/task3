from fastapi import FastAPI, Form, HTTPException, Request, Query
from pydantic import BaseModel
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Optional, Dict, Any
import uvicorn

app = FastAPI()

class TokenData(BaseModel):
    token: str
    time: str

# Function to write data to Google Sheet using Google Sheets API.
def write_to_sheet(data: dict, credentials: Credentials):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    spreadsheet_id = '1A8Mpe-dStdBKjc7DIc4WQSWRm-YK2KFB4o7qGVFBcY8'  # Replace with your actual spreadsheet ID
    range_name = 'Sheet1'  # Replace with your actual sheet name and range
    values = [list(data.values())]
    body = {
        'values': values
    }
    result = sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

@app.post("/receive-data/{param:path}")
async def receive_data(
    param: str,
    request: Request,
    token: Optional[str] = Form(None),
    time: Optional[str] = Form(None),
    token_query: Optional[str] = Query(None, alias="token"),
    time_query: Optional[str] = Query(None, alias="time")
):
    # Determine if data is coming in as form data, query parameters, or JSON payload
    if request.headers.get('content-type') == 'application/x-www-form-urlencoded':
        form_data = await request.form()
        data = dict(form_data)
    elif request.headers.get('content-type') == 'application/json':
        data = await request.json()
    else:
        data = dict(request.query_params)

    # Add token and time to the data
    data['token'] = token or token_query
    data['time'] = time or time_query
    data['param'] = param

    # Prepare the row data
    row_data = {
        "Order Code": 123456789,
        "Ticker": data.get("param", ""),
        "Sale Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Customer Name": data.get("Customer Name", "Unknown"),
        "Gender": data.get("Gender", "Unknown"),
        "City": data.get("City", "Unknown"),
        "Order Amount": data.get("Order Amount", "0"),
        "Token": data.get("token", "None"),
        "Time": data.get("time", "None")
    }

    # Load the credentials
    creds = Credentials(token=data['token'])
    print(creds)
    # Write the row data to the sheet
    try:
        write_to_sheet(row_data, creds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return row_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
