import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class JournalGenerator:
    """マネーフォワード形式の仕訳を生成"""
    
    def __init__(self):
        # 勘定科目マッピング
        self.accounts = {
            "purchase": "仕入高",
            "sales": "売上高",
            "commission": "支払手数料",
            "shipping": "荷造運賃",
            "accounts_payable": "未払金",
            "accounts_receivable": "売掛金",
            "inventory": "商品",
            "inventory_adjustment": "期末商品棚卸高"
        }
    
    def generate_purchase_journals(self, amazon_items: List[Dict]) -> List[Dict]:
        """
        Amazon仕入れの仕訳を生成
        
        仕訳例:
        借方: 仕入高 10,000 / 貸方: 未払金 10,000
        """
        journals = []
        
        for item in amazon_items:
            journal = {
                "取引日": item['order_date'],
                "借方勘定科目": self.accounts["purchase"],
                "借方補助科目": "",
                "借方部門": "",
                "借方金額": int(item['total_price']),
                "借方税区分": "課税仕入10%",
                "貸方勘定科目": self.accounts["accounts_payable"],
                "貸方補助科目": "",
                "貸方部門": "",
                "貸方金額": int(item['total_price']),
                "貸方税区分": "",
                "摘要": f"Amazon仕入 {item['product_name'][:20]}... 注文番号:{item['order_number']}"
            }
            journals.append(journal)
        
        return journals
    
    def generate_sales_journals(self, mercari_items: List[Dict]) -> List[Dict]:
        """
        メルカリ販売の仕訳を生成
        
        仕訳例:
        借方: 売掛金 10,000 / 貸方: 売上高 10,000
        借方: 支払手数料 1,000 / 貸方: 売掛金 1,000
        借方: 荷造運賃 700 / 貸方: 売掛金 700
        """
        journals = []
        
        for item in mercari_items:
            # キャンセル・返品は除外
            if item.get('is_cancelled'):
                continue
            
            # 売上計上
            journal_sale = {
                "取引日": item['transaction_date'],
                "借方勘定科目": self.accounts["accounts_receivable"],
                "借方補助科目": "",
                "借方部門": "",
                "借方金額": int(item['sale_amount']),
                "借方税区分": "",
                "貸方勘定科目": self.accounts["sales"],
                "貸方補助科目": "",
                "貸方部門": "",
                "貸方金額": int(item['sale_amount']),
                "貸方税区分": "課税売上10%",
                "摘要": f"メルカリ売上 {item['product_name'][:20]}..."
            }
            journals.append(journal_sale)
            
            # 販売手数料
            if item['commission'] > 0:
                journal_commission = {
                    "取引日": item['transaction_date'],
                    "借方勘定科目": self.accounts["commission"],
                    "借方補助科目": "",
                    "借方部門": "",
                    "借方金額": int(item['commission']),
                    "借方税区分": "対象外",
                    "貸方勘定科目": self.accounts["accounts_receivable"],
                    "貸方補助科目": "",
                    "貸方部門": "",
                    "貸方金額": int(item['commission']),
                    "貸方税区分": "",
                    "摘要": f"メルカリ手数料 {item['product_name'][:20]}..."
                }
                journals.append(journal_commission)
            
            # 配送料
            if item['shipping_fee'] > 0:
                journal_shipping = {
                    "取引日": item['transaction_date'],
                    "借方勘定科目": self.accounts["shipping"],
                    "借方補助科目": "",
                    "借方部門": "",
                    "借方金額": int(item['shipping_fee']),
                    "借方税区分": "課税仕入10%",
                    "貸方勘定科目": self.accounts["accounts_receivable"],
                    "貸方補助科目": "",
                    "貸方部門": "",
                    "貸方金額": int(item['shipping_fee']),
                    "貸方税区分": "",
                    "摘要": f"配送料 {item['product_name'][:20]}..."
                }
                journals.append(journal_shipping)
        
        return journals
    
    def generate_inventory_journals(self, inventory_items: List[Dict], year_end_date: str) -> List[Dict]:
        """
        期末在庫の仕訳を生成
        
        仕訳例:
        借方: 商品 50,000 / 貸方: 期末商品棚卸高 50,000
        """
        journals = []
        
        total_inventory_value = sum([item['total_price'] for item in inventory_items])
        
        if total_inventory_value > 0:
            journal = {
                "取引日": year_end_date,
                "借方勘定科目": self.accounts["inventory"],
                "借方補助科目": "",
                "借方部門": "",
                "借方金額": int(total_inventory_value),
                "借方税区分": "",
                "貸方勘定科目": self.accounts["inventory_adjustment"],
                "貸方補助科目": "",
                "貸方部門": "",
                "貸方金額": int(total_inventory_value),
                "貸方税区分": "",
                "摘要": f"期末商品棚卸高 {len(inventory_items)}点"
            }
            journals.append(journal)
        
        return journals
    
    def export_to_csv(
        self, 
        journals: List[Dict], 
        output_path: Path
    ) -> Path:
        """
        仕訳をマネーフォワード形式のCSVで出力
        """
        df = pd.DataFrame(journals)
        
        # マネーフォワードの必須カラム順
        columns = [
            "取引日",
            "借方勘定科目",
            "借方補助科目",
            "借方部門",
            "借方金額",
            "借方税区分",
            "貸方勘定科目",
            "貸方補助科目",
            "貸方部門",
            "貸方金額",
            "貸方税区分",
            "摘要"
        ]
        
        df = df[columns]
        
        # CSV出力（Shift-JIS、BOM付き）
        df.to_csv(output_path, index=False, encoding='shift_jis', errors='replace')
        
        return output_path
    
    def generate_all_journals(
        self,
        amazon_items: List[Dict],
        mercari_items: List[Dict],
        inventory_items: List[Dict],
        year_end_date: str = None
    ) -> List[Dict]:
        """
        すべての仕訳を一括生成
        """
        all_journals = []
        
        # 仕入れ
        all_journals.extend(self.generate_purchase_journals(amazon_items))
        
        # 販売
        all_journals.extend(self.generate_sales_journals(mercari_items))
        
        # 在庫（期末日が指定されている場合のみ）
        if year_end_date and inventory_items:
            all_journals.extend(self.generate_inventory_journals(inventory_items, year_end_date))
        
        # 日付順にソート
        all_journals.sort(key=lambda x: x['取引日'])
        
        return all_journals
