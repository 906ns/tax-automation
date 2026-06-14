import pytest
from backend.journal_generator import JournalGenerator


@pytest.fixture
def generator():
    return JournalGenerator()


SAMPLE_AMAZON = [
    {
        "order_date": "2024-01-10",
        "product_name": "Nintendo Switch 本体",
        "order_number": "123-4567890-0000001",
        "total_price": 25000.0,
    }
]

SAMPLE_MERCARI = [
    {
        "transaction_date": "2024-02-01",
        "product_name": "Nintendo Switch 本体 美品",
        "sale_amount": 30000.0,
        "commission": 3000.0,
        "shipping_fee": 700.0,
        "is_cancelled": False,
    }
]

SAMPLE_MERCARI_CANCELLED = [
    {
        "transaction_date": "2024-02-01",
        "product_name": "キャンセル商品",
        "sale_amount": 5000.0,
        "commission": 500.0,
        "shipping_fee": 500.0,
        "is_cancelled": True,
    }
]


class TestPurchaseJournals:
    def test_generates_one_journal_per_item(self, generator):
        journals = generator.generate_purchase_journals(SAMPLE_AMAZON)

        assert len(journals) == 1

    def test_debit_is_purchase_credit_is_payable(self, generator):
        journal = generator.generate_purchase_journals(SAMPLE_AMAZON)[0]

        assert journal["借方勘定科目"] == "仕入高"
        assert journal["貸方勘定科目"] == "未払金"

    def test_amounts_match(self, generator):
        journal = generator.generate_purchase_journals(SAMPLE_AMAZON)[0]

        assert journal["借方金額"] == 25000
        assert journal["貸方金額"] == 25000

    def test_description_contains_order_number(self, generator):
        journal = generator.generate_purchase_journals(SAMPLE_AMAZON)[0]

        assert "123-4567890-0000001" in journal["摘要"]


class TestSalesJournals:
    def test_generates_sale_commission_shipping(self, generator):
        journals = generator.generate_sales_journals(SAMPLE_MERCARI)

        assert len(journals) == 3
        accounts = [j["借方勘定科目"] for j in journals]
        assert "売掛金" in accounts
        assert "支払手数料" in accounts
        assert "荷造運賃" in accounts

    def test_sale_amounts(self, generator):
        journals = generator.generate_sales_journals(SAMPLE_MERCARI)
        sale = [j for j in journals if j["借方勘定科目"] == "売掛金"][0]

        assert sale["借方金額"] == 30000
        assert sale["貸方金額"] == 30000
        assert sale["貸方勘定科目"] == "売上高"

    def test_commission_amount(self, generator):
        journals = generator.generate_sales_journals(SAMPLE_MERCARI)
        commission = [j for j in journals if j["借方勘定科目"] == "支払手数料"][0]

        assert commission["借方金額"] == 3000

    def test_cancelled_items_excluded(self, generator):
        journals = generator.generate_sales_journals(SAMPLE_MERCARI_CANCELLED)

        assert len(journals) == 0

    def test_zero_commission_skipped(self, generator):
        items = [{**SAMPLE_MERCARI[0], "commission": 0.0}]
        journals = generator.generate_sales_journals(items)

        accounts = [j["借方勘定科目"] for j in journals]
        assert "支払手数料" not in accounts

    def test_zero_shipping_skipped(self, generator):
        items = [{**SAMPLE_MERCARI[0], "shipping_fee": 0.0}]
        journals = generator.generate_sales_journals(items)

        accounts = [j["借方勘定科目"] for j in journals]
        assert "荷造運賃" not in accounts


class TestInventoryJournals:
    def test_generates_inventory_journal(self, generator):
        inventory = [{"total_price": 25000.0}, {"total_price": 15000.0}]
        journals = generator.generate_inventory_journals(inventory, "2024-12-31")

        assert len(journals) == 1
        assert journals[0]["借方勘定科目"] == "商品"
        assert journals[0]["貸方勘定科目"] == "期末商品棚卸高"
        assert journals[0]["借方金額"] == 40000

    def test_empty_inventory_no_journal(self, generator):
        journals = generator.generate_inventory_journals([], "2024-12-31")

        assert len(journals) == 0


class TestGenerateAll:
    def test_sorted_by_date(self, generator):
        journals = generator.generate_all_journals(SAMPLE_AMAZON, SAMPLE_MERCARI, [])

        dates = [j["取引日"] for j in journals]
        assert dates == sorted(dates)

    def test_inventory_included_when_year_end_set(self, generator):
        inventory = [{"total_price": 10000.0}]
        journals = generator.generate_all_journals(
            SAMPLE_AMAZON, SAMPLE_MERCARI, inventory, "2024-12-31"
        )

        has_inventory = any(j["借方勘定科目"] == "商品" for j in journals)
        assert has_inventory is True

    def test_inventory_excluded_when_no_year_end(self, generator):
        inventory = [{"total_price": 10000.0}]
        journals = generator.generate_all_journals(
            SAMPLE_AMAZON, SAMPLE_MERCARI, inventory
        )

        has_inventory = any(j["借方勘定科目"] == "商品" for j in journals)
        assert has_inventory is False
