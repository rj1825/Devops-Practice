import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

# Database connection URL (defaults to local SQLite database)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanban_sales.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    joined_date = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product", back_populates="orders")


def init_db():
    Base.metadata.create_all(bind=engine)
    populate_sample_data()


def populate_sample_data():
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Customer).first() is not None:
        db.close()
        return

    # 1. Add Customers
    c1 = Customer(name="John Doe", email="john.doe@example.com", joined_date=datetime.utcnow() - timedelta(days=90))
    c2 = Customer(name="Jane Smith", email="jane.smith@example.com", joined_date=datetime.utcnow() - timedelta(days=60))
    c3 = Customer(name="Alice Johnson", email="alice.j@example.com", joined_date=datetime.utcnow() - timedelta(days=30))
    c4 = Customer(name="Bob Kovacs", email="bob.kovacs@example.com", joined_date=datetime.utcnow() - timedelta(days=10))
    db.add_all([c1, c2, c3, c4])
    db.commit()

    # 2. Add Products
    p1 = Product(name="Premium Wireless Laptop", category="Electronics", price=1249.99, stock=50)
    p2 = Product(name="Ergonomic Office Chair", category="Furniture", price=299.99, stock=30)
    p3 = Product(name="Noise-Cancelling Headphones", category="Electronics", price=199.99, stock=100)
    p4 = Product(name="Performance Running Shoes", category="Apparel", price=120.00, stock=80)
    p5 = Product(name="Organic Cotton T-Shirt", category="Apparel", price=24.99, stock=200)
    db.add_all([p1, p2, p3, p4, p5])
    db.commit()

    # 3. Add Orders (simulating dates over last 3 weeks)
    o1 = Order(customer_id=c1.id, product_id=p1.id, quantity=1, total_amount=1249.99, order_date=datetime.utcnow() - timedelta(days=20))
    o2 = Order(customer_id=c1.id, product_id=p5.id, quantity=2, total_amount=49.98, order_date=datetime.utcnow() - timedelta(days=15))
    
    o3 = Order(customer_id=c2.id, product_id=p2.id, quantity=1, total_amount=299.99, order_date=datetime.utcnow() - timedelta(days=18))
    o4 = Order(customer_id=c2.id, product_id=p3.id, quantity=1, total_amount=199.99, order_date=datetime.utcnow() - timedelta(days=8))
    
    o5 = Order(customer_id=c3.id, product_id=p4.id, quantity=1, total_amount=120.00, order_date=datetime.utcnow() - timedelta(days=5))
    o6 = Order(customer_id=c3.id, product_id=p5.id, quantity=4, total_amount=99.96, order_date=datetime.utcnow() - timedelta(days=2))
    
    o7 = Order(customer_id=c4.id, product_id=p3.id, quantity=2, total_amount=399.98, order_date=datetime.utcnow() - timedelta(days=1))
    db.add_all([o1, o2, o3, o4, o5, o6, o7])
    
    db.commit()
    db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
