# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime # For date validation in searchTripsRoute

# Import models from the models package - class names are still PascalCase
from models import (
    User, Admin, Trip, Ticket, Order, Payment, Refund,
    Stop, Route, Feedback, Response, Notification, OrderLineItem # Location removed earlier
)

app = Flask(__name__)
app.secret_key = 'your_very_secret_dev_key_123!'

mockUserID = "mock_user_001"
mock_adminID = "admin_user_001"

# --- Basic Routes ---
@app.route('/')
def home():
    return render_template('index.html', title='Welcome')

# --- User Facing Routes ---
@app.route('/search-trips', methods=['GET'])
def searchTripsRoute(): # Route function names are often camelCase or snake_case
    originQuery = request.args.get('origin', '').strip()
    destinationQuery = request.args.get('destination', '').strip()
    dateQuery = request.args.get('date', '').strip()

    tripsFound = []
    searchPerformed = bool(originQuery or destinationQuery or dateQuery)
    validationPassed = True

    if searchPerformed:
        if originQuery and originQuery.isdigit():
            flash("Invalid input: Origin cannot be just numbers.", "error")
            validationPassed = False
        if destinationQuery and destinationQuery.isdigit():
            flash("Invalid input: Destination cannot be just numbers.", "error")
            validationPassed = False
        if dateQuery:
            try:
                datetime.strptime(dateQuery, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "error")
                validationPassed = False
        
        if validationPassed:
            tripsFound = Trip.search(
                origin=originQuery if originQuery else None,
                destination=destinationQuery if destinationQuery else None,
                date_str=dateQuery if dateQuery else None # Trip.search method uses date_str
            )
            if not tripsFound:
                 flash("No trips found matching your criteria.", "info")
    else:
        tripsFound = Trip.getAll() # Method name camelCase
        if not tripsFound:
            flash("No trips are currently available.", "info")

    return render_template('search_trips.html',
                           title='Search & Book Tickets',
                           trips=tripsFound,
                           searchOrigin=originQuery,
                           searchDestination=destinationQuery,
                           searchDate=dateQuery,
                           searchPerformed=searchPerformed)

@app.route('/book-trip/<tripID>', methods=['GET', 'POST'])
def bookTripRoute(tripID): # Route function name
    currentUserID = mockUserID
    tripToBook = Trip.findByID(tripID) # Method name camelCase

    if not tripToBook:
        flash("Trip not found.", "error"); return redirect(url_for('searchTripsRoute'))

    if request.method == 'POST':
        numTicketsToBook = 1 # Local var

        if tripToBook.availableSeats < numTicketsToBook: # Access camelCase attribute
            flash("Not enough available seats.", "error")
            return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}',
                                   trip=tripToBook, booking_successful=False)
        else:
            newOrder = Order(userID=currentUserID, status="PendingPayment") # Pass camelCase params
            newOrder.save()

            lineItem = OrderLineItem(
                orderID=newOrder.orderID, # Access camelCase attribute
                itemID=tripToBook.tripID,
                itemType="TripTicket",      # Pass camelCase params
                quantity=numTicketsToBook,
                unitPrice=tripToBook.price # Access lowercase attribute (price was not changed)
            )
            lineItem.save()

            orderTotalAmount = newOrder.calculateTotalAmount() # Call camelCase method

            mockPaymentSuccessful = True
            savedPayment = None
            if mockPaymentSuccessful:
                newPayment = Payment(orderID=newOrder.orderID, amount=orderTotalAmount, status="Completed") # Pass camelCase params
                newPayment.save()
                savedPayment = newPayment
                newOrder.status = "Completed" # status is lowercase
                newOrder.save()
            else:
                newOrder.status = "PaymentFailed"
                newOrder.save()
                flash("Payment failed.", "error")
                return render_template('book_trip_form.html', title=f'Book Trip: {tripToBook.tripID}',
                                       trip=tripToBook, booking_successful=False)

            if tripToBook.updateSeats(numTicketsToBook, operation="book"): # Call camelCase method
                tripToBook.save()

                createdTicketsInfo = [] # Local var
                for _ in range(numTicketsToBook):
                    newTicket = Ticket(userID=currentUserID, tripID=tripToBook.tripID,
                                        orderID=newOrder.orderID, paymentID=savedPayment.paymentID) # Pass camelCase params
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

@app.route('/standalone-refund-demo', methods=['GET', 'POST'])
def requestRefundStandaloneRoute(): # Route function name
    currentUserID = mockUserID

    if request.method == 'POST':
        orderIDToRefund = request.form.get('order_id_to_refund') # Form data is snake_case
        orderToRefund = Order.findByID(orderIDToRefund) # Call camelCase method

        if not orderToRefund:
            flash("Order not found.", "error")
        elif orderToRefund.userID != currentUserID: # Access camelCase attribute
            flash("This order does not belong to you.", "error")
        elif orderToRefund.status != "Completed":
            flash(f"Order (Status: {orderToRefund.status}) not eligible for refund.", "warning")
        else:
            paymentForOrder = Payment.findByOrderID(orderToRefund.orderID) # Call camelCase method
            ticketsForOrder = Ticket.findByOrderID(orderToRefund.orderID) # Call camelCase method

            if not paymentForOrder:
                flash("Payment for this order not found. Cannot process refund.", "error")
            elif paymentForOrder.status == "Refunded":
                flash("This order has already been fully refunded.", "info")
                if orderToRefund.status != "Refunded":
                    orderToRefund.status = "Refunded"; orderToRefund.save()
            else:
                refundProcessedCount = 0 # Local var
                for ticket in ticketsForOrder:
                    if ticket.status == "Active":
                        tripOfTicket = Trip.findByID(ticket.tripID) # Call camelCase method

                        lineItemsForOrder = OrderLineItem.findByOrderID(orderToRefund.orderID) # Call camelCase method
                        refundAmountThisTicket = 0 # Local var
                        if lineItemsForOrder:
                            numOriginalTicketsInOrder = sum(li.quantity for li in lineItemsForOrder if li.itemType == "TripTicket") # Access camelCase attr
                            if numOriginalTicketsInOrder > 0:
                                refundAmountThisTicket = orderToRefund.calculateTotalAmount() / numOriginalTicketsInOrder # Call camelCase method
                            else:
                                refundAmountThisTicket = paymentForOrder.amount / len(ticketsForOrder) if ticketsForOrder else 0
                        else:
                             refundAmountThisTicket = paymentForOrder.amount / len(ticketsForOrder) if ticketsForOrder else 0

                        newRefund = Refund(paymentID=paymentForOrder.paymentID, # Access camelCase attr
                                            orderID=orderToRefund.orderID, # Access camelCase attr
                                            ticketID=ticket.ticketID, # Access camelCase attr
                                            refundAmount=refundAmountThisTicket) # Pass camelCase param
                        newRefund.updateStatus("Processed") # Call camelCase method
                        newRefund.save()
                        
                        ticket.status = "Refunded"
                        ticket.save()

                        if tripOfTicket:
                            tripOfTicket.updateSeats(1, operation="refund") # Call camelCase method
                            tripOfTicket.save()
                        refundProcessedCount += 1

                if refundProcessedCount > 0:
                    all_tickets_refunded = all(t.status == "Refunded" for t in Ticket.findByOrderID(orderToRefund.orderID)) # Call camelCase method
                    if all_tickets_refunded:
                        paymentForOrder.status = "Refunded"
                        paymentForOrder.save()
                        orderToRefund.status = "Refunded"
                        orderToRefund.save()
                        flash(f"All {refundProcessedCount} ticket(s) in the order refunded successfully. Order status updated.", "success")
                    else:
                        flash(f"{refundProcessedCount} ticket(s) in the order refunded. Some tickets may not have been active or already refunded.", "info")
                else:
                    flash("No active tickets found in this order to refund.", "info")

        return redirect(url_for('requestRefundStandaloneRoute'))

    ordersDataForDisplay = [] # Local var
    userOrders = Order.findByUserID(currentUserID) # Call camelCase method
    if userOrders:
        for order in userOrders:
            tripInfoForDisplay = "Trip info N/A" # Local var
            lineItems = order.getLineItems() # Call camelCase method
            if lineItems:
                firstTicketLineItem = next((li for li in lineItems if li.itemType == "TripTicket"), None) # Access camelCase attr
                if firstTicketLineItem:
                    trip = Trip.findByID(firstTicketLineItem.itemID) # Access camelCase attr
                    if trip:
                        tripInfoForDisplay = f"{trip.origin} to {trip.destination}"

            ordersDataForDisplay.append({"order": order, "trip_info": tripInfoForDisplay, "total_amount": order.calculateTotalAmount()}) # Call camelCase method

    if not ordersDataForDisplay:
         flash(f"No orders found for user '{currentUserID}'. Book a trip or ensure mock data exists.", "info")

    return render_template('refund_request_standalone.html',
                           title='Standalone Refund Demo',
                           orders_to_display=ordersDataForDisplay,
                           mockUserID=currentUserID)


# --- Admin Routes ---
def adminRequired(f): # Function name lowercase
    print(f"Mock Admin Access for: {mock_adminID}")
    return f

@app.route('/admin/manage-routes', methods=['GET'])
@adminRequired
def adminManageRoutesRoute(): # Route function name
    routes = Route.getAll() # Call camelCase method
    return render_template('admin_manage_routes.html', title="Admin: Manage Routes", routes=routes)

@app.route('/admin/route/<routeID>/stops', methods=['GET'])
@adminRequired
def adminRouteStopsRoute(routeID): # Route function name
    route = Route.findByID(routeID) # Call camelCase method
    if not route:
        flash(f"Route with ID {routeID} not found.", "error")
        return redirect(url_for('adminManageRoutesRoute'))

    stopsOnRouteDetails = [] # Local var
    for stopID_val in route.stopIDs: # Access camelCase attr
        stop = Stop.findByID(stopID_val) # Call camelCase method
        if stop:
            location = stop.getLocation() # Call camelCase method
            stopsOnRouteDetails.append({"stop": stop, "location": location})

    return render_template('admin_route_stops.html',
                           title=f"Admin: Stops for {route.routeName}", # Access camelCase attr
                           route=route, stops_on_route=stopsOnRouteDetails)

@app.route('/admin/update-stop-location/<routeID>/<stopID>', methods=['GET', 'POST'])
@adminRequired
def adminUpdateStopLocationRoute(routeID, stopID): # Route function name
    route = Route.findByID(routeID) # Call camelCase method
    stopToUpdate = Stop.findByID(stopID) # Call camelCase method
    currentLocation = None # Local var
    if stopToUpdate:
        currentLocation = stopToUpdate.getLocation() # Call camelCase method

    if not route or not stopToUpdate or not currentLocation:
        flash("Route, Stop, or its current Location not found for update.", "error")
        return redirect(url_for('adminManageRoutesRoute'))

    if request.method == 'POST':
        # Form data is snake_case
        newLatitudeStr = request.form.get('latitude', '').strip()
        newLongitudeStr = request.form.get('longitude', '').strip()
        newAddress = request.form.get('addressLine1', '').strip()
        newCity = request.form.get('city', '').strip()
        newPostcodeStr = request.form.get('postcode', '').strip()

        errors = []
        newLatitude = None # Local vars
        newLongitude = None

        if not newLatitudeStr: errors.append("New Latitude is required.")
        # ... (other validations) ...
        if newLatitudeStr:
            try:
                newLatitude = float(newLatitudeStr)
                if not (-90 <= newLatitude <= 90):
                    errors.append("Latitude must be between -90 and 90.")
            except ValueError: errors.append("Latitude must be a valid number.")
        if newLongitudeStr:
            try:
                newLongitude = float(newLongitudeStr)
                if not (-180 <= newLongitude <= 180):
                    errors.append("Longitude must be between -180 and 180.")
            except ValueError: errors.append("Longitude must be a valid number.")
        # ... (other validations for address, city, postcode) ...

        if errors:
            for error_msg in errors:
                flash(error_msg, "error")
        else:
            if route.findStopID(stopID): # Call camelCase method
                if newLatitude is not None and newLongitude is not None:
                    success, message = stopToUpdate.updateLocationDetails( # Call camelCase method
                        newLatitude, newLongitude, newAddress, newCity, newPostcodeStr
                    )
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('adminRouteStopsRoute', routeID=routeID))
                    else:
                        flash(message, 'error')
                else:
                    flash("Latitude or Longitude was not correctly processed.", "error")
            else:
                flash(f"Stop ID '{stopID}' not found on Route '{route.routeName}'.", "error") # Access camelCase attr
    
    return render_template('admin_update_stop_location_form.html',
                           title=f"Update Location for Stop: {stopToUpdate.stopName}", # Access camelCase attr
                           route=route,
                           stop=stopToUpdate,
                           current_location=currentLocation)

@app.route('/admin/feedbacks', methods=['GET'])
@adminRequired
def adminManageFeedbacksRoute(): # Route function name
    statusFilter = request.args.get('status', 'New') # Local var
    allFeedbacks = Feedback.getAll(statusFilter=statusFilter if statusFilter != "All" else None) # Call camelCase method

    feedbacksDataForDisplay = [] # Local var
    if allFeedbacks:
        for fb in allFeedbacks:
            submitter = User.findByID(fb.submitterUserID) # Call camelCase method, access camelCase attr
            submitterName = submitter.username if submitter else "Unknown User" # Local var
            responses = fb.getResponses() # Call camelCase method
            feedbacksDataForDisplay.append({"feedback": fb, "submitter_name": submitterName, "responses": responses})

    allStatuses = ["All", "New", "Pending", "Responded", "Closed"]
    return render_template('admin_manage_feedbacks.html',
                           title="Admin: Manage User Feedbacks",
                           feedbacks_data=feedbacksDataForDisplay,
                           all_statuses=allStatuses, current_status_filter=statusFilter)

@app.route('/admin/feedback/<feedbackID>/respond', methods=['GET', 'POST'])
@adminRequired
def adminRespondToFeedbackRoute(feedbackID): # Route function name
    adminUserID = mock_adminID
    feedbackToRespond = Feedback.findByID(feedbackID) # Call camelCase method

    if not feedbackToRespond:
        flash("Feedback item not found.", "error"); return redirect(url_for('adminManageFeedbacksRoute'))

    submitter = User.findByID(feedbackToRespond.submitterUserID) # Call camelCase method, access camelCase attr
    submitterName = submitter.username if submitter else "Unknown User"
    existingResponses = feedbackToRespond.getResponses() # Call camelCase method

    if request.method == 'POST':
        responseText = request.form.get('response_text', '').strip() # snake_case from form
        if not responseText:
            flash("Response text cannot be empty.", "error")
        else:
            newResponse = Response(feedbackID=feedbackID, responderAdminID=adminUserID, responseContent=responseText) # Pass camelCase params
            newResponse.save()

            feedbackToRespond.addResponseID(newResponse.responseID) # Call camelCase method, access camelCase attr
            feedbackToRespond.updateStatus("Responded") # Call camelCase method
            feedbackToRespond.save()

            notifMsg = f"Admin responded to your feedback (ID: {feedbackID}): '{responseText[:30]}...'" # Local var
            notification = Notification(recipientUserID=feedbackToRespond.submitterUserID, # Pass camelCase params
                                        senderUserID=adminUserID, messageContent=notifMsg,
                                        notificationType="FeedbackResponse")
            notification.save()

            flash("Response submitted and user notified.", "success")
            return redirect(url_for('adminManageFeedbacksRoute'))

    return render_template('admin_respond_feedback_form.html',
                           title=f"Respond to Feedback ID: {feedbackToRespond.feedbackID}", # Access camelCase attr
                           feedback=feedbackToRespond, submitter_name=submitterName, existing_responses=existingResponses)


# --- Main execution ---
if __name__ == '__main__':
    if not User.findByID(mockUserID): # Call camelCase method
        User(username="mockuser", email="mock@example.com", password="password", userID=mockUserID).save()
    
    admin_user = User.findByID(mock_adminID) # Call camelCase method
    if not admin_user or not isinstance(admin_user, Admin):
        if admin_user and not isinstance(admin_user, Admin):
            print(f"Warning: User {mock_adminID} exists but is not an Admin. Overwriting with Admin type.")
        Admin(username="admin", email="admin@example.com", password="adminpassword", userID=mock_adminID, adminLevel="superuser").save() # Pass camelCase param

    app.run(debug=True)