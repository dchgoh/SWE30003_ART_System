# services.py
from models import User, Trip, Ticket, Order, Payment, Refund, Location, Stop, Route, Feedback, Response, Notification
from repositories import UserRepository, TripRepository, TicketRepository, OrderRepository, PaymentRepository, RefundRepository, LocationRepository, StopRepository, RouteRepository, FeedbackRepository, ResponseRepository, NotificationRepository

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()


class BookingService:
    def __init__(self):
        self.trip_repository = TripRepository()
        self.ticket_repository = TicketRepository()
        self.order_repository = OrderRepository()
        self.payment_repository = PaymentRepository()

    def search_available_trips(self, origin=None, destination=None, date_str=None):
        return self.trip_repository.search_trips(origin, destination, date_str)

    def get_trip_details(self, trip_id):
        return self.trip_repository.find_by_id(trip_id)

    def purchase_ticket(self, user_id, trip_id, num_tickets=1): # Returns (first_ticket, order, message)
        trip = self.trip_repository.find_by_id(trip_id)
        if not trip: return None, None, "Trip not found."
        if trip.available_seats < num_tickets: return None, None, "Not enough available seats."

        order_total_amount = trip.price * num_tickets
        new_order = Order(user_id=user_id, trip_id=trip_id, num_tickets=num_tickets, total_amount=order_total_amount, status="PendingPayment")
        saved_order = self.order_repository.save(new_order)
        if not saved_order: return None, None, "Failed to create order."

        mock_payment_successful = True 
        saved_payment = None
        if mock_payment_successful:
            new_payment = Payment(order_id=saved_order.order_id, amount=saved_order.total_amount, status="Completed")
            saved_payment = self.payment_repository.save(new_payment)
            if not saved_payment:
                saved_order.status = "PaymentFailed"; self.order_repository.save(saved_order)
                return None, None, "Payment processing failed."
            saved_order.status = "Completed"; self.order_repository.save(saved_order)
        else:
            saved_order.status = "PaymentFailed"; self.order_repository.save(saved_order)
            return None, None, "Payment failed."

        if self.trip_repository.update_trip_seats(trip_id, num_tickets, operation="book"):
            created_tickets = []
            all_tickets_saved = True
            for _ in range(num_tickets):
                new_ticket = Ticket(user_id=user_id, trip_id=trip_id, order_id=saved_order.order_id, payment_id=saved_payment.payment_id)
                saved_ticket_obj = self.ticket_repository.save(new_ticket)
                if not saved_ticket_obj: all_tickets_saved = False; break
                created_tickets.append(saved_ticket_obj)
            
            if all_tickets_saved and created_tickets:
                return created_tickets[0], saved_order, f"{num_tickets} Ticket(s) purchased!"
            else:
                self.trip_repository.update_trip_seats(trip_id, num_tickets, operation="refund")
                saved_payment.status = "RequiresRefund"; self.payment_repository.save(saved_payment)
                saved_order.status = "TicketCreationFailure"; self.order_repository.save(saved_order)
                for ct in created_tickets: self.ticket_repository.delete(ct.ticket_id)
                return None, None, "Failed to create tickets after payment."
        else:
            saved_payment.status = "RequiresRefund"; self.payment_repository.save(saved_payment)
            saved_order.status = "SeatBookingFailure"; self.order_repository.save(saved_order)
            return None, None, "Payment ok, but failed to secure seats. Contact support."

    def get_user_orders(self, user_id): # Used by /my-bookings for listing
        return self.order_repository.find_by_user_id(user_id)

    def get_order_details(self, order_id): # Used by refund confirmation
        return self.order_repository.find_by_id(order_id)


class RefundService:
    def __init__(self):
        self.order_repository = OrderRepository()
        self.ticket_repository = TicketRepository()
        self.payment_repository = PaymentRepository()
        self.refund_repository = RefundRepository()
        self.trip_repository = TripRepository()

    def get_all_orders_for_user_display(self, user_id):
        all_user_orders = self.order_repository.find_by_user_id(user_id)
        orders_with_details = []
        for order in all_user_orders:
            trip = self.trip_repository.find_by_id(order.trip_id)
            # Add tickets associated with this order for more detailed display if needed
            # tickets = self.ticket_repository.find_by_order_id(order.order_id)
            orders_with_details.append({"order": order, "trip": trip}) # , "tickets": tickets
        return orders_with_details

    def process_refund_for_order(self, user_id, order_id_to_refund):
        order = self.order_repository.find_by_id(order_id_to_refund)
        if not order: return False, "Order for refund not found."
        if order.user_id != user_id: return False, "Order does not belong to this user."
        if order.status != "Completed": return False, f"Order (Status: {order.status}) not eligible for refund."

        tickets_in_order = self.ticket_repository.find_by_order_id(order.order_id)
        if not tickets_in_order:
            order.status = "ErrorNoTicketsForRefund"; self.order_repository.save(order)
            return False, "Order has no tickets to refund."

        any_refund_processed_in_this_call = False
        all_active_tickets_processed_successfully = True
        overall_messages = []

        for ticket in tickets_in_order:
            if ticket.status == "Active":
                if not ticket.void():
                    overall_messages.append(f"Ticket {ticket.ticket_id} already void or in non-refundable state.")
                    continue # Skip to next ticket
                self.ticket_repository.save(ticket) # Save voided status

                self.trip_repository.update_trip_seats(ticket.trip_id, 1, operation="refund")

                original_payment = self.payment_repository.find_by_id(ticket.payment_id)
                if not original_payment:
                    ticket.status = "ErrorNoPaymentFoundForRefund"; self.ticket_repository.save(ticket)
                    overall_messages.append(f"No payment record for ticket {ticket.ticket_id}.")
                    all_active_tickets_processed_successfully = False
                    continue
                
                if original_payment.status == "Refunded": # Entire payment already refunded
                    ticket.status = "Refunded"; self.ticket_repository.save(ticket)
                    overall_messages.append(f"Ticket {ticket.ticket_id} part of an already refunded payment.")
                    any_refund_processed_in_this_call = True # Counts as "handled"
                    continue

                refund_amount = order.total_amount / order.num_tickets if order.num_tickets > 0 else 0
                new_refund = Refund(payment_id=original_payment.payment_id, order_id=order.order_id, 
                                    ticket_id=ticket.ticket_id, refund_amount=refund_amount)
                
                mock_gateway_success = True 
                if mock_gateway_success:
                    new_refund.update_status("Processed")
                    ticket.status = "Refunded"
                    overall_messages.append(f"Ticket {ticket.ticket_id} refunded.")
                    any_refund_processed_in_this_call = True
                else:
                    new_refund.update_status("Failed")
                    ticket.status = "RefundFailed"
                    overall_messages.append(f"Gateway refund failed for ticket {ticket.ticket_id}.")
                    all_active_tickets_processed_successfully = False
                
                self.refund_repository.save(new_refund)
                self.ticket_repository.save(ticket)

                if mock_gateway_success: # If this ticket refund was successful, update payment
                    # Simplification: assume one payment object covers all tickets in this order,
                    # so if any ticket is refunded, mark payment as Refunded.
                    # A more complex system might track partial refunds on a single payment object.
                    original_payment.status = "Refunded" 
                    self.payment_repository.save(original_payment)
            elif ticket.status == "Refunded":
                overall_messages.append(f"Ticket {ticket.ticket_id} was previously refunded.")
                any_refund_processed_in_this_call = True # Consider it handled

        # Update order status
        final_ticket_statuses = [t.status for t in self.ticket_repository.find_by_order_id(order.order_id)]
        if all(s == "Refunded" for s in final_ticket_statuses):
            order.status = "Refunded"
        elif any(s == "Refunded" for s in final_ticket_statuses):
            order.status = "PartiallyRefunded"
        elif not any_refund_processed_in_this_call and not all_active_tickets_processed_successfully :
             order.status = "RefundProcessingError" # No new refunds and some error
        # If some tickets were active but couldn't be refunded, order might remain "Completed" or a specific error state
        
        self.order_repository.save(order)
        
        combined_message = "Refund processing attempt: " + " | ".join(overall_messages) if overall_messages else "No active tickets were eligible for refund in this order."
        return any_refund_processed_in_this_call, combined_message
    
class AdminRouteService:
    def __init__(self):
        self.route_repository = RouteRepository()
        self.stop_repository = StopRepository()
        self.location_repository = LocationRepository()
        # self.admin_repository = UserRepository() # Or a dedicated AdminRepository if you create one

    def get_all_routes(self):
        return self.route_repository.get_all()

    def get_route_details_with_stops(self, route_id):
        route = self.route_repository.find_by_id(route_id)
        if not route:
            return None, None
        
        stops_on_route = []
        for stop_id in route.stop_ids:
            stop = self.stop_repository.find_by_id(stop_id)
            if stop:
                location = self.location_repository.find_by_id(stop.location_id)
                stops_on_route.append({"stop": stop, "location": location})
        return route, stops_on_route


    def update_stop_location_details(self, admin_user_id, route_id, stop_id, 
                                     new_latitude, new_longitude, new_address, new_city, new_postcode):
        # TODO: Add admin authorization check if admin_user_id is a real user
        
        route = self.route_repository.find_by_id(route_id)
        if not route:
            return False, "Route not found."

        # Sequence Diagram: Route.findStop()
        # In our model, Route.stop_ids holds IDs. We fetch the Stop object using its ID.
        target_stop_id_on_route = route.find_stop_id(stop_id) # Checks if stop_id is part of this route's stop_ids
        if not target_stop_id_on_route: # target_stop_id_on_route will be stop_id if found, else None
            return False, f"Stop ID '{stop_id}' not found on Route '{route.route_name}'."

        stop_to_update = self.stop_repository.find_by_id(stop_id)
        if not stop_to_update:
            return False, f"Stop with ID '{stop_id}' does not exist in the system."

        # Sequence Diagram: Stop.updateLocation() -> Location.setLocationDetails()
        # The Stop model's update_location method will handle fetching its Location object
        # and calling set_details on it, then saving the Location object.
        success, message = stop_to_update.update_location(
            self.location_repository, # Pass the repo so Stop can save its Location
            new_latitude, new_longitude, 
            new_address, new_city, new_postcode
        )
        
        if success:
            # No need to save Stop object itself if only its associated Location changed,
            # unless Stop model also stores some denormalized location info that needs update.
            # self.stop_repository.save(stop_to_update) # Only if Stop object itself changed
            return True, "Stop location updated successfully."
        else:
            return False, f"Failed to update stop location: {message}"

    # --- Helper methods for Admin UI ---
    def get_all_stops_with_locations(self):
        stops = self.stop_repository.get_all()
        detailed_stops = []
        for stop in stops:
            location = self.location_repository.find_by_id(stop.location_id)
            detailed_stops.append({"stop": stop, "location": location})
        return detailed_stops

    def get_stop_details_with_location(self, stop_id):
        stop = self.stop_repository.find_by_id(stop_id)
        if not stop: return None, None
        location = self.location_repository.find_by_id(stop.location_id)
        return stop, location
    
class NotificationService: # Simple service for sending notifications
    def __init__(self):
        self.notification_repository = NotificationRepository()
        self.user_repository = UserRepository() # To get user details if needed

    def send_notification(self, recipient_user_id, sender_user_id, message_content, notification_type="General"):
        # In a real app, this might involve email, SMS, or push notifications
        # For now, we just save it to our JSON "database"
        
        # Basic check if recipient exists (optional)
        # recipient = self.user_repository.find_by_id(recipient_user_id) # Assuming find_by_id exists in UserRepository
        # if not recipient:
        #     print(f"Warning: Recipient user ID {recipient_user_id} not found for notification.")
        #     return None

        new_notification = Notification(
            recipient_user_id=recipient_user_id,
            sender_user_id=sender_user_id,
            message_content=message_content,
            notification_type=notification_type
        )
        return self.notification_repository.save(new_notification)

class AdminFeedbackService:
    def __init__(self):
        self.feedback_repository = FeedbackRepository()
        self.response_repository = ResponseRepository()
        self.notification_service = NotificationService() # Use the notification service
        self.user_repository = UserRepository() # To get submitter names

    def get_all_feedbacks(self, status_filter=None):
        feedbacks = self.feedback_repository.get_all(status_filter=status_filter)
        # Enrich with submitter username for display
        enriched_feedbacks = []
        for fb in feedbacks:
            submitter = self.user_repository.find_by_username(fb.submitter_user_id) # Assuming submitter_user_id is username for now
            # If submitter_user_id is actual user_id, use self.user_repository.find_by_id(fb.submitter_user_id)
            submitter_name = submitter.username if submitter else "Unknown User"
            responses = self.response_repository.find_by_feedback_id(fb.feedback_id)
            enriched_feedbacks.append({
                "feedback": fb, 
                "submitter_name": submitter_name,
                "responses": responses # List of Response objects
            })
        return sorted(enriched_feedbacks, key=lambda x: x['feedback'].submission_datetime, reverse=True)


    def get_feedback_details(self, feedback_id):
        feedback = self.feedback_repository.find_by_id(feedback_id)
        if not feedback:
            return None, None, None
        submitter = self.user_repository.find_by_username(feedback.submitter_user_id) # Or by ID
        submitter_name = submitter.username if submitter else "Unknown User"
        responses = self.response_repository.find_by_feedback_id(feedback_id)
        return feedback, submitter_name, responses

    def submit_admin_response(self, admin_user_id, feedback_id, response_text):
        # Sequence Diagram: Admin -> Response.createResponse(), Response.sendResponse()
        feedback_to_update = self.feedback_repository.find_by_id(feedback_id)
        if not feedback_to_update:
            return False, "Feedback not found."
        
        if not response_text.strip():
            return False, "Response text cannot be empty."

        # 1. Create and Save Response Object
        new_response = Response(
            feedback_id=feedback_id,
            responder_admin_id=admin_user_id, # This should be the actual ID of the logged-in admin
            response_content=response_text
        )
        saved_response = self.response_repository.save(new_response)
        if not saved_response:
            return False, "Failed to save admin response."

        # Add response_id to feedback's list of responses
        feedback_to_update.add_response_id(saved_response.response_id)

        # Sequence Diagram: Response -> Feedback.updateStatus()
        feedback_to_update.update_status("Responded") # Or "Closed" depending on workflow
        self.feedback_repository.save(feedback_to_update) # Persist updated feedback

        # Sequence Diagram: Response -> Feedback.sendNotification() -> ArtPassenger.sendNotification()
        # We use NotificationService here
        notification_message = f"Admin has responded to your feedback (ID: {feedback_id}). Response: '{response_text[:50]}...'"
        self.notification_service.send_notification(
            recipient_user_id=feedback_to_update.submitter_user_id,
            sender_user_id=admin_user_id, # Admin is the sender
            message_content=notification_message,
            notification_type="FeedbackResponse"
        )
        return True, "Response submitted and user notified."

# Example how a user might submit feedback (not directly part of admin respond flow, but for context)
class UserFeedbackService:
    def __init__(self):
        self.feedback_repository = FeedbackRepository()

    def submit_feedback(self, user_id, content, rating=None, trip_id=None):
        if not content.strip():
            return None, "Feedback content cannot be empty."
        new_feedback = Feedback(
            submitter_user_id=user_id,
            feedback_content=content,
            rating=rating,
            related_trip_id=trip_id
        )
        saved = self.feedback_repository.save(new_feedback)
        return saved, "Feedback submitted successfully." if saved else "Failed to submit feedback."