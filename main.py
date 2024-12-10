from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="учет домашних финансов")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CategoryCreate(BaseModel):
    name: str

class CategoryRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class TransactionCreate(BaseModel):
    amount: float
    type: str
    date: date
    description: Optional[str] = None
    category_id: int

class TransactionRead(BaseModel):
    id: int
    amount: float
    type: str
    date: date
    description: Optional[str]
    category: CategoryRead

    class Config:
        orm_mode = True

@app.post("/categories/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="категория уже существует")
    new_category = models.Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.get("/categories/", response_model=List[CategoryRead])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories



@app.post("/transactions/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="категория не найдена")
    if transaction.type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="тип транзакции должен быть income или expense")
    new_transaction = models.Transaction(
        amount=transaction.amount,
        type=transaction.type,
        date=transaction.date,
        description=transaction.description,
        category_id=transaction.category_id
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@app.get("/transactions/", response_model=List[TransactionRead])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()
    return transactions

@app.get("/transactions/{transaction_id}", response_model=TransactionRead)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="транзакция не найдена")
    return transaction
@app.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, updated_transaction: TransactionCreate, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="транзакция не найдена")
    category = db.query(models.Category).filter(models.Category.id == updated_transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="категория не найдена")
    if updated_transaction.type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="тип транзакции должен быть 'income' или 'expense'")
    transaction.amount = updated_transaction.amount
    transaction.type = updated_transaction.type
    transaction.date = updated_transaction.date
    transaction.description = updated_transaction.description
    transaction.category_id = updated_transaction.category_id
    db.commit()
    db.refresh(transaction)
    return transaction

@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="транзакция не найдена")
    db.delete(transaction)
    db.commit()
    return


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, log_level="info")