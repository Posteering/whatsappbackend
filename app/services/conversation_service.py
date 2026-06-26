import logging
import re
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.commerce import Vendor
from app.models.rider import DispatchRider
from app.ai.chat import AIAssistant
from app.ai.prompts import get_secretary_system_prompt
from app.services.onboarding_service import OnboardingService
from app.services.payment_service import PaymentService
from app.services.escalation_service import EscalationService
from app.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIAssistant()
        self.whatsapp_client = WhatsAppClient()
        self.onboarding = OnboardingService(db)
        self.payment = PaymentService(db)
        self.escalation = EscalationService(db)

    async def process_incoming_message(self, phone_number: str, message_text: str):
        # 1. Onboarding
        user, is_new = await self.onboarding.handle_user_greeting(phone_number)
        if is_new:
            return # Wait for their response with name

        # 2. Get active conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.status == "active"
        ).first()

        if not conversation:
            conversation = Conversation(user_id=user.id)
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        # 3. Save User Message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            type="text",
            content=message_text
        )
        self.db.add(user_msg)
        self.db.commit()

        # 4. Get Conversation History
        history = self.db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at).all()
        context = [{"role": msg.role, "content": msg.content} for msg in history[-10:] if msg.content]

        # 4.5. Inject Vendor Context if applicable
        vendor_info = self.db.query(Vendor).filter(Vendor.contact_phone == phone_number).first()
        if vendor_info:
            ai_input_text = f"[SYSTEM: You are talking to Vendor: {vendor_info.name} (id: {vendor_info.id})]\nUser: {message_text}"
        else:
            ai_input_text = message_text

        # 4.6. Intercept System Buttons
        from app.models.commerce import Order, MenuItem
        btn_match = re.search(r'\[INTERACTIVE_BTN:\s*(.+?)\]', message_text)
        if btn_match:
            btn_id = btn_match.group(1).strip()
            
            if btn_id.startswith("SELECT_VENDOR_"):
                v_id = btn_id.replace("SELECT_VENDOR_", "")
                vendor = self.db.query(Vendor).filter(Vendor.id == v_id).first()
                if vendor:
                    menu_items = self.db.query(MenuItem).filter(MenuItem.vendor_id == v_id).limit(10).all()
                    ai_input_text = f"[SYSTEM: User selected vendor {vendor.name} (ID: {vendor.id}). Here is their menu: "
                    if menu_items:
                        ai_input_text += ", ".join([f"{m.name} (₦{m.price})" for m in menu_items])
                    else:
                        ai_input_text += "No menu items found."
                    ai_input_text += ". Acknowledge the selection and present the menu nicely to the user.]"

            elif btn_id.startswith("ACCEPT_ORDER_"):
                o_id = btn_id.replace("ACCEPT_ORDER_", "")
                order = self.db.query(Order).filter(Order.id == o_id).first()
                if order and order.vendor_status == "pending":
                    order.vendor_status = "accepted"
                    self.db.commit()
                    # Send Payment Link to Customer
                    customer = self.db.query(User).filter(User.id == order.user_id).first()
                    invoice = await self.payment.create_invoice(order.id, order.total_amount)
                    vacct = await self.payment.create_virtual_account(invoice.id)
                    payment_msg = f"✅ *Your order has been accepted by the vendor!*\n\n*Invoice: #{invoice.invoice_number}*\nTotal: ₦{order.total_amount}\n\nPlease transfer exactly ₦{order.total_amount} to:\nBank: {vacct.bank_name}\nAccount: {vacct.account_number}\nName: {vacct.account_name}\n\nThis account expires in 30 minutes."
                    await self.whatsapp_client.send_text_message(to=customer.phone_number, text=payment_msg)
                    return await self.whatsapp_client.send_text_message(to=phone_number, text="✅ You have accepted the order. We have sent the invoice to the customer.")
                else:
                    return await self.whatsapp_client.send_text_message(to=phone_number, text="⚠️ This order has already been processed or does not exist.")

            elif btn_id.startswith("DECLINE_ORDER_"):
                o_id = btn_id.replace("DECLINE_ORDER_", "")
                order = self.db.query(Order).filter(Order.id == o_id).first()
                if order and order.vendor_status == "pending":
                    order.vendor_status = "declined"
                    order.status = "cancelled"
                    self.db.commit()
                    customer = self.db.query(User).filter(User.id == order.user_id).first()
                    decline_msg = "❌ *Order Declined*\nThe vendor is currently unable to accept your order. Please try searching for another vendor."
                    await self.whatsapp_client.send_text_message(to=customer.phone_number, text=decline_msg)
                    return await self.whatsapp_client.send_text_message(to=phone_number, text="❌ You have declined the order.")

            elif btn_id.startswith("COMPLETE_ORDER_"):
                o_id = btn_id.replace("COMPLETE_ORDER_", "")
                order = self.db.query(Order).filter(Order.id == o_id).first()
                if order and order.status == "paid":
                    order.status = "completed"
                    self.db.commit()
                    customer = self.db.query(User).filter(User.id == order.user_id).first()
                    sections = [
                        {
                            "title": "Rate the Vendor",
                            "rows": [
                                {"id": f"RATE_VENDOR_{order.vendor_id}_5", "title": "⭐️⭐️⭐️⭐️⭐️ Excellent"},
                                {"id": f"RATE_VENDOR_{order.vendor_id}_4", "title": "⭐️⭐️⭐️⭐️ Good"},
                                {"id": f"RATE_VENDOR_{order.vendor_id}_3", "title": "⭐️⭐️⭐️ Average"},
                                {"id": f"RATE_VENDOR_{order.vendor_id}_2", "title": "⭐️⭐️ Poor"},
                                {"id": f"RATE_VENDOR_{order.vendor_id}_1", "title": "⭐️ Terrible"}
                            ]
                        }
                    ]
                    await self.whatsapp_client.send_interactive_list(
                        to=customer.phone_number,
                        text=f"✅ Your order from this vendor is complete! Please rate your experience:",
                        button_text="Rate Vendor",
                        sections=sections
                    )
                    return await self.whatsapp_client.send_text_message(to=phone_number, text="✅ Order marked as completed!")

            elif btn_id.startswith("RATE_VENDOR_"):
                # Format: RATE_VENDOR_{vendor_id}_{rating}
                parts = btn_id.split("_")
                rating = int(parts[-1])
                vendor_id = "_".join(parts[2:-1])
                vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
                if vendor:
                    if vendor.rating == 0.0 or vendor.rating is None:
                        vendor.rating = float(rating)
                    else:
                        vendor.rating = round((vendor.rating + rating) / 2.0, 1)
                    self.db.commit()
                    return await self.whatsapp_client.send_text_message(to=phone_number, text=f"Thank you! You rated the vendor {rating} stars. ⭐️")
                else:
                    return await self.whatsapp_client.send_text_message(to=phone_number, text="⚠️ This order has already been processed or does not exist.")

        # 5. Generate AI Response
        system_prompt = get_secretary_system_prompt()
        ai_response_text = await self.ai.generate_response(system_prompt, ai_input_text, context)

        # 6. Parse actions (Payments / Escalation / Dispatch / Vendor / Registration / Marketplace)
        payment_match = re.search(r'<TRIGGER_PAYMENT:\s*([\d\.]+)>', ai_response_text)
        escalate_match = re.search(r'<ESCALATE_HUMAN>', ai_response_text)
        dispatch_match = re.search(r'<FIND_DISPATCH:\s*(.+?)>', ai_response_text)
        vendor_match = re.search(r'<SEARCH_VENDOR:\s*(.+?),\s*(.+?)>', ai_response_text)
        register_vendor_match = re.search(r'<REGISTER_VENDOR:\s*(.+?),\s*(.+?),\s*(.+?),\s*(.+?)>', ai_response_text)
        register_rider_match = re.search(r'<REGISTER_RIDER:\s*(.+?),\s*(.+?),\s*(.+?)>', ai_response_text)
        add_menu_match = re.search(r'<ADD_MENU_ITEM:\s*(.+?),\s*(.+?),\s*(.+?),\s*(.+?),\s*(.+?)>', ai_response_text)
        create_order_match = re.search(r'<CREATE_ORDER:\s*(.+?),\s*(delivery|pickup),\s*(.+?)>', ai_response_text, re.IGNORECASE)

        # Handle Dispatch Search
        dispatch_results_text = ""
        if dispatch_match:
            location = dispatch_match.group(1).strip()
            riders = self.db.query(DispatchRider).filter(DispatchRider.current_location.ilike(f"%{location}%"), DispatchRider.is_available == True).limit(3).all()
            if riders:
                dispatch_results_text = "\n\n*Available Dispatch Riders near you:*\n"
                for i, r in enumerate(riders, 1):
                    dispatch_results_text += f"{i}. {r.name} ({r.vehicle_type}) - 📞 {r.phone_number} (⭐️ {r.rating})\n"
            else:
                dispatch_results_text = "\n\n*Sorry, we couldn't find any available dispatch riders near that location right now.*"

        # Handle Vendor Search
        vendor_results_text = ""
        show_vendor_list_match = False
        vendor_sections = []
        if vendor_match:
            category = vendor_match.group(1).strip()
            location = vendor_match.group(2).strip()
            vendors = self.db.query(Vendor).filter(Vendor.location.ilike(f"%{location}%")).limit(10).all()
            if vendors:
                rows = []
                for v in vendors:
                    rows.append({
                        "id": f"SELECT_VENDOR_{v.id}",
                        "title": v.name[:24], # WhatsApp title limit
                        "description": f"⭐ {v.rating} | {v.description}"[:72]
                    })
                vendor_sections = [{"title": f"Vendors in {location}"[:24], "rows": rows}]
                show_vendor_list_match = True
                vendor_results_text = "\n\n_I have sent a list of vendors. Please click the button below to select one._"
            else:
                vendor_results_text = f"\n\n*Sorry, we couldn't find any {category} vendors near {location}.*"

        # Handle Registration
        registration_results_text = ""
        if register_vendor_match:
            try:
                v_name = register_vendor_match.group(1).strip()
                v_category = register_vendor_match.group(2).strip()
                v_location = register_vendor_match.group(3).strip()
                v_desc = register_vendor_match.group(4).strip()
                new_vendor = Vendor(name=v_name, location=v_location, description=v_desc, contact_phone=phone_number, rating=5.0)
                self.db.add(new_vendor)
                self.db.commit()
                self.db.refresh(new_vendor)
                registration_results_text = f"\n\n✅ Excellent! Your vendor profile *{v_name}* has been successfully registered.\n\n*Your Vendor ID for the Dashboard is:*\n`{new_vendor.id}`\n\nPlease save this ID to log into your Dashboard."
            except Exception as e:
                registration_results_text = "\n\n❌ Sorry, there was an error registering your vendor profile."
                
        if register_rider_match:
            try:
                r_name = register_rider_match.group(1).strip()
                r_vehicle = register_rider_match.group(2).strip()
                r_location = register_rider_match.group(3).strip()
                new_rider = DispatchRider(name=r_name, vehicle_type=r_vehicle, current_location=r_location, phone_number=phone_number, is_available=True, rating=5.0)
                self.db.add(new_rider)
                self.db.commit()
                registration_results_text = f"\n\n✅ Excellent! You have been successfully registered as a *{r_vehicle}* Dispatch Rider."
            except Exception as e:
                registration_results_text = "\n\n❌ Sorry, there was an error registering you as a rider."

        marketplace_results_text = ""
        if add_menu_match:
            try:
                m_vendor_id = add_menu_match.group(1).strip()
                m_name = add_menu_match.group(2).strip()
                m_price = float(add_menu_match.group(3).strip())
                m_desc = add_menu_match.group(4).strip()
                m_media_id = add_menu_match.group(5).strip()
                
                from app.models.commerce import MenuItem
                img_url = f"https://api.whatsapp.com/v1/media/{m_media_id}" if m_media_id and m_media_id.lower() != "none" else None
                new_item = MenuItem(vendor_id=m_vendor_id, name=m_name, price=m_price, description=m_desc, image_url=img_url)
                self.db.add(new_item)
                self.db.commit()
                marketplace_results_text = f"\n\n✅ Added *{m_name}* to your catalog!"
            except Exception as e:
                logger.error(f"Error adding menu item: {e}")
                marketplace_results_text = "\n\n❌ Failed to add menu item."

        if create_order_match:
            try:
                from app.models.commerce import Order, OrderItem, MenuItem
                o_vendor_id = create_order_match.group(1).strip()
                delivery_type = create_order_match.group(2).strip().lower()
                items_str = create_order_match.group(3).strip()
                
                item_pairs = [pair.strip().split('=') for pair in items_str.split(',')]
                
                total_amount = 0.0
                if delivery_type == "delivery":
                    total_amount += 1000.0  # Mock delivery fee
                
                new_order = Order(user_id=user.id, vendor_id=o_vendor_id, total_amount=0.0, vendor_status="pending")
                self.db.add(new_order)
                self.db.commit()
                
                for name, qty_str in item_pairs:
                    qty = int(qty_str)
                    menu_item = self.db.query(MenuItem).filter(MenuItem.vendor_id == o_vendor_id, MenuItem.name.ilike(f"%{name.strip()}%")).first()
                    if menu_item:
                        total_amount += menu_item.price * qty
                        order_item = OrderItem(order_id=new_order.id, menu_item_id=menu_item.id, quantity=qty, price_at_purchase=menu_item.price)
                        self.db.add(order_item)
                
                new_order.total_amount = total_amount
                self.db.commit()
                
                self.latest_order_id = new_order.id
                
                vendor = self.db.query(Vendor).filter(Vendor.id == o_vendor_id).first()
                if vendor and vendor.contact_phone:
                    buttons = [
                        {"id": f"ACCEPT_ORDER_{new_order.id}", "title": "✅ Accept Order"},
                        {"id": f"DECLINE_ORDER_{new_order.id}", "title": "❌ Decline Order"}
                    ]
                    delivery_info = "🚚 Delivery (₦1000)" if delivery_type == "delivery" else "🛍️ Pickup"
                    await self.whatsapp_client.send_interactive_buttons(
                        to=vendor.contact_phone,
                        text=f"🔔 *New Order Requested!*\n\n*Customer:* {user.name}\n*Type:* {delivery_info}\n*Total:* ₦{total_amount}\n*Items:* {items_str}\n\nPlease accept or decline this order:",
                        buttons=buttons
                    )
                
                marketplace_results_text = f"\n\n✅ Your {delivery_type} order for ₦{total_amount} has been sent to the vendor. I will notify you with the invoice as soon as they accept it!"
                
                # Removed payment trigger auto-injection
                payment_match = None
                ai_response_text = re.sub(r'<TRIGGER_PAYMENT:\s*([\d\.]+)>', '', ai_response_text)
                    
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                marketplace_results_text = "\n\n❌ Failed to create order."

        # Clean tokens from response
        clean_text = re.sub(r'<TRIGGER_PAYMENT:\s*[\d\.]+>', '', ai_response_text).strip()
        clean_text = re.sub(r'<ESCALATE_HUMAN>', '', clean_text).strip()
        clean_text = re.sub(r'<FIND_DISPATCH:\s*.+?>', '', clean_text).strip()
        clean_text = re.sub(r'<SEARCH_VENDOR:\s*.+?>', '', clean_text).strip()
        clean_text = re.sub(r'<REGISTER_VENDOR:\s*.+?>', '', clean_text).strip()
        clean_text = re.sub(r'<REGISTER_RIDER:\s*.+?>', '', clean_text).strip()
        clean_text = re.sub(r'<ADD_MENU_ITEM:\s*.+?>', '', clean_text).strip()
        clean_text = re.sub(r'<CREATE_ORDER:\s*.+?>', '', clean_text).strip()
        
        show_menu_match = re.search(r'<SHOW_MAIN_MENU>', clean_text)
        clean_text = re.sub(r'<SHOW_MAIN_MENU>', '', clean_text).strip()
        
        # Append results to the final message
        final_message = clean_text + dispatch_results_text + vendor_results_text + registration_results_text + marketplace_results_text

        # 7. Save Assistant Message
        ai_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            type="text",
            content=final_message
        )
        self.db.add(ai_msg)
        self.db.commit()

        # 8. Send WhatsApp Message
        if final_message:
            # Truncate text message if > 4096 just in case
            safe_text = final_message[:4090]
            await self.whatsapp_client.send_text_message(to=phone_number, text=safe_text)

        if show_vendor_list_match and vendor_sections:
            await self.whatsapp_client.send_interactive_list(
                to=phone_number, 
                text="Please select a vendor from the options below:", 
                button_text="View Vendors", 
                sections=vendor_sections
            )

        if show_menu_match:
            sections = [
                {
                    "title": "Customer Services",
                    "rows": [
                        {"id": "FIND_DISPATCH", "title": "Find Dispatch Rider"},
                        {"id": "FIND_VENDOR", "title": "Find Vendor"}
                    ]
                },
                {
                    "title": "Vendor / Rider Hub",
                    "rows": [
                        {"id": "REGISTER_VENDOR", "title": "Register Vendor"},
                        {"id": "REGISTER_RIDER", "title": "Register Dispatch Rider"}
                    ]
                },
                {
                    "title": "Support",
                    "rows": [
                        {"id": "SPEAK_HUMAN", "title": "Speak to Human"}
                    ]
                }
            ]
            await self.whatsapp_client.send_interactive_list(to=phone_number, text="How can I help you today? Please choose an option below:", button_text="Main Menu", sections=sections)

        # 9. Execute Actions
        if escalate_match:
            await self.escalation.escalate_to_human(conversation.id, phone_number)
        elif payment_match:
            amount = float(payment_match.group(1))
            order_id = getattr(self, "latest_order_id", None)
            await self.payment.generate_payment_link(user.id, phone_number, amount, conversation.id, order_id=order_id)
