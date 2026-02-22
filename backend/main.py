from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
import shutil
from datetime import datetime

from .config import settings, ensure_directories
from .database import get_db, init_db
from .models import AmazonPurchase, MercariSale, ProductMatch
from .ai_extractor import AmazonInvoiceExtractor
from .csv_processor import MercariCSVProcessor
from .matching import ProductMatcher
from .journal_generator import JournalGenerator

# アプリケーション初期化
app = FastAPI(title="確定申告自動化ツール")

# ディレクトリ作成
ensure_directories()

# データベース初期化
init_db()

# 静的ファイルとテンプレート
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
templates = Jinja2Templates(directory=settings.template_dir)

# モジュール初期化
extractor = AmazonInvoiceExtractor()
csv_processor = MercariCSVProcessor()
matcher = ProductMatcher()
journal_gen = JournalGenerator()


# ルート
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """アップロードページ"""
    return templates.TemplateResponse("upload.html", {"request": request})


# Amazon PDF アップロード
@app.post("/api/upload/amazon")
async def upload_amazon_pdfs(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Amazon請求書PDFをアップロードして抽出"""
    results = []
    
    for file in files:
        # ファイルを保存
        file_path = settings.upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # AI抽出
            items = extractor.extract_from_pdf(file_path)
            
            # データベースに保存
            for item in items:
                purchase = AmazonPurchase(
                    order_number=item['order_number'],
                    order_date=datetime.strptime(item['order_date'], '%Y-%m-%d'),
                    product_name=item['product_name'],
                    asin=item.get('asin'),
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price'],
                    invoice_number=item.get('invoice_number'),
                    pdf_filename=file.filename
                )
                db.add(purchase)
            
            db.commit()
            
            results.append({
                "filename": file.filename,
                "success": True,
                "items_count": len(items),
                "items": items
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}


# メルカリ CSV アップロード
@app.post("/api/upload/mercari")
async def upload_mercari_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """メルカリ売上CSVをアップロード"""
    # ファイルを保存
    file_path = settings.upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # CSV処理
        items = csv_processor.process_csv(file_path)
        
        # データベースに保存
        for item in items:
            sale = MercariSale(
                transaction_date=datetime.strptime(item['transaction_date'], '%Y-%m-%d'),
                product_name=item['product_name'],
                sale_amount=item['sale_amount'],
                commission=item['commission'],
                shipping_fee=item['shipping_fee'],
                profit=item['profit'],
                status=item['status'],
                is_cancelled=item['is_cancelled'],
                csv_filename=file.filename
            )
            db.add(sale)
        
        db.commit()
        
        return {
            "success": True,
            "filename": file.filename,
            "items_count": len(items),
            "items": items
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# データ取得API
@app.get("/api/data/amazon")
async def get_amazon_data(db: Session = Depends(get_db)):
    """Amazon仕入れデータを取得"""
    purchases = db.query(AmazonPurchase).order_by(AmazonPurchase.order_date.desc()).all()
    return {
        "items": [
            {
                "id": p.id,
                "order_number": p.order_number,
                "order_date": p.order_date.strftime('%Y-%m-%d'),
                "product_name": p.product_name,
                "asin": p.asin,
                "quantity": p.quantity,
                "unit_price": p.unit_price,
                "total_price": p.total_price,
                "invoice_number": p.invoice_number
            }
            for p in purchases
        ]
    }


@app.get("/api/data/mercari")
async def get_mercari_data(db: Session = Depends(get_db)):
    """メルカリ販売データを取得"""
    sales = db.query(MercariSale).order_by(MercariSale.transaction_date.desc()).all()
    return {
        "items": [
            {
                "id": s.id,
                "transaction_date": s.transaction_date.strftime('%Y-%m-%d'),
                "product_name": s.product_name,
                "sale_amount": s.sale_amount,
                "commission": s.commission,
                "shipping_fee": s.shipping_fee,
                "profit": s.profit,
                "status": s.status,
                "is_cancelled": s.is_cancelled
            }
            for s in sales
        ]
    }


# マッチング提案
@app.get("/api/matching/suggestions")
async def get_matching_suggestions(db: Session = Depends(get_db)):
    """マッチング候補を取得"""
    # データを取得
    amazon_items = await get_amazon_data(db)
    mercari_items = await get_mercari_data(db)
    
    # マッチング提案
    suggestions = matcher.suggest_matches(
        amazon_items['items'],
        mercari_items['items']
    )
    
    return {"suggestions": suggestions}


# マッチング保存
@app.post("/api/matching/save")
async def save_matching(
    matches: List[dict],
    db: Session = Depends(get_db)
):
    """手動マッチングを保存"""
    try:
        for match in matches:
            product_match = ProductMatch(
                amazon_purchase_id=match['amazon_id'],
                mercari_sale_id=match['mercari_id'],
                is_manual=True
            )
            db.add(product_match)
        
        db.commit()
        return {"success": True, "message": f"{len(matches)}件の紐付けを保存しました"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# 在庫取得
@app.get("/api/inventory")
async def get_inventory(db: Session = Depends(get_db)):
    """在庫を取得"""
    # マッチング済みペアを取得
    matches = db.query(ProductMatch).all()
    matched_pairs = [(m.amazon_purchase_id, m.mercari_sale_id) for m in matches]
    
    # Amazon商品を取得
    amazon_items = await get_amazon_data(db)
    
    # 在庫を計算
    inventory = matcher.get_inventory(amazon_items['items'], matched_pairs)
    inventory_value = matcher.calculate_inventory_value(inventory)
    
    return {
        "inventory": inventory,
        "total_value": inventory_value,
        "count": len(inventory)
    }


# 仕訳生成
@app.post("/api/journal/generate")
async def generate_journals(
    year_end_date: str = None,
    db: Session = Depends(get_db)
):
    """仕訳を生成してCSV出力"""
    try:
        # データを取得
        amazon_items = await get_amazon_data(db)
        mercari_items = await get_mercari_data(db)
        inventory_data = await get_inventory(db)
        
        # 仕訳生成
        journals = journal_gen.generate_all_journals(
            amazon_items['items'],
            mercari_items['items'],
            inventory_data['inventory'],
            year_end_date
        )
        
        # CSV出力
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"仕訳_{timestamp}.csv"
        output_path = settings.output_dir / output_filename
        
        journal_gen.export_to_csv(journals, output_path)
        
        return {
            "success": True,
            "filename": output_filename,
            "journals_count": len(journals),
            "download_url": f"/api/download/{output_filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ファイルダウンロード
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """生成したCSVをダウンロード"""
    file_path = settings.output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )


# データリセット
@app.post("/api/reset")
async def reset_data(db: Session = Depends(get_db)):
    """全データをリセット"""
    try:
        db.query(ProductMatch).delete()
        db.query(MercariSale).delete()
        db.query(AmazonPurchase).delete()
        db.commit()
        
        return {"success": True, "message": "データをリセットしました"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
