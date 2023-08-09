import re

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request
import db_connection
from Helper_func import extract_session_id,get_str_from_food_dict


in_progress = {}
app = FastAPI()

@app.post('/')
async def handle_post_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = extract_session_id(output_contexts[0]["name"])
    intent_handler_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }
    return intent_handler_dict[intent](parameters, session_id)

def add_to_order(parameters : dict, session_id):
    food_items = parameters['food_item']
    quantity = parameters["item_no"]
    if len(food_items) != len(quantity):
        fulfillment_text = f"Sorry please specify quantity of those items"
    else:
        new_food_dict = dict(zip(food_items, quantity))
        if session_id in in_progress:
            current_food_dict = in_progress[session_id]
            current_food_dict.update(new_food_dict)
            in_progress[session_id] = current_food_dict
        else:
            in_progress[session_id] = new_food_dict
        order_str = get_str_from_food_dict(in_progress[session_id])
        fulfillment_text = f"So far the items you ordered {order_str}. Do you need anything else?"

    return (JSONResponse(content={
            "fulfillmentText": f"{fulfillment_text}"
        }))

def remove_from_order(parameters : dict, session_id):
    if session_id not in in_progress:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    current_order = in_progress[session_id]
    food_item = parameters["food_item"]
    food_items = []
    if type(food_item) == str:
        food_items.append(food_item)
    elif type(food_item) == list:
        for fi in food_item:
            food_items.append(fi)

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have the {",".join(no_such_items),type(food_items),item,current_order}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
         })

def complete_order(parameters : dict,session_id):
    if session_id not in in_progress:
        fulfillment_text = f"I'm having a trouble in finding your order would you please reorder "
    else:
        order = in_progress[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = f"I'm having a trouble because in process your order due to backend server please reorder{order_id, session_id} "
        else:
            order_total = db_connection.get_total_order_price(order_id)
            fulfillment_text = f"Awesome we placed your order here is your id #{order_id}  "\
            f"your order total is {order_total} you can pay at the time of your delivery"
        del in_progress[session_id]
    return (JSONResponse(content={
        "fulfillmentText": f"{fulfillment_text}"
    }))

def save_to_db(order: dict):
    next_order_id = db_connection.get_next_order_id()
    for food_item, quantity in order.items():
        rcode = db_connection.insert_order_item(
            food_item,quantity,next_order_id
        )
        if rcode == -1:
            return -1
    db_connection.insert_order_tracking(next_order_id, "In progress")
    return next_order_id

def track_order(parameters : dict, session_id):
    order_id = int(parameters['order_id'])
    status = db_connection.get_order_status(order_id)
    if status:
        fulfillment_text = f"The order status for order id : {order_id} is : {status} "
    else:
        fulfillment_text = f"The order with the order id :{order_id} you are looking for not found: "
    return (JSONResponse(content={
        "fulfillmentText": f"{fulfillment_text}"
    }))


@app.get('/')
async def handle_get_request():
    return {"message": "GET request received at the root endpoint."}















# from fastapi import FastAPI
# from fastapi.responses import JSONResponse
# from fastapi import Request
# app = FastAPI()
#
#
# @app.post('/')
# async def handle_request(request: Request):
#     payload = await request.json()
#     intent = payload['queryResult']['intent']['displayName']
#     parameters = payload['queryResult']['parameters']
#     output_contexts = payload['queryResult']['outputContexts']
#
#     if intent == "track.order - context: ongoing-tracking":
#         return(JSONResponse(content={
#             "fulfillmentText": f"Received =={intent}== in the backend"
#         }))






