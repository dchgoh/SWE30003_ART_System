# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session 
from models import User, Admin, Trip, Ticket, Order, Payment, Refund, Location, Stop, Route, Feedback, Response, Notification # Import all models

app = Flask(__name__)
app.secret_key = 'your_very_secret_dev_key_123!' 

mockUserID = "mock_user_001" 
mock_adminID = "admin_user_001" # Assuming an admin user exists in users.json with this ID and isAdmin=True

# --- Basic Routes ---
@app.route('/')
def home():
    return render_template('index.html', title='Welcome')

# --- User Facing Routes ---
# REGISTRATION ROUTE IS REMOVED

@app.route('/search-trips', methods=['GET'])
def searchTripsRoute():
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

@app.route('/book-trip/<tripID>', methods=['GET', 'POST'])
def bookTripRoute(tripID):
    currentUserID = mockUserID 
    tripToBook = Trip.findByID(tripID)

    if not tripToBook:
        flash("Trip not found.", "error"); return redirect(url_for('searchTripsRoute'))

    if request.method == 'POST':
        numTicketsToBook = 1 # Simplified
        if tripToBook.availableSeats < numTicketsToBook:
            flash("Not enough available seats.", "error")
        else:
            # --- Booking Logic (moved from service, simplified) ---
            orderTotalAmount = tripToBook.price * numTicketsToBook
            newOrder = Order(userID=currentUserID, tripID=tripID, 
                              numTickets=numTicketsToBook, totalAmount=orderTotalAmount, status="PendingPayment")
            newOrder.save() # Order saves itself

            mock_payment_successful = True # Simulate payment
            if mock_payment_successful:
                newPayment = Payment(orderID=newOrder.orderID, amount=newOrder.totalAmount, status="Completed")
                newPayment.save() # Payment saves itself
                newOrder.status = "Completed"
                newOrder.save() # Update and save order

                # Update trip seats
                tripToBook.updateSeats(numTicketsToBook, operation="book")
                tripToBook.save() # Trip saves itself

                # Create tickets
                createdTicketsInfo = []
                for _ in range(numTicketsToBook):
                    newTicket = Ticket(userID=currentUserID, tripID=tripID, 
                                        orderID=newOrder.orderID, paymentID=newPayment.paymentID)
                    newTicket.save() # Ticket saves itself
                    createdTicketsInfo.append(newTicket) # Keep for display/return
                
                flash(f"{numTicketsToBook} Ticket(s) purchased!", 'success')
                return render_template('book_trip_form.html', title=f'Booking Confirmed', 
                                       trip=tripToBook, order=newOrder, 
                                       ticket=createdTicketsInfo[0] if createdTicketsInfo else None, # Show first ticket
                                       booking_successful=True)
            else: # Payment failed
                newOrder.status = "PaymentFailed"
                newOrder.save()
                flash("Payment failed.", "error")
    
    return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}', 
                           trip=tripToBook, booking_successful=False)


# --- STANDALONE REFUND DEMO ROUTE ---
@app.route('/standalone-refund-demo', methods=['GET', 'POST'])
def requestRefundStandaloneRoute():
    currentUserID = mockUserID 

    if request.method == 'POST':
        orderID_to_refund = request.form.get('orderID_to_refund')
        order_to_refund = Order.findByID(orderID_to_refund)

        if not order_to_refund:
            flash("Order not found.", "error")
        elif order_to_refund.userID != currentUserID:
            flash("This order does not belong to you.", "error")
        elif order_to_refund.status != "Completed":
            flash(f"Order (Status: {order_to_refund.status}) not eligible for refund.", "warning")
        else:
            # --- Refund Logic (moved from service, simplified) ---
            success_overall = True
            messages = []
            tickets_for_order = Ticket.findByOrderID(order_to_refund.orderID)
            
            if not tickets_for_order:
                order_to_refund.status = "ErrorNoTicketsForRefund"; order_to_refund.save()
                flash("Order has no tickets to refund.", "error")
            else:
                payment_for_order = Payment.findByOrderID(order_to_refund.orderID)
                if not payment_for_order:
                     flash("Original payment for order not found.", "error")
                     success_overall = False
                
                if payment_for_order and payment_for_order.status == "Refunded":
                    flash("Payment already refunded.", "info")
                    order_to_refund.status = "Refunded"; order_to_refund.save()

                elif payment_for_order: # Proceed if payment exists and not already refunded
                    numTickets_refunded_this_op = 0
                    for ticket in tickets_for_order:
                        if ticket.status == "Active":
                            if ticket.void():
                                ticket.save() # Save voided status
                                trip_of_ticket = Trip.findByID(ticket.tripID)
                                if trip_of_ticket:
                                    trip_of_ticket.updateSeats(1, operation="refund") # Assuming 1 ticket = 1 seat
                                    trip_of_ticket.save()
                                
                                # Create refund record for this ticket
                                refundAmount_this_ticket = order_to_refund.totalAmount / order_to_refund.numTickets if order_to_refund.numTickets > 0 else 0
                                new_refund = Refund(paymentID=ticket.paymentID, orderID=order_to_refund.orderID,
                                                    ticketID=ticket.ticketID, refundAmount=refundAmount_this_ticket)
                                mock_gateway_refund_success = True # Simulate
                                if mock_gateway_refund_success:
                                    new_refund.updateStatus("Processed")
                                    ticket.status = "Refunded"
                                    numTickets_refunded_this_op += 1
                                else:
                                    new_refund.updateStatus("Failed")
                                    ticket.status = "RefundFailed"
                                    success_overall = False
                                new_refund.save()
                                ticket.save() # Save new ticket status
                            else: # Could not void
                                messages.append(f"Could not void ticket {ticket.ticketID}")
                                success_overall = False
                    
                    if numTickets_refunded_this_op > 0:
                         # Update overall payment and order status
                        payment_for_order.status = "Refunded" # Simplification
                        payment_for_order.save()
                        if numTickets_refunded_this_op == order_to_refund.numTickets:
                            order_to_refund.status = "Refunded"
                        else:
                            order_to_refund.status = "PartiallyRefunded"
                        order_to_refund.save()
                        flash("Refund processed for eligible tickets.", "success")
                    elif success_overall: # No active tickets, but no errors
                        flash("No active tickets found in this order to refund.", "info")
                    else: # Some error occurred
                        flash("Refund processing encountered issues: " + " | ".join(messages), "error")
                        
        return redirect(url_for('requestRefundStandaloneRoute'))

    orders_data_for_display = []
    user_orders = Order.find_by_userID(currentUserID)
    if user_orders:
        for order in user_orders:
            trip = Trip.findByID(order.tripID)
            orders_data_for_display.append({"order": order, "trip": trip})
            
    if not orders_data_for_display:
         flash(f"No orders found for user '{currentUserID}'. Please ensure sample data exists.", "info")

    return render_template('refund_request_standalone.html', 
                           title='Standalone Refund Demo', 
                           orders_to_display=orders_data_for_display,
                           mockUserID=currentUserID)


# --- Admin Routes ---
def adminRequired(f): # Basic placeholder
    # In real app, check admin session
    print(f"Mock Admin Access for: {mock_adminID}")
    return f

@app.route('/admin/manage-routes', methods=['GET'])
@adminRequired 
def adminManageRoutesRoute():
    routes = Route.getAll()
    return render_template('admin_manage_routes.html', title="Admin: Manage Routes", routes=routes)

@app.route('/admin/route/<routeID>/stops', methods=['GET'])
@adminRequired
def adminRouteStopsRoute(routeID):
    route = Route.findByID(routeID)
    if not route:
        flash(f"Route with ID {routeID} not found.", "error")
        return redirect(url_for('adminManageRoutesRoute'))
    
    stops_on_route_details = []
    for stopID in route.stopIDs:
        stop = Stop.findByID(stopID)
        if stop:
            location = stop.get_location() # Use Stop's helper method
            stops_on_route_details.append({"stop": stop, "location": location})
            
    return render_template('admin_route_stops.html', 
                           title=f"Admin: Stops for {route.routeName}", 
                           route=route, stops_on_route=stops_on_route_details)

@app.route('/admin/update-stop-location/<routeID>/<stopID>', methods=['GET', 'POST'])
@adminRequired
def adminUpdateStopLocationRoute(routeID, stopID):
    admin_userID = mock_adminID 

    route = Route.findByID(routeID) 
    stop_to_update = Stop.findByID(stopID)
    current_location = None
    if stop_to_update:
        current_location = stop_to_update.get_location()

    if not route or not stop_to_update or not current_location:
        flash("Route, Stop, or its Location not found for update.", "error")
        return redirect(url_for('adminManageRoutesRoute')) 

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
                if route.findStopID(stopID): # Check if stop belongs to route
                    success, message = stop_to_update.updateLocationDetails(lat_f, lon_f, new_address, new_city, new_postcode)
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('adminRouteStopsRoute', routeID=routeID))
                    else:
                        flash(message, 'error')
                else:
                    flash(f"Stop ID '{stopID}' not found on Route '{route.routeName}'.", "error")

            except ValueError:
                flash("Latitude and Longitude must be valid numbers.", "error")
    
    return render_template('admin_update_stop_location_form.html', 
                           title=f"Update Location for Stop: {stop_to_update.stopName}",
                           route=route, stop=stop_to_update, current_location=current_location)

@app.route('/admin/feedbacks', methods=['GET'])
@adminRequired
def adminManageFeedbacksRoute():
    status_filter = request.args.get('status', 'New')
    all_feedbacks = Feedback.getAll(status_filter=status_filter if status_filter != "All" else None)
    
    feedbacks_data_for_display = []
    if all_feedbacks:
        for fb in all_feedbacks:
            submitter = User.findByID(fb.submitterUserID) # Find by actual userID now
            submitter_name = submitter.username if submitter else "Unknown User"
            responses = fb.get_responses() # Use Feedback's helper method
            feedbacks_data_for_display.append({"feedback": fb, "submitter_name": submitter_name, "responses": responses})
    
    all_statuses = ["All", "New", "Pending", "Responded", "Closed"] 
    return render_template('admin_manage_feedbacks.html', 
                           title="Admin: Manage User Feedbacks", 
                           feedbacks_data=feedbacks_data_for_display,
                           all_statuses=all_statuses, current_status_filter=status_filter)

@app.route('/admin/feedback/<feedbackID>/respond', methods=['GET', 'POST'])
@adminRequired
def adminRespondToFeedbackRoute(feedbackID):
    admin_userID = mock_adminID 
    feedback_to_respond = Feedback.findByID(feedbackID)

    if not feedback_to_respond:
        flash("Feedback item not found.", "error"); return redirect(url_for('adminManageFeedbacksRoute'))

    submitter = User.findByID(feedback_to_respond.submitterUserID)
    submitter_name = submitter.username if submitter else "Unknown User"
    existing_responses = feedback_to_respond.get_responses()

    if request.method == 'POST':
        response_text = request.form.get('response_text')
        if not response_text or not response_text.strip():
            flash("Response text cannot be empty.", "error")
        else:
            # --- Response Logic (moved from service) ---
            new_response = Response(feedbackID=feedbackID, responderAdminID=admin_userID, responseContent=response_text)
            new_response.save() # Response saves itself
            
            feedback_to_respond.addResponseID(new_response.responseID)
            feedback_to_respond.updateStatus("Responded")
            feedback_to_respond.save() # Feedback saves itself

            # Create and save notification
            notif_msg = f"Admin responded to your feedback (ID: {feedbackID}): '{response_text[:30]}...'"
            notification = Notification(recipientuserID=feedback_to_respond.submitterUserID,
                                        senderuserID=admin_userID, messageContent=notif_msg,
                                        notificationType="FeedbackResponse")
            notification.save() # Notification saves itself

            flash("Response submitted and user notified (mock).", "success")
            return redirect(url_for('adminManageFeedbacksRoute'))
                
    return render_template('admin_respond_feedback_form.html',
                           title=f"Respond to Feedback ID: {feedback_to_respond.feedbackID}",
                           feedback=feedback_to_respond, submitter_name=submitter_name, existing_responses=existing_responses)

# --- Main execution ---
if __name__ == '__main__':
    
   # Ensure mock users exist
    if not User.findByID(mockUserID): # Assuming mockUserID is correctly defined and used
        User(username="mockuser", email="mock@example.com", password="password", userID=mockUserID).save()
    
    # Use the defined variable name: mock_adminID
    if not User.findByID(mock_adminID): 
        Admin(username="admin", email="admin@example.com", password="adminpassword", userID=mock_adminID, adminLevel="superuser").save()


    app.run(debug=True)