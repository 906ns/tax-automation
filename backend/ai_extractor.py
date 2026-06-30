import anthropic
from pathlib import Path
from typing import List, Dict, Any
import json
import PyPDF2
from .config import settings


class AmazonInvoiceExtractor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-haiku-4-5-20251001"

    def extract_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        PDFから請求書情報を抽出

        Returns:
            List[Dict]: 抽出された商品情報のリスト
        """
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()

            prompt = f"""
以下はAmazonの適格請求書のテキストです。以下の情報を抽出してJSON形式で返してください。
複数の商品がある場合は、配列で返してください。

抽出する情報:
- order_number: 注文番号
- order_date: 注文日（YYYY-MM-DD形式）
- product_name: 商品名
- asin: ASIN番号（ある場合）
- quantity: 数量
- unit_price: 単価（税込）
- total_price: 合計金額（税込）
- invoice_number: 適格請求書番号（登録番号）

請求書テキスト:
{text_content}

必ず以下の形式のJSONで返してください（他のテキストは含めないでください）:
{{
    "items": [
        {{
            "order_number": "123-4567890-1234567",
            "order_date": "2024-12-25",
            "product_name": "商品名",
            "asin": "B08XXXX",
            "quantity": 1,
            "unit_price": 1000.0,
            "total_price": 1000.0,
            "invoice_number": "T1234567890123"
        }}
    ]
}}
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)
            return result.get("items", [])

        except Exception as e:
            print(f"PDF抽出エラー: {str(e)}")
            raise Exception(f"PDF抽出に失敗しました: {str(e)}")

    def extract_batch(self, pdf_paths: List[Path]) -> Dict[str, List[Dict[str, Any]]]:
        """複数のPDFをバッチ処理"""
        results = {}
        for pdf_path in pdf_paths:
            try:
                items = self.extract_from_pdf(pdf_path)
                results[pdf_path.name] = {"success": True, "items": items}
            except Exception as e:
                results[pdf_path.name] = {"success": False, "error": str(e)}
        return results
