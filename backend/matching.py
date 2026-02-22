from difflib import SequenceMatcher
from typing import List, Dict, Tuple
from datetime import datetime

class ProductMatcher:
    """商品の紐付けを支援するクラス"""
    
    def __init__(self):
        self.similarity_threshold = 0.6  # 類似度の閾値
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        2つの文字列の類似度を計算（0.0～1.0）
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def suggest_matches(
        self, 
        amazon_items: List[Dict], 
        mercari_items: List[Dict]
    ) -> List[Dict]:
        """
        Amazon仕入れとメルカリ販売の紐付け候補を提案
        
        Args:
            amazon_items: Amazon仕入れデータのリスト
            mercari_items: メルカリ販売データのリスト
        
        Returns:
            マッチング候補のリスト
            [
                {
                    "amazon_id": 1,
                    "mercari_id": 5,
                    "similarity": 0.85,
                    "amazon_product": "商品名A",
                    "mercari_product": "商品名A（美品）",
                    "amazon_date": "2024-01-01",
                    "mercari_date": "2024-01-15"
                }
            ]
        """
        suggestions = []
        
        # 既にマッチ済みのメルカリIDを追跡
        matched_mercari_ids = set()
        
        # Amazon商品ごとにループ
        for amazon_item in amazon_items:
            best_matches = []
            
            # メルカリ商品とマッチング
            for mercari_item in mercari_items:
                # 既にマッチ済み or キャンセルはスキップ
                if mercari_item['id'] in matched_mercari_ids or mercari_item.get('is_cancelled'):
                    continue
                
                # 商品名の類似度を計算
                similarity = self.calculate_similarity(
                    amazon_item['product_name'],
                    mercari_item['product_name']
                )
                
                # 日付チェック（販売日 >= 仕入れ日）
                amazon_date = datetime.strptime(amazon_item['order_date'], '%Y-%m-%d')
                mercari_date = datetime.strptime(mercari_item['transaction_date'], '%Y-%m-%d')
                
                if mercari_date >= amazon_date and similarity >= self.similarity_threshold:
                    best_matches.append({
                        "amazon_id": amazon_item['id'],
                        "mercari_id": mercari_item['id'],
                        "similarity": round(similarity, 2),
                        "amazon_product": amazon_item['product_name'],
                        "mercari_product": mercari_item['product_name'],
                        "amazon_date": amazon_item['order_date'],
                        "mercari_date": mercari_item['transaction_date'],
                        "amazon_price": amazon_item['total_price'],
                        "mercari_price": mercari_item['sale_amount']
                    })
            
            # 類似度が高い順にソート
            best_matches.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 上位の候補のみ追加（最大3件）
            for match in best_matches[:3]:
                suggestions.append(match)
        
        return suggestions
    
    def get_inventory(
        self, 
        amazon_items: List[Dict], 
        matched_pairs: List[Tuple[int, int]]
    ) -> List[Dict]:
        """
        未販売の在庫を取得
        
        Args:
            amazon_items: Amazon仕入れデータ
            matched_pairs: マッチング済みペア [(amazon_id, mercari_id), ...]
        
        Returns:
            在庫リスト
        """
        matched_amazon_ids = set([pair[0] for pair in matched_pairs])
        
        inventory = []
        for item in amazon_items:
            if item['id'] not in matched_amazon_ids:
                inventory.append({
                    "id": item['id'],
                    "product_name": item['product_name'],
                    "order_date": item['order_date'],
                    "quantity": item['quantity'],
                    "unit_price": item['unit_price'],
                    "total_price": item['total_price']
                })
        
        return inventory
    
    def calculate_inventory_value(self, inventory: List[Dict]) -> float:
        """
        在庫の合計金額を計算
        """
        return sum([item['total_price'] for item in inventory])
