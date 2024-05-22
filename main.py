from fastapi import FastAPI, HTTPException, Request, Form, Query, Body, APIRouter
from pydantic import BaseModel
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Optional, Dict
import uvicorn

app = FastAPI()

class TokenData(BaseModel):
    token: str
    time: str

def write_to_sheet(data: dict, credentials: Credentials):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    spreadsheet_id = '1A8Mpe-dStdBKjc7DIc4WQSWRm-YK2KFB4o7qGVFBcY8'
    range_name = 'Sheet1'
    values = [list(data.values())]
    body = {'values': values}
    result = sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

async def extract_data(request: Request, param: str, token: str, time: str) -> Dict:
    # Initialize an empty data dictionary
    data = {'param': param, 'token': token, 'time': time}

    # Determine if data is coming in as form data, query parameters, or JSON payload
    if request.headers.get('content-type') == 'application/x-www-form-urlencoded':
        form_data = await request.form()
        data.update(form_data)
    elif request.headers.get('content-type') == 'application/json':
        json_data = await request.json()
        data.update(json_data)
    else:
        data.update(request.query_params)

    return data

@app.api_route("/receive-data/{param:path}", methods=["GET", "POST", "PATCH"])
async def receive_data(
    param: str,
    request: Request,
    token: Optional[str] = Form(None),
    time: Optional[str] = Form(None),
    token_query: Optional[str] = Query(None, alias="token"),
    time_query: Optional[str] = Query(None, alias="time"),
    json_body: Optional[TokenData] = Body(None)
):
    # Consolidate token and time inputs
    actual_token = token or token_query or (json_body.token if json_body else None)
    actual_time = time or time_query or (json_body.time if json_body else None)

    data = await extract_data(request, param, actual_token, actual_time)

    # Prepare the row data
    row_data = {
        "Order Code": 123456789,
        "Ticker": data.get("param", ""),
        "Sale Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Customer Name": data.get("Customer Name", "Unknown"),
        "Gender": data.get("Gender", "Unknown"),
        "City": data.get("City", "Unknown"),
        "Order Amount": data.get("Order Amount", "0")
    }

    # Load the credentials
    creds = Credentials(token=data['token'])

    # Write the row data to the sheet
    try:
        write_to_sheet(row_data, creds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return row_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
