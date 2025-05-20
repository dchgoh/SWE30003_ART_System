# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session 
from services import UserService, BookingService, RefundService, AdminRouteService, AdminFeedbackService

app = Flask(__name__)
app.secret_key = 'your_very_secret_dev_key_123!' # Important: Change for production

# --- Instantiate your services ---
user_service = UserService()
booking_service = BookingService()
refund_service = RefundService() 
admin_route_service = AdminRouteService()
admin_feedback_service = AdminFeedbackService()
mock_user_id = "mock_user_001" # TODO: Replace with actual session management for regular users
mock_admin_id = "admin_user_001" # TODO: Replace with actual admin authentication/session


# --- Basic Routes ---
@app.route('/')
def home():
    return render_template('index.html', title='Welcome')

@app.route('/search-trips', methods=['GET'])
def search_trips_route():
    origin_query = request.args.get('origin', '').strip()
    destination_query = request.args.get('destination', '').strip()
    date_query = request.args.get('date', '').strip()
    trips_found = booking_service.search_available_trips(
        origin=origin_query if origin_query else None,
        destination=destination_query if destination_query else None,
        date_str=date_query if date_query else None
    )
    search_performed = bool(origin_query or destination_query or date_query)
    return render_template('search_trips.html',
                           title='Search & Book Tickets',
                           trips=trips_found,
                           search_origin=origin_query,
                           search_destination=destination_query,
                           search_date=date_query,
                           search_performed=search_performed)

@app.route('/book-trip/<trip_id>', methods=['GET', 'POST'])
def book_trip_route(trip_id):

    current_user_id = mock_user_id 

    trip = booking_service.get_trip_details(trip_id)
    if not trip:
        flash("Trip not found.", "error")
        return redirect(url_for('search_trips_route'))

    if request.method == 'POST':
        num_tickets_to_book = 1 # Can be enhanced to get from form
        # purchase_ticket service method now returns (first_ticket, order, message)
        ticket, order, message = booking_service.purchase_ticket(current_user_id, trip_id, num_tickets=num_tickets_to_book)
        if ticket and order:
            flash(message, 'success')
            # Re-fetch trip details to show updated seat count for the current page render
            updated_trip = booking_service.get_trip_details(trip_id) 
            return render_template('book_trip_form.html', title=f'Booking Confirmed', trip=updated_trip, order=order, ticket=ticket, booking_successful=True)
        else:
            flash(message, 'error')
            # If booking failed, show the form again with the error
            return render_template('book_trip_form.html', title=f'Book Trip: {trip.trip_id}', trip=trip, booking_successful=False)

    # GET request: show the booking confirmation form
    return render_template('book_trip_form.html', title=f'Book Trip: {trip.trip_id}', trip=trip, booking_successful=False)


# --- STANDALONE REFUND DEMO ROUTE ---
@app.route('/standalone-refund-demo', methods=['GET', 'POST'])
def request_refund_standalone_route():
    current_user_id = mock_user_id # For demo purposes. TODO: Use session


    if request.method == 'POST':
        order_id_to_refund = request.form.get('order_id_to_refund')
        if not order_id_to_refund:
            flash("No order selected for refund.", "error")
        else:
            # The service method internally checks if the order belongs to the user
            success, message = refund_service.process_refund_for_order(current_user_id, order_id_to_refund)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
        return redirect(url_for('request_refund_standalone_route')) # Refresh page

    # GET request: Display sample/existing orders for the user
    # Using a method that gets ALL orders to show various statuses
    orders_to_display_data = refund_service.get_all_orders_for_user_display(current_user_id) 
    
    if not orders_to_display_data:
         flash(f"No orders found for demo user '{current_user_id}'. Please ensure sample data exists.", "info")

    return render_template('refund_request_standalone.html', 
                           title='Standalone Refund Demo', 
                           orders_to_display=orders_to_display_data,
                           mock_user_id=current_user_id)

# --- Admin Routes for Managing Routes, Stops, Locations ---

# Placeholder for admin authentication - replace with a real decorator
def admin_required(f):
    # @wraps(f) #
    def decorated_function(*args, **kwargs):
        # if 'admin_id' not in session: # Example admin session check
        #     flash("Admin access required.", "danger")
        #     return redirect(url_for('admin_login_route')) # Assuming an admin login
        print(f"Mock Admin Access Granted for: {mock_admin_id}") # For demo
        return f(*args, **kwargs)
    # return decorated_function 
    return f # Bypassing auth for now for easier testing, REMOVE/REPLACE IN REAL APP


@app.route('/admin/manage-routes', methods=['GET'])
@admin_required 
def admin_manage_routes_route():
    routes = admin_route_service.get_all_routes()
    return render_template('admin_manage_routes.html', title="Admin: Manage Routes", routes=routes)

@app.route('/admin/route/<route_id>/stops', methods=['GET'])
@admin_required
def admin_route_stops_route(route_id):
    route, stops_on_route = admin_route_service.get_route_details_with_stops(route_id)
    if not route:
        flash(f"Route with ID {route_id} not found.", "error")
        return redirect(url_for('admin_manage_routes_route'))
    return render_template('admin_route_stops.html', title=f"Admin: Stops for {route.route_name}", route=route, stops_on_route=stops_on_route)

@app.route('/admin/update-stop-location/<route_id>/<stop_id>', methods=['GET', 'POST'])
@admin_required
def admin_update_stop_location_route(route_id, stop_id):
    # admin_user_id = session.get('admin_id', mock_admin_id) # TODO: Use admin session
    admin_user_id = mock_admin_id # Using mock for now

    route = admin_route_service.route_repository.find_by_id(route_id) 
    stop, current_location = admin_route_service.get_stop_details_with_location(stop_id)

    if not route or not stop or not current_location:
        flash("Route, Stop, or its Location not found.", "error")
        # Redirect to a more sensible place if a route exists but stop doesn't, etc.
        return redirect(url_for('admin_manage_routes_route')) 

    if request.method == 'POST':
        new_latitude_str = request.form.get('latitude')
        new_longitude_str = request.form.get('longitude')
        new_address = request.form.get('address')
        new_city = request.form.get('city')
        new_postcode = request.form.get('postcode')

        if not all([new_latitude_str, new_longitude_str, new_address, new_city, new_postcode]):
            flash("All location fields are required.", "error")
        else:
            try:
                new_latitude = float(new_latitude_str)
                new_longitude = float(new_longitude_str)
            except ValueError:
                flash("Latitude and Longitude must be valid numbers.", "error")
            else:
                success, message = admin_route_service.update_stop_location_details(
                    admin_user_id, route_id, stop_id,
                    new_latitude, new_longitude, new_address, new_city, new_postcode
                )
                if success:
                    flash(message, 'success')
                    return redirect(url_for('admin_route_stops_route', route_id=route_id))
                else:
                    flash(message, 'error')
    
    return render_template('admin_update_stop_location_form.html', 
                           title=f"Update Location for Stop: {stop.stop_name}",
                           route=route,
                           stop=stop, 
                           current_location=current_location)

@app.route('/admin/feedbacks', methods=['GET'])
@admin_required # Assuming you have an admin auth decorator
def admin_manage_feedbacks_route():
    # Allow filtering by status, e.g., show "New" feedbacks by default
    status_filter = request.args.get('status', 'New') # Default to 'New' or None to show all
    
    feedbacks_data = admin_feedback_service.get_all_feedbacks(status_filter=status_filter if status_filter != "All" else None)
    
    # Possible statuses for filtering dropdown
    all_statuses = ["All", "New", "Pending", "Responded", "Closed"] 

    return render_template('admin_manage_feedbacks.html', 
                           title="Admin: Manage User Feedbacks", 
                           feedbacks_data=feedbacks_data,
                           all_statuses=all_statuses,
                           current_status_filter=status_filter)

@app.route('/admin/feedback/<feedback_id>/respond', methods=['GET', 'POST'])
@admin_required
def admin_respond_to_feedback_route(feedback_id):
    admin_user_id = mock_admin_id # TODO: Get actual logged-in admin ID from session

    feedback, submitter_name, existing_responses = admin_feedback_service.get_feedback_details(feedback_id)
    if not feedback:
        flash("Feedback item not found.", "error")
        return redirect(url_for('admin_manage_feedbacks_route'))

    if request.method == 'POST':
        response_text = request.form.get('response_text')
        if not response_text or not response_text.strip():
            flash("Response text cannot be empty.", "error")
        else:
            success, message = admin_feedback_service.submit_admin_response(
                admin_user_id, feedback_id, response_text
            )
            if success:
                flash(message, "success")
                return redirect(url_for('admin_manage_feedbacks_route')) # Go back to list
            else:
                flash(message, "error")
                
    # For GET or if POST had an error and re-renders form
    return render_template('admin_respond_feedback_form.html',
                           title=f"Respond to Feedback ID: {feedback.feedback_id}",
                           feedback=feedback,
                           submitter_name=submitter_name,
                           existing_responses=existing_responses)

# --- Main execution ---
if __name__ == '__main__':
    app.run(debug=True)