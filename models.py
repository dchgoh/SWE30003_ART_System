# models.py
import uuid
from datetime import datetime
import hashlib
import json
import os

# --- Helper function for JSON file operations ---
def _load_data(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []
    # Add a check for empty file to prevent JSONDecodeError
    if os.path.getsize(file_path) == 0:
        return []
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: Data in {file_path} is not a list. Initializing as empty.")
                with open(file_path, 'w') as f_reset: json.dump([], f_reset)
                return []
            return data
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {file_path}. Returning empty list.")
            return []

def _save_data(file_path, all_items_data):
    with open(file_path, 'w') as f:
        json.dump(all_items_data, f, indent=4)

# --- File Paths ---
USER_DATA_FILE = 'users.json'
TRIP_DATA_FILE = 'trips.json'
TICKET_DATA_FILE = 'tickets.json'
ORDER_DATA_FILE = 'orders.json'
PAYMENT_DATA_FILE = 'payments.json'
REFUND_DATA_FILE = 'refunds.json'
LOCATION_DATA_FILE = 'locations.json'
STOP_DATA_FILE = 'stops.json'
ROUTE_DATA_FILE = 'routes.json'
FEEDBACK_DATA_FILE = 'feedbacks.json'
RESPONSE_DATA_FILE = 'responses.json'
NOTIFICATION_DATA_FILE = 'notifications.json'


class User:
    FILE_PATH = USER_DATA_FILE

    def __init__(self, username, email, password, user_id=None, is_admin=False, admin_level=None):
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.username = username
        self.email = email
        if password:
            self.password_hash = self._hash_password(password)
        else:
            self.password_hash = None 
        self.is_admin = is_admin
        self.admin_level = admin_level if is_admin else None

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password_to_check):
        if not self.password_hash or not password_to_check:
            return False
        return self.password_hash == self._hash_password(password_to_check)

    def to_dict(self):
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin
        }
        if self.is_admin:
            data['admin_level'] = self.admin_level
        return data
    
    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            print(f"Error: User.from_dict expected dict, got {type(data)}: {data}")
            return None
        user = cls(
            username=data.get('username'), 
            email=data.get('email'), 
            password=None,
            user_id=data.get('user_id'),
            is_admin=data.get('is_admin', False),
            admin_level=data.get('admin_level') if data.get('is_admin') else None
        )
        user.password_hash = data.get('password_hash')
        if not all([user.user_id, user.username, user.email, user.password_hash]):
            # print(f"Warning: User data missing critical fields: {data}") # Can be noisy
            return None # Invalid user object
        return user

    def save(self):
        all_users_data = _load_data(User.FILE_PATH)
        updated = False
        # Check for conflicts before attempting to save if it's a new user (no user_id match)
        is_new_user = True
        for i, user_data_dict in enumerate(all_users_data):
            if user_data_dict.get('user_id') == self.user_id:
                # This is an update
                all_users_data[i] = self.to_dict()
                updated = True
                is_new_user = False
                break
        
        if is_new_user: # Only check for username/email conflict if it's a new user
            for user_data_dict in all_users_data:
                if user_data_dict.get('username') == self.username:
                    print(f"Error: Username '{self.username}' already exists.")
                    return False
                if user_data_dict.get('email') == self.email:
                    print(f"Error: Email '{self.email}' already exists.")
                    return False
            all_users_data.append(self.to_dict())
        elif not updated and not is_new_user: # Should not happen if ID is unique
             print(f"Error: User with ID {self.user_id} not found for update, but not treated as new.")
             return False


        _save_data(User.FILE_PATH, all_users_data)
        return True

    @classmethod
    def find_by_id(cls, user_id_to_find):
        all_users_data = _load_data(User.FILE_PATH)
        for user_data in all_users_data:
            if user_data.get('user_id') == user_id_to_find:
                return cls.from_dict(user_data)
        return None

    @classmethod
    def find_by_username(cls, username_to_find):
        all_users_data = _load_data(User.FILE_PATH)
        for user_data in all_users_data:
            if user_data.get('username') == username_to_find:
                return cls.from_dict(user_data)
        return None
    
    @classmethod
    def get_all(cls):
        all_users_data = _load_data(User.FILE_PATH)
        users = []
        for user_data in all_users_data:
            user_obj = cls.from_dict(user_data)
            if user_obj:
                users.append(user_obj)
        return users


class Admin(User):
    def __init__(self, username, email, password, user_id=None, admin_level="superuser"):
        super().__init__(username, email, password, user_id, is_admin=True, admin_level=admin_level)


# --- Trip Model ---
class Trip:
    FILE_PATH = TRIP_DATA_FILE
    def __init__(self, trip_id, origin, destination, departure_time, price, available_seats):
        self.trip_id = trip_id
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time 
        self.price = price
        self.available_seats = int(available_seats) # Ensure it's an int

    def to_dict(self):
        return {
            'trip_id': self.trip_id, 
            'origin': self.origin, 
            'destination': self.destination, 
            'departure_time': str(self.departure_time), 
            'price': float(self.price), 
            'available_seats': int(self.available_seats)
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['trip_id','origin','destination','departure_time','price','available_seats']):
            print(f"Warning: Trip data missing critical fields or not a dict: {data}")
            return None
        try: # Add type conversion robustness
            return cls(
                trip_id=data['trip_id'],
                origin=data['origin'],
                destination=data['destination'],
                departure_time=data['departure_time'],
                price=float(data['price']),
                available_seats=int(data['available_seats'])
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Trip data: {e}. Data: {data}")
            return None


    def save(self):
        all_data = _load_data(Trip.FILE_PATH)
        updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('trip_id') == self.trip_id:
                all_data[i] = self.to_dict()
                updated = True
                break
        if not updated:
            all_data.append(self.to_dict())
        _save_data(Trip.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Trip.FILE_PATH)
        for item_data in all_data:
            if item_data.get('trip_id') == item_id:
                return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Trip.FILE_PATH)
        items = []
        for item_data in all_data:
            item_obj = cls.from_dict(item_data)
            if item_obj: items.append(item_obj)
        return items
        
    @classmethod
    def search(cls, origin=None, destination=None, date_str=None):
        all_trips = cls.get_all()
        filtered_trips = []
        for trip in all_trips:
            # Ensure trip is not None (could happen if from_dict failed for an entry)
            if not trip: 
                continue 
            match = True
            if origin and origin.lower() not in trip.origin.lower(): match = False
            if destination and destination.lower() not in trip.destination.lower(): match = False
            if date_str and date_str not in trip.departure_time: match = False
            if match and trip.available_seats > 0:
                filtered_trips.append(trip)
        return filtered_trips
        
    def update_seats(self, num_seats, operation="book"):
        if operation == "book":
            if self.available_seats >= num_seats:
                self.available_seats -= num_seats
                return True
            else:
                return False
        elif operation == "refund":
            self.available_seats += num_seats
            return True
        return False # Invalid operation

# --- Payment Model ---
class Payment:
    FILE_PATH = PAYMENT_DATA_FILE
    def __init__(self, order_id, amount, method="MockCard", status="Completed", payment_id=None):
        self.payment_id = payment_id if payment_id else str(uuid.uuid4())
        self.order_id = order_id
        self.amount = float(amount)
        self.method = method
        self.status = status
        self.payment_datetime = datetime.now()

    def to_dict(self):
        return {'payment_id':self.payment_id, 'order_id':self.order_id, 'amount':self.amount, 
                'method':self.method, 'status':self.status, 'payment_datetime':self.payment_datetime.isoformat()}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['order_id','amount','payment_id']):
            print(f"Warning: Payment data missing critical fields or not a dict: {data}")
            return None
        try:
            payment = cls(
                order_id=data.get('order_id'),
                amount=float(data.get('amount')),
                method=data.get('method', "MockCard"),
                status=data.get('status', "Completed"),
                payment_id=data.get('payment_id')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Payment data: {e}. Data: {data}")
            return None

        dt_str = data.get('payment_datetime')
        if dt_str:
            try:
                payment.payment_datetime = datetime.fromisoformat(dt_str)
            except ValueError:
                print(f"Warning: Invalid payment_datetime format for {payment.payment_id}. Using current time.")
                payment.payment_datetime = datetime.now() 
        return payment

    def save(self):
        all_data = _load_data(Payment.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('payment_id') == self.payment_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Payment.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('payment_id') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def find_by_order_id(cls, order_id_to_find):
        all_data = _load_data(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('order_id') == order_id_to_find: return cls.from_dict(item_data)
        return None


# --- Ticket Model ---
class Ticket:
    FILE_PATH = TICKET_DATA_FILE
    def __init__(self, user_id, trip_id, order_id, payment_id, seat_number=None, issue_datetime=None, ticket_id=None, status="Active"):
        self.ticket_id = ticket_id if ticket_id else str(uuid.uuid4())
        self.user_id = user_id
        self.trip_id = trip_id
        self.order_id = order_id
        self.payment_id = payment_id
        self.seat_number = seat_number if seat_number else "Any Available"
        self.issue_datetime = issue_datetime if issue_datetime else datetime.now()
        self.status = status

    def void(self):
        if self.status == "Active":
            self.status = "Voided"
            return True
        return False

    def to_dict(self):
        return {'ticket_id':self.ticket_id,'user_id':self.user_id,'trip_id':self.trip_id,
                'order_id':self.order_id,'payment_id':self.payment_id,'seat_number':self.seat_number,
                'issue_datetime':self.issue_datetime.isoformat(),'status':self.status}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['user_id','trip_id','order_id','payment_id','ticket_id']):
            print(f"Warning: Ticket data missing critical fields or not a dict: {data}")
            return None
        
        ticket = cls(
            user_id=data.get('user_id'), trip_id=data.get('trip_id'), order_id=data.get('order_id'),
            payment_id=data.get('payment_id'), seat_number=data.get('seat_number'),
            ticket_id=data.get('ticket_id'), status=data.get('status', "Active")
        )
        dt_str = data.get('issue_datetime')
        if dt_str:
            try: ticket.issue_datetime = datetime.fromisoformat(dt_str)
            except ValueError: ticket.issue_datetime = datetime.now()
        return ticket

    def save(self):
        all_data = _load_data(Ticket.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('ticket_id') == self.ticket_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Ticket.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Ticket.FILE_PATH)
        for item_data in all_data:
            if item_data.get('ticket_id') == item_id: return cls.from_dict(item_data)
        return None
        
    @classmethod
    def find_by_order_id(cls, order_id_to_find):
        all_data = _load_data(Ticket.FILE_PATH)
        tickets = []
        for item_data in all_data:
            if item_data.get('order_id') == order_id_to_find:
                ticket_obj = cls.from_dict(item_data)
                if ticket_obj: tickets.append(ticket_obj)
        return tickets
        
    @classmethod
    def delete_by_order_id(cls, order_id_to_delete):
        all_data = _load_data(Ticket.FILE_PATH)
        remaining_items = [item for item in all_data if item.get('order_id') != order_id_to_delete]
        if len(remaining_items) < len(all_data): # Check if any were actually removed
            _save_data(Ticket.FILE_PATH, remaining_items)
            return True
        return False


# --- Order Model ---
class Order:
    FILE_PATH = ORDER_DATA_FILE
    def __init__(self, user_id, trip_id, num_tickets, total_amount, order_id=None, status="PendingPayment"):
        self.order_id = order_id if order_id else str(uuid.uuid4())
        self.user_id = user_id
        self.trip_id = trip_id
        self.num_tickets = int(num_tickets)
        self.total_amount = float(total_amount)
        self.order_datetime = datetime.now()
        self.status = status

    def to_dict(self):
        return {'order_id':self.order_id,'user_id':self.user_id,'trip_id':self.trip_id,
                'num_tickets':self.num_tickets,'total_amount':self.total_amount,
                'order_datetime':self.order_datetime.isoformat(),'status':self.status}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['user_id','trip_id','num_tickets','total_amount','order_id']):
            print(f"Warning: Order data missing critical fields or not a dict: {data}")
            return None
        try:
            order = cls(
                user_id=data.get('user_id'), trip_id=data.get('trip_id'),
                num_tickets=int(data.get('num_tickets')), total_amount=float(data.get('total_amount')),
                order_id=data.get('order_id'), status=data.get('status', 'PendingPayment')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Order data: {e}. Data: {data}")
            return None
            
        dt_str = data.get('order_datetime')
        if dt_str:
            try: order.order_datetime = datetime.fromisoformat(dt_str)
            except ValueError: order.order_datetime = datetime.now()
        return order

    def save(self):
        all_data = _load_data(Order.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('order_id') == self.order_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Order.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Order.FILE_PATH)
        for item_data in all_data:
            if item_data.get('order_id') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def find_by_user_id(cls, user_id_to_find):
        all_data = _load_data(Order.FILE_PATH)
        orders = []
        for item_data in all_data:
            if item_data.get('user_id') == user_id_to_find:
                order_obj = cls.from_dict(item_data)
                if order_obj: orders.append(order_obj)
        return orders


# --- Refund Model ---
class Refund:
    FILE_PATH = REFUND_DATA_FILE
    def __init__(self, payment_id, order_id, ticket_id, refund_amount, refund_reason="User requested", refund_id=None, status="Pending"):
        self.refund_id = refund_id if refund_id else str(uuid.uuid4())
        self.payment_id=payment_id; self.order_id=order_id; self.ticket_id=ticket_id; self.refund_amount=float(refund_amount)
        self.refund_reason=refund_reason; self.status=status; self.request_datetime=datetime.now(); self.processed_datetime=None

    def update_status(self, new_status):
        self.status = new_status
        if self.status in ["Processed", "Failed"]: self.processed_datetime = datetime.now()

    def to_dict(self):
        return {'refund_id':self.refund_id,'payment_id':self.payment_id,'order_id':self.order_id,
                'ticket_id':self.ticket_id,'refund_amount':self.refund_amount,'refund_reason':self.refund_reason,
                'status':self.status,'request_datetime':self.request_datetime.isoformat(),
                'processed_datetime':self.processed_datetime.isoformat() if self.processed_datetime else None}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['payment_id','order_id','ticket_id','refund_amount','refund_id']):
            print(f"Warning: Refund data missing critical fields or not a dict: {data}")
            return None
        try:
            refund = cls(
                payment_id=data.get('payment_id'), order_id=data.get('order_id'), ticket_id=data.get('ticket_id'),
                refund_amount=float(data.get('refund_amount')), refund_reason=data.get('refund_reason'),
                refund_id=data.get('refund_id'), status=data.get('status', 'Pending')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Refund data: {e}. Data: {data}")
            return None

        req_dt_str = data.get('request_datetime')
        if req_dt_str:
            try: refund.request_datetime = datetime.fromisoformat(req_dt_str)
            except ValueError: refund.request_datetime = datetime.now()
        
        proc_dt_str = data.get('processed_datetime')
        if proc_dt_str:
            try: refund.processed_datetime = datetime.fromisoformat(proc_dt_str)
            except ValueError: refund.processed_datetime = None # If invalid, keep it None
        return refund
        
    def save(self):
        all_data = _load_data(Refund.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('refund_id') == self.refund_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Refund.FILE_PATH, all_data)


# --- Location Model ---
class Location:
    FILE_PATH = LOCATION_DATA_FILE
    def __init__(self, latitude, longitude, address_line1, city, postcode, location_id=None):
        self.location_id=location_id or str(uuid.uuid4()); self.latitude=float(latitude); self.longitude=float(longitude)
        self.address_line1=address_line1; self.city=city; self.postcode=postcode

    def set_details(self,latitude=None,longitude=None,address_line1=None,city=None,postcode=None):
        if latitude is not None: self.latitude = float(latitude)
        if longitude is not None: self.longitude = float(longitude)
        if address_line1 is not None: self.address_line1 = address_line1
        if city is not None: self.city = city
        if postcode is not None: self.postcode = postcode
        return True

    def to_dict(self):
        return {'location_id':self.location_id,'latitude':self.latitude,'longitude':self.longitude,
                'address_line1':self.address_line1,'city':self.city,'postcode':self.postcode}

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['latitude','longitude','address_line1','city','postcode']):
            print(f"Warning: Location data missing critical fields or not a dict: {data}")
            return None
        try:
            return cls(
                latitude=float(data.get('latitude')), longitude=float(data.get('longitude')),
                address_line1=data.get('address_line1'), city=data.get('city'),
                postcode=data.get('postcode'), location_id=data.get('location_id')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Location data: {e}. Data: {data}")
            return None

    def save(self):
        all_data = _load_data(Location.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('location_id') == self.location_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Location.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Location.FILE_PATH)
        for item_data in all_data:
            if item_data.get('location_id') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Location.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items


# --- Stop Model ---
class Stop:
    FILE_PATH = STOP_DATA_FILE
    def __init__(self, stop_name, location_id, stop_id=None, stop_code=None):
        self.stop_id = stop_id if stop_id else str(uuid.uuid4())
        self.stop_name = stop_name
        self.location_id = location_id
        self.stop_code = stop_code if stop_code else self.stop_id[:6].upper()

    def to_dict(self):
        return {'stop_id':self.stop_id,'stop_name':self.stop_name,'location_id':self.location_id,'stop_code':self.stop_code}

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['stop_name','location_id']):
            print(f"Warning: Stop data missing critical fields or not a dict: {data}")
            return None
        return cls(
            stop_name=data.get('stop_name'), location_id=data.get('location_id'),
            stop_id=data.get('stop_id'), stop_code=data.get('stop_code')
        )

    def update_location_details(self, new_latitude, new_longitude, new_address, new_city, new_postcode):
        location = Location.find_by_id(self.location_id)
        if location:
            location.set_details(new_latitude, new_longitude, new_address, new_city, new_postcode)
            location.save()
            return True, "Location details updated successfully."
        return False, f"Location with ID {self.location_id} not found for this stop."

    def save(self):
        all_data = _load_data(Stop.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('stop_id') == self.stop_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Stop.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Stop.FILE_PATH)
        for item_data in all_data:
            if item_data.get('stop_id') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Stop.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items
        
    def get_location(self): 
        return Location.find_by_id(self.location_id)


# --- Route Model ---
class Route:
    FILE_PATH = ROUTE_DATA_FILE
    def __init__(self, route_name, description, route_id=None, stop_ids=None):
        self.route_id = route_id if route_id else str(uuid.uuid4())
        self.route_name = route_name
        self.description = description
        self.stop_ids = stop_ids if stop_ids is not None else []

    def add_stop_id(self, stop_id):
        if stop_id not in self.stop_ids: self.stop_ids.append(stop_id); return True
        return False
    def find_stop_id(self, stop_id_to_find): return stop_id_to_find if stop_id_to_find in self.stop_ids else None
    def to_dict(self): 
        return {'route_id':self.route_id,'route_name':self.route_name,
                'description':self.description,'stop_ids':self.stop_ids}
    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not data.get('route_name') or not data.get('route_id'):
            print(f"Warning: Route data missing critical fields or not a dict: {data}")
            return None
        route = cls(route_name=data.get('route_name'), description=data.get('description'), route_id=data.get('route_id'))
        route.stop_ids = data.get('stop_ids', [])
        return route

    def save(self):
        all_data = _load_data(Route.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('route_id') == self.route_id: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Route.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Route.FILE_PATH)
        for item_data in all_data:
            if item_data.get('route_id') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Route.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items
        
    def get_stops_objects(self):
        stops = []
        for stop_id in self.stop_ids:
            stop_obj = Stop.find_by_id(stop_id)
            if stop_obj: stops.append(stop_obj)
        return stops


# --- Feedback Model ---
class Feedback:
    FILE_PATH = FEEDBACK_DATA_FILE
    def __init__(self, submitter_user_id, feedback_content, rating=None, related_trip_id=None, feedback_id=None, status="New", submission_datetime=None, response_ids=None): # noqa
        self.feedback_id=feedback_id or str(uuid.uuid4());self.submitter_user_id=submitter_user_id;self.feedback_content=feedback_content;self.rating=rating;self.related_trip_id=related_trip_id;self.status=status;self.submission_datetime=submission_datetime or datetime.now();self.response_ids=response_ids or [] # noqa
    def update_status(self,new_status): self.status=new_status
    def add_response_id(self,rid): (self.response_ids.append(rid)) if rid not in self.response_ids else None
    def to_dict(self): return {'feedback_id':self.feedback_id,'submitter_user_id':self.submitter_user_id,'feedback_content':self.feedback_content,'rating':self.rating,'related_trip_id':self.related_trip_id,'status':self.status,'submission_datetime':self.submission_datetime.isoformat(),'response_ids':self.response_ids} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['submitter_user_id','feedback_content']): return None
        fb_items = {k:v for k,v in data.items() if k not in ['submission_datetime','response_ids']}
        fb = cls(**fb_items)
        dt_str=data.get('submission_datetime')
        if dt_str: 
            try: fb.submission_datetime=datetime.fromisoformat(dt_str)
            except ValueError: fb.submission_datetime=datetime.now()
        else: fb.submission_datetime = datetime.now()
        fb.response_ids=data.get('response_ids',[])
        return fb
    def save(self): 
        all_data=_load_data(Feedback.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('feedback_id')==self.feedback_id: all_data[i]=self.to_dict(); upd=True; break
        if not upd: all_data.append(self.to_dict())
        _save_data(Feedback.FILE_PATH,all_data)
    @classmethod
    def find_by_id(cls,fid): return next((cls.from_dict(d) for d in _load_data(Feedback.FILE_PATH) if d.get('feedback_id')==fid),None)
    @classmethod
    def get_all(cls,status_filter=None): 
        feedbacks=[cls.from_dict(d) for d in _load_data(Feedback.FILE_PATH) if d]
        valid_feedbacks = [fb for fb in feedbacks if fb] # Filter out None objects
        if status_filter:
            return [fb for fb in valid_feedbacks if fb.status==status_filter]
        return valid_feedbacks
    def get_responses(self): return [Response.find_by_id(rid) for rid in self.response_ids if Response.find_by_id(rid)]

# --- Response Model ---
class Response:
    FILE_PATH = RESPONSE_DATA_FILE
    def __init__(self, feedback_id, responder_admin_id, response_content, response_id=None, response_datetime=None):
        self.response_id=response_id or str(uuid.uuid4());self.feedback_id=feedback_id;self.responder_admin_id=responder_admin_id;self.response_content=response_content;self.response_datetime=response_datetime or datetime.now() # noqa
    def to_dict(self): return {'response_id':self.response_id,'feedback_id':self.feedback_id,'responder_admin_id':self.responder_admin_id,'response_content':self.response_content,'response_datetime':self.response_datetime.isoformat()} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['feedback_id','responder_admin_id','response_content']): return None
        resp_items = {k:v for k,v in data.items() if k!='response_datetime'}
        resp=cls(**resp_items)
        dt_str=data.get('response_datetime')
        if dt_str: 
            try: resp.response_datetime=datetime.fromisoformat(dt_str)
            except ValueError: resp.response_datetime=datetime.now()
        else: resp.response_datetime=datetime.now()
        return resp
    def save(self): 
        all_data=_load_data(Response.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('response_id')==self.response_id: all_data[i]=self.to_dict(); upd=True; break
        if not upd: all_data.append(self.to_dict())
        _save_data(Response.FILE_PATH,all_data)
    @classmethod
    def find_by_id(cls,rid): return next((cls.from_dict(d) for d in _load_data(Response.FILE_PATH) if d.get('response_id')==rid),None)
    @classmethod
    def find_by_feedback_id(cls,fid): 
        all_data = _load_data(Response.FILE_PATH)
        responses = []
        for item_data in all_data:
            if item_data.get('feedback_id') == fid:
                resp_obj = cls.from_dict(item_data)
                if resp_obj: responses.append(resp_obj)
        return responses

# --- Notification Model ---
class Notification:
    FILE_PATH = NOTIFICATION_DATA_FILE
    def __init__(self, recipient_user_id, sender_user_id, message_content, notification_type="General", notification_id=None, sent_datetime=None, read_status=False): # noqa
        self.notification_id=notification_id or str(uuid.uuid4());self.recipient_user_id=recipient_user_id;self.sender_user_id=sender_user_id;self.message_content=message_content;self.notification_type=notification_type;self.sent_datetime=sent_datetime or datetime.now();self.read_status=read_status # noqa
    def mark_as_read(self): self.read_status=True
    def to_dict(self): return {'notification_id':self.notification_id,'recipient_user_id':self.recipient_user_id,'sender_user_id':self.sender_user_id,'message_content':self.message_content,'notification_type':self.notification_type,'sent_datetime':self.sent_datetime.isoformat(),'read_status':self.read_status} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['recipient_user_id','message_content']): return None
        notif_items = {k:v for k,v in data.items() if k!='sent_datetime'}
        notif=cls(**notif_items)
        dt_str=data.get('sent_datetime')
        if dt_str: 
            try: notif.sent_datetime=datetime.fromisoformat(dt_str)
            except ValueError: notif.sent_datetime=datetime.now()
        else: notif.sent_datetime=datetime.now()
        return notif
    def save(self): 
        all_data=_load_data(Notification.FILE_PATH)
        all_data.append(self.to_dict()) # Notifications are usually just appended
        _save_data(Notification.FILE_PATH,all_data)
    @classmethod
    def find_by_recipient_id(cls,uid,unread_only=False): 
        notifications_data = _load_data(Notification.FILE_PATH)
        notifications = []
        for item_data in notifications_data:
            if item_data.get('recipient_user_id') == uid:
                notif_obj = cls.from_dict(item_data)
                if notif_obj: notifications.append(notif_obj)
        
        if unread_only:
            return [n for n in notifications if not n.read_status]
        return notifications