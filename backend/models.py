from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class AmazonPurchase(Base):
    """Amazon仕入れデータ"""
    __tablename__ = "amazon_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True)
    order_date = Column(DateTime)
    product_name = Column(String)
    asin = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    invoice_number = Column(String)  # 適格請求書番号
    pdf_filename = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    matches = relationship("ProductMatch", back_populates="amazon_purchase")

class MercariSale(Base):
    """メルカリ販売データ"""
    __tablename__ = "mercari_sales"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(DateTime)
    product_name = Column(String)
    sale_amount = Column(Float)
    commission = Column(Float)
    shipping_fee = Column(Float)
    profit = Column(Float)
    status = Column(String)  # 完了、返品、キャンセルなど
    is_cancelled = Column(Boolean, default=False)
    csv_filename = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    matches = relationship("ProductMatch", back_populates="mercari_sale")

class ProductMatch(Base):
    """仕入れと販売の紐付け"""
    __tablename__ = "product_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    amazon_purchase_id = Column(Integer, ForeignKey("amazon_purchases.id"))
    mercari_sale_id = Column(Integer, ForeignKey("mercari_sales.id"))
    matched_at = Column(DateTime, default=datetime.now)
    is_manual = Column(Boolean, default=True)  # 手動紐付けかAI提案か
    confidence_score = Column(Float, nullable=True)  # AI提案の場合の信頼度
    
    # リレーション
    amazon_purchase = relationship("AmazonPurchase", back_populates="matches")
    mercari_sale = relationship("MercariSale", back_populates="matches")

class OtherExpense(Base):
    """その他の経費"""
    __tablename__ = "other_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_date = Column(DateTime)
    category = Column(String)  # 梱包材、配送用品など
    description = Column(Text)
    amount = Column(Float)
    vendor = Column(String)  # 購入先
    created_at = Column(DateTime, default=datetime.now)

class Journal(Base):
    """生成された仕訳"""
    __tablename__ = "journals"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(DateTime)
    debit_account = Column(String)  # 借方科目
    debit_amount = Column(Float)
    credit_account = Column(String)  # 貸方科目
    credit_amount = Column(Float)
    description = Column(Text)
    reference_type = Column(String)  # amazon_purchase, mercari_sale, inventory など
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
