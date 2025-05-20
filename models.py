# models.py
import uuid
from datetime import datetime
import hashlib # For User model if you have password hashing

class User:
    def __init__(self, username, email, password, user_id=None):
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.username = username
        self.email = email
        if password:
            self.password_hash = self._hash_password(password)
        else:
            self.password_hash = None 

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password_to_check):
        if not self.password_hash or not password_to_check:
            return False
        return self.password_hash == self._hash_password(password_to_check)

    def to_dict(self):
        """Converts the User object to a dictionary for JSON serialization."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
    
    @classmethod
    def from_dict(cls, data):
        """Creates a User instance from a dictionary (e.g., loaded from JSON)."""
        if not isinstance(data, dict):
            print(f"Error: User.from_dict expected a dictionary, but received {type(data)}: {data}")
            return None # Or raise TypeError("User data must be a dictionary")

        # Extract values safely using .get()
        user_id = data.get('user_id')
        username = data.get('username')
        email = data.get('email')
        password_hash_from_data = data.get('password_hash')

        # Basic validation for critical fields
        if not user_id or not username or not email or not password_hash_from_data:
            print(f"Warning: User data missing one or more critical fields (user_id, username, email, password_hash). Data: {data}")
            # Depending on your application's strictness, you might want to return None here
            # if any critical field is missing, making the object invalid.
            # For now, we proceed but the object might be incomplete.
            # return None 

        # When creating from dict, we don't have the original password, only the hash.
        # So, pass password=None to __init__ and then set the hash directly.
        user = cls(
            username=username, 
            email=email, 
            password=None,  # Plain password not available during loading
            user_id=user_id
        )
        user.password_hash = password_hash_from_data # Set the loaded hash

        return user

class Trip:
    def __init__(self, trip_id, origin, destination, departure_time, price, available_seats):
        self.trip_id = trip_id
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time 
        self.price = price
        self.available_seats = available_seats

    def __str__(self):
        return f"Trip {self.trip_id}: {self.origin} to {self.destination} at {self.departure_time} ({self.available_seats} seats left)"

    def to_dict(self):
        return {
            'trip_id': self.trip_id,
            'origin': self.origin,
            'destination': self.destination,
            'departure_time': str(self.departure_time), # Ensure serializable if datetime
            'price': self.price,
            'available_seats': self.available_seats
        }

    @classmethod
    def from_dict(cls, data):
        # Assuming all fields are critical for a trip
        if not all(key in data for key in ['trip_id', 'origin', 'destination', 'departure_time', 'price', 'available_seats']):
            print(f"Warning: Trip data missing critical fields: {data}")
            return None # Or raise an error
        return cls(**data)


class Payment:
    def __init__(self, order_id, amount, method="MockCard", status="Completed", payment_id=None):
        self.payment_id = payment_id if payment_id else str(uuid.uuid4())
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.status = status
        self.payment_datetime = datetime.now()

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'method': self.method,
            'status': self.status,
            'payment_datetime': self.payment_datetime.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        payment = cls(
            order_id=data.get('order_id'), # Critical
            amount=data.get('amount'),     # Critical
            method=data.get('method', "MockCard"),
            status=data.get('status', "Completed"),
            payment_id=data.get('payment_id') # Critical
        )
        if not payment.order_id or payment.amount is None or not payment.payment_id:
            print(f"Warning: Payment data missing critical fields: {data}")
            return None

        dt_str = data.get('payment_datetime')
        if dt_str:
            try: payment.payment_datetime = datetime.fromisoformat(dt_str)
            except ValueError: payment.payment_datetime = datetime.now(); print(f"Warning: Invalid payment_datetime format for {payment.payment_id}")
        else: payment.payment_datetime = datetime.now()
        return payment


class Ticket:
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
            self.status = "Voided"; return True
        return False

    def to_dict(self):
        return {
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'trip_id': self.trip_id,
            'order_id': self.order_id,
            'payment_id': self.payment_id,
            'seat_number': self.seat_number,
            'issue_datetime': self.issue_datetime.isoformat(),
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        ticket = cls( 
            user_id=data.get('user_id'),
            trip_id=data.get('trip_id'),
            order_id=data.get('order_id'), # Corrected: use .get()
            payment_id=data.get('payment_id'), # Corrected: use .get()
            seat_number=data.get('seat_number'),
            ticket_id=data.get('ticket_id'),
            status=data.get('status', "Active")
        )
        # Check for critical missing fields after initial object creation
        if not ticket.user_id or not ticket.trip_id or not ticket.ticket_id or not ticket.order_id or not ticket.payment_id:
            print(f"Warning: Ticket data missing critical fields: {data}")
            # Depending on requirements, you might return None here or raise an error.
            # If these are truly essential for the object to be valid.
            # For now, it will proceed with potentially None values for these fields if missing.

        dt_str = data.get('issue_datetime')
        if dt_str:
            try: ticket.issue_datetime = datetime.fromisoformat(dt_str)
            except ValueError: ticket.issue_datetime = datetime.now(); print(f"Warning: Invalid issue_datetime format for ticket {ticket.ticket_id}")
        else: ticket.issue_datetime = datetime.now() 
        return ticket


class Order:
    def __init__(self, user_id, trip_id, num_tickets, total_amount, order_id=None, status="Completed"):
        self.order_id = order_id if order_id else str(uuid.uuid4())
        self.user_id = user_id
        self.trip_id = trip_id
        self.num_tickets = num_tickets
        self.total_amount = total_amount
        self.order_datetime = datetime.now()
        self.status = status

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'trip_id': self.trip_id,
            'num_tickets': self.num_tickets,
            'total_amount': self.total_amount,
            'order_datetime': self.order_datetime.isoformat(),
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        order = cls(
            user_id=data.get('user_id'),
            trip_id=data.get('trip_id'),
            num_tickets=data.get('num_tickets'),
            total_amount=data.get('total_amount'),
            order_id=data.get('order_id'),
            status=data.get('status', 'Completed')
        )
        if not order.user_id or not order.trip_id or order.num_tickets is None or order.total_amount is None or not order.order_id:
            print(f"Warning: Order data missing critical fields: {data}")
            return None

        dt_str = data.get('order_datetime')
        if dt_str:
            try: order.order_datetime = datetime.fromisoformat(dt_str)
            except ValueError: order.order_datetime = datetime.now(); print(f"Warning: Invalid order_datetime format for {order.order_id}")
        else: order.order_datetime = datetime.now()
        return order


class Refund:
    def __init__(self, payment_id, order_id, ticket_id, refund_amount, refund_reason="User requested cancellation", refund_id=None, status="Pending"):
        self.refund_id = refund_id if refund_id else str(uuid.uuid4())
        self.payment_id = payment_id
        self.order_id = order_id
        self.ticket_id = ticket_id 
        self.refund_amount = refund_amount
        self.refund_reason = refund_reason
        self.status = status
        self.request_datetime = datetime.now()
        self.processed_datetime = None

    def update_status(self, new_status):
        self.status = new_status
        if self.status == "Processed" or self.status == "Failed": 
            self.processed_datetime = datetime.now()

    def to_dict(self):
        return {
            'refund_id': self.refund_id,
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'ticket_id': self.ticket_id,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason,
            'status': self.status,
            'request_datetime': self.request_datetime.isoformat(),
            'processed_datetime': self.processed_datetime.isoformat() if self.processed_datetime else None,
        }

    @classmethod
    def from_dict(cls, data):
        refund = cls(
            payment_id=data.get('payment_id'),
            order_id=data.get('order_id'),
            ticket_id=data.get('ticket_id'),
            refund_amount=data.get('refund_amount'),
            refund_reason=data.get('refund_reason'),
            refund_id=data.get('refund_id'),
            status=data.get('status', 'Pending')
        )
        if not refund.payment_id or not refund.order_id or not refund.ticket_id or refund.refund_amount is None or not refund.refund_id:
            print(f"Warning: Refund data missing critical fields: {data}")
            return None

        req_dt_str = data.get('request_datetime')
        if req_dt_str:
            try: refund.request_datetime = datetime.fromisoformat(req_dt_str)
            except ValueError: refund.request_datetime = datetime.now(); print(f"Warning: Invalid request_datetime for refund {refund.refund_id}")
        else: refund.request_datetime = datetime.now()

        proc_dt_str = data.get('processed_datetime')
        if proc_dt_str:
            try: refund.processed_datetime = datetime.fromisoformat(proc_dt_str)
            except ValueError: refund.processed_datetime = None; print(f"Warning: Invalid processed_datetime for refund {refund.refund_id}")
        return refund
    
class Location:
    def __init__(self, latitude, longitude, address_line1, city, postcode, location_id=None):
        self.location_id = location_id if location_id else str(uuid.uuid4())
        self.latitude = latitude
        self.longitude = longitude
        self.address_line1 = address_line1
        self.city = city
        self.postcode = postcode

    def set_details(self, latitude=None, longitude=None, address_line1=None, city=None, postcode=None):
        """Updates location details if new values are provided."""
        if latitude is not None: self.latitude = latitude
        if longitude is not None: self.longitude = longitude
        if address_line1 is not None: self.address_line1 = address_line1
        if city is not None: self.city = city
        if postcode is not None: self.postcode = postcode
        return True # Indicate success

    def __str__(self):
        return f"{self.address_line1}, {self.city}"

    def to_dict(self):
        return {
            'location_id': self.location_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address_line1': self.address_line1,
            'city': self.city,
            'postcode': self.postcode
        }

    @classmethod
    def from_dict(cls, data):
        if not all(k in data for k in ['latitude', 'longitude', 'address_line1', 'city', 'postcode']):
            print(f"Warning: Location data missing critical fields: {data}")
            return None
        return cls(
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            address_line1=data.get('address_line1'),
            city=data.get('city'),
            postcode=data.get('postcode'),
            location_id=data.get('location_id')
        )


class Stop:
    def __init__(self, stop_name, location_id, stop_id=None, stop_code=None): # location_id links to a Location object
        self.stop_id = stop_id if stop_id else str(uuid.uuid4())
        self.stop_name = stop_name
        self.location_id = location_id # This will be the ID of a Location object
        self.stop_code = stop_code if stop_code else self.stop_id[:6].upper() # Example stop code
        # self.location_obj = None # To hold the actual Location object, loaded by repository/service

    def update_location(self, location_repository, new_latitude, new_longitude, new_address, new_city, new_postcode):
        """
        Updates the associated Location object's details.
        The Stop object itself primarily holds the location_id.
        The actual Location object is fetched and updated.
        """
        location = location_repository.find_by_id(self.location_id)
        if location:
            success = location.set_details(new_latitude, new_longitude, new_address, new_city, new_postcode)
            if success:
                location_repository.save(location) # Persist changes to the Location object
                return True, "Location details updated successfully."
            else:
                return False, "Failed to set new location details on Location object."
        return False, f"Location with ID {self.location_id} not found for this stop."


    def to_dict(self):
        return {
            'stop_id': self.stop_id,
            'stop_name': self.stop_name,
            'location_id': self.location_id,
            'stop_code': self.stop_code
        }

    @classmethod
    def from_dict(cls, data):
        if not all(k in data for k in ['stop_name', 'location_id']):
            print(f"Warning: Stop data missing critical fields: {data}")
            return None
        return cls(
            stop_name=data.get('stop_name'),
            location_id=data.get('location_id'),
            stop_id=data.get('stop_id'),
            stop_code=data.get('stop_code')
        )


class Route:
    def __init__(self, route_name, description, route_id=None):
        self.route_id = route_id if route_id else str(uuid.uuid4())
        self.route_name = route_name
        self.description = description
        self.stop_ids = [] # List of stop_id strings in order for this route
        # self.stops_objs = [] # To hold actual Stop objects, loaded by repository/service

    def add_stop_id(self, stop_id):
        if stop_id not in self.stop_ids:
            self.stop_ids.append(stop_id)
            return True
        return False # Stop already exists

    def remove_stop_id(self, stop_id):
        if stop_id in self.stop_ids:
            self.stop_ids.remove(stop_id)
            return True
        return False

    def find_stop_id(self, stop_id_to_find): # As per sequence diagram, Route finds its own stop
        """Checks if a stop_id is part of this route."""
        return stop_id_to_find if stop_id_to_find in self.stop_ids else None
    
    # The updateStopLocation would be handled by a service, which then calls methods on Route, Stop, Location

    def to_dict(self):
        return {
            'route_id': self.route_id,
            'route_name': self.route_name,
            'description': self.description,
            'stop_ids': self.stop_ids
        }

    @classmethod
    def from_dict(cls, data):
        if not data.get('route_name'):
            print(f"Warning: Route data missing route_name: {data}")
            return None
        route = cls(
            route_name=data.get('route_name'),
            description=data.get('description'),
            route_id=data.get('route_id')
        )
        route.stop_ids = data.get('stop_ids', [])
        return route

# Admin model can be a specialization of User or a simple flag
class Admin(User):
    def __init__(self, username, email, password, user_id=None, admin_level="superuser"):
        super().__init__(username, email, password, user_id)
        self.admin_level = admin_level
        # You might add specific permissions or roles here

    def to_dict(self):
        data = super().to_dict()
        data['admin_level'] = self.admin_level
        data['is_admin'] = True # Flag for easier identification
        return data

    @classmethod
    def from_dict(cls, data):
        # If loading from User data that doesn't have admin_level, provide default
        user = super(Admin, cls).from_dict(data)
        if user: # Ensure base user was created successfully
            admin = cls(username=user.username, email=user.email, password=None, user_id=user.user_id) # Password already hashed
            admin.password_hash = user.password_hash
            admin.admin_level = data.get('admin_level', 'default_admin')
            return admin
        return None
    
class Feedback:
    def __init__(self, submitter_user_id, feedback_content, rating=None, related_trip_id=None, feedback_id=None, status="New", submission_datetime=None):
        self.feedback_id = feedback_id if feedback_id else str(uuid.uuid4())
        self.submitter_user_id = submitter_user_id # ID of the ArtPassenger
        self.feedback_content = feedback_content
        self.rating = rating # Optional, e.g., 1-5 stars
        self.related_trip_id = related_trip_id # Optional link to a trip
        self.status = status # e.g., "New", "Pending", "Responded", "Closed"
        self.submission_datetime = submission_datetime if submission_datetime else datetime.now()
        self.response_ids = [] # List of response_id strings associated with this feedback

    def update_status(self, new_status):
        self.status = new_status
        return True

    def add_response_id(self, response_id):
        if response_id not in self.response_ids:
            self.response_ids.append(response_id)

    def to_dict(self):
        return {
            'feedback_id': self.feedback_id,
            'submitter_user_id': self.submitter_user_id,
            'feedback_content': self.feedback_content,
            'rating': self.rating,
            'related_trip_id': self.related_trip_id,
            'status': self.status,
            'submission_datetime': self.submission_datetime.isoformat(),
            'response_ids': self.response_ids
        }

    @classmethod
    def from_dict(cls, data):
        if not data.get('submitter_user_id') or not data.get('feedback_content'):
            print(f"Warning: Feedback data missing critical fields: {data}")
            return None
        feedback = cls(
            submitter_user_id=data.get('submitter_user_id'),
            feedback_content=data.get('feedback_content'),
            rating=data.get('rating'),
            related_trip_id=data.get('related_trip_id'),
            feedback_id=data.get('feedback_id'),
            status=data.get('status', "New")
        )
        dt_str = data.get('submission_datetime')
        if dt_str:
            try: feedback.submission_datetime = datetime.fromisoformat(dt_str)
            except ValueError: feedback.submission_datetime = datetime.now()
        else: feedback.submission_datetime = datetime.now()
        feedback.response_ids = data.get('response_ids', [])
        return feedback

class Response: # An Admin's response to a piece of Feedback
    def __init__(self, feedback_id, responder_admin_id, response_content, response_id=None, response_datetime=None):
        self.response_id = response_id if response_id else str(uuid.uuid4())
        self.feedback_id = feedback_id # Link to the original Feedback
        self.responder_admin_id = responder_admin_id # ID of the Admin who responded
        self.response_content = response_content
        self.response_datetime = response_datetime if response_datetime else datetime.now()

    def to_dict(self):
        return {
            'response_id': self.response_id,
            'feedback_id': self.feedback_id,
            'responder_admin_id': self.responder_admin_id,
            'response_content': self.response_content,
            'response_datetime': self.response_datetime.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        if not all(k in data for k in ['feedback_id', 'responder_admin_id', 'response_content']):
            print(f"Warning: Response data missing critical fields: {data}")
            return None
        response = cls(
            feedback_id=data.get('feedback_id'),
            responder_admin_id=data.get('responder_admin_id'),
            response_content=data.get('response_content'),
            response_id=data.get('response_id')
        )
        dt_str = data.get('response_datetime')
        if dt_str:
            try: response.response_datetime = datetime.fromisoformat(dt_str)
            except ValueError: response.response_datetime = datetime.now()
        else: response.response_datetime = datetime.now()
        return response

class Notification: # Simplified notification model
    def __init__(self, recipient_user_id, sender_user_id, message_content, notification_type="FeedbackResponse", notification_id=None, sent_datetime=None, read_status=False):
        self.notification_id = notification_id if notification_id else str(uuid.uuid4())
        self.recipient_user_id = recipient_user_id
        self.sender_user_id = sender_user_id # Could be an Admin ID or System ID
        self.message_content = message_content
        self.notification_type = notification_type
        self.sent_datetime = sent_datetime if sent_datetime else datetime.now()
        self.read_status = read_status

    def mark_as_read(self):
        self.read_status = True

    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'recipient_user_id': self.recipient_user_id,
            'sender_user_id': self.sender_user_id,
            'message_content': self.message_content,
            'notification_type': self.notification_type,
            'sent_datetime': self.sent_datetime.isoformat(),
            'read_status': self.read_status
        }

    @classmethod
    def from_dict(cls, data):
        # Basic validation
        if not all(k in data for k in ['recipient_user_id', 'message_content']):
            print(f"Warning: Notification data missing critical fields: {data}")
            return None
        notification = cls(
            recipient_user_id=data.get('recipient_user_id'),
            sender_user_id=data.get('sender_user_id', "System"), # Default sender
            message_content=data.get('message_content'),
            notification_type=data.get('notification_type', "General"),
            notification_id=data.get('notification_id')
        )
        dt_str = data.get('sent_datetime')
        if dt_str:
            try: notification.sent_datetime = datetime.fromisoformat(dt_str)
            except ValueError: notification.sent_datetime = datetime.now()
        else: notification.sent_datetime = datetime.now()
        notification.read_status = data.get('read_status', False)
        return notification