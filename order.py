from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, ForeignKey

from pydantic import BaseModel
from typing import List

from database import Base, engine, get_db
from product import Product   # important for stock validation

# =========================
# ROUTER
# =========================
router = APIRouter(prefix="/orders", tags=["Orders"])

# =========================
# ORDER TABLE
# =========================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="Pending")
    total_amount = Column(Float, default=0)

# =========================
# ORDER ITEM TABLE
# =========================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer)
    product_id = Column(Integer)
    quantity = Column(Integer)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

# =========================
# REQUEST SCHEMAS
# =========================
class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest]

class UpdateStatusRequest(BaseModel):
    status: str

# =========================
# CREATE ORDER
# =========================
@router.post("/create")
def create_order(data: CreateOrderRequest, db: Session = Depends(get_db)):

    order = Order(status="Pending", total_amount=0)
    db.add(order)
    db.commit()
    db.refresh(order)

    total = 0

    for item in data.items:

        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # RULE: stock check
        if item.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        if product.price <= 0:
            raise HTTPException(status_code=400, detail="Invalid product price")

        item_price = product.price * item.quantity
        total += item_price

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=item_price
        )

        db.add(order_item)

    order.total_amount = total

    db.commit()

    return {
        "message": "Order created successfully",
        "order_id": order.id,
        "total_amount": total
    }

# =========================
# LIST ORDERS
# =========================
@router.get("/list")
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()

# =========================
# GET ORDER DETAILS
# =========================
@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    return {
        "order": order,
        "items": items
    }

# =========================
# UPDATE ORDER STATUS
# =========================
@router.put("/update-status/{order_id}")
def update_status(order_id: int, data: UpdateStatusRequest, db: Session = Depends(get_db)):

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed_status = ["Pending", "Confirmed", "Delivered", "Cancelled"]

    if data.status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid status")

    # =========================
    # BUSINESS RULE: STOCK REDUCTION
    # =========================
    if data.status == "Confirmed":

        items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()

            if product.stock_quantity < item.quantity:
                raise HTTPException(status_code=400, detail="Stock mismatch")

            product.stock_quantity -= item.quantity

    order.status = data.status

    db.commit()

    return {
        "message": "Order status updated",
        "order_id": order.id,
        "status": order.status
    }
