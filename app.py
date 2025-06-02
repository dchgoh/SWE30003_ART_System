# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session 
from models import User, Admin, Trip, Ticket, Order, Payment, Refund, Location, Stop, Route, Feedback, Response, Notification # Import all models

app = Flask(__name__)
app.secret_key = 'your_very_secret_dev_key_123!' 

mock_user_id = "mock_user_001" 
mock_admin_id = "admin_user_001" # Assuming an admin user exists in users.json with this ID and is_admin=True

# --- Basic Routes ---
@app.route('/')
def home():
    return render_template('index.html', title='Welcome')

# --- User Facing Routes ---
# REGISTRATION ROUTE IS REMOVED

@app.route('/search-trips', methods=['GET'])
def search_trips_route():
    origin_query = request.args.get('origin', '').strip()
    destination_query = request.args.get('destination', '').strip()
    date_query = request.args.get('date', '').strip()
    
    # Use model's static search method
    trips_found = Trip.search( 
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
    trip_to_book = Trip.find_by_id(trip_id)

    if not trip_to_book:
        flash("Trip not found.", "error"); return redirect(url_for('search_trips_route'))

    if request.method == 'POST':
        num_tickets_to_book = 1 # Simplified
        if trip_to_book.available_seats < num_tickets_to_book:
            flash("Not enough available seats.", "error")
        else:
            # --- Booking Logic (moved from service, simplified) ---
            order_total_amount = trip_to_book.price * num_tickets_to_book
            new_order = Order(user_id=current_user_id, trip_id=trip_id, 
                              num_tickets=num_tickets_to_book, total_amount=order_total_amount, status="PendingPayment")
            new_order.save() # Order saves itself

            mock_payment_successful = True # Simulate payment
            if mock_payment_successful:
                new_payment = Payment(order_id=new_order.order_id, amount=new_order.total_amount, status="Completed")
                new_payment.save() # Payment saves itself
                new_order.status = "Completed"
                new_order.save() # Update and save order

                # Update trip seats
                trip_to_book.update_seats(num_tickets_to_book, operation="book")
                trip_to_book.save() # Trip saves itself

                # Create tickets
                created_tickets_info = []
                for _ in range(num_tickets_to_book):
                    new_ticket = Ticket(user_id=current_user_id, trip_id=trip_id, 
                                        order_id=new_order.order_id, payment_id=new_payment.payment_id)
                    new_ticket.save() # Ticket saves itself
                    created_tickets_info.append(new_ticket) # Keep for display/return
                
                flash(f"{num_tickets_to_book} Ticket(s) purchased!", 'success')
                return render_template('book_trip_form.html', title=f'Booking Confirmed', 
                                       trip=trip_to_book, order=new_order, 
                                       ticket=created_tickets_info[0] if created_tickets_info else None, # Show first ticket
                                       booking_successful=True)
            else: # Payment failed
                new_order.status = "PaymentFailed"
                new_order.save()
                flash("Payment failed.", "error")
    
    return render_template('book_trip_form.html', title=f'Book Trip: {trip_to_book.trip_id}', 
                           trip=trip_to_book, booking_successful=False)


# --- STANDALONE REFUND DEMO ROUTE ---
@app.route('/standalone-refund-demo', methods=['GET', 'POST'])
def request_refund_standalone_route():
    current_user_id = mock_user_id 

    if request.method == 'POST':
        order_id_to_refund = request.form.get('order_id_to_refund')
        order_to_refund = Order.find_by_id(order_id_to_refund)

        if not order_to_refund:
            flash("Order not found.", "error")
        elif order_to_refund.user_id != current_user_id:
            flash("This order does not belong to you.", "error")
        elif order_to_refund.status != "Completed":
            flash(f"Order (Status: {order_to_refund.status}) not eligible for refund.", "warning")
        else:
            # --- Refund Logic (moved from service, simplified) ---
            success_overall = True
            messages = []
            tickets_for_order = Ticket.find_by_order_id(order_to_refund.order_id)
            
            if not tickets_for_order:
                order_to_refund.status = "ErrorNoTicketsForRefund"; order_to_refund.save()
                flash("Order has no tickets to refund.", "error")
            else:
                payment_for_order = Payment.find_by_order_id(order_to_refund.order_id)
                if not payment_for_order:
                     flash("Original payment for order not found.", "error")
                     success_overall = False
                
                if payment_for_order and payment_for_order.status == "Refunded":
                    flash("Payment already refunded.", "info")
                    order_to_refund.status = "Refunded"; order_to_refund.save()

                elif payment_for_order: # Proceed if payment exists and not already refunded
                    num_tickets_refunded_this_op = 0
                    for ticket in tickets_for_order:
                        if ticket.status == "Active":
                            if ticket.void():
                                ticket.save() # Save voided status
                                trip_of_ticket = Trip.find_by_id(ticket.trip_id)
                                if trip_of_ticket:
                                    trip_of_ticket.update_seats(1, operation="refund") # Assuming 1 ticket = 1 seat
                                    trip_of_ticket.save()
                                
                                # Create refund record for this ticket
                                refund_amount_this_ticket = order_to_refund.total_amount / order_to_refund.num_tickets if order_to_refund.num_tickets > 0 else 0
                                new_refund = Refund(payment_id=ticket.payment_id, order_id=order_to_refund.order_id,
                                                    ticket_id=ticket.ticket_id, refund_amount=refund_amount_this_ticket)
                                mock_gateway_refund_success = True # Simulate
                                if mock_gateway_refund_success:
                                    new_refund.update_status("Processed")
                                    ticket.status = "Refunded"
                                    num_tickets_refunded_this_op += 1
                                else:
                                    new_refund.update_status("Failed")
                                    ticket.status = "RefundFailed"
                                    success_overall = False
                                new_refund.save()
                                ticket.save() # Save new ticket status
                            else: # Could not void
                                messages.append(f"Could not void ticket {ticket.ticket_id}")
                                success_overall = False
                    
                    if num_tickets_refunded_this_op > 0:
                         # Update overall payment and order status
                        payment_for_order.status = "Refunded" # Simplification
                        payment_for_order.save()
                        if num_tickets_refunded_this_op == order_to_refund.num_tickets:
                            order_to_refund.status = "Refunded"
                        else:
                            order_to_refund.status = "PartiallyRefunded"
                        order_to_refund.save()
                        flash("Refund processed for eligible tickets.", "success")
                    elif success_overall: # No active tickets, but no errors
                        flash("No active tickets found in this order to refund.", "info")
                    else: # Some error occurred
                        flash("Refund processing encountered issues: " + " | ".join(messages), "error")
                        
        return redirect(url_for('request_refund_standalone_route'))

    orders_data_for_display = []
    user_orders = Order.find_by_user_id(current_user_id)
    if user_orders:
        for order in user_orders:
            trip = Trip.find_by_id(order.trip_id)
            orders_data_for_display.append({"order": order, "trip": trip})
            
    if not orders_data_for_display:
         flash(f"No orders found for user '{current_user_id}'. Please ensure sample data exists.", "info")

    return render_template('refund_request_standalone.html', 
                           title='Standalone Refund Demo', 
                           orders_to_display=orders_data_for_display,
                           mock_user_id=current_user_id)


# --- Admin Routes ---
def admin_required(f): # Basic placeholder
    # In real app, check admin session
    print(f"Mock Admin Access for: {mock_admin_id}")
    return f

@app.route('/admin/manage-routes', methods=['GET'])
@admin_required 
def admin_manage_routes_route():
    routes = Route.get_all()
    return render_template('admin_manage_routes.html', title="Admin: Manage Routes", routes=routes)

@app.route('/admin/route/<route_id>/stops', methods=['GET'])
@admin_required
def admin_route_stops_route(route_id):
    route = Route.find_by_id(route_id)
    if not route:
        flash(f"Route with ID {route_id} not found.", "error")
        return redirect(url_for('admin_manage_routes_route'))
    
    stops_on_route_details = []
    for stop_id in route.stop_ids:
        stop = Stop.find_by_id(stop_id)
        if stop:
            location = stop.get_location() # Use Stop's helper method
            stops_on_route_details.append({"stop": stop, "location": location})
            
    return render_template('admin_route_stops.html', 
                           title=f"Admin: Stops for {route.route_name}", 
                           route=route, stops_on_route=stops_on_route_details)

@app.route('/admin/update-stop-location/<route_id>/<stop_id>', methods=['GET', 'POST'])
@admin_required
def admin_update_stop_location_route(route_id, stop_id):
    admin_user_id = mock_admin_id 

    route = Route.find_by_id(route_id) 
    stop_to_update = Stop.find_by_id(stop_id)
    current_location = None
    if stop_to_update:
        current_location = stop_to_update.get_location()

    if not route or not stop_to_update or not current_location:
        flash("Route, Stop, or its Location not found for update.", "error")
        return redirect(url_for('admin_manage_routes_route')) 

    if request.method == 'POST':
        # ... (form data retrieval and validation as before) ...
        new_latitude_str = request.form.get('latitude'); new_longitude_str = request.form.get('longitude')
        new_address = request.form.get('address'); new_city = request.form.get('city'); new_postcode = request.form.get('postcode')

        if not all([new_latitude_str, new_longitude_str, new_address, new_city, new_postcode]):
            flash("All location fields are required.", "error")
        else:
            try:
                lat_f = float(new_latitude_str); lon_f = float(new_longitude_str)
                # --- Update Logic (moved from service) ---
                if route.find_stop_id(stop_id): # Check if stop belongs to route
                    success, message = stop_to_update.update_location_details(lat_f, lon_f, new_address, new_city, new_postcode)
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('admin_route_stops_route', route_id=route_id))
                    else:
                        flash(message, 'error')
                else:
                    flash(f"Stop ID '{stop_id}' not found on Route '{route.route_name}'.", "error")

            except ValueError:
                flash("Latitude and Longitude must be valid numbers.", "error")
    
    return render_template('admin_update_stop_location_form.html', 
                           title=f"Update Location for Stop: {stop_to_update.stop_name}",
                           route=route, stop=stop_to_update, current_location=current_location)

@app.route('/admin/feedbacks', methods=['GET'])
@admin_required
def admin_manage_feedbacks_route():
    status_filter = request.args.get('status', 'New')
    all_feedbacks = Feedback.get_all(status_filter=status_filter if status_filter != "All" else None)
    
    feedbacks_data_for_display = []
    if all_feedbacks:
        for fb in all_feedbacks:
            submitter = User.find_by_id(fb.submitter_user_id) # Find by actual user_id now
            submitter_name = submitter.username if submitter else "Unknown User"
            responses = fb.get_responses() # Use Feedback's helper method
            feedbacks_data_for_display.append({"feedback": fb, "submitter_name": submitter_name, "responses": responses})
    
    all_statuses = ["All", "New", "Pending", "Responded", "Closed"] 
    return render_template('admin_manage_feedbacks.html', 
                           title="Admin: Manage User Feedbacks", 
                           feedbacks_data=feedbacks_data_for_display,
                           all_statuses=all_statuses, current_status_filter=status_filter)

@app.route('/admin/feedback/<feedback_id>/respond', methods=['GET', 'POST'])
@admin_required
def admin_respond_to_feedback_route(feedback_id):
    admin_user_id = mock_admin_id 
    feedback_to_respond = Feedback.find_by_id(feedback_id)

    if not feedback_to_respond:
        flash("Feedback item not found.", "error"); return redirect(url_for('admin_manage_feedbacks_route'))

    submitter = User.find_by_id(feedback_to_respond.submitter_user_id)
    submitter_name = submitter.username if submitter else "Unknown User"
    existing_responses = feedback_to_respond.get_responses()

    if request.method == 'POST':
        response_text = request.form.get('response_text')
        if not response_text or not response_text.strip():
            flash("Response text cannot be empty.", "error")
        else:
            # --- Response Logic (moved from service) ---
            new_response = Response(feedback_id=feedback_id, responder_admin_id=admin_user_id, response_content=response_text)
            new_response.save() # Response saves itself
            
            feedback_to_respond.add_response_id(new_response.response_id)
            feedback_to_respond.update_status("Responded")
            feedback_to_respond.save() # Feedback saves itself

            # Create and save notification
            notif_msg = f"Admin responded to your feedback (ID: {feedback_id}): '{response_text[:30]}...'"
            notification = Notification(recipient_user_id=feedback_to_respond.submitter_user_id,
                                        sender_user_id=admin_user_id, message_content=notif_msg,
                                        notification_type="FeedbackResponse")
            notification.save() # Notification saves itself

            flash("Response submitted and user notified (mock).", "success")
            return redirect(url_for('admin_manage_feedbacks_route'))
                
    return render_template('admin_respond_feedback_form.html',
                           title=f"Respond to Feedback ID: {feedback_to_respond.feedback_id}",
                           feedback=feedback_to_respond, submitter_name=submitter_name, existing_responses=existing_responses)

# --- Main execution ---
if __name__ == '__main__':
    # Initialize some sample data if files are empty (optional, for easier first run)
    # You might want a more robust seeding script for complex data.
    # For example, ensure mock_user_001 and admin_user_001 exist in users.json
    # TripRepository already initializes sample trips if trips.json is empty.
    
    # Example: Ensure mock users exist
    if not User.find_by_id(mock_user_id):
        User(username="mockuser", email="mock@example.com", password="password", user_id=mock_user_id).save()
    if not User.find_by_id(mock_admin_id): # Assuming Admin inherits User and is saved via User.save()
        Admin(username="admin", email="admin@example.com", password="adminpassword", user_id=mock_admin_id, admin_level="superuser").save()


    app.run(debug=True)