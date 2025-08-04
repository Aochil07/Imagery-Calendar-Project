# Imagery-Calendar-Project
画像生成AIを用いた、展望記憶トレーニングを促すカレンダーアプリ


# Google Calendar Image Generator

Googleカレンダーに予定を作成し、Stable Diffusionで画像を生成してDriveにアップロードするPythonアプリケーションです。

## セットアップ

### 1. 必要なファイルの準備

#### Google認証情報
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. 以下のAPIを有効化：
   - Google Calendar API
   - Google Drive API
   - Gmail API
3. OAuth 2.0クライアントIDを作成（デスクトップアプリケーション）
4. ダウンロードしたJSONファイルを`credentials.json`として保存

#### 環境変数
`.env`ファイルを作成し、以下の内容を追加：
```
DEEPL_API_KEY=your-deepl-api-key
```

### 2. 依存関係のインストール
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client deepl python-dotenv requests
```

### 3. 初回実行
```bash
python quickstart.py
```
初回実行時にブラウザが開き、Googleアカウントでの認証が必要です。

## 使用方法

```python
from quickstart import create_event_with_image

result = create_event_with_image(
    event_title="会議",
    event_description="プロジェクトの進捗確認",
    event_location="会議室A",
    event_date=datetime.date(2024, 1, 15),
    start_time=datetime.time(10, 0),
    end_time=datetime.time(11, 0),
    attendees_list=["colleague@example.com"],
    mail_to="manager@example.com"
)
```

## 注意事項

- `credentials.json`、`token.json`、`.env`ファイルは絶対にGitHubにアップロードしないでください
- これらのファイルは`.gitignore`で除外されています
- 初回実行時に`token.json`が自動生成されます
