from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from main import Base, engine, get_db
from sqlalchemy import Column, Integer, String




router = APIRouter(prefix="/categories", tags=["Categories"])


class Category(Base):
    __tablename__ = "categories"


    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)




    Base.metadata.create_all(bind=engine)


class CategoryRequest(BaseModel):
    name: str


@router.post("/create")
def create_category(data: CategoryRequest, db: Session = Depends(get_db)):


    existing = db.query(Category).filter(Category.name == data.name).first()


    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")


    category = Category(name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)


    return {"message": "Category created successfully"}


@router.get("/list")
def list_categories(db: Session = Depends(get_db)):


    return db.query(Category).all()


@router.put("/update/{category_id}")
def update_category(category_id: int, data: CategoryRequest, db: Session = Depends(get_db)):


    category = db.query(Category).filter(Category.id == category_id).first()


    if not category:
        raise HTTPException(status_code=404, detail="Category not found")


    category.name = data.name


    db.commit()
    db.refresh(category)


    return {"message": "Category updated successfully"}


@router.delete("/delete/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):


    category = db.query(Category).filter(Category.id == category_id).first()


    if not category:
        raise HTTPException(status_code=404, detail="Category not found")


    db.delete(category)
    db.commit()


    return {"message": "Category deleted successfully"}
