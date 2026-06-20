from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float

from pydantic import BaseModel

from database import Base, engine, get_db

# =========================
# ROUTER
# =========================
router = APIRouter(prefix="/products", tags=["Products"])

# =========================
# PRODUCT MODEL
# =========================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    category_id = Column(Integer)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    stock_quantity = Column(Integer)
    status = Column(String)  # Active / Inactive
    

Base.metadata.create_all(bind=engine)

# =========================
# REQUEST SCHEMA
# =========================
class ProductRequest(BaseModel):
    category_id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    status: str

# =========================
# CREATE PRODUCT
# =========================
@router.post("/create")
def create_product(data: ProductRequest, db: Session = Depends(get_db)):

    product = Product(
        category_id=data.category_id,
        name=data.name,
        description=data.description,
        price=data.price,
        stock_quantity=data.stock_quantity,
        status=data.status
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return {"message": "Product created successfully"}

# =========================
# LIST PRODUCTS
# =========================
@router.get("/list")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# =========================
# GET PRODUCT DETAILS
# =========================
@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

# =========================
# UPDATE PRODUCT
# =========================
@router.put("/update/{product_id}")
def update_product(product_id: int, data: ProductRequest, db: Session = Depends(get_db)):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.category_id = data.category_id
    product.name = data.name
    product.description = data.description
    product.price = data.price
    product.stock_quantity = data.stock_quantity
    product.status = data.status

    db.commit()
    db.refresh(product)

    return {"message": "Product updated successfully"}

# =========================
# DELETE PRODUCT
# =========================
@router.delete("/delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}
