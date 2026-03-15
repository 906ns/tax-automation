# 確定申告自動化ツール

Amazon仕入れ → メルカリ販売の物販ビジネス向け確定申告支援ツール

## 機能

- Amazon適格請求書（PDF）からの仕入れデータ抽出（Gemini AI使用）
- メルカリ売上CSVの処理
- 仕入れと販売の手動紐付け
- 在庫管理
- マネーフォワード形式での仕訳CSV出力

## 必要な準備

1. **Docker Desktopのインストール**
   - Windows: https://www.docker.com/products/docker-desktop
   - Mac: 同上

2. **Gemini APIキーの取得**
   - https://aistudio.google.com/app/apikey
   - 無料で取得可能

## 📸 スクリーンショット

![確定申告自動化ツール](tax-automation/screenshot.png)

---

## セットアップ

1. `.env.example`を`.env`にコピーして、Gemini APIキーを設定
   ```bash
   cp .env.example .env
   # .envファイルを編集してAPIキーを入力
   ```

2. Dockerコンテナを起動
   ```bash
   docker-compose up -d
   ```

3. ブラウザで http://localhost:8000 にアクセス

## 使い方

1. **PDFアップロード**: Amazon適格請求書をアップロード
2. **抽出結果確認**: AIが抽出したデータを確認・修正
3. **CSVアップロード**: メルカリ売上CSVをアップロード
4. **商品紐付け**: 仕入れと販売を紐付け
5. **仕訳出力**: マネーフォワード形式でCSV出力

## 停止方法

```bash
docker-compose down
```

## トラブルシューティング

### ポート8000が使用中の場合
`docker-compose.yml`の`ports`を変更してください
```yaml
ports:
  - "8001:8000"  # 8001など別のポートに変更
```

### データのリセット
```bash
rm -rf data/data.db uploads/* outputs/*
docker-compose restart
```
