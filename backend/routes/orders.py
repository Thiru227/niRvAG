"""
Orders Route — Static order lookup
"""
from flask import Blueprint, request, jsonify
import json
import os

orders_bp = Blueprint('orders', __name__)

ORDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'orders.json')


def load_orders():
    try:
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f).get('orders', [])
    except Exception:
        return []


@orders_bp.route('/orders/lookup', methods=['GET'])
def lookup_order():
    """Lookup order by order_id or customer_email"""
    order_id = request.args.get('order_id', '').strip()
    email = request.args.get('email', '').strip()

    orders = load_orders()
    results = []

    for o in orders:
        if order_id and o['order_id'].lower() == order_id.lower():
            results.append(o)
        elif email and o['customer_email'].lower() == email.lower():
            results.append(o)

    if not results:
        return jsonify({"error": "No orders found", "orders": []}), 404

    return jsonify({"orders": results})


@orders_bp.route('/orders', methods=['GET'])
def list_orders():
    """List all orders (admin view)"""
    orders = load_orders()
    return jsonify({"orders": orders, "total": len(orders)})
