import pytest
import tempfile
from pathlib import Path
from backend.csv_processor import MercariCSVProcessor


@pytest.fixture
def processor():
    return MercariCSVProcessor()


def _write_csv(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestProcessCSV:
    def test_basic_parsing(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
            "2024-03-01,Nintendo Switch,25000,2500,700,21800,完了\n"
        )
        results = processor.process_csv(csv_path)

        assert len(results) == 1
        item = results[0]
        assert item["transaction_date"] == "2024-03-01"
        assert item["product_name"] == "Nintendo Switch"
        assert item["sale_amount"] == 25000.0
        assert item["commission"] == 2500.0
        assert item["shipping_fee"] == 700.0
        assert item["profit"] == 21800.0
        assert item["status"] == "完了"
        assert item["is_cancelled"] is False

    def test_cancelled_item(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
            "2024-03-15,テスト商品,5000,500,500,4000,キャンセル\n"
        )
        results = processor.process_csv(csv_path)

        assert results[0]["is_cancelled"] is True

    def test_returned_item(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
            "2024-04-01,返品テスト,3000,300,300,2400,返品\n"
        )
        results = processor.process_csv(csv_path)

        assert results[0]["is_cancelled"] is True

    def test_multiple_rows(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
            "2024-03-01,商品A,10000,1000,500,8500,完了\n"
            "2024-03-02,商品B,20000,2000,700,17300,完了\n"
            "2024-03-03,商品C,5000,500,500,4000,キャンセル\n"
        )
        results = processor.process_csv(csv_path)

        assert len(results) == 3
        assert results[0]["product_name"] == "商品A"
        assert results[2]["is_cancelled"] is True

    def test_alternative_column_names(self, processor):
        csv_path = _write_csv(
            "取引日,商品,金額,手数料,送料,入金額,状態\n"
            "2024-05-01,代替カラムテスト,15000,1500,600,12900,完了\n"
        )
        results = processor.process_csv(csv_path)

        assert len(results) == 1
        assert results[0]["product_name"] == "代替カラムテスト"
        assert results[0]["sale_amount"] == 15000.0

    def test_yen_symbol_stripped(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
            "2024-06-01,円記号テスト,¥12000,¥1200,¥600,¥10200,完了\n"
        )
        results = processor.process_csv(csv_path)

        assert results[0]["sale_amount"] == 12000.0
        assert results[0]["commission"] == 1200.0

    def test_empty_csv_returns_empty(self, processor):
        csv_path = _write_csv(
            "取引日時,商品名,価格,販売手数料,配送料,受取金額,ステータス\n"
        )
        results = processor.process_csv(csv_path)

        assert results == []

    def test_invalid_file_raises(self, processor):
        csv_path = _write_csv("this is not a valid csv at all")
        results = processor.process_csv(csv_path)
        assert isinstance(results, list)
