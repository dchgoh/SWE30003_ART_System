# models.py
import uuid
from datetime import datetime
import hashlib
import json
import os

# --- Helper function for JSON file operations ---
def _loadData(filePath): 
    if not os.path.exists(filePath):
        with open(filePath, 'w') as f:
            json.dump([], f)
        return []
    if os.path.getsize(filePath) == 0: # Check for empty file
        return []
    with open(filePath, 'r') as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: Data in {filePath} is not a list. Initializing as empty.")
                with open(filePath, 'w') as f_reset: json.dump([], f_reset)
                return []
            return data
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {filePath}. Returning empty list.")
            return []

def _saveData(filePath, allItemsData): 
    with open(filePath, 'w') as f:
        json.dump(allItemsData, f, indent=4)

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
ORDER_LINE_ITEM_DATA_FILE = 'order_line_items.json'


class User:
    FILE_PATH = USER_DATA_FILE
    def __init__(self, username, email, password, userID=None, isAdmin=False, adminLevel=None, phone=None, firstName=None, lastName=None, dateRegistered=None, accountStatus="Active"):
        self.userID = userID if userID else str(uuid.uuid4())
        self.username = username
        self.email = email
        self.passwordHash = self._hashPassword(password) if password else None
        self.isAdmin = isAdmin
        self.adminLevel = adminLevel if isAdmin else None
        self.phone = phone
        self.firstName = firstName
        self.lastName = lastName
        self.dateRegistered = dateRegistered if dateRegistered else datetime.now()
        self.accountStatus = accountStatus

    def _hashPassword(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def checkPassword(self, passwordToCheck):
        if not self.passwordHash or not passwordToCheck:
            return False
        return self.passwordHash == self._hashPassword(passwordToCheck)

    def toDict(self):
        data = {'userID': self.userID, 'username': self.username, 'email': self.email,
                'passwordHash': self.passwordHash, 'isAdmin': self.isAdmin,
                'phone':self.phone,'firstName':self.firstName,'lastName':self.lastName,
                'dateRegistered':self.dateRegistered.isoformat() if isinstance(self.dateRegistered,datetime) else str(self.dateRegistered),
                'accountStatus':self.accountStatus,'_userType':self.__class__.__name__}
        if self.isAdmin and hasattr(self, 'adminLevel'): # Ensure adminLevel exists before adding
            data['adminLevel'] = self.adminLevel
        return data
    
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data, dict): return None
        userType = data.get('_userType')
        userID = data.get('userID'); username = data.get('username'); email = data.get('email')
        passwordHashFromData = data.get('passwordHash'); phone = data.get('phone')
        firstName = data.get('firstName'); lastName = data.get('lastName')
        dateRegisteredStr = data.get('dateRegistered'); accountStatus = data.get('accountStatus', "Active")
        dateRegistered = datetime.fromisoformat(dateRegisteredStr) if dateRegisteredStr else datetime.now()
        try:
            if dateRegisteredStr: dateRegistered = datetime.fromisoformat(dateRegisteredStr)
        except (TypeError, ValueError): dateRegistered = datetime.now()


        if not all([userID, username, email, passwordHashFromData]): return None
        instance = None
        if userType == "Admin":
            instance = Admin(username,email,None,userID,phone,firstName,lastName,dateRegistered,accountStatus,data.get('adminLevel','default'))
        elif userType == "ArtPassenger":
            instance = ArtPassenger(username,email,None,userID,phone,firstName,lastName,dateRegistered,accountStatus,data.get('paymentMethods',[]),data.get('bookingHistory',[]),data.get('preferences',{}),data.get('loyaltyPoints',0))
        else:
            instance = cls(username,email,None,userID,phone,firstName,lastName,dateRegistered,accountStatus)
        if instance: instance.passwordHash = passwordHashFromData
        return instance

    def save(self):
        allData = _loadData(User.FILE_PATH)
        updated = False
        isNew = not any(d.get('userID') == self.userID for d in allData)

        if isNew:
            for d in allData:
                if d.get('username') == self.username: print(f"Save fail: Username '{self.username}' exists."); return False
                if d.get('email') == self.email: print(f"Save fail: Email '{self.email}' exists."); return False
            allData.append(self.toDict())
            updated = True # Consider adding new as a form of update to the file
        else: # This is an update for an existing userID
            for i, d in enumerate(allData):
                if d.get('userID') == self.userID:
                    # Check for username/email conflict with *other* users
                    for other_d in allData:
                        if other_d.get('userID') != self.userID:
                            if other_d.get('username') == self.username: print(f"Update fail: Username '{self.username}' taken."); return False
                            if other_d.get('email') == self.email: print(f"Update fail: Email '{self.email}' taken."); return False
                    allData[i] = self.toDict()
                    updated = True
                    break
        if updated: _saveData(User.FILE_PATH, allData)
        return updated

    @classmethod
    def findByID(cls, userIDToFind):
        allData = _loadData(User.FILE_PATH)
        for d in allData:
            if d.get('userID') == userIDToFind: return User.fromDict(d) # Use base factory
        return None

    @classmethod
    def findByUsername(cls, usernameToFind):
        allData = _loadData(User.FILE_PATH)
        for d in allData:
            if d.get('username') == usernameToFind: return User.fromDict(d) # Use base factory
        return None
    
    @classmethod
    def getAll(cls):
        allData = _loadData(User.FILE_PATH); items = []
        for d in allData:
            obj = User.fromDict(d) # Use base factory
            if obj: items.append(obj)
        return items

class ArtPassenger(User):
    def __init__(self,username,email,password,userID=None,phone=None,firstName=None,lastName=None,dateRegistered=None,accountStatus="Active",paymentMethods=None,bookingHistory=None,preferences=None,loyaltyPoints=0):
        super().__init__(username,email,password,userID,phone,firstName,lastName,dateRegistered,accountStatus)
        self.paymentMethods=paymentMethods or []; self.bookingHistory=bookingHistory or []
        self.preferences=preferences or {}; self.loyaltyPoints=int(loyaltyPoints)
    def toDict(self):
        data=super().toDict()
        data.update({'paymentMethods':self.paymentMethods,'bookingHistory':self.bookingHistory,'preferences':self.preferences,'loyaltyPoints':self.loyaltyPoints})
        return data

class Admin(User):
    def __init__(self,username,email,password,userID=None,phone=None,firstName=None,lastName=None,dateRegistered=None,accountStatus="Active",adminLevel="staff",permissions=None,assignedArea=None):
        super().__init__(username,email,password,userID,phone,firstName,lastName,dateRegistered,accountStatus)
        self.adminLevel=adminLevel; self.permissions=permissions or []; self.assignedArea=assignedArea
    def toDict(self):
        data=super().toDict()
        data.update({'adminLevel':self.adminLevel,'permissions':self.permissions,'assignedArea':self.assignedArea})
        return data

# --- Trip Model ---
class Trip:
    FILE_PATH = TRIP_DATA_FILE
    def __init__(self, tripID, origin, destination, departureTime, price, availableSeats):
        self.tripID = tripID; self.origin=origin; self.destination=destination; self.departureTime=departureTime
        self.price=float(price); self.availableSeats=int(availableSeats)
    def toDict(self):
        return {'tripID':self.tripID,'origin':self.origin,'destination':self.destination,
                'departureTime':str(self.departureTime),'price':self.price,'availableSeats':self.availableSeats}
    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['tripID','origin','destination','departureTime','price','availableSeats']): return None
        try: return cls(data.get('tripID'),data.get('origin'),data.get('destination'),data.get('departureTime'),float(data.get('price')),int(data.get('availableSeats')))
        except (ValueError,TypeError): return None
    def save(self):
        allData = _loadData(Trip.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('tripID') == self.tripID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Trip.FILE_PATH, allData)
    @classmethod
    def findByID(cls,itemID):
        allData = _loadData(Trip.FILE_PATH)
        for itemData in allData:
            if itemData.get('tripID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def getAll(cls):
        allData = _loadData(Trip.FILE_PATH); items = []
        for itemData in allData:
            obj = cls.fromDict(itemData)
            if obj: items.append(obj)
        return items
    @classmethod
    def search(cls, origin=None, destination=None, dateStr=None):
        allTrips = cls.getAll(); filteredTrips = []
        for trip in allTrips:
            if not trip: continue
            match = True
            if origin and origin.lower() not in trip.origin.lower(): match = False
            if destination and destination.lower() not in trip.destination.lower(): match = False
            if dateStr and dateStr not in trip.departureTime: match = False
            if match and trip.availableSeats > 0: filteredTrips.append(trip)
        return filteredTrips
    def updateSeats(self, numSeats, operation="book"):
        numSeats = int(numSeats)
        if operation == "book":
            if self.availableSeats >= numSeats: self.availableSeats -= numSeats; return True
            return False
        elif operation == "refund": self.availableSeats += numSeats; return True
        return False

# --- OrderLineItem Model ---
class OrderLineItem:
    FILE_PATH = ORDER_LINE_ITEM_DATA_FILE
    def __init__(self, orderID, itemID, itemType, quantity, unitPrice, lineItemID=None):
        self.lineItemID = lineItemID if lineItemID else str(uuid.uuid4())
        self.orderID = orderID; self.itemID = itemID; self.itemType = itemType
        self.quantity = int(quantity); self.unitPrice = float(unitPrice)
    def calculateLineTotal(self): return self.quantity * self.unitPrice
    def toDict(self):
        return {'lineItemID':self.lineItemID,'orderID':self.orderID,'itemID':self.itemID,
                'itemType':self.itemType,'quantity':self.quantity,'unitPrice':self.unitPrice}
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data,dict) or not all(k in data for k in ['orderID','itemID','itemType','quantity','unitPrice']): return None
        try: return cls(data.get('orderID'),data.get('itemID'),data.get('itemType'),int(data.get('quantity')),float(data.get('unitPrice')),data.get('lineItemID'))
        except(ValueError,TypeError): return None
    def save(self):
        allData = _loadData(OrderLineItem.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('lineItemID') == self.lineItemID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(OrderLineItem.FILE_PATH, allData)
    @classmethod
    def findByID(cls,itemID):
        allData = _loadData(OrderLineItem.FILE_PATH)
        for itemData in allData:
            if itemData.get('lineItemID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def findByOrderID(cls,orderIDToFind):
        allData = _loadData(OrderLineItem.FILE_PATH); items = []
        for itemData in allData:
            if itemData.get('orderID') == orderIDToFind:
                obj = cls.fromDict(itemData)
                if obj: items.append(obj)
        return items

# --- Order Model (Works with OrderLineItem) ---
class Order:
    FILE_PATH = ORDER_DATA_FILE
    def __init__(self, userID, orderID=None, status="PendingPayment", orderDatetime=None):
        self.orderID = orderID if orderID else str(uuid.uuid4())
        self.userID = userID
        self.orderDatetime = orderDatetime if orderDatetime else datetime.now()
        self.status = status
    def getLineItems(self): return OrderLineItem.findByOrderID(self.orderID)
    def calculateTotalAmount(self):
        total = 0; lineItems = self.getLineItems()
        if lineItems:
            for item in lineItems:
                if item: total += item.calculateLineTotal()
        return total
    def toDict(self):
        return {'orderID':self.orderID,'userID':self.userID,'orderDatetime':self.orderDatetime.isoformat(),'status':self.status}
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data,dict) or not all(k in data for k in ['userID','orderID']): return None
        order = cls(userID=data.get('userID'),status=data.get('status','PendingPayment'),orderID=data.get('orderID'))
        dtStr = data.get('orderDatetime')
        if dtStr:
            try: order.orderDatetime = datetime.fromisoformat(dtStr)
            except ValueError: order.orderDatetime = datetime.now()
        return order
    def save(self):
        allData = _loadData(Order.FILE_PATH); updated = False; dictToSave = self.toDict()
        for i, itemData in enumerate(allData):
            if itemData.get('orderID') == self.orderID: allData[i] = dictToSave; updated = True; break
        if not updated: allData.append(dictToSave)
        _saveData(Order.FILE_PATH, allData); return True
    @classmethod
    def findByID(cls, itemID):
        allData = _loadData(Order.FILE_PATH)
        for itemData in allData:
            if itemData.get('orderID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def findByUserID(cls, userID):
        allData = _loadData(Order.FILE_PATH); orders = []
        for itemData in allData:
            if itemData.get('userID') == userID:
                obj = cls.fromDict(itemData)
                if obj: orders.append(obj)
        return orders
    @classmethod
    def getAll(cls):
        allData = _loadData(Order.FILE_PATH); items = []
        for itemData in allData:
            obj = cls.fromDict(itemData)
            if obj: items.append(obj)
        return items

# --- Ticket Model ---
class Ticket:
    FILE_PATH = TICKET_DATA_FILE
    def __init__(self, userID, tripID, orderID, paymentID, seatNumber=None, issueDatetime=None, ticketID=None, status="Active"):
        self.ticketID=ticketID or str(uuid.uuid4()); self.userID=userID; self.tripID=tripID; self.orderID=orderID; self.paymentID=paymentID
        self.seatNumber=seatNumber or "Any Available"; self.issueDatetime=issueDatetime or datetime.now(); self.status=status
    def void(self):
        if self.status=="Active": self.status="Voided"; return True
        return False
    def toDict(self): return {'ticketID':self.ticketID,'userID':self.userID,'tripID':self.tripID,'orderID':self.orderID,'paymentID':self.paymentID,'seatNumber':self.seatNumber,'issueDatetime':self.issueDatetime.isoformat(),'status':self.status}
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data,dict) or not all(k in data for k in ['userID','tripID','orderID','paymentID','ticketID']): return None
        ticket=cls(userID=data.get('userID'),tripID=data.get('tripID'),orderID=data.get('orderID'),paymentID=data.get('paymentID'),seatNumber=data.get('seatNumber'),ticketID=data.get('ticketID'),status=data.get('status',"Active"))
        dtStr=data.get('issueDatetime')
        if dtStr:
            try: ticket.issueDatetime=datetime.fromisoformat(dtStr)
            except ValueError: ticket.issueDatetime=datetime.now()
        return ticket
    def save(self):
        allData = _loadData(Ticket.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('ticketID') == self.ticketID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Ticket.FILE_PATH, allData)
    @classmethod
    def findByID(cls,itemID):
        allData = _loadData(Ticket.FILE_PATH)
        for itemData in allData:
            if itemData.get('ticketID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def findByOrderID(cls,orderIDToFind):
        allData = _loadData(Ticket.FILE_PATH); items = []
        for itemData in allData:
            if itemData.get('orderID') == orderIDToFind:
                obj = cls.fromDict(itemData)
                if obj: items.append(obj)
        return items
    @classmethod
    def deleteByOrderID(cls,orderIDToDelete):
        allData = _loadData(Ticket.FILE_PATH)
        remainingItems = [d for d in allData if d.get('orderID') != orderIDToDelete]
        if len(remainingItems) < len(allData):
            _saveData(Ticket.FILE_PATH, remainingItems); return True
        return False

# --- Payment Model ---
class Payment: # Copied expanded version from previous response
    FILE_PATH = PAYMENT_DATA_FILE
    def __init__(self, orderID, amount, method="MockCard", status="Completed", paymentID=None):
        self.paymentID=paymentID or str(uuid.uuid4()); self.orderID=orderID; self.amount=float(amount); self.method=method; self.status=status; self.paymentDatetime=datetime.now()
    def toDict(self): return {'paymentID':self.paymentID, 'orderID':self.orderID, 'amount':self.amount, 'method':self.method, 'status':self.status, 'paymentDatetime':self.paymentDatetime.isoformat()}
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data,dict) or not all(k in data for k in ['orderID','amount','paymentID']): return None
        try: payment=cls(orderID=data.get('orderID'),amount=float(data.get('amount')),method=data.get('method',"MockCard"),status=data.get('status',"Completed"),paymentID=data.get('paymentID'))
        except(ValueError,TypeError): return None
        dtStr=data.get('paymentDatetime')
        if dtStr:
            try: payment.paymentDatetime=datetime.fromisoformat(dtStr)
            except ValueError: payment.paymentDatetime=datetime.now()
        return payment
    def save(self): 
        allData = _loadData(Payment.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('paymentID') == self.paymentID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Payment.FILE_PATH, allData)
    @classmethod
    def findByID(cls,itemID): 
        allData = _loadData(Payment.FILE_PATH)
        for itemData in allData:
            if itemData.get('paymentID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def findByOrderID(cls,orderIDToFind): 
        allData = _loadData(Payment.FILE_PATH)
        for itemData in allData:
            if itemData.get('orderID') == orderIDToFind: return cls.fromDict(itemData)
        return None

# --- Refund Model ---
class Refund: # Copied expanded version
    FILE_PATH = REFUND_DATA_FILE
    def __init__(self, paymentID, orderID, ticketID, refundAmount, refundReason="User requested", refundID=None, status="Pending"):
        self.refundID=refundID or str(uuid.uuid4()); self.paymentID=paymentID; self.orderID=orderID; self.ticketID=ticketID; self.refundAmount=float(refundAmount)
        self.refundReason=refundReason; self.status=status; self.requestDatetime=datetime.now(); self.processedDatetime=None
    def updateStatus(self,newStatus): self.status=newStatus; self.processedDatetime=datetime.now() if newStatus in ["Processed","Failed"] else None
    def toDict(self): return {'refundID':self.refundID,'paymentID':self.paymentID,'orderID':self.orderID,'ticketID':self.ticketID,'refundAmount':self.refundAmount,'refundReason':self.refundReason,'status':self.status,'requestDatetime':self.requestDatetime.isoformat(),'processedDatetime':self.processedDatetime.isoformat() if self.processedDatetime else None}
    @classmethod
    def fromDict(cls, data):
        if not isinstance(data,dict) or not all(k in data for k in ['paymentID','orderID','ticketID','refundAmount','refundID']): return None
        try: refund=cls(paymentID=data.get('paymentID'),orderID=data.get('orderID'),ticketID=data.get('ticketID'),refundAmount=float(data.get('refundAmount')),refundReason=data.get('refundReason'),refundID=data.get('refundID'),status=data.get('status','Pending'))
        except(ValueError,TypeError): return None
        reqDtStr=data.get('requestDatetime')
        if reqDtStr:
            try: refund.requestDatetime=datetime.fromisoformat(reqDtStr)
            except ValueError: refund.requestDatetime=datetime.now()
        procDtStr=data.get('processedDatetime')
        if procDtStr:
            try: refund.processedDatetime=datetime.fromisoformat(procDtStr)
            except ValueError: refund.processedDatetime=None
        return refund
    def save(self): 
        allData = _loadData(Refund.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('refundID') == self.refundID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Refund.FILE_PATH, allData)

# --- Location Model ---
class Location: # Copied expanded version
    FILE_PATH = LOCATION_DATA_FILE
    def __init__(self, latitude, longitude, addressLine1, city, postcode, locationID=None):
        self.locationID=locationID or str(uuid.uuid4()); self.latitude=float(latitude); self.longitude=float(longitude)
        self.addressLine1=addressLine1; self.city=city; self.postcode=postcode
    def setDetails(self,latitude=None,longitude=None,addressLine1=None,city=None,postcode=None):
        if latitude is not None: self.latitude = float(latitude)
        if longitude is not None: self.longitude = float(longitude)
        if addressLine1 is not None: self.addressLine1 = addressLine1
        if city is not None: self.city = city
        if postcode is not None: self.postcode = postcode
        return True
    def toDict(self): return {'locationID':self.locationID,'latitude':self.latitude,'longitude':self.longitude,'addressLine1':self.addressLine1,'city':self.city,'postcode':self.postcode}
    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['latitude','longitude','addressLine1','city','postcode']): return None
        try: return cls(latitude=float(data.get('latitude')),longitude=float(data.get('longitude')),addressLine1=data.get('addressLine1'),city=data.get('city'),postcode=data.get('postcode'),locationID=data.get('locationID'))
        except(ValueError,TypeError): return None
    def save(self): 
        allData = _loadData(Location.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('locationID') == self.locationID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Location.FILE_PATH, allData)
    @classmethod
    def findByID(cls, itemID): 
        allData = _loadData(Location.FILE_PATH)
        for itemData in allData:
            if itemData.get('locationID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def getAll(cls): 
        allData = _loadData(Location.FILE_PATH); items = []
        for itemData in allData:
            obj = cls.fromDict(itemData)
            if obj: items.append(obj)
        return items

# --- Stop Model ---
class Stop: # Copied expanded version
    FILE_PATH = STOP_DATA_FILE
    def __init__(self, stopName, locationID, stopID=None, stopCode=None):
        self.stopID = stopID if stopID else str(uuid.uuid4())
        self.stopName = stopName; self.locationID = locationID
        self.stopCode = stopCode if stopCode else self.stopID[:6].upper()
    def toDict(self): return {'stopID':self.stopID,'stopName':self.stopName,'locationID':self.locationID,'stopCode':self.stopCode}
    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not all(k in data for k in ['stopName','locationID']): return None
        return cls(stopName=data.get('stopName'), locationID=data.get('locationID'),stopID=data.get('stopID'), stopCode=data.get('stopCode'))
    def updateLocationDetails(self, newLatitude, newLongitude, newAddressLine1, newCity, newPostcode):
        location = Location.findByID(self.locationID)
        if location:
            location.setDetails(newLatitude, newLongitude, newAddressLine1, newCity, newPostcode)
            location.save()
            return True, "Location details updated successfully."
        return False, f"Location with ID {self.locationID} not found for this stop."
    def save(self): 
        allData = _loadData(Stop.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('stopID') == self.stopID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Stop.FILE_PATH, allData)
    @classmethod
    def findByID(cls, itemID): 
        allData = _loadData(Stop.FILE_PATH)
        for itemData in allData:
            if itemData.get('stopID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def getAll(cls): 
        allData = _loadData(Stop.FILE_PATH); items = []
        for itemData in allData:
            obj = cls.fromDict(itemData)
            if obj: items.append(obj)
        return items
    def getLocation(self): return Location.findByID(self.locationID)

# --- Route Model ---
class Route: # Copied expanded version
    FILE_PATH = ROUTE_DATA_FILE
    def __init__(self, routeName, description, routeID=None, stopIDs=None):
        self.routeID = routeID if routeID else str(uuid.uuid4())
        self.routeName = routeName; self.description = description
        self.stopIDs = stopIDs if stopIDs is not None else []
    def addStopID(self, stopID):
        if stopID not in self.stopIDs: self.stopIDs.append(stopID); return True
        return False
    def findStopID(self, stopIDToFind): return stopIDToFind if stopIDToFind in self.stopIDs else None
    def toDict(self): return {'routeID':self.routeID,'routeName':self.routeName,'description':self.description,'stopIDs':self.stopIDs}
    @classmethod
    def fromDict(cls,data):
        if not isinstance(data,dict) or not data.get('routeName') or not data.get('routeID'): return None
        route = cls(routeName=data.get('routeName'), description=data.get('description'), routeID=data.get('routeID'))
        route.stopIDs = data.get('stopIDs', []); return route
    def save(self): 
        allData = _loadData(Route.FILE_PATH); updated = False
        for i, itemData in enumerate(allData):
            if itemData.get('routeID') == self.routeID: allData[i] = self.toDict(); updated = True; break
        if not updated: allData.append(self.toDict())
        _saveData(Route.FILE_PATH, allData)
    @classmethod
    def findByID(cls, itemID): 
        allData = _loadData(Route.FILE_PATH)
        for itemData in allData:
            if itemData.get('routeID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def getAll(cls): 
        allData = _loadData(Route.FILE_PATH); items = []
        for itemData in allData:
            obj = cls.fromDict(itemData)
            if obj: items.append(obj)
        return items
    def getStopsObjects(self):
        stops = []; [stops.append(obj) for stopID in self.stopIDs if (obj := Stop.findByID(stopID))]
        return stops

# --- Feedback Model ---
class Feedback: # Copied expanded version
    FILE_PATH = FEEDBACK_DATA_FILE
    def __init__(self, submitterUserID, feedbackContent, rating=None, relatedTripID=None, feedbackID=None, status="New", submissionDatetime=None, responseIDs=None):
        self.feedbackID=feedbackID or str(uuid.uuid4());self.submitterUserID=submitterUserID;self.feedbackContent=feedbackContent;self.rating=rating;self.relatedTripID=relatedTripID;self.status=status;self.submissionDatetime=submissionDatetime or datetime.now();self.responseIDs=responseIDs or []
    def updateStatus(self,newStatus): self.status=newStatus
    def addResponseID(self,rid): (self.responseIDs.append(rid)) if rid not in self.responseIDs else None
    def toDict(self): return {'feedbackID':self.feedbackID,'submitterUserID':self.submitterUserID,'feedbackContent':self.feedbackContent,'rating':self.rating,'relatedTripID':self.relatedTripID,'status':self.status,'submissionDatetime':self.submissionDatetime.isoformat(),'responseIDs':self.responseIDs}
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['submitterUserID','feedbackContent']): return None
        fbItems = {k:v for k,v in data.items() if k not in ['submissionDatetime','responseIDs']}
        fb = cls(**fbItems)
        dtStr=data.get('submissionDatetime')
        if dtStr: 
            try: fb.submissionDatetime=datetime.fromisoformat(dtStr)
            except ValueError: fb.submissionDatetime=datetime.now()
        else: fb.submissionDatetime = datetime.now()
        fb.responseIDs=data.get('responseIDs',[]); return fb
    def save(self): 
        allData=_loadData(Feedback.FILE_PATH);upd=False
        for i,d in enumerate(allData):
            if d.get('feedbackID')==self.feedbackID: allData[i]=self.toDict(); upd=True; break
        if not upd: allData.append(self.toDict())
        _saveData(Feedback.FILE_PATH,allData)
    @classmethod
    def findByID(cls,itemID): 
        allData = _loadData(Feedback.FILE_PATH)
        for itemData in allData:
            if itemData.get('feedbackID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def getAll(cls,statusFilter=None): 
        allData = _loadData(Feedback.FILE_PATH); items = []
        for d in allData:
            obj = cls.fromDict(d)
            if obj: items.append(obj)
        if statusFilter: return [fb for fb in items if fb.status==statusFilter]
        return items
    def getResponses(self): return [Response.findByID(rid) for rid in self.responseIDs if Response.findByID(rid)]

# --- Response Model ---
class Response: # Copied expanded version
    FILE_PATH = RESPONSE_DATA_FILE
    def __init__(self, feedbackID, responderAdminID, responseContent, responseID=None, responseDatetime=None):
        self.responseID=responseID or str(uuid.uuid4());self.feedbackID=feedbackID;self.responderAdminID=responderAdminID;self.responseContent=responseContent;self.responseDatetime=responseDatetime or datetime.now()
    def toDict(self): return {'responseID':self.responseID,'feedbackID':self.feedbackID,'responderAdminID':self.responderAdminID,'responseContent':self.responseContent,'responseDatetime':self.responseDatetime.isoformat()}
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['feedbackID','responderAdminID','responseContent']): return None
        respItems = {k:v for k,v in data.items() if k!='responseDatetime'}
        resp=cls(**respItems)
        dtStr=data.get('responseDatetime')
        if dtStr: 
            try: resp.responseDatetime=datetime.fromisoformat(dtStr)
            except ValueError: resp.responseDatetime=datetime.now()
        else: resp.responseDatetime=datetime.now()
        return resp
    def save(self): 
        allData=_loadData(Response.FILE_PATH);upd=False
        for i,d in enumerate(allData):
            if d.get('responseID')==self.responseID: allData[i]=self.toDict(); upd=True; break
        if not upd: allData.append(self.toDict())
        _saveData(Response.FILE_PATH,allData)
    @classmethod
    def findByID(cls,itemID): 
        allData = _loadData(Response.FILE_PATH)
        for itemData in allData:
            if itemData.get('responseID') == itemID: return cls.fromDict(itemData)
        return None
    @classmethod
    def findByFeedbackID(cls,feedbackIDToFind): 
        allData = _loadData(Response.FILE_PATH); items = []
        for d in allData:
            if d.get('feedbackID') == feedbackIDToFind:
                obj = cls.fromDict(d)
                if obj: items.append(obj)
        return items

# --- Notification Model ---
class Notification: # Copied expanded version
    FILE_PATH = NOTIFICATION_DATA_FILE
    def __init__(self, recipientUserID, senderUserID, messageContent, notificationType="General", notificationID=None, sentDatetime=None, readStatus=False):
        self.notificationID=notificationID or str(uuid.uuid4());self.recipientUserID=recipientUserID;self.senderUserID=senderUserID;self.messageContent=messageContent;self.notificationType=notificationType;self.sentDatetime=sentDatetime or datetime.now();self.readStatus=readStatus
    def markAsRead(self): self.readStatus=True
    def toDict(self): return {'notificationID':self.notificationID,'recipientUserID':self.recipientUserID,'senderUserID':self.senderUserID,'messageContent':self.messageContent,'notificationType':self.notificationType,'sentDatetime':self.sentDatetime.isoformat(),'readStatus':self.readStatus}
    @classmethod
    def fromDict(cls,data): 
        if not isinstance(data,dict) or not all(k in data for k in ['recipientUserID','messageContent']): return None
        notifItems = {k:v for k,v in data.items() if k!='sentDatetime'}
        notif=cls(**notifItems)
        dtStr=data.get('sentDatetime')
        if dtStr: 
            try: notif.sentDatetime=datetime.fromisoformat(dtStr)
            except ValueError: notif.sentDatetime=datetime.now()
        else: notif.sentDatetime=datetime.now()
        return notif
    def save(self): 
        allData=_loadData(Notification.FILE_PATH)
        allData.append(self.toDict()) # Notifications are typically just appended
        _saveData(Notification.FILE_PATH,allData)
    @classmethod
    def findByRecipientID(cls,userIDToFind,unreadOnly=False): 
        allData = _loadData(Notification.FILE_PATH); items = []
        for d in allData:
            if d.get('recipientUserID') == userIDToFind:
                obj = cls.fromDict(d)
                if obj: items.append(obj)
        if unreadOnly: return [n for n in items if not n.readStatus]
        return items