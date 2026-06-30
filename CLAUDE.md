# CLAUDE.md

確定申告自動化ツール — Amazon仕入れ→メルカリ販売の物販ビジネス向け、シングルユーザーのローカルツール。
Amazon適格請求書PDFからGemini APIで仕入れデータを抽出し、メルカリ売上CSVと紐付けて、マネーフォワード形式の仕訳CSVを出力する。

## Commands
```bash
# Docker起動
docker-compose up -d

# ローカル開発（.venv = Python 3.10）
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# テスト
pytest
pytest tests/test_csv_processor.py -v    # 単一ファイル
```

## Architecture
FastAPI + SQLAlchemy + SQLite。フロントは Jinja2 + Vanilla JS（SPAではない）。
ルーティングは backend/main.py に集約（分割なし）。モデルは models.py の5テーブル。

データの流れ:
```
PDF → PyPDF2でテキスト抽出 → Gemini APIでJSON化 → AmazonPurchase
CSV → pandasパース → MercariSale
AmazonPurchase + MercariSale → ProductMatch（商品名の類似度で紐付け）
全データ → 仕訳CSV（Shift-JIS、マネーフォワード形式）
```

## Key Design Decisions（コードから読み取りにくい意図）
- AI抽出結果はDB保存前に必ず人間が確認・修正する（税務データの正確性保証）
- キャンセル・返品ステータスの取引は仕訳から自動除外
- 仕訳CSVは Shift-JIS（マネーフォワードのインポート要件）
- 商品名の紐付けは difflib.SequenceMatcher、閾値0.6
- AI抽出は2段構成（PyPDF2でテキスト化 → LLMへ送る）

## Environment
- `GEMINI_API_KEY` が必須（`.env`に設定）
- SQLite: `data/data.db` / アップロード: `uploads/` / 出力: `outputs/`
