# 確定申告自動化ツール - セットアップガイド

## 📋 必要なもの

1. **Docker Desktop**（Windows/Mac）
2. **Gemini API キー**（無料で取得可能）
3. **Amazon 適格請求書 PDF**
4. **メルカリ売上 CSV**

---

## 🚀 セットアップ手順

### 1. Docker Desktop のインストール

#### Windows の場合
1. https://www.docker.com/products/docker-desktop からダウンロード
2. インストーラーを実行
3. 再起動後、Docker Desktop を起動

#### Mac の場合
1. 同じく https://www.docker.com/products/docker-desktop からダウンロード
2. Docker.dmg を開いて Applications にドラッグ
3. Docker Desktop を起動

### 2. Gemini API キーの取得

1. https://aistudio.google.com/app/apikey にアクセス
2. Google アカウントでログイン
3. 「Create API Key」をクリック
4. 生成された API キーをコピー（後で使用）

### 3. プロジェクトのセットアップ

1. **tax-automation フォルダをデスクトップなどに配置**

2. **環境変数ファイルを作成**
   ```
   .env.example を .env にコピーして、API キーを設定
   ```

   **Windows の場合（PowerShell）:**
   ```powershell
   cd tax-automation
   Copy-Item .env.example .env
   notepad .env
   ```

   **Mac の場合（ターミナル）:**
   ```bash
   cd tax-automation
   cp .env.example .env
   nano .env
   ```

   `.env` ファイルを開いて、以下のように API キーを記入:
   ```
   GEMINI_API_KEY=あなたのAPIキー
   ```

3. **Docker コンテナを起動**

   **Windows の場合（PowerShell）:**
   ```powershell
   docker-compose up -d
   ```

   **Mac の場合（ターミナル）:**
   ```bash
   docker-compose up -d
   ```

   初回は Docker イメージのダウンロードとビルドに 5-10 分かかります。

4. **ブラウザでアクセス**
   ```
   http://localhost:8000
   ```

---

## 📱 使い方

### ステップ1: データアップロード

1. **Amazon 適格請求書（PDF）**
   - フリマアシストなどでダウンロードした PDF をアップロード
   - 複数ファイルを一度にアップロード可能
   - AI が自動で商品情報を抽出

2. **メルカリ売上 CSV**
   - メルカリからダウンロードした売上 CSV をアップロード
   - 取引情報を自動で読み込み

### ステップ2: データ確認

- アップロードしたデータを確認
- 抽出ミスがあれば後で手動で修正可能

### ステップ3: 商品紐付け

- AI が商品名の類似度から紐付け候補を提案
- チェックボックスで選択して保存
- 在庫も自動計算

### ステップ4: 仕訳出力

1. 期末日を選択（通常は 12/31）
2. 「仕訳 CSV を生成」をクリック
3. ダウンロードした CSV をマネーフォワードにインポート

---

## 🔧 トラブルシューティング

### Docker が起動しない
- Docker Desktop が起動しているか確認
- Windows: WSL2 が有効になっているか確認

### ポート 8000 が使用中
`docker-compose.yml` を編集:
```yaml
ports:
  - "8001:8000"  # 8001 など別のポートに変更
```

その後、`http://localhost:8001` でアクセス

### Gemini API エラー
- `.env` ファイルに正しい API キーが設定されているか確認
- API キーにクォート（" や '）は不要
- コンテナを再起動: `docker-compose restart`

### PDF 抽出がうまくいかない
- PDF が適格請求書の形式か確認
- 画像化された PDF は抽出精度が低い場合がある

---

## 🛑 停止と再起動

### 停止
```bash
docker-compose down
```

### 再起動
```bash
docker-compose up -d
```

### データをリセット
Web UI の「全データをリセット」ボタンを使用
または:
```bash
rm -rf data/data.db uploads/* outputs/*
docker-compose restart
```

---

## 📂 ディレクトリ構成

```
tax-automation/
├── backend/           # バックエンド（Python/FastAPI）
├── frontend/          # フロントエンド（HTML/CSS/JS）
├── uploads/           # アップロードファイル保存先
├── outputs/           # 生成された CSV 保存先
├── data/              # データベース
├── docker-compose.yml # Docker 設定
└── .env               # 環境変数（API キー）
```

---

## 💡 ヒント

- **API コスト**: Gemini API は月 1500 リクエスト無料。月 30 件 × 12 ヶ月 = 360 件程度なら無料枠内
- **バックアップ**: 定期的に `data/data.db` をバックアップ推奨
- **CSV 形式**: マネーフォワードの仕訳インポートは Shift-JIS（BOM 付き）で出力
- **在庫管理**: 期末在庫は資産計上されるため、正確な紐付けが重要

---

## 📞 サポート

問題が解決しない場合は、以下を確認してください:

1. Docker Desktop が起動しているか
2. `.env` ファイルに正しい API キーが設定されているか
3. `docker-compose logs` でエラーログを確認

---

## 🔄 アップデート

新しいバージョンが公開された場合:

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

---

これで確定申告の準備が効率的にできます！🎉
