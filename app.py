# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session 
from models import (User, Admin, Trip, Ticket, Order, Payment, Refund, 
                    Location, Stop, Route, Feedback, Response, Notification, OrderLineItem) # Assuming OrderLineItem is used

app = Flask(__name__)
app.secret_key = 'your_very_secret_dev_key_123!' 

mockUserID = "mock_user_001" 
mock_adminID = "admin_user_001" 

# --- Basic Routes ---
@app.route('/')
def home():
    return render_template('index.html', title='Welcome')

# --- User Facing Routes ---
# REGISTRATION ROUTE IS REMOVED

@app.route('/search-trips', methods=['GET'])
def searchTripsRoute(): # camelCase route function name
    originQuery = request.args.get('origin', '').strip()      # camelCase local variable
    destinationQuery = request.args.get('destination', '').strip() # camelCase local variable
    dateQuery = request.args.get('date', '').strip()         # camelCase local variable
    
    # Use model's static search method with camelCase parameters
    tripsFound = Trip.search( 
        origin=originQuery if originQuery else None,
        destination=destinationQuery if destinationQuery else None,
        dateStr=dateQuery if dateQuery else None # CORRECTED: dateStr to match model method
    )
    searchPerformed = bool(originQuery or destinationQuery or dateQuery) # camelCase local variable
    return render_template('search_trips.html',
                           title='Search & Book Tickets',
                           trips=tripsFound,
                           search_origin=originQuery,      # Template variable can be snake_case if preferred for HTML
                           search_destination=destinationQuery,
                           search_date=dateQuery,
                           search_performed=searchPerformed)

@app.route('/book-trip/<tripID>', methods=['GET', 'POST'])
def bookTripRoute(tripID): # camelCase parameter
    currentUserID = mockUserID 
    tripToBook = Trip.findByID(tripID) # camelCase method call

    if not tripToBook:
        flash("Trip not found.", "error"); return redirect(url_for('searchTripsRoute'))

    if request.method == 'POST':
        numTicketsToBook = 1 # camelCase local variable
        
        if tripToBook.availableSeats < numTicketsToBook: # camelCase attribute access
            flash("Not enough available seats.", "error")
            return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}', 
                                   trip=tripToBook, booking_successful=False)
        else:
            # --- Booking Logic with OrderLineItem ---
            newOrder = Order(userID=currentUserID, status="PendingPayment") # camelCase parameters
            newOrder.save()

            # Create OrderLineItem
            lineItem = OrderLineItem(
                orderID=newOrder.orderID, # camelCase attribute
                itemID=tripToBook.tripID, 
                itemType="TripTicket",      
                quantity=numTicketsToBook,
                unitPrice=tripToBook.price
            )
            lineItem.save()

            orderTotalAmount = newOrder.calculateTotalAmount() # camelCase method call

            mockPaymentSuccessful = True 
            savedPayment = None
            if mockPaymentSuccessful:
                newPayment = Payment(orderID=newOrder.orderID, amount=orderTotalAmount, status="Completed") # camelCase parameter
                newPayment.save()
                savedPayment = newPayment 
                newOrder.status = "Completed"
                newOrder.save() 
            else:
                newOrder.status = "PaymentFailed"
                newOrder.save()
                flash("Payment failed.", "error")
                return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}', 
                                       trip=tripToBook, booking_successful=False)

            if tripToBook.updateSeats(numTicketsToBook, operation="book"): # camelCase method call
                tripToBook.save()

                createdTicketsInfo = [] # camelCase local variable
                for _ in range(numTicketsToBook):
                    newTicket = Ticket(userID=currentUserID, tripID=tripToBook.tripID, 
                                        orderID=newOrder.orderID, paymentID=savedPayment.paymentID) # camelCase parameters
                    newTicket.save()
                    createdTicketsInfo.append(newTicket)
                
                flash(f"{numTicketsToBook} Ticket(s) purchased for Order {newOrder.orderID}!", 'success')
                return render_template('book_trip_form.html', title=f'Booking Confirmed', 
                                       trip=tripToBook, order=newOrder, 
                                       ticket=createdTicketsInfo[0] if createdTicketsInfo else None, 
                                       booking_successful=True)
            else: 
                flash("Critical error: Payment successful, but failed to secure seats.", "error")
                if savedPayment:
                    savedPayment.status = "RequiresRefund"; savedPayment.save()
                newOrder.status = "SeatBookingFailure"; newOrder.save()
                return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}', 
                                   trip=tripToBook, booking_successful=False)
    
    return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}', 
                           trip=tripToBook, booking_successful=False)


# --- STANDALONE REFUND DEMO ROUTE ---
@app.route('/standalone-refund-demo', methods=['GET', 'POST'])
def requestRefundStandaloneRoute(): # camelCase function name
    currentUserID = mockUserID 

    if request.method == 'POST':
        orderIDToRefund = request.form.get('order_id_to_refund') # snake_case from form, fine
        orderToRefund = Order.findByID(orderIDToRefund) # camelCase method call

        if not orderToRefund:
            flash("Order not found.", "error")
        elif orderToRefund.userID != currentUserID: # camelCase attribute
            flash("This order does not belong to you.", "error")
        elif orderToRefund.status != "Completed":
            flash(f"Order (Status: {orderToRefund.status}) not eligible for refund.", "warning")
        else:
            # --- Refund Logic (Simplified for full order refund) ---
            paymentForOrder = Payment.findByOrderID(orderToRefund.orderID) # camelCase method call
            ticketsForOrder = Ticket.findByOrderID(orderToRefund.orderID) # camelCase method call

            if not paymentForOrder:
                flash("Payment for this order not found. Cannot process refund.", "error")
            elif paymentForOrder.status == "Refunded":
                flash("This order has already been fully refunded.", "info")
                orderToRefund.status = "Refunded"; orderToRefund.save()
            else:
                refundProcessedCount = 0 # camelCase local variable
                for ticket in ticketsForOrder:
                    if ticket.status == "Active":
                        ticket.void()
                        ticket.save()
                        tripOfTicket = Trip.findByID(ticket.tripID) # camelCase method call
                        if tripOfTicket:
                            tripOfTicket.updateSeats(1, operation="refund") # camelCase method call
                            tripOfTicket.save()
                        
                        # Assuming OrderLineItem was used to store original item prices for accurate refund amount
                        # For simplicity now, using a proportional amount if Order had total and numTickets
                        # If Order totalAmount is from lineItems, this needs to be more precise
                        lineItemsForOrder = OrderLineItem.findByOrderID(orderToRefund.orderID)
                        refundAmountThisTicket = 0
                        if lineItemsForOrder: # Calculate based on line items if they exist
                            # This simplistic approach assumes one line item per ticket
                            # and that line item's itemID matches ticket.tripID (if itemType is TripTicket)
                            # or line item's itemID matches ticket.ticketID (if itemType is specific Ticket)
                            # A more robust link would be needed.
                            # For now, let's assume the order's calculated total is what we work with proportionally.
                            numOriginalTicketsInOrder = 0
                            for li in lineItemsForOrder:
                                if li.itemType == "TripTicket": # Or whatever type you use for tickets
                                    numOriginalTicketsInOrder += li.quantity
                            
                            if numOriginalTicketsInOrder > 0:
                                refundAmountThisTicket = orderToRefund.calculateTotalAmount() / numOriginalTicketsInOrder
                            else: # Fallback if line items don't match up, less accurate
                                refundAmountThisTicket = paymentForOrder.amount / len(ticketsForOrder) if ticketsForOrder else 0


                        newRefund = Refund(paymentID=paymentForOrder.paymentID, 
                                            orderID=orderToRefund.orderID,
                                            ticketID=ticket.ticketID, 
                                            refundAmount=refundAmountThisTicket)
                        newRefund.updateStatus("Processed") # camelCase method call
                        newRefund.save()
                        ticket.status = "Refunded"
                        ticket.save()
                        refundProcessedCount += 1
                
                if refundProcessedCount > 0:
                    paymentForOrder.status = "Refunded"
                    paymentForOrder.save()
                    orderToRefund.status = "Refunded" 
                    orderToRefund.save()
                    flash(f"{refundProcessedCount} ticket(s) in the order refunded successfully.", "success")
                else:
                    flash("No active tickets found in this order to refund.", "info")
                        
        return redirect(url_for('requestRefundStandaloneRoute'))

    ordersDataForDisplay = [] # camelCase local variable
    userOrders = Order.findByUserID(currentUserID) # camelCase method call
    if userOrders:
        for order in userOrders:
            tripInfoForDisplay = "Trip info N/A (check line items)" # Default
            lineItems = order.getLineItems() # camelCase method call
            if lineItems:
                firstTicketLineItem = next((li for li in lineItems if li.itemType == "TripTicket"), None)
                if firstTicketLineItem:
                    # Assuming lineItem.itemID for "TripTicket" is the tripID
                    trip = Trip.findByID(firstTicketLineItem.itemID) 
                    if trip:
                        tripInfoForDisplay = f"{trip.origin} to {trip.destination}"
            
            ordersDataForDisplay.append({"order": order, "trip_info": tripInfoForDisplay, "total_amount": order.calculateTotalAmount()})
            
    if not ordersDataForDisplay:
         flash(f"No orders found for user '{currentUserID}'. Please ensure sample data exists.", "info")

    return render_template('refund_request_standalone.html', 
                           title='Standalone Refund Demo', 
                           orders_to_display=ordersDataForDisplay,
                           mockUserID=currentUserID) # Parameter name to template


# --- Admin Routes ---
def adminRequired(f): 
    print(f"Mock Admin Access for: {mock_adminID}")
    return f

@app.route('/admin/manage-routes', methods=['GET'])
@adminRequired 
def adminManageRoutesRoute(): # camelCase function name
    routes = Route.getAll() # camelCase method call
    return render_template('admin_manage_routes.html', title="Admin: Manage Routes", routes=routes)

@app.route('/admin/route/<routeID>/stops', methods=['GET'])
@adminRequired
def adminRouteStopsRoute(routeID): # camelCase parameter
    route = Route.findByID(routeID) # camelCase method call
    if not route:
        flash(f"Route with ID {routeID} not found.", "error")
        return redirect(url_for('adminManageRoutesRoute'))
    
    stopsOnRouteDetails = [] # camelCase local variable
    for stopID in route.stopIDs: # camelCase attribute
        stop = Stop.findByID(stopID) # camelCase method call
        if stop:
            location = stop.getLocation() # camelCase method call
            stopsOnRouteDetails.append({"stop": stop, "location": location})
            
    return render_template('admin_route_stops.html', 
                           title=f"Admin: Stops for {route.routeName}", # camelCase attribute
                           route=route, stops_on_route=stopsOnRouteDetails)

@app.route('/admin/update-stop-location/<routeID>/<stopID>', methods=['GET', 'POST'])
@adminRequired
def adminUpdateStopLocationRoute(routeID, stopID): # camelCase parameters
    adminUserID = mock_adminID # camelCase variable

    route = Route.findByID(routeID) 
    stopToUpdate = Stop.findByID(stopID) # camelCase local variable
    currentLocation = None # camelCase local variable
    if stopToUpdate:
        currentLocation = stopToUpdate.getLocation()

    if not route or not stopToUpdate or not currentLocation:
        flash("Route, Stop, or its Location not found for update.", "error")
        return redirect(url_for('adminManageRoutesRoute')) 

    if request.method == 'POST':
        newLatitudeStr = request.form.get('latitude')
        newLongitudeStr = request.form.get('longitude')
        newAddress = request.form.get('addressLine1') # Match form field if it's addressLine1
        newCity = request.form.get('city')
        newPostcode = request.form.get('postcode')

        if not all([newLatitudeStr, newLongitudeStr, newAddress, newCity, newPostcode]):
            flash("All location fields are required.", "error")
        else:
            try:
                latF = float(newLatitudeStr); lonF = float(newLongitudeStr) # camelCase local variable
                if route.findStopID(stopID): # camelCase method call
                    success, message = stopToUpdate.updateLocationDetails(latF, lonF, newAddress, newCity, newPostcode) # camelCase method call
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
                           title=f"Update Location for Stop: {stopToUpdate.stopName}", # camelCase attribute
                           route=route, stop=stopToUpdate, current_location=currentLocation)

@app.route('/admin/feedbacks', methods=['GET'])
@adminRequired
def adminManageFeedbacksRoute(): # camelCase function name
    statusFilter = request.args.get('status', 'New') # camelCase local variable
    allFeedbacks = Feedback.getAll(statusFilter=statusFilter if statusFilter != "All" else None) # camelCase method call, parameter
    
    feedbacksDataForDisplay = [] # camelCase local variable
    if allFeedbacks:
        for fb in allFeedbacks:
            submitter = User.findByID(fb.submitterUserID) # camelCase attribute
            submitterName = submitter.username if submitter else "Unknown User" # camelCase local variable
            responses = fb.getResponses() # camelCase method call
            feedbacksDataForDisplay.append({"feedback": fb, "submitter_name": submitterName, "responses": responses})
    
    allStatuses = ["All", "New", "Pending", "Responded", "Closed"] 
    return render_template('admin_manage_feedbacks.html', 
                           title="Admin: Manage User Feedbacks", 
                           feedbacks_data=feedbacksDataForDisplay,
                           all_statuses=allStatuses, current_status_filter=statusFilter)

@app.route('/admin/feedback/<feedbackID>/respond', methods=['GET', 'POST'])
@adminRequired
def adminRespondToFeedbackRoute(feedbackID): # camelCase parameter
    adminUserID = mock_adminID 
    feedbackToRespond = Feedback.findByID(feedbackID) # camelCase method call

    if not feedbackToRespond:
        flash("Feedback item not found.", "error"); return redirect(url_for('adminManageFeedbacksRoute'))

    submitter = User.findByID(feedbackToRespond.submitterUserID) # camelCase attribute
    submitterName = submitter.username if submitter else "Unknown User"
    existingResponses = feedbackToRespond.getResponses() # camelCase method call

    if request.method == 'POST':
        responseText = request.form.get('response_text') # snake_case from form, fine
        if not responseText or not responseText.strip(): # camelCase variable
            flash("Response text cannot be empty.", "error")
        else:
            newResponse = Response(feedbackID=feedbackID, responderAdminID=adminUserID, responseContent=responseText) # camelCase parameters
            newResponse.save()
            
            feedbackToRespond.addResponseID(newResponse.responseID) # camelCase method call
            feedbackToRespond.updateStatus("Responded") # camelCase method call
            feedbackToRespond.save()

            notifMsg = f"Admin responded to your feedback (ID: {feedbackID}): '{responseText[:30]}...'" # camelCase variable
            notification = Notification(recipientUserID=feedbackToRespond.submitterUserID, # camelCase parameters
                                        senderUserID=adminUserID, messageContent=notifMsg,
                                        notificationType="FeedbackResponse")
            notification.save()

            flash("Response submitted and user notified (mock).", "success")
            return redirect(url_for('adminManageFeedbacksRoute'))
                
    return render_template('admin_respond_feedback_form.html',
                           title=f"Respond to Feedback ID: {feedbackToRespond.feedbackID}", # camelCase attribute
                           feedback=feedbackToRespond, submitter_name=submitterName, existing_responses=existingResponses)

# --- Main execution ---
if __name__ == '__main__':
    if not User.findByID(mockUserID): 
        User(username="mockuser", email="mock@example.com", password="password", userID=mockUserID).save()
    if not User.findByID(mock_adminID): 
        Admin(username="admin", email="admin@example.com", password="adminpassword", userID=mock_adminID, adminLevel="superuser").save()
    app.run(debug=True)