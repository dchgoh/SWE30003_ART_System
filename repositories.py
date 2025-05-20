# repositories.py
import json
import os
from models import User, Admin, Trip, Ticket, Payment, Order, Refund, Location, Stop, Route, Feedback, Response, Notification

# --- User Repository ---
USER_DATA_FILE = 'users.json'
class UserRepository:
    def __init__(self):
        if not os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'w') as f: json.dump([], f)

    def _load_users(self):
        if not os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'w') as f: json.dump([], f)
        with open(USER_DATA_FILE, 'r') as f:
            try:
                users_data = json.load(f)
                if not isinstance(users_data, list): users_data = []
            except json.JSONDecodeError: users_data = []
        return [user_obj for ud in users_data if (user_obj := User.from_dict(ud)) is not None]

    def _save_users(self, users):
        user_dicts = []
        for user in users:
            if isinstance(user, User): user_dicts.append(user.to_dict())
            else: print(f"Warning: Attempted to save a non-User object: {user}"); continue
        with open(USER_DATA_FILE, 'w') as f: json.dump(user_dicts, f, indent=4)

    def find_by_username(self, username):
        users = self._load_users()
        for user in users:
            if user.username == username: return user
        return None

    def find_by_email(self, email):
        users = self._load_users()
        for user in users:
            if user.email == email: return user
        return None

    def find_by_id(self, user_id):
        users = self._load_users()
        for user in users:
            if user.user_id == user_id: return user
        return None

    def save(self, user_to_save):
        """
        Saves a user. Primarily for updating existing users if registration is removed.
        If adding new users manually to JSON, this might not be called by the app.
        """
        users = self._load_users()
        updated = False
        for i, u in enumerate(users):
            if u.user_id == user_to_save.user_id:
                existing_user_by_name = self.find_by_username(user_to_save.username)
                if existing_user_by_name and existing_user_by_name.user_id != user_to_save.user_id:
                    print(f"Error: Cannot update. Username '{user_to_save.username}' is taken by another user.")
                    return False 
                existing_user_by_email = self.find_by_email(user_to_save.email)
                if existing_user_by_email and existing_user_by_email.user_id != user_to_save.user_id:
                    print(f"Error: Cannot update. Email '{user_to_save.email}' is registered to another user.")
                    return False
                
                users[i] = user_to_save # Update existing user
                updated = True
                break
        
        if not updated:
            print(f"Warning/Error: Attempted to save a new user '{user_to_save.username}' but registration is disabled or user ID not found for update.")
            return False 

        self._save_users(users)
        return True
    
    def get_all_users(self): # Useful for an admin view perhaps
        return self._load_users()

# --- Trip Repository ---
TRIP_DATA_FILE = 'trips.json'
class TripRepository:
    def __init__(self):
        if not os.path.exists(TRIP_DATA_FILE) or os.path.getsize(TRIP_DATA_FILE) == 0:
            self._initialize_sample_trips()
    def _initialize_sample_trips(self): # ... (as before) ...
        sample_trips_data = [
            {'trip_id': "TRP001", 'origin': "Kuching Sentral", 'destination': "Serian", 'departure_time': "2025-07-15 09:00", 'price': 15.00, 'available_seats': 50},
            {'trip_id': "TRP002", 'origin': "Kuching Sentral", 'destination': "Sibu", 'departure_time': "2025-07-15 10:00", 'price': 60.00, 'available_seats': 30},
            {'trip_id': "TRP003", 'origin': "Serian", 'destination': "Kuching Sentral", 'departure_time': "2025-07-15 14:00", 'price': 15.00, 'available_seats': 45},
            {'trip_id': "TRP004", 'origin': "Sibu", 'destination': "Miri", 'departure_time': "2025-07-16 08:00", 'price': 80.00, 'available_seats': 25},
            {'trip_id': "TRP005", 'origin': "Kuching Sentral", 'destination': "Miri", 'departure_time': "2025-07-16 11:00", 'price': 120.00, 'available_seats': 0},
        ]
        with open(TRIP_DATA_FILE, 'w') as f: json.dump(sample_trips_data, f, indent=4)
    def _load_trips(self): # CORRECTED PATTERN
        if not os.path.exists(TRIP_DATA_FILE): self._initialize_sample_trips()
        with open(TRIP_DATA_FILE, 'r') as f:
            try:
                trips_data = json.load(f)
                if not isinstance(trips_data, list): self._initialize_sample_trips(); return self._load_trips()
            except json.JSONDecodeError: self._initialize_sample_trips(); return self._load_trips()
        return [trip_obj for td in trips_data if (trip_obj := Trip.from_dict(td)) is not None]
    def _save_trips(self, trips): # ... (as before) ...
        trip_dicts = []
        for trip in trips:
            if isinstance(trip, Trip): trip_dicts.append(trip.to_dict())
            else: print(f"Warning: Attempted to save a non-Trip object: {trip}"); continue
        with open(TRIP_DATA_FILE, 'w') as f: json.dump(trip_dicts, f, indent=4)
    def get_all_trips(self): return self._load_trips()
    def find_by_id(self, trip_id): # ... (as before) ...
        trips = self._load_trips()
        for trip in trips:
            if trip.trip_id == trip_id: return trip
        return None
    def search_trips(self, origin=None, destination=None, date_str=None): # ... (as before) ...
        all_trips = self._load_trips(); filtered_trips = []
        for trip in all_trips:
            match = True
            if origin and origin.lower() not in trip.origin.lower(): match = False
            if destination and destination.lower() not in trip.destination.lower(): match = False
            if date_str and date_str not in trip.departure_time: match = False 
            if match and trip.available_seats > 0: filtered_trips.append(trip)
        return filtered_trips
    def update_trip_seats(self, trip_id, num_seats=1, operation="book"): # ... (as before) ...
        trips = self._load_trips(); trip_found_and_updated = False
        for trip in trips:
            if trip.trip_id == trip_id:
                if operation == "book":
                    if trip.available_seats >= num_seats: trip.available_seats -= num_seats; trip_found_and_updated = True
                    else: return False 
                elif operation == "refund": trip.available_seats += num_seats; trip_found_and_updated = True
                else: return False 
                break 
        if trip_found_and_updated: self._save_trips(trips); return True
        return False 

# --- Ticket Repository ---
TICKET_DATA_FILE = 'tickets.json'
class TicketRepository:
    def __init__(self):
        if not os.path.exists(TICKET_DATA_FILE):
            with open(TICKET_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_tickets(self): # CORRECTED PATTERN
        if not os.path.exists(TICKET_DATA_FILE): 
            with open(TICKET_DATA_FILE, 'w') as f: json.dump([], f)
        with open(TICKET_DATA_FILE, 'r') as f:
            try:
                tickets_data = json.load(f)
                if not isinstance(tickets_data, list): tickets_data = []
            except json.JSONDecodeError: tickets_data = []
        return [ticket_obj for td in tickets_data if (ticket_obj := Ticket.from_dict(td)) is not None]
    def _save_tickets(self, tickets): # ... (as before) ...
        ticket_dicts = []
        for ticket in tickets:
            if isinstance(ticket, Ticket): ticket_dicts.append(ticket.to_dict())
            else: print(f"Warning: Attempted to save a non-Ticket object: {ticket}"); continue
        with open(TICKET_DATA_FILE, 'w') as f: json.dump(ticket_dicts, f, indent=4)
    def save(self, ticket_to_save): # ... (as before) ...
        tickets = self._load_tickets(); updated = False
        for i, t in enumerate(tickets):
            if t.ticket_id == ticket_to_save.ticket_id: tickets[i] = ticket_to_save; updated = True; break
        if not updated: tickets.append(ticket_to_save)
        self._save_tickets(tickets); return ticket_to_save
    def delete(self, ticket_id): # ... (as before) ...
        tickets = self._load_tickets()
        tickets_after_deletion = [t for t in tickets if t.ticket_id != ticket_id]
        if len(tickets_after_deletion) < len(tickets): 
            self._save_tickets(tickets_after_deletion); return True
        return False
    def find_by_id(self, ticket_id): # ... (as before) ...
        tickets = self._load_tickets()
        for ticket in tickets:
            if ticket.ticket_id == ticket_id: return ticket
        return None
    def find_by_user_id(self, user_id, active_only=False): # ... (as before) ...
        tickets = self._load_tickets()
        user_tickets = [ticket for ticket in tickets if ticket.user_id == user_id]
        if active_only: return [ticket for ticket in user_tickets if ticket.status == "Active"]
        return user_tickets
    def find_by_order_id(self, order_id): # ... (as before) ...
        tickets = self._load_tickets()
        return [ticket for ticket in tickets if ticket.order_id == order_id]

# --- Payment Repository ---
PAYMENT_DATA_FILE = 'payments.json'
class PaymentRepository:
    def __init__(self):
        if not os.path.exists(PAYMENT_DATA_FILE):
            with open(PAYMENT_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_payments(self): # CORRECTED PATTERN
        if not os.path.exists(PAYMENT_DATA_FILE): 
            with open(PAYMENT_DATA_FILE, 'w') as f: json.dump([], f)
        with open(PAYMENT_DATA_FILE, 'r') as f:
            try:
                payments_data = json.load(f)
                if not isinstance(payments_data, list): payments_data = []
            except json.JSONDecodeError: payments_data = []
        return [payment_obj for pd in payments_data if (payment_obj := Payment.from_dict(pd)) is not None]
    def _save_payments(self, payments): # ... (as before) ...
        payment_dicts = []
        for payment in payments:
            if isinstance(payment, Payment): payment_dicts.append(payment.to_dict())
            else: print(f"Warning: Attempted to save a non-Payment object: {payment}"); continue
        with open(PAYMENT_DATA_FILE, 'w') as f: json.dump(payment_dicts, f, indent=4)
    def save(self, payment_to_save): # ... (as before) ...
        payments = self._load_payments(); updated = False
        for i, p in enumerate(payments):
            if p.payment_id == payment_to_save.payment_id: payments[i] = payment_to_save; updated = True; break
        if not updated: payments.append(payment_to_save)
        self._save_payments(payments); return payment_to_save
    def find_by_id(self, payment_id): # ... (as before) ...
        payments = self._load_payments()
        for p in payments:
            if p.payment_id == payment_id: return p
        return None
    def find_by_order_id(self, order_id): # ... (as before) ...
        payments = self._load_payments()
        for p in payments:
            if p.order_id == order_id: return p 
        return None

# --- Order Repository ---
ORDER_DATA_FILE = 'orders.json'
class OrderRepository:
    def __init__(self):
        if not os.path.exists(ORDER_DATA_FILE):
            with open(ORDER_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_orders(self): # CORRECTED PATTERN
        if not os.path.exists(ORDER_DATA_FILE): 
            with open(ORDER_DATA_FILE, 'w') as f: json.dump([], f)
        with open(ORDER_DATA_FILE, 'r') as f:
            try:
                orders_data = json.load(f)
                if not isinstance(orders_data, list): orders_data = []
            except json.JSONDecodeError: orders_data = []
        return [order_obj for od in orders_data if (order_obj := Order.from_dict(od)) is not None]
    def _save_orders(self, orders): # ... (as before) ...
        order_dicts = []
        for order in orders:
            if isinstance(order, Order): order_dicts.append(order.to_dict())
            else: print(f"Warning: Attempted to save a non-Order object: {order}"); continue
        with open(ORDER_DATA_FILE, 'w') as f: json.dump(order_dicts, f, indent=4)
    def save(self, order_to_save): # ... (as before) ...
        orders = self._load_orders(); updated = False
        for i, o in enumerate(orders):
            if o.order_id == order_to_save.order_id: orders[i] = order_to_save; updated = True; break
        if not updated: orders.append(order_to_save)
        self._save_orders(orders); return order_to_save
    def find_by_id(self, order_id): # ... (as before) ...
        orders = self._load_orders()
        for o in orders:
            if o.order_id == order_id: return o
        return None
    def find_by_user_id(self, user_id): # ... (as before) ...
        orders = self._load_orders()
        return [o for o in orders if o.user_id == user_id]

# --- Refund Repository ---
REFUND_DATA_FILE = 'refunds.json'
class RefundRepository:
    def __init__(self):
        if not os.path.exists(REFUND_DATA_FILE):
            with open(REFUND_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_refunds(self): # CORRECTED PATTERN
        if not os.path.exists(REFUND_DATA_FILE): 
            with open(REFUND_DATA_FILE, 'w') as f: json.dump([], f)
        with open(REFUND_DATA_FILE, 'r') as f:
            try:
                refunds_data = json.load(f)
                if not isinstance(refunds_data, list): refunds_data = []
            except json.JSONDecodeError: refunds_data = []
        return [refund_obj for rd in refunds_data if (refund_obj := Refund.from_dict(rd)) is not None]
    def _save_refunds(self, refunds): # ... (as before) ...
        refund_dicts = []
        for refund in refunds:
            if isinstance(refund, Refund): refund_dicts.append(refund.to_dict())
            else: print(f"Warning: Attempted to save a non-Refund object: {refund}"); continue
        with open(REFUND_DATA_FILE, 'w') as f: json.dump(refund_dicts, f, indent=4)
    def save(self, refund_to_save): # ... (as before) ...
        refunds = self._load_refunds(); updated = False
        for i, r in enumerate(refunds):
            if r.refund_id == refund_to_save.refund_id: refunds[i] = refund_to_save; updated = True; break
        if not updated: refunds.append(refund_to_save)
        self._save_refunds(refunds); return refund_to_save
    def find_by_id(self, refund_id): # ... (as before) ...
        refunds = self._load_refunds()
        for r in refunds:
            if r.refund_id == refund_id: return r
        return None
    def find_by_payment_id(self, payment_id): # ... (as before) ...
        refunds = self._load_refunds()
        return [r for r in refunds if r.payment_id == payment_id] 
    def find_by_order_id(self, order_id): # ... (as before) ...
        refunds = self._load_refunds()
        return [r for r in refunds if r.order_id == order_id]
    
# --- Location Repository ---
LOCATION_DATA_FILE = 'locations.json'
class LocationRepository:
    def __init__(self):
        if not os.path.exists(LOCATION_DATA_FILE):
            with open(LOCATION_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_locations(self):
        if not os.path.exists(LOCATION_DATA_FILE): 
            with open(LOCATION_DATA_FILE, 'w') as f: json.dump([], f)
        with open(LOCATION_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [loc_obj for ld in data if (loc_obj := Location.from_dict(ld)) is not None]
    def _save_locations(self, locations):
        with open(LOCATION_DATA_FILE, 'w') as f:
            json.dump([loc.to_dict() for loc in locations if isinstance(loc, Location)], f, indent=4)
    def save(self, location_to_save):
        locations = self._load_locations()
        updated = False
        for i, loc in enumerate(locations):
            if loc.location_id == location_to_save.location_id:
                locations[i] = location_to_save; updated = True; break
        if not updated: locations.append(location_to_save)
        self._save_locations(locations); return location_to_save
    def find_by_id(self, location_id):
        for loc in self._load_locations():
            if loc.location_id == location_id: return loc
        return None
    def get_all(self): return self._load_locations()


# --- Stop Repository ---
STOP_DATA_FILE = 'stops.json'
class StopRepository:
    def __init__(self):
        if not os.path.exists(STOP_DATA_FILE):
            with open(STOP_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_stops(self):
        if not os.path.exists(STOP_DATA_FILE): 
            with open(STOP_DATA_FILE, 'w') as f: json.dump([], f)
        with open(STOP_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [stop_obj for sd in data if (stop_obj := Stop.from_dict(sd)) is not None]
    def _save_stops(self, stops):
        with open(STOP_DATA_FILE, 'w') as f:
            json.dump([s.to_dict() for s in stops if isinstance(s, Stop)], f, indent=4)
    def save(self, stop_to_save):
        stops = self._load_stops()
        updated = False
        for i, s in enumerate(stops):
            if s.stop_id == stop_to_save.stop_id:
                stops[i] = stop_to_save; updated = True; break
        if not updated: stops.append(stop_to_save)
        self._save_stops(stops); return stop_to_save
    def find_by_id(self, stop_id):
        for s in self._load_stops():
            if s.stop_id == stop_id: return s
        return None
    def get_all(self): return self._load_stops()


# --- Route Repository ---
ROUTE_DATA_FILE = 'routes.json'
class RouteRepository:
    def __init__(self):
        if not os.path.exists(ROUTE_DATA_FILE):
            with open(ROUTE_DATA_FILE, 'w') as f: json.dump([], f) # Initialize with sample routes if desired
    def _load_routes(self):
        if not os.path.exists(ROUTE_DATA_FILE): 
            with open(ROUTE_DATA_FILE, 'w') as f: json.dump([], f)
        with open(ROUTE_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [route_obj for rd in data if (route_obj := Route.from_dict(rd)) is not None]
    def _save_routes(self, routes):
        with open(ROUTE_DATA_FILE, 'w') as f:
            json.dump([r.to_dict() for r in routes if isinstance(r, Route)], f, indent=4)
    def save(self, route_to_save):
        routes = self._load_routes()
        updated = False
        for i, r in enumerate(routes):
            if r.route_id == route_to_save.route_id:
                routes[i] = route_to_save; updated = True; break
        if not updated: routes.append(route_to_save)
        self._save_routes(routes); return route_to_save
    def find_by_id(self, route_id):
        for r in self._load_routes():
            if r.route_id == route_id: return r
        return None
    def get_all(self): return self._load_routes()

# --- Feedback Repository ---
FEEDBACK_DATA_FILE = 'feedbacks.json'
class FeedbackRepository:
    def __init__(self):
        if not os.path.exists(FEEDBACK_DATA_FILE):
            with open(FEEDBACK_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_feedbacks(self):
        if not os.path.exists(FEEDBACK_DATA_FILE): 
            with open(FEEDBACK_DATA_FILE, 'w') as f: json.dump([], f)
        with open(FEEDBACK_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [fb_obj for fd in data if (fb_obj := Feedback.from_dict(fd)) is not None]
    def _save_feedbacks(self, feedbacks):
        with open(FEEDBACK_DATA_FILE, 'w') as f:
            json.dump([fb.to_dict() for fb in feedbacks if isinstance(fb, Feedback)], f, indent=4)
    def save(self, feedback_to_save):
        feedbacks = self._load_feedbacks()
        updated = False
        for i, fb in enumerate(feedbacks):
            if fb.feedback_id == feedback_to_save.feedback_id:
                feedbacks[i] = feedback_to_save; updated = True; break
        if not updated: feedbacks.append(feedback_to_save)
        self._save_feedbacks(feedbacks); return feedback_to_save
    def find_by_id(self, feedback_id):
        for fb in self._load_feedbacks():
            if fb.feedback_id == feedback_id: return fb
        return None
    def get_all(self, status_filter=None): # e.g., get_all(status_filter="New")
        feedbacks = self._load_feedbacks()
        if status_filter:
            return [fb for fb in feedbacks if fb.status == status_filter]
        return feedbacks
    def find_by_user_id(self, user_id):
        return [fb for fb in self._load_feedbacks() if fb.submitter_user_id == user_id]

# --- Response Repository ---
RESPONSE_DATA_FILE = 'responses.json'
class ResponseRepository:
    def __init__(self):
        if not os.path.exists(RESPONSE_DATA_FILE):
            with open(RESPONSE_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_responses(self):
        if not os.path.exists(RESPONSE_DATA_FILE): 
            with open(RESPONSE_DATA_FILE, 'w') as f: json.dump([], f)
        with open(RESPONSE_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [res_obj for rd in data if (res_obj := Response.from_dict(rd)) is not None]
    def _save_responses(self, responses):
        with open(RESPONSE_DATA_FILE, 'w') as f:
            json.dump([res.to_dict() for res in responses if isinstance(res, Response)], f, indent=4)
    def save(self, response_to_save):
        responses = self._load_responses()
        updated = False # Response objects are typically immutable after creation, but save can handle both
        for i, res in enumerate(responses):
            if res.response_id == response_to_save.response_id:
                responses[i] = response_to_save; updated = True; break
        if not updated: responses.append(response_to_save)
        self._save_responses(responses); return response_to_save
    def find_by_id(self, response_id):
        for res in self._load_responses():
            if res.response_id == response_id: return res
        return None
    def find_by_feedback_id(self, feedback_id):
        return [res for res in self._load_responses() if res.feedback_id == feedback_id]

# --- Notification Repository (Simplified) ---
NOTIFICATION_DATA_FILE = 'notifications.json'
class NotificationRepository:
    def __init__(self):
        if not os.path.exists(NOTIFICATION_DATA_FILE):
            with open(NOTIFICATION_DATA_FILE, 'w') as f: json.dump([], f)
    def _load_notifications(self):
        if not os.path.exists(NOTIFICATION_DATA_FILE): 
            with open(NOTIFICATION_DATA_FILE, 'w') as f: json.dump([], f)
        with open(NOTIFICATION_DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list): data = []
            except json.JSONDecodeError: data = []
        return [notif_obj for nd in data if (notif_obj := Notification.from_dict(nd)) is not None]
    def _save_notifications(self, notifications):
        with open(NOTIFICATION_DATA_FILE, 'w') as f:
            json.dump([n.to_dict() for n in notifications if isinstance(n, Notification)], f, indent=4)
    def save(self, notification_to_save):
        notifications = self._load_notifications()
        # Notifications are typically just added
        notifications.append(notification_to_save)
        self._save_notifications(notifications); return notification_to_save
    def find_by_recipient_id(self, user_id, unread_only=False):
        notifications = [n for n in self._load_notifications() if n.recipient_user_id == user_id]
        if unread_only:
            return [n for n in notifications if not n.read_status]
        return notifications