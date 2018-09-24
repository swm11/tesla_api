from datetime import datetime, timedelta
import requests

from charge import Charge
from climate import Climate
from vehicles import Vehicles
from vehicle_state import VehicleState

TESLA_API_BASE_URL = 'https://owner-api.teslamotors.com/'
TOKEN_URL = TESLA_API_BASE_URL + 'oauth/token'
API_URL = TESLA_API_BASE_URL + 'api/1'

OAUTH_CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
OAUTH_CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'

class ApiClient:
    def __init__(self, email, password):
        self._token = None

        self._email = email
        self._password = password

        self.charge = Charge(self)
        self.climate = Climate(self)
        self.vehicles = Vehicles(self)
        self.vehicle_state = VehicleState(self)

    def _get_new_token(self):
        request_data = {
            'grant_type': 'password',
            'client_id': OAUTH_CLIENT_ID,
            'client_secret': OAUTH_CLIENT_SECRET,
            'email': self._email,
            'password': self._password
        }

        response = requests.post(TOKEN_URL, data=request_data)
        response_json = response.json()

        if 'response' in response_json:
            raise AuthenticationError(response_json['response'])

        return response_json

    def _refresh_token(self, refresh_token):
        request_data = {
            'grant_type': 'refresh_token',
            'client_id': OAUTH_CLIENT_ID,
            'client_secret': OAUTH_CLIENT_SECRET,
            'refresh_token': refresh_token,
        }

        response = requests.post(TOKEN_URL, data=request_data)
        response_json = response.json()

        if 'response' in response_json:
            raise AuthenticationError(response_json['response'])

        return response_json

    def _validate_token(self):
        if not self._token:
            self._token = self._get_new_token()

        expiry_time = timedelta(seconds=self._token["expires_in"])
        expiration_date = datetime.fromtimestamp(self._token["created_at"]) + expiry_time

        if expiration_date <= datetime.utcnow():
            self._token = self._refresh_token(self._token["refresh_token"])
            print(self._token)

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self._token["access_token"]}'
        }

    def get(self, endpoint):
        self._validate_token()

        response = requests.get(f'{API_URL}/{endpoint}', headers=self._get_headers())
        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json['response']

    def post(self, endpoint):
        self._validate_token()

        response = requests.post(f'{API_URL}/{endpoint}', headers=self._get_headers())
        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json['response']


class AuthenticationError(Exception):
    def __init__(self, error):
        super().__init__(f'Authentication to the Tesla API failed: {error}')

class ApiError(Exception):
    def __init__(self, error):
        super().__init__(f'Tesla API call failed: {error}')
