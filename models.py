# models.py
import uuid
from datetime import datetime
import hashlib
import json
import os

# --- Helper function for JSON file operations ---
def _loadData(file_path):
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

def _saveData(file_path, all_items_data):
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

    def __init__(self, username, email, password, userID=None, 
                 # Attributes from A2 User that might be common
                 phone=None, firstName=None, lastName=None, 
                 dateRegistered=None, accountStatus="Active"):
        self.userID = userID if userID else str(uuid.uuid4())
        self.username = username
        self.email = email
        self.passwordHash = self._hashPassword(password) if password else None
        
        # Common attributes from A2 User diagram (optional, add if you use them)
        self.phone = phone
        self.firstName = firstName
        self.lastName = lastName
        self.dateRegistered = dateRegistered if dateRegistered else datetime.now()
        self.accountStatus = accountStatus

    def _hashPassword(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def checkPassword(self, passwordToCheck):
        if not self.passwordHash or not passwordToCheck: return False
        return self.passwordHash == self._hashPassword(passwordToCheck)

    def toDict(self):
        """Converts the User object to a dictionary for JSON serialization."""
        data = {
            'userID': self.userID,
            'username': self.username,
            'email': self.email,
            'passwordHash': self.passwordHash,
            'phone': self.phone,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'dateRegistered': self.dateRegistered.isoformat() if isinstance(self.dateRegistered, datetime) else str(self.dateRegistered),
            'accountStatus': self.accountStatus,
            '_userType': self.__class__.__name__ # Store the actual class name
        }
        return data
    
    @classmethod
    def fromDict(cls, data):
        """
        Factory method to create User, Admin, or ArtPassenger based on _userType.
        This method should ideally be called by findByID, getAll etc.
        """
        if not isinstance(data, dict):
            print(f"Error: User.fromDict expected dict, got {type(data)}: {data}")
            return None

        userType = data.get('_userType')
        
        # Common attributes extraction
        userID = data.get('userID')
        username = data.get('username')
        email = data.get('email')
        passwordHashFromData = data.get('passwordHash')
        phone = data.get('phone')
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        dateRegisteredStr = data.get('dateRegistered')
        accountStatus = data.get('accountStatus', "Active")

        dateRegistered = None
        if dateRegisteredStr:
            try: dateRegistered = datetime.fromisoformat(dateRegisteredStr)
            except ValueError: dateRegistered = datetime.now() # Fallback

        # Basic validation
        if not userID or not username or not email or not passwordHashFromData:
            print(f"Warning: User data missing critical fields (userID, username, email, passwordHash). Data: {data}")
            return None

        instance = None
        if userType == "Admin":
            instance = Admin(username=username, email=email, password=None, userID=userID,
                             phone=phone, firstName=firstName, lastName=lastName,
                             dateRegistered=dateRegistered, accountStatus=accountStatus,
                             adminLevel=data.get('adminLevel', 'default')) # Get admin specific
        elif userType == "ArtPassenger":
            instance = ArtPassenger(username=username, email=email, password=None, userID=userID,
                                    phone=phone, firstName=firstName, lastName=lastName,
                                    dateRegistered=dateRegistered, accountStatus=accountStatus,
                                    # Get ArtPassenger specific attributes
                                    paymentMethods=data.get('paymentMethods', []), 
                                    bookingHistory=data.get('bookingHistory', []),
                                    preferences=data.get('preferences', {}),
                                    loyaltyPoints=data.get('loyaltyPoints', 0))
        else: # Default to base User or handle as error
            instance = cls(username=username, email=email, password=None, userID=userID,
                           phone=phone, firstName=firstName, lastName=lastName,
                           dateRegistered=dateRegistered, accountStatus=accountStatus)
        
        if instance:
            instance.passwordHash = passwordHashFromData
        return instance

    def save(self):
        allUsersData = _loadData(User.FILE_PATH)
        updated = False
        isNewUser = True
        dict_to_save = self.toDict() # Get data from the correct instance (User, Admin, or ArtPassenger)

        for i, userDataDict in enumerate(allUsersData):
            if userDataDict.get('userID') == self.userID:
                allUsersData[i] = dict_to_save
                updated = True; isNewUser = False; break
        
        if isNewUser:
            for userDataDict in allUsersData: # Conflict check for new users
                if userDataDict.get('username') == self.username: print(f"Error: Username exists."); return False
                if userDataDict.get('email') == self.email: print(f"Error: Email exists."); return False
            allUsersData.append(dict_to_save)
        elif not updated and not isNewUser: return False

        _saveData(User.FILE_PATH, allUsersData); return True

    @classmethod
    def findByID(cls, userIDToFind):
        allUsersData = _loadData(User.FILE_PATH)
        for userData in allUsersData:
            if userData.get('userID') == userIDToFind:
                # Use the factory fromDict to create the correct type
                return User.fromDict(userData) 
        return None

    @classmethod
    def findByUsername(cls, usernameToFind):
        allUsersData = _loadData(User.FILE_PATH)
        for userData in allUsersData:
            if userData.get('username') == usernameToFind:
                return User.fromDict(userData)
        return None
    
    @classmethod
    def getAll(cls):
        allUsersData = _loadData(User.FILE_PATH); users = []
        for userData in allUsersData:
            userObj = User.fromDict(userData) # Use factory
            if userObj: users.append(userObj)
        return users

# --- ArtPassenger Child Class ---
class ArtPassenger(User):
    def __init__(self, username, email, password, userID=None, 
                 phone=None, firstName=None, lastName=None, 
                 dateRegistered=None, accountStatus="Active",
                 # ArtPassenger specific attributes from A2 UML
                 paymentMethods=None, bookingHistory=None, preferences=None, loyaltyPoints=0):
        super().__init__(username, email, password, userID, phone, firstName, lastName, dateRegistered, accountStatus)
        self.paymentMethods = paymentMethods if paymentMethods is not None else [] # e.g., list of payment method details/tokens
        self.bookingHistory = bookingHistory if bookingHistory is not None else [] # e.g., list of orderIDs
        self.preferences = preferences if preferences is not None else {} # e.g., dict of user prefs
        self.loyaltyPoints = int(loyaltyPoints)

    def toDict(self):
        data = super().toDict()
        data.update({
            'paymentMethods': self.paymentMethods,
            'bookingHistory': self.bookingHistory,
            'preferences': self.preferences,
            'loyaltyPoints': self.loyaltyPoints
        })
        return data

    # fromDict is handled by User.fromDict factory method
    
    # --- ArtPassenger specific methods from A2 UML (logic now in app.py or other models) ---
    # These methods would be called from app.py, using the ArtPassenger instance
    # They might interact with Order, Ticket, Feedback models directly
    def makeBooking(self, tripID, numTickets=1):
        # This method on ArtPassenger would now primarily delegate or be a thin wrapper.
        # The actual booking logic involving Order, Ticket, Payment creation and saving
        # would be in app.py or potentially a (now removed) BookingService.
        # For the "Smart Models" approach, app.py would do:
        # trip = Trip.findByID(tripID)
        # order = Order(userID=self.userID, tripID=tripID, ...)
        # order.save() ... etc.
        print(f"User {self.username} attempting to book {numTickets} for trip {tripID}. (Logic in app.py)")
        # This method can return data needed by app.py to proceed
        return {"status": "pending_app_logic", "userID": self.userID, "tripID": tripID}

    def submitFeedback(self, feedbackContent, rating=None, relatedTripID=None):
        # Logic in app.py will create Feedback object and save it
        print(f"User {self.username} submitting feedback: {feedbackContent}. (Logic in app.py)")
        # This method can return data needed by app.py
        return {"status": "pending_app_logic", "userID": self.userID, "content": feedbackContent}


# --- Admin Child Class ---
class Admin(User):
    def __init__(self, username, email, password, userID=None, 
                 phone=None, firstName=None, lastName=None, 
                 dateRegistered=None, accountStatus="Active",
                 # Admin specific attributes from A2 UML
                 adminLevel="staff", permissions=None, assignedArea=None):
        super().__init__(username, email, password, userID, phone, firstName, lastName, dateRegistered, accountStatus)
        self.adminLevel = adminLevel
        self.permissions = permissions if permissions is not None else [] # e.g. list of permission strings
        self.assignedArea = assignedArea

    def toDict(self):
        data = super().toDict()
        data.update({
            'adminLevel': self.adminLevel,
            'permissions': self.permissions,
            'assignedArea': self.assignedArea
        })
        return data
    
    # fromDict is handled by User.fromDict factory method

    # --- Admin specific methods from A2 UML (logic now in app.py or other models) ---
    # Example:
    def respondToFeedback(self, feedbackID, responseText):
        # Logic in app.py will find Feedback, create Response, save, etc.
        print(f"Admin {self.username} responding to feedback {feedbackID}. (Logic in app.py)")
        return {"status": "pending_app_logic", "feedbackID": feedbackID, "adminID": self.userID}


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

    def toDict(self):
        return {
            'tripID': self.tripID, 
            'origin': self.origin, 
            'destination': self.destination, 
            'departureTime': str(self.departureTime), 
            'price': float(self.price), 
            'availableSeats': int(self.availableSeats)
        }

    @classmethod
    def fromDict(cls, data):
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
        all_data = _loadData(Trip.FILE_PATH)
        updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('tripID') == self.tripID:
                all_data[i] = self.toDict()
                updated = True
                break
        if not updated:
            all_data.append(self.toDict())
        _saveData(Trip.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Trip.FILE_PATH)
        for item_data in all_data:
            if item_data.get('tripID') == item_id:
                return cls.fromDict(item_data)
        return None

    @classmethod
    def getAll(cls):
        all_data = _loadData(Trip.FILE_PATH)
        items = []
        for item_data in all_data:
            item_obj = cls.fromDict(item_data)
            if item_obj: items.append(item_obj)
        return items
        
    @classmethod
    def search(cls, origin=None, destination=None, date_str=None):
        all_trips = cls.getAll()
        filtered_trips = []
        for trip in all_trips:
            # Ensure trip is not None (could happen if fromDict failed for an entry)
            if not trip: 
                continue 
            match = True
            if origin and origin.lower() not in trip.origin.lower(): match = False
            if destination and destination.lower() not in trip.destination.lower(): match = False
            if date_str and date_str not in trip.departureTime: match = False
            if match and trip.availableSeats > 0:
                filtered_trips.append(trip)
        return filtered_trips
        
    def updateSeats(self, num_seats, operation="book"):
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
        self.paymentDatetime = datetime.now()

    def toDict(self):
        return {'paymentID':self.paymentID, 'orderID':self.orderID, 'amount':self.amount, 
                'method':self.method, 'status':self.status, 'paymentDatetime':self.paymentDatetime.isoformat()}

    @classmethod
    def fromDict(cls, data):
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

        dt_str = data.get('paymentDatetime')
        if dt_str:
            try:
                payment.paymentDatetime = datetime.fromisoformat(dt_str)
            except ValueError:
                print(f"Warning: Invalid paymentDatetime format for {payment.paymentID}. Using current time.")
                payment.paymentDatetime = datetime.now() 
        return payment

    def save(self):
        all_data = _loadData(Payment.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('paymentID') == self.paymentID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Payment.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('paymentID') == item_id: return cls.fromDict(item_data)
        return None

    @classmethod
    def findByOrderID(cls, orderID_to_find):
        all_data = _loadData(Payment.FILE_PATH)
        for item_data in all_data:
            if item_data.get('orderID') == orderID_to_find: return cls.fromDict(item_data)
        return None


# --- Ticket Model ---
class Ticket:
    FILE_PATH = TICKET_DATA_FILE
    def __init__(self, userID, tripID, orderID, paymentID, seatNumber=None, issueDatetime=None, ticketID=None, status="Active"):
        self.ticketID = ticketID if ticketID else str(uuid.uuid4())
        self.userID = userID
        self.tripID = tripID
        self.orderID = orderID
        self.paymentID = paymentID
        self.seatNumber = seatNumber if seatNumber else "Any Available"
        self.issueDatetime = issueDatetime if issueDatetime else datetime.now()
        self.status = status

    def void(self):
        if self.status == "Active":
            self.status = "Voided"
            return True
        return False

    def toDict(self):
        return {'ticketID':self.ticketID,'userID':self.userID,'tripID':self.tripID,
                'orderID':self.orderID,'paymentID':self.paymentID,'seatNumber':self.seatNumber,
                'issueDatetime':self.issueDatetime.isoformat(),'status':self.status}

    @classmethod
    def fromDict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['userID','tripID','orderID','paymentID','ticketID']):
            print(f"Warning: Ticket data missing critical fields or not a dict: {data}")
            return None
        
        ticket = cls(
            userID=data.get('userID'), tripID=data.get('tripID'), orderID=data.get('orderID'),
            paymentID=data.get('paymentID'), seatNumber=data.get('seatNumber'),
            ticketID=data.get('ticketID'), status=data.get('status', "Active")
        )
        dt_str = data.get('issueDatetime')
        if dt_str:
            try: ticket.issueDatetime = datetime.fromisoformat(dt_str)
            except ValueError: ticket.issueDatetime = datetime.now()
        return ticket

    def save(self):
        all_data = _loadData(Ticket.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('ticketID') == self.ticketID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Ticket.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Ticket.FILE_PATH)
        for item_data in all_data:
            if item_data.get('ticketID') == item_id: return cls.fromDict(item_data)
        return None
        
    @classmethod
    def findByOrderID(cls, orderID_to_find):
        all_data = _loadData(Ticket.FILE_PATH)
        tickets = []
        for item_data in all_data:
            if item_data.get('orderID') == orderID_to_find:
                ticket_obj = cls.fromDict(item_data)
                if ticket_obj: tickets.append(ticket_obj)
        return tickets
        
    @classmethod
    def deleteByOrderID(cls, orderID_to_delete):
        all_data = _loadData(Ticket.FILE_PATH)
        remaining_items = [item for item in all_data if item.get('orderID') != orderID_to_delete]
        if len(remaining_items) < len(all_data): # Check if any were actually removed
            _saveData(Ticket.FILE_PATH, remaining_items)
            return True
        return False


# --- Order Model ---
class Order:
    FILE_PATH = ORDER_DATA_FILE
    def __init__(self, userID, tripID, numTickets, totalAmount, orderID=None, status="PendingPayment"):
        self.orderID = orderID if orderID else str(uuid.uuid4())
        self.userID = userID
        self.tripID = tripID
        self.numTickets = int(numTickets)
        self.totalAmount = float(totalAmount)
        self.orderDatetime = datetime.now()
        self.status = status

    def toDict(self):
        return {'orderID':self.orderID,'userID':self.userID,'tripID':self.tripID,
                'numTickets':self.numTickets,'totalAmount':self.totalAmount,
                'orderDatetime':self.orderDatetime.isoformat(),'status':self.status}

    @classmethod
    def fromDict(cls, data):
        if not isinstance(data, dict) or not all(k in data for k in ['userID','tripID','numTickets','totalAmount','orderID']):
            print(f"Warning: Order data missing critical fields or not a dict: {data}")
            return None
        try:
            order = cls(
                userID=data.get('userID'), tripID=data.get('tripID'),
                numTickets=int(data.get('numTickets')), totalAmount=float(data.get('totalAmount')),
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
        all_data = _loadData(Order.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('orderID') == self.orderID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Order.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Order.FILE_PATH)
        for item_data in all_data:
            if item_data.get('orderID') == item_id: return cls.fromDict(item_data)
        return None

    @classmethod
    def find_by_userID(cls, userID_to_find):
        all_data = _loadData(Order.FILE_PATH)
        orders = []
        for item_data in all_data:
            if item_data.get('userID') == userID_to_find:
                order_obj = cls.fromDict(item_data)
                if order_obj: orders.append(order_obj)
        return orders


# --- Refund Model ---
class Refund:
    FILE_PATH = REFUND_DATA_FILE
    def __init__(self, paymentID, orderID, ticketID, refundAmount, refundReason="User requested", refundID=None, status="Pending"):
        self.refundID = refundID if refundID else str(uuid.uuid4())
        self.paymentID=paymentID; self.orderID=orderID; self.ticketID=ticketID; self.refundAmount=float(refundAmount)
        self.refundReason=refundReason; self.status=status; self.requestDatetime=datetime.now(); self.processedDatetime=None

    def updateStatus(self, new_status):
        self.status = new_status
        if self.status in ["Processed", "Failed"]: self.processedDatetime = datetime.now()

    def toDict(self):
        return {'refundID':self.refundID,'paymentID':self.paymentID,'orderID':self.orderID,
                'ticketID':self.ticketID,'refundAmount':self.refundAmount,'refundReason':self.refundReason,
                'status':self.status,'requestDatetime':self.requestDatetime.isoformat(),
                'processedDatetime':self.processedDatetime.isoformat() if self.processedDatetime else None}

    @classmethod
    def fromDict(cls, data):
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

        req_dt_str = data.get('requestDatetime')
        if req_dt_str:
            try: refund.requestDatetime = datetime.fromisoformat(req_dt_str)
            except ValueError: refund.requestDatetime = datetime.now()
        
        proc_dt_str = data.get('processedDatetime')
        if proc_dt_str:
            try: refund.processedDatetime = datetime.fromisoformat(proc_dt_str)
            except ValueError: refund.processedDatetime = None # If invalid, keep it None
        return refund
        
    def save(self):
        all_data = _loadData(Refund.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('refundID') == self.refundID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Refund.FILE_PATH, all_data)


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

    def toDict(self):
        return {'locationID':self.locationID,'latitude':self.latitude,'longitude':self.longitude,
                'addressLine1':self.addressLine1,'city':self.city,'postcode':self.postcode}

    @classmethod
    def fromDict(cls,data):
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
        all_data = _loadData(Location.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('locationID') == self.locationID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Location.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Location.FILE_PATH)
        for item_data in all_data:
            if item_data.get('locationID') == item_id: return cls.fromDict(item_data)
        return None

    @classmethod
    def getAll(cls):
        all_data = _loadData(Location.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.fromDict(item_data))]
        return items


# --- Stop Model ---
class Stop:
    FILE_PATH = STOP_DATA_FILE
    def __init__(self, stopName, locationID, stopID=None, stopCode=None):
        self.stopID = stopID if stopID else str(uuid.uuid4())
        self.stopName = stopName
        self.locationID = locationID
        self.stopCode = stopCode if stopCode else self.stopID[:6].upper()

    def toDict(self):
        return {'stopID':self.stopID,'stopName':self.stopName,'locationID':self.locationID,'stopCode':self.stopCode}

    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['stopName','locationID']):
            print(f"Warning: Stop data missing critical fields or not a dict: {data}")
            return None
        return cls(
            stopName=data.get('stopName'), locationID=data.get('locationID'),
            stopID=data.get('stopID'), stopCode=data.get('stopCode')
        )

    def updateLocationDetails(self, new_latitude, new_longitude, new_address, new_city, new_postcode):
        location = Location.findByID(self.locationID)
        if location:
            location.set_details(new_latitude, new_longitude, new_address, new_city, new_postcode)
            location.save()
            return True, "Location details updated successfully."
        return False, f"Location with ID {self.locationID} not found for this stop."

    def save(self):
        all_data = _loadData(Stop.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('stopID') == self.stopID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Stop.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Stop.FILE_PATH)
        for item_data in all_data:
            if item_data.get('stopID') == item_id: return cls.fromDict(item_data)
        return None

    @classmethod
    def getAll(cls):
        all_data = _loadData(Stop.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.fromDict(item_data))]
        return items
        
    def get_location(self): 
        return Location.findByID(self.locationID)


# --- Route Model ---
class Route:
    FILE_PATH = ROUTE_DATA_FILE
    def __init__(self, routeName, description, routeID=None, stopIDs=None):
        self.routeID = routeID if routeID else str(uuid.uuid4())
        self.routeName = routeName
        self.description = description
        self.stopIDs = stopIDs if stopIDs is not None else []

    def addStopID(self, stopID):
        if stopID not in self.stopIDs: self.stopIDs.append(stopID); return True
        return False
    def findStopID(self, stopID_to_find): return stopID_to_find if stopID_to_find in self.stopIDs else None
    def toDict(self): 
        return {'routeID':self.routeID,'routeName':self.routeName,
                'description':self.description,'stopIDs':self.stopIDs}
    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not data.get('routeName') or not data.get('routeID'):
            print(f"Warning: Route data missing critical fields or not a dict: {data}")
            return None
        route = cls(routeName=data.get('routeName'), description=data.get('description'), routeID=data.get('routeID'))
        route.stopIDs = data.get('stopIDs', [])
        return route

    def save(self):
        all_data = _loadData(Route.FILE_PATH); updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get('routeID') == self.routeID: all_data[i] = self.toDict(); updated = True; break
        if not updated: all_data.append(self.toDict())
        _saveData(Route.FILE_PATH, all_data)

    @classmethod
    def findByID(cls, item_id):
        all_data = _loadData(Route.FILE_PATH)
        for item_data in all_data:
            if item_data.get('routeID') == item_id: return cls.fromDict(item_data)
        return None

    @classmethod
    def getAll(cls):
        all_data = _loadData(Route.FILE_PATH)
        items = []; [items.append(obj) for item_data in all_data if (obj := cls.fromDict(item_data))]
        return items
        
    def getStopsObjects(self):
        stops = []
        for stopID in self.stopIDs:
            stop_obj = Stop.findByID(stopID)
            if stop_obj: stops.append(stop_obj)
        return stops


# --- Feedback Model ---
class Feedback:
    FILE_PATH = FEEDBACK_DATA_FILE
    def __init__(self, submitterUserID, feedbackContent, rating=None, relatedtripID=None, feedbackID=None, status="New", submissionDatetime=None, responseIDs=None): # noqa
        self.feedbackID=feedbackID or str(uuid.uuid4());self.submitterUserID=submitterUserID;self.feedbackContent=feedbackContent;self.rating=rating;self.relatedtripID=relatedtripID;self.status=status;self.submissionDatetime=submissionDatetime or datetime.now();self.responseIDs=responseIDs or [] # noqa
    def updateStatus(self,new_status): self.status=new_status
    def addResponseID(self,rid): (self.responseIDs.append(rid)) if rid not in self.responseIDs else None
    def toDict(self): return {'feedbackID':self.feedbackID,'submitterUserID':self.submitterUserID,'feedbackContent':self.feedbackContent,'rating':self.rating,'relatedtripID':self.relatedtripID,'status':self.status,'submissionDatetime':self.submissionDatetime.isoformat(),'responseIDs':self.responseIDs} # noqa
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['submitterUserID','feedbackContent']): return None
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
        all_data=_loadData(Feedback.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('feedbackID')==self.feedbackID: all_data[i]=self.toDict(); upd=True; break
        if not upd: all_data.append(self.toDict())
        _saveData(Feedback.FILE_PATH,all_data)
    @classmethod
    def findByID(cls,fid): return next((cls.fromDict(d) for d in _loadData(Feedback.FILE_PATH) if d.get('feedbackID')==fid),None)
    @classmethod
    def getAll(cls,status_filter=None): 
        feedbacks=[cls.fromDict(d) for d in _loadData(Feedback.FILE_PATH) if d]
        valid_feedbacks = [fb for fb in feedbacks if fb] # Filter out None objects
        if status_filter:
            return [fb for fb in valid_feedbacks if fb.status==status_filter]
        return valid_feedbacks
    def get_responses(self): return [Response.findByID(rid) for rid in self.responseIDs if Response.findByID(rid)]

# --- Response Model ---
class Response:
    FILE_PATH = RESPONSE_DATA_FILE
    def __init__(self, feedbackID, responderAdminID, responseContent, responseID=None, responseDatetime=None):
        self.responseID=responseID or str(uuid.uuid4());self.feedbackID=feedbackID;self.responderAdminID=responderAdminID;self.responseContent=responseContent;self.responseDatetime=responseDatetime or datetime.now() # noqa
    def toDict(self): return {'responseID':self.responseID,'feedbackID':self.feedbackID,'responderAdminID':self.responderAdminID,'responseContent':self.responseContent,'responseDatetime':self.responseDatetime.isoformat()} # noqa
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['feedbackID','responderAdminID','responseContent']): return None
        resp_items = {k:v for k,v in data.items() if k!='responseDatetime'}
        resp=cls(**resp_items)
        dt_str=data.get('responseDatetime')
        if dt_str: 
            try: resp.responseDatetime=datetime.fromisoformat(dt_str)
            except ValueError: resp.responseDatetime=datetime.now()
        else: resp.responseDatetime=datetime.now()
        return resp
    def save(self): 
        all_data=_loadData(Response.FILE_PATH);upd=False
        for i,d in enumerate(all_data):
            if d.get('responseID')==self.responseID: all_data[i]=self.toDict(); upd=True; break
        if not upd: all_data.append(self.toDict())
        _saveData(Response.FILE_PATH,all_data)
    @classmethod
    def findByID(cls,rid): return next((cls.fromDict(d) for d in _loadData(Response.FILE_PATH) if d.get('responseID')==rid),None)
    @classmethod
    def find_by_feedbackID(cls,fid): 
        all_data = _loadData(Response.FILE_PATH)
        responses = []
        for item_data in all_data:
            if item_data.get('feedbackID') == fid:
                resp_obj = cls.fromDict(item_data)
                if resp_obj: responses.append(resp_obj)
        return responses

# --- Notification Model ---
class Notification:
    FILE_PATH = NOTIFICATION_DATA_FILE
    def __init__(self, recipientuserID, senderuserID, messageContent, notificationType="General", notificationID=None, sentDatetime=None, readStatus=False): # noqa
        self.notificationID=notificationID or str(uuid.uuid4());self.recipientuserID=recipientuserID;self.senderuserID=senderuserID;self.messageContent=messageContent;self.notificationType=notificationType;self.sentDatetime=sentDatetime or datetime.now();self.readStatus=readStatus # noqa
    def mark_as_read(self): self.readStatus=True
    def toDict(self): return {'notificationID':self.notificationID,'recipientuserID':self.recipientuserID,'senderuserID':self.senderuserID,'messageContent':self.messageContent,'notificationType':self.notificationType,'sentDatetime':self.sentDatetime.isoformat(),'readStatus':self.readStatus} # noqa
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['recipientuserID','messageContent']): return None
        notif_items = {k:v for k,v in data.items() if k!='sentDatetime'}
        notif=cls(**notif_items)
        dt_str=data.get('sentDatetime')
        if dt_str: 
            try: notif.sentDatetime=datetime.fromisoformat(dt_str)
            except ValueError: notif.sentDatetime=datetime.now()
        else: notif.sentDatetime=datetime.now()
        return notif
    def save(self): 
        all_data=_loadData(Notification.FILE_PATH)
        all_data.append(self.toDict()) # Notifications are usually just appended
        _saveData(Notification.FILE_PATH,all_data)
    @classmethod
    def find_by_recipient_id(cls,uid,unread_only=False): 
        notifications_data = _loadData(Notification.FILE_PATH)
        notifications = []
        for item_data in notifications_data:
            if item_data.get('recipientuserID') == uid:
                notif_obj = cls.fromDict(item_data)
                if notif_obj: notifications.append(notif_obj)
        
        if unread_only:
            return [n for n in notifications if not n.readStatus]
        return notifications