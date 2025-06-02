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

    def __init__(self, username, email, password, userID=None, isAdmin=False, admin_level=None):
        self.userID = userID if userID else str(uuid.uuid4())
        self.username = username
        self.email = email
        if password:
            self.password_hash = self._hash_password(password)
        else:
            self.password_hash = None 
        self.isAdmin = isAdmin
        self.admin_level = admin_level if isAdmin else None

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password_to_check):
        if not self.password_hash or not password_to_check:
            return False
        return self.password_hash == self._hash_password(password_to_check)

    def to_dict(self):
        data = {
            'userID': self.userID,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'isAdmin': self.isAdmin
        }
        if self.isAdmin:
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
            userID=data.get('userID'),
            isAdmin=data.get('isAdmin', False),
            admin_level=data.get('admin_level') if data.get('isAdmin') else None
        )
        user.password_hash = data.get('password_hash')
        if not all([user.userID, user.username, user.email, user.password_hash]):
            # print(f"Warning: User data missing critical fields: {data}") # Can be noisy
            return None # Invalid user object
        return user

    def save(self):
        all_users_data = _load_data(User.FILE_PATH)
        updated = False
        # Check for conflicts before attempting to save if it's a new user (no userID match)
        is_new_user = True
        for i, user_data_dict in enumerate(all_users_data):
            if user_data_dict.get('userID') == self.userID:
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
             print(f"Error: User with ID {self.userID} not found for update, but not treated as new.")
             return False


        _save_data(User.FILE_PATH, all_users_data)
        return True

    @classmethod
    def find_by_id(cls, userID_to_find):
        all_users_data = _load_data(User.FILE_PATH)
        for user_data in all_users_data:
            if user_data.get('userID') == userID_to_find:
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
    def __init__(self, username, email, password, userID=None, admin_level="superuser"):
        super().__init__(username, email, password, userID, isAdmin=True, admin_level=admin_level)


# --- Trip Model ---
class Trip:
    FILE_PATH = TRIP_DATA_FILE
    def __init__(self, tripID, origin, destination, departureTime, price, availableSeats):
        self.tripID = tripID
        self.origin = origin
        self.destination = destination
        self.departureTime = departureTime 
        self.price = price
        self.availableSeats = int(availableSeats) # Ensure it's an int

    def to_dict(self):
        return {
            'tripID': self.tripID, 
            'origin': self.origin, 
            'destination': self.destination, 
            'departureTime': str(self.departureTime), 
            'price': float(self.price), 
            'availableSeats': int(self.availableSeats)
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['tripID','origin','destination','departureTime','price','availableSeats']):
            print(f"Warning: Trip data missing critical fields or not a dict: {data}")
            return None
        try: # Add type conversion robustness
            return cls(
                tripID=data['tripID'],
                origin=data['origin'],
                destination=data['destination'],
                departureTime=data['departureTime'],
                price=float(data['price']),
                availableSeats=int(data['availableSeats'])
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Trip data: {e}. Data: {data}")
            return None


    def save(self):
        all_data = _load_data(Trip.FILE_PATH)
        updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('tripID') == self.tripID:
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
            if item_data.get('tripID') == item_id:
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
            if date_str and date_str not in trip.departureTime: match = False
            if match and trip.availableSeats > 0:
                filtered_trips.append(trip)
        return filtered_trips
        
    def update_seats(self, num_seats, operation="book"):
        if operation == "book":
            if self.availableSeats >= num_seats:
                self.availableSeats -= num_seats
                return True
            else:
                return False
        elif operation == "refund":
            self.availableSeats += num_seats
            return True
        return False # Invalid operation

# --- Payment Model ---
class Payment:
    FILE_PATH = PAYMENT_DATA_FILE
    def __init__(self, orderID, amount, method="MockCard", status="Completed", paymentID=None):
        self.paymentID = paymentID if paymentID else str(uuid.uuid4())
        self.orderID = orderID
        self.amount = float(amount)
        self.method = method
        self.status = status
        self.payment_datetime = datetime.now()

    def to_dict(self):
        return {'paymentID':self.paymentID, 'orderID':self.orderID, 'amount':self.amount, 
                'method':self.method, 'status':self.status, 'payment_datetime':self.payment_datetime.isoformat()}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['orderID','amount','paymentID']):
            print(f"Warning: Payment data missing critical fields or not a dict: {data}")
            return None
        try:
            payment = cls(
                orderID=data.get('orderID'),
                amount=float(data.get('amount')),
                method=data.get('method', "MockCard"),
                status=data.get('status', "Completed"),
                paymentID=data.get('paymentID')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Payment data: {e}. Data: {data}")
            return None

        dt_str = data.get('payment_datetime')
        if dt_str:
            try:
                payment.payment_datetime = datetime.fromisoformat(dt_str)
            except ValueError:
                print(f"Warning: Invalid payment_datetime format for {payment.paymentID}. Using current time.")
                payment.payment_datetime = datetime.now() 
        return payment

    def save(self):
        all_data = _load_data(Payment.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('paymentID') == self.paymentID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Payment.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('paymentID') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def find_by_orderID(cls, orderID_to_find):
        all_data = _load_data(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('orderID') == orderID_to_find: return cls.from_dict(item_data)
        return None


# --- Ticket Model ---
class Ticket:
    FILE_PATH = TICKET_DATA_FILE
    def __init__(self, userID, tripID, orderID, paymentID, seatNumber=None, issue_datetime=None, ticketID=None, status="Active"):
        self.ticketID = ticketID if ticketID else str(uuid.uuid4())
        self.userID = userID
        self.tripID = tripID
        self.orderID = orderID
        self.paymentID = paymentID
        self.seatNumber = seatNumber if seatNumber else "Any Available"
        self.issue_datetime = issue_datetime if issue_datetime else datetime.now()
        self.status = status

    def void(self):
        if self.status == "Active":
            self.status = "Voided"
            return True
        return False

    def to_dict(self):
        return {'ticketID':self.ticketID,'userID':self.userID,'tripID':self.tripID,
                'orderID':self.orderID,'paymentID':self.paymentID,'seatNumber':self.seatNumber,
                'issue_datetime':self.issue_datetime.isoformat(),'status':self.status}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['userID','tripID','orderID','paymentID','ticketID']):
            print(f"Warning: Ticket data missing critical fields or not a dict: {data}")
            return None
        
        ticket = cls(
            userID=data.get('userID'), tripID=data.get('tripID'), orderID=data.get('orderID'),
            paymentID=data.get('paymentID'), seatNumber=data.get('seatNumber'),
            ticketID=data.get('ticketID'), status=data.get('status', "Active")
        )
        dt_str = data.get('issue_datetime')
        if dt_str:
            try: ticket.issue_datetime = datetime.fromisoformat(dt_str)
            except ValueError: ticket.issue_datetime = datetime.now()
        return ticket

    def save(self):
        all_data = _load_data(Ticket.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('ticketID') == self.ticketID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Ticket.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Ticket.FILE_PATH)
        for item_data in all_data:
            if item_data.get('ticketID') == item_id: return cls.from_dict(item_data)
        return None
        
    @classmethod
    def find_by_orderID(cls, orderID_to_find):
        all_data = _load_data(Ticket.FILE_PATH)
        tickets = []
        for item_data in all_data:
            if item_data.get('orderID') == orderID_to_find:
                ticket_obj = cls.from_dict(item_data)
                if ticket_obj: tickets.append(ticket_obj)
        return tickets
        
    @classmethod
    def delete_by_orderID(cls, orderID_to_delete):
        all_data = _load_data(Ticket.FILE_PATH)
        remaining_items = [item for item in all_data if item.get('orderID') != orderID_to_delete]
        if len(remaining_items) < len(all_data): # Check if any were actually removed
            _save_data(Ticket.FILE_PATH, remaining_items)
            return True
        return False


# --- Order Model ---
class Order:
    FILE_PATH = ORDER_DATA_FILE
    def __init__(self, userID, tripID, num_tickets, totalAmount, orderID=None, status="PendingPayment"):
        self.orderID = orderID if orderID else str(uuid.uuid4())
        self.userID = userID
        self.tripID = tripID
        self.num_tickets = int(num_tickets)
        self.totalAmount = float(totalAmount)
        self.orderDatetime = datetime.now()
        self.status = status

    def to_dict(self):
        return {'orderID':self.orderID,'userID':self.userID,'tripID':self.tripID,
                'num_tickets':self.num_tickets,'totalAmount':self.totalAmount,
                'orderDatetime':self.orderDatetime.isoformat(),'status':self.status}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['userID','tripID','num_tickets','totalAmount','orderID']):
            print(f"Warning: Order data missing critical fields or not a dict: {data}")
            return None
        try:
            order = cls(
                userID=data.get('userID'), tripID=data.get('tripID'),
                num_tickets=int(data.get('num_tickets')), totalAmount=float(data.get('totalAmount')),
                orderID=data.get('orderID'), status=data.get('status', 'PendingPayment')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Order data: {e}. Data: {data}")
            return None
            
        dt_str = data.get('orderDatetime')
        if dt_str:
            try: order.orderDatetime = datetime.fromisoformat(dt_str)
            except ValueError: order.orderDatetime = datetime.now()
        return order

    def save(self):
        all_data = _load_data(Order.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('orderID') == self.orderID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Order.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Order.FILE_PATH)
        for item_data in all_data:
            if item_data.get('orderID') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def find_by_userID(cls, userID_to_find):
        all_data = _load_data(Order.FILE_PATH)
        orders = []
        for item_data in all_data:
            if item_data.get('userID') == userID_to_find:
                order_obj = cls.from_dict(item_data)
                if order_obj: orders.append(order_obj)
        return orders


# --- Refund Model ---
class Refund:
    FILE_PATH = REFUND_DATA_FILE
    def __init__(self, paymentID, orderID, ticketID, refundAmount, refundReason="User requested", refundID=None, status="Pending"):
        self.refundID = refundID if refundID else str(uuid.uuid4())
        self.paymentID=paymentID; self.orderID=orderID; self.ticketID=ticketID; self.refundAmount=float(refundAmount)
        self.refundReason=refundReason; self.status=status; self.request_datetime=datetime.now(); self.processed_datetime=None

    def update_status(self, new_status):
        self.status = new_status
        if self.status in ["Processed", "Failed"]: self.processed_datetime = datetime.now()

    def to_dict(self):
        return {'refundID':self.refundID,'paymentID':self.paymentID,'orderID':self.orderID,
                'ticketID':self.ticketID,'refundAmount':self.refundAmount,'refundReason':self.refundReason,
                'status':self.status,'request_datetime':self.request_datetime.isoformat(),
                'processed_datetime':self.processed_datetime.isoformat() if self.processed_datetime else None}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['paymentID','orderID','ticketID','refundAmount','refundID']):
            print(f"Warning: Refund data missing critical fields or not a dict: {data}")
            return None
        try:
            refund = cls(
                paymentID=data.get('paymentID'), orderID=data.get('orderID'), ticketID=data.get('ticketID'),
                refundAmount=float(data.get('refundAmount')), refundReason=data.get('refundReason'),
                refundID=data.get('refundID'), status=data.get('status', 'Pending')
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
            if item_data.get('refundID') == self.refundID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Refund.FILE_PATH, all_data)


# --- Location Model ---
class Location:
    FILE_PATH = LOCATION_DATA_FILE
    def __init__(self, latitude, longitude, addressLine1, city, postcode, locationID=None):
        self.locationID=locationID or str(uuid.uuid4()); self.latitude=float(latitude); self.longitude=float(longitude)
        self.addressLine1=addressLine1; self.city=city; self.postcode=postcode

    def set_details(self,latitude=None,longitude=None,addressLine1=None,city=None,postcode=None):
        if latitude is not None: self.latitude = float(latitude)
        if longitude is not None: self.longitude = float(longitude)
        if addressLine1 is not None: self.addressLine1 = addressLine1
        if city is not None: self.city = city
        if postcode is not None: self.postcode = postcode
        return True

    def to_dict(self):
        return {'locationID':self.locationID,'latitude':self.latitude,'longitude':self.longitude,
                'addressLine1':self.addressLine1,'city':self.city,'postcode':self.postcode}

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['latitude','longitude','addressLine1','city','postcode']):
            print(f"Warning: Location data missing critical fields or not a dict: {data}")
            return None
        try:
            return cls(
                latitude=float(data.get('latitude')), longitude=float(data.get('longitude')),
                addressLine1=data.get('addressLine1'), city=data.get('city'),
                postcode=data.get('postcode'), locationID=data.get('locationID')
            )
        except (ValueError, TypeError) as e:
            print(f"Error converting Location data: {e}. Data: {data}")
            return None

    def save(self):
        all_data = _load_data(Location.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('locationID') == self.locationID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Location.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Location.FILE_PATH)
        for item_data in all_data:
            if item_data.get('locationID') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Location.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items


# --- Stop Model ---
class Stop:
    FILE_PATH = STOP_DATA_FILE
    def __init__(self, stopName, locationID, stopID=None, stopCode=None):
        self.stopID = stopID if stopID else str(uuid.uuid4())
        self.stopName = stopName
        self.locationID = locationID
        self.stopCode = stopCode if stopCode else self.stopID[:6].upper()

    def to_dict(self):
        return {'stopID':self.stopID,'stopName':self.stopName,'locationID':self.locationID,'stopCode':self.stopCode}

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['stopName','locationID']):
            print(f"Warning: Stop data missing critical fields or not a dict: {data}")
            return None
        return cls(
            stopName=data.get('stopName'), locationID=data.get('locationID'),
            stopID=data.get('stopID'), stopCode=data.get('stopCode')
        )

    def update_location_details(self, new_latitude, new_longitude, new_address, new_city, new_postcode):
        location = Location.find_by_id(self.locationID)
        if location:
            location.set_details(new_latitude, new_longitude, new_address, new_city, new_postcode)
            location.save()
            return True, "Location details updated successfully."
        return False, f"Location with ID {self.locationID} not found for this stop."

    def save(self):
        all_data = _load_data(Stop.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('stopID') == self.stopID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Stop.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Stop.FILE_PATH)
        for item_data in all_data:
            if item_data.get('stopID') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Stop.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items
        
    def get_location(self): 
        return Location.find_by_id(self.locationID)


# --- Route Model ---
class Route:
    FILE_PATH = ROUTE_DATA_FILE
    def __init__(self, routeName, description, routeID=None, stopIDs=None):
        self.routeID = routeID if routeID else str(uuid.uuid4())
        self.routeName = routeName
        self.description = description
        self.stopIDs = stopIDs if stopIDs is not None else []

    def add_stopID(self, stopID):
        if stopID not in self.stopIDs: self.stopIDs.append(stopID); return True
        return False
    def find_stopID(self, stopID_to_find): return stopID_to_find if stopID_to_find in self.stopIDs else None
    def to_dict(self): 
        return {'routeID':self.routeID,'routeName':self.routeName,
                'description':self.description,'stopIDs':self.stopIDs}
    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or not data.get('routeName') or not data.get('routeID'):
            print(f"Warning: Route data missing critical fields or not a dict: {data}")
            return None
        route = cls(routeName=data.get('routeName'), description=data.get('description'), routeID=data.get('routeID'))
        route.stopIDs = data.get('stopIDs', [])
        return route

    def save(self):
        all_data = _load_data(Route.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('routeID') == self.routeID: all_data[i] = self.to_dict(); updated = True; break
        if not updated: all_data.append(self.to_dict())
        _save_data(Route.FILE_PATH, all_data)

    @classmethod
    def find_by_id(cls, item_id):
        all_data = _load_data(Route.FILE_PATH)
        for item_data in all_data:
            if item_data.get('routeID') == item_id: return cls.from_dict(item_data)
        return None

    @classmethod
    def get_all(cls):
        all_data = _load_data(Route.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.from_dict(item_data))]
        return items
        
    def get_stops_objects(self):
        stops = []
        for stopID in self.stopIDs:
            stop_obj = Stop.find_by_id(stopID)
            if stop_obj: stops.append(stop_obj)
        return stops


# --- Feedback Model ---
class Feedback:
    FILE_PATH = FEEDBACK_DATA_FILE
    def __init__(self, submitter_userID, feedback_content, rating=None, relatedtripID=None, feedbackID=None, status="New", submissionDatetime=None, responseIDs=None): # noqa
        self.feedbackID=feedbackID or str(uuid.uuid4());self.submitter_userID=submitter_userID;self.feedback_content=feedback_content;self.rating=rating;self.relatedtripID=relatedtripID;self.status=status;self.submissionDatetime=submissionDatetime or datetime.now();self.responseIDs=responseIDs or [] # noqa
    def update_status(self,new_status): self.status=new_status
    def add_responseID(self,rid): (self.responseIDs.append(rid)) if rid not in self.responseIDs else None
    def to_dict(self): return {'feedbackID':self.feedbackID,'submitter_userID':self.submitter_userID,'feedback_content':self.feedback_content,'rating':self.rating,'relatedtripID':self.relatedtripID,'status':self.status,'submissionDatetime':self.submissionDatetime.isoformat(),'responseIDs':self.responseIDs} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['submitter_userID','feedback_content']): return None
        fb_items = {k:v for k,v in data.items() if k not in ['submissionDatetime','responseIDs']}
        fb = cls(**fb_items)
        dt_str=data.get('submissionDatetime')
        if dt_str: 
            try: fb.submissionDatetime=datetime.fromisoformat(dt_str)
            except ValueError: fb.submissionDatetime=datetime.now()
        else: fb.submissionDatetime = datetime.now()
        fb.responseIDs=data.get('responseIDs',[])
        return fb
    def save(self): 
        all_data=_load_data(Feedback.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('feedbackID')==self.feedbackID: all_data[i]=self.to_dict(); upd=True; break
        if not upd: all_data.append(self.to_dict())
        _save_data(Feedback.FILE_PATH,all_data)
    @classmethod
    def find_by_id(cls,fid): return next((cls.from_dict(d) for d in _load_data(Feedback.FILE_PATH) if d.get('feedbackID')==fid),None)
    @classmethod
    def get_all(cls,status_filter=None): 
        feedbacks=[cls.from_dict(d) for d in _load_data(Feedback.FILE_PATH) if d]
        valid_feedbacks = [fb for fb in feedbacks if fb] # Filter out None objects
        if status_filter:
            return [fb for fb in valid_feedbacks if fb.status==status_filter]
        return valid_feedbacks
    def get_responses(self): return [Response.find_by_id(rid) for rid in self.responseIDs if Response.find_by_id(rid)]

# --- Response Model ---
class Response:
    FILE_PATH = RESPONSE_DATA_FILE
    def __init__(self, feedbackID, responder_adminID, responseContent, responseID=None, responseDatetime=None):
        self.responseID=responseID or str(uuid.uuid4());self.feedbackID=feedbackID;self.responder_adminID=responder_adminID;self.responseContent=responseContent;self.responseDatetime=responseDatetime or datetime.now() # noqa
    def to_dict(self): return {'responseID':self.responseID,'feedbackID':self.feedbackID,'responder_adminID':self.responder_adminID,'responseContent':self.responseContent,'responseDatetime':self.responseDatetime.isoformat()} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['feedbackID','responder_adminID','responseContent']): return None
        resp_items = {k:v for k,v in data.items() if k!='responseDatetime'}
        resp=cls(**resp_items)
        dt_str=data.get('responseDatetime')
        if dt_str: 
            try: resp.responseDatetime=datetime.fromisoformat(dt_str)
            except ValueError: resp.responseDatetime=datetime.now()
        else: resp.responseDatetime=datetime.now()
        return resp
    def save(self): 
        all_data=_load_data(Response.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('responseID')==self.responseID: all_data[i]=self.to_dict(); upd=True; break
        if not upd: all_data.append(self.to_dict())
        _save_data(Response.FILE_PATH,all_data)
    @classmethod
    def find_by_id(cls,rid): return next((cls.from_dict(d) for d in _load_data(Response.FILE_PATH) if d.get('responseID')==rid),None)
    @classmethod
    def find_by_feedbackID(cls,fid): 
        all_data = _load_data(Response.FILE_PATH)
        responses = []
        for item_data in all_data:
            if item_data.get('feedbackID') == fid:
                resp_obj = cls.from_dict(item_data)
                if resp_obj: responses.append(resp_obj)
        return responses

# --- Notification Model ---
class Notification:
    FILE_PATH = NOTIFICATION_DATA_FILE
    def __init__(self, recipientuserID, senderuserID, message_content, notificationType="General", notificationID=None, sent_datetime=None, read_status=False): # noqa
        self.notificationID=notificationID or str(uuid.uuid4());self.recipientuserID=recipientuserID;self.senderuserID=senderuserID;self.message_content=message_content;self.notificationType=notificationType;self.sent_datetime=sent_datetime or datetime.now();self.read_status=read_status # noqa
    def mark_as_read(self): self.read_status=True
    def to_dict(self): return {'notificationID':self.notificationID,'recipientuserID':self.recipientuserID,'senderuserID':self.senderuserID,'message_content':self.message_content,'notificationType':self.notificationType,'sent_datetime':self.sent_datetime.isoformat(),'read_status':self.read_status} # noqa
    @classmethod
    def from_dict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['recipientuserID','message_content']): return None
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
            if item_data.get('recipientuserID') == uid:
                notif_obj = cls.from_dict(item_data)
                if notif_obj: notifications.append(notif_obj)
        
        if unread_only:
            return [n for n in notifications if not n.read_status]
        return notifications