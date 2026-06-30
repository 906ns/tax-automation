import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class MercariCSVProcessor:
    def __init__(self):
        pass
    
    def process_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        メルカリのCSVを処理
        
        想定されるCSVカラム:
        - 取引日時, 商品名, 価格, 販売手数料, 配送料, 受取金額, ステータス など
        
        Returns:
            List[Dict]: 処理された販売データ
        """
        try:
            # CSVを読み込み（エンコーディングを自動検出）
            try:
                df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='shift-jis', on_bad_lines='skip')
            
            # カラム名を正規化（スペースや全角を削除）
            df.columns = df.columns.str.strip().str.replace(' ', '')
            
            results = []
            
            for _, row in df.iterrows():
                # カラム名のバリエーションに対応
                transaction_date = self._extract_date(row)
                product_name = self._extract_product_name(row)
                sale_amount = self._extract_sale_amount(row)
                commission = self._extract_commission(row)
                shipping_fee = self._extract_shipping_fee(row)
                profit = self._extract_profit(row)
                status = self._extract_status(row)
                
                # キャンセル・返品の判定
                is_cancelled = status and ('キャンセル' in status or '返品' in status or 'cancel' in status.lower())
                
                item = {
                    "transaction_date": transaction_date,
                    "product_name": product_name,
                    "sale_amount": sale_amount,
                    "commission": commission,
                    "shipping_fee": shipping_fee,
                    "profit": profit,
                    "status": status,
                    "is_cancelled": is_cancelled
                }
                
                results.append(item)
            
            return results
            
        except Exception as e:
            raise Exception(f"CSV処理に失敗しました: {str(e)}")
    
    def _extract_date(self, row) -> str:
        """取引日時を抽出"""
        possible_columns = ['購入日時', '取引日時', '取引日', '日付', 'date', '購入日']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                # 日付をパース
                try:
                    date_obj = pd.to_datetime(row[col])
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    return str(row[col])
        return None
    
    def _extract_product_name(self, row) -> str:
        """商品名を抽出"""
        possible_columns = ['商品名', '商品', 'product', 'item']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col])
        return "不明"
    
    def _extract_sale_amount(self, row) -> float:
        """売上金額を抽出"""
        possible_columns = ['商品代金', '価格', '売上', '販売価格', 'price', '金額']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                return float(str(row[col]).replace(',', '').replace('¥', '').replace('円', ''))
        return 0.0
    
    def _extract_commission(self, row) -> float:
        """販売手数料を抽出"""
        possible_columns = ['販売手数料', '手数料', 'commission', 'fee']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                value = str(row[col]).replace(',', '').replace('¥', '').replace('円', '')
                # マイナス記号を除去
                value = value.replace('-', '')
                return float(value)
        return 0.0
    
    def _extract_shipping_fee(self, row) -> float:
        """配送料を抽出"""
        possible_columns = ['配送料', '送料', 'shipping', 'delivery']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                value = str(row[col]).replace(',', '').replace('¥', '').replace('円', '')
                value = value.replace('-', '')
                return float(value)
        return 0.0
    
    def _extract_profit(self, row) -> float:
        """利益を抽出（または計算）"""
        possible_columns = ['販売利益', '受取金額', '利益', '売上金額', 'profit', '入金額']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                return float(str(row[col]).replace(',', '').replace('¥', '').replace('円', ''))
        
        # 利益が直接ない場合は計算
        sale = self._extract_sale_amount(row)
        commission = self._extract_commission(row)
        shipping = self._extract_shipping_fee(row)
        return sale - commission - shipping
    
    def _extract_status(self, row) -> str:
        """ステータスを抽出"""
        possible_columns = ['ステータス', '状態', 'status', '取引状況']
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col])
        return "完了"
