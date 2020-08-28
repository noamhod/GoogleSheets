from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1FqirnoEGIWUxcUnxq45wKLXSQWCV5_NrGN2_ovVCwr4'
SAMPLE_RANGE_NAME = 'Beam!A1:E'

DICT_SAMPLE_RANGE_NAME = {
   'Constants':'A1:E',
   'Beam':'A1:E',
   'Laser':'A1:D',
   'Targets':'A1:F',
   'IP chamber':'A1:F',
   'Magnets':'A1:F',
   'Tracker':'A1:G',
}

def get(service,sheetid,sheetrange,doprint=True):
   # Call the Sheets API
   sheet = service.spreadsheets()
   result = sheet.values().get(spreadsheetId=sheetid, range=sheetrange).execute()
   values = result.get('values', [])
   if not values: print('No data found.')
   else:
      print("\n--------- Sheet:",sheetrange)
      for row in values: print(row)
   return values


def main():
   """Shows basic usage of the Sheets API. Prints values from a sample spreadsheet."""
   creds = None
   # The file token.pickle stores the user's access and refresh tokens, and is
   # created automatically when the authorization flow completes for the first
   # time.
   if os.path.exists('token.pickle'):
      with open('token.pickle', 'rb') as token:
         creds = pickle.load(token)
   # If there are no (valid) credentials available, let the user log in.
   if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
         creds.refresh(Request())
      else:
         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
         creds = flow.run_local_server(port=0)
         # Save the credentials for the next run
         with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

   service = build('sheets', 'v4', credentials=creds)
   # data = get(service,SAMPLE_SPREADSHEET_ID,SAMPLE_RANGE_NAME)

   for sheetname,rangename in DICT_SAMPLE_RANGE_NAME.items():
      sheetrange = sheetname+"!"+rangename
      data = get(service,SAMPLE_SPREADSHEET_ID,sheetrange)

if __name__ == '__main__':
    main()
