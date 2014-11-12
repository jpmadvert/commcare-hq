from jsonobject.api import JsonObject
from jsonobject.properties import StringProperty, BooleanProperty, DecimalProperty, ListProperty
import requests
from corehq.apps.commtrack.models import SupplyPointCase
from custom.api.utils import EndpointMixin

class MigrationException(Exception):
    pass


class Product(JsonObject):
    name = StringProperty()
    units = StringProperty()
    sms_code = StringProperty()
    description = StringProperty()
    is_active = BooleanProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            name=json_rep['name'],
            units=json_rep['units'],
            sms_code=json_rep['sms_code'],
            description=json_rep['description'],
            is_active=json_rep['is_active']
        )

    def __repr__(self):
        return str(self.__dict__)


class ILSUser(JsonObject):
    username = StringProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    email = StringProperty()
    password = StringProperty()
    is_staff = BooleanProperty()
    is_active = BooleanProperty()
    is_superuser = BooleanProperty()
    last_login = StringProperty()
    date_joined = StringProperty()
    location = DecimalProperty()
    supply_point = DecimalProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            username=json_rep['username'],
            first_name=json_rep['first_name'],
            last_name=json_rep['last_name'],
            email=json_rep['email'],
            password=json_rep['password'],
            is_staff=json_rep['is_staff'],
            is_active=json_rep['is_active'],
            is_superuser=json_rep['is_superuser'],
            last_login=json_rep['last_login'],
            date_joined=json_rep['date_joined'],
            location=json_rep['location'],
            supply_point=json_rep['supply_point']
        )

    def __repr__(self):
        return str(self.__dict__)


class SMSUser(JsonObject):
    id = DecimalProperty()
    name = StringProperty()
    role = StringProperty()
    is_active = StringProperty()
    supply_point = DecimalProperty()
    email = StringProperty()
    phone_numbers = ListProperty()
    backend = StringProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            id=json_rep['id'],
            name=json_rep['name'],
            role=json_rep['role'],
            is_active=json_rep['is_active'],
            supply_point=json_rep['supply_point'],
            email=json_rep['email'],
            phone_numbers=json_rep['phone_numbers'],
            backend=json_rep['backend']
        )

    def __repr__(self):
        return str(self.__dict__)


class Location(JsonObject):
    id = DecimalProperty()
    name = StringProperty()
    location_type = StringProperty()
    parent = DecimalProperty()
    latitude = StringProperty()
    longitude = StringProperty()
    code = StringProperty()
    groups = ListProperty()
    historical_groups = ListProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            id=json_rep['id'],
            name=json_rep['name'],
            location_type=json_rep['type'],
            parent=json_rep['parent_id'],
            latitude=json_rep['latitude'],
            longitude=json_rep['longitude'],
            code=json_rep['code'],
            groups=json_rep['groups'],
            historical_groups=json_rep.get('historical_groups')
        )

    def __repr__(self):
        return str(self.__dict__)


class ProductStock(JsonObject):
    supply_point_id = DecimalProperty()
    quantity = DecimalProperty()
    product_code = StringProperty()
    last_modified = StringProperty()
    auto_monthly_consumption = DecimalProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            supply_point_id=json_rep['supply_point'],
            quantity=json_rep['quantity'],
            product_code=json_rep['product'],
            last_modified=json_rep['last_modified'],
            auto_monthly_consumption=json_rep['auto_monthly_consumption']
        )

    def __repr__(self):
        return str(self.__dict__)


class StockTransaction(JsonObject):
    beginning_balance = DecimalProperty()
    date = StringProperty()
    ending_balance = DecimalProperty()
    product_code = StringProperty()
    quantity = DecimalProperty()
    report_type = StringProperty()
    supply_point_id = DecimalProperty()

    @classmethod
    def from_json(cls, json_rep):
        return cls(
            beginning_balance=json_rep['beginning_balance'],
            date=json_rep['date'],
            ending_balance=json_rep['ending_balance'],
            product_code=json_rep['product'],
            quantity=json_rep['quantity'],
            report_type=json_rep['report_type'],
            supply_point_id=json_rep['supply_point']
        )

    def __repr__(self):
        return str(self.__dict__)


class ILSGatewayEndpoint(EndpointMixin):

    models_map = {
        'product': Product,
        'webuser': ILSUser,
        'smsuser': SMSUser,
        'location': Location,
        'product_stock': ProductStock,
        'stock_transaction': StockTransaction
    }

    def __init__(self, base_uri, username, password):
        self.base_uri = base_uri.rstrip('/')
        self.username = username
        self.password = password
        self.products_url = self._urlcombine(self.base_uri, '/products/')
        self.webusers_url = self._urlcombine(self.base_uri, '/webusers/')
        self.smsusers_url = self._urlcombine(self.base_uri, '/smsusers/')
        self.locations_url = self._urlcombine(self.base_uri, '/locations/')
        self.productstock_url = self._urlcombine(self.base_uri, '/productstocks/')
        self.stocktransactions_url = self._urlcombine(self.base_uri, '/stocktransactions/')

    def get_objects(self, url, params=None, filters=None, limit=1000, offset=0, **kwargs):
        params = params if params else {}
        if filters:
            params.update(filters)

        params.update({
            'limit': limit,
            'offset': offset
        })

        if 'next_url_params' in kwargs and kwargs['next_url_params']:
            url = url + "?" + kwargs['next_url_params']
            params = {}

        response = requests.get(url, params=params,
                                auth=self._auth())
        if response.status_code == 200 and 'objects' in response.json():
            meta = response.json()['meta']
            objects = response.json()['objects']
        elif response.status_code == 401:
            raise MigrationException('Invalid credentials.')
        else:
            raise MigrationException('Something went wrong during migration.')

        return meta, objects

    def _get_location_id(self, facility, domain):
        sp = SupplyPointCase.view('hqcase/by_domain_external_id',
                                  key=[domain, str(facility)],
                                  reduce=False,
                                  include_docs=True).first()
        return sp.location_id

    def get_products(self, **kwargs):
        meta, products = self.get_objects(self.products_url, **kwargs)
        for product in products:
            yield self.models_map['product'].from_json(product)

    def get_webusers(self, **kwargs):
        meta, users = self.get_objects(self.webusers_url, **kwargs)
        for user in users:
            yield self.models_map['webuser'].from_json(user)

    def get_smsusers(self, **kwargs):
        meta, users = self.get_objects(self.smsusers_url, **kwargs)
        return meta, [self.models_map['smsuser'].from_json(user) for user in users]

    def get_location(self, id, params=None):
        response = requests.get(self.locations_url + str(id) + "/", params=params, auth=self._auth())
        return response.json()

    def get_locations(self, **kwargs):
        meta, locations = self.get_objects(self.locations_url, **kwargs)
        return meta, [self.models_map['location'].from_json(location) for location in locations]

    def get_productstocks(self, **kwargs):
        meta, product_stocks = self.get_objects(self.productstock_url, **kwargs)
        return meta, [self.models_map['product_stock'].from_json(product_stock) for product_stock in product_stocks]

    def get_stocktransactions(self, **kwargs):
        meta, stock_transactions = self.get_objects(self.stocktransactions_url, **kwargs)
        return meta, [self.models_map['stock_transaction'].from_json(stock_transaction)
                      for stock_transaction in stock_transactions]
