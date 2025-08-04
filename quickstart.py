import datetime
import os.path
import os
import requests
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import deepl
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# .envファイルから環境変数を読み込む
load_dotenv()

# Google Cloud Translation APIの認証情報を環境変数で指定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-credentials.json"

# SCOPESをカレンダー・Drive両方に対応
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send"
]

def translate_ja_to_en(text):
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        raise ValueError("DEEPL_API_KEYが設定されていません")
    translator = deepl.Translator(api_key)
    result = translator.translate_text(text, source_lang="JA", target_lang="EN-US")
    # resultがリストの場合と単一オブジェクトの場合に対応
    if isinstance(result, list):
        return result[0].text
    else:
        return result.text

def generate_image_with_sd(prompt, output_path="output.png"):
    # Stable Diffusion Web UI APIで画像生成
    response = requests.post(
        "http://127.0.0.1:7860/sdapi/v1/txt2img",
        json={
            "prompt": prompt,
            "steps": 20,
            "width": 512,
            "height": 512
        }
    )
    result = response.json()
    img_data = base64.b64decode(result['images'][0])
    with open(output_path, "wb") as f:
        f.write(img_data)
    return output_path

def upload_to_drive(service, file_path, file_name):
    # Google Driveに画像をアップロードし、共有リンクを取得
    file_metadata = {
        'name': file_name,
        'mimeType': 'image/png'
    }
    media = MediaFileUpload(file_path, mimetype='image/png')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    # 共有設定（Anyone with the link）
    service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',
            'role': 'reader',
        },
    ).execute()
    file_url = f"https://drive.google.com/uc?id={file_id}"
    return file_url

def send_mail_with_image(service, to, subject, body_text, image_path):
    import base64
    # 画像をBase64エンコード
    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode()
    html_body = f"""
    <html>
      <body>
        <p>{body_text}</p>
        <img src=\"data:image/png;base64,{img_b64}\" />
      </body>
    </html>
    """
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}
    service.users().messages().send(userId="me", body=message_body).execute()

def get_google_services():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    calendar_service = build("calendar", "v3", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    return calendar_service, drive_service, gmail_service

def create_event_with_image(event_title, event_description, event_location, event_date, start_time, end_time, attendees_list, mail_to=None):
    try:
        calendar_service, drive_service, gmail_service = get_google_services()
        # 日付・時刻をISO形式に変換
        tz = 'Asia/Tokyo'
        start_dt = datetime.datetime.combine(event_date, start_time)
        end_dt = datetime.datetime.combine(event_date, end_time)
        start_iso = start_dt.strftime('%Y-%m-%dT%H:%M:%S+09:00')
        end_iso = end_dt.strftime('%Y-%m-%dT%H:%M:%S+09:00')
        attendees = []
        for email in attendees_list:
            if email.strip():
                attendees.append({'email': email.strip()})
        # 1. 予定を作成
        event = {
            'summary': event_title,
            'location': event_location,
            'description': event_description,
            'start': {
                'dateTime': start_iso,
                'timeZone': tz,
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': tz,
            },
            'attendees': attendees,
        }
        created_event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        event_id = created_event['id']
        event_url = created_event.get('htmlLink')
        # 2. Stable Diffusion用プロンプトは説明のみを英訳
        jp_prompt = event_description
        en_prompt = translate_ja_to_en(jp_prompt)
        image_path = generate_image_with_sd(en_prompt)
        # 3. Google Driveにアップロード
        image_url = upload_to_drive(drive_service, image_path, "event_image.png")
        # 4. 予定の説明欄に画像URLを追記して更新
        updated_description = event_description + f"\n画像: {image_url}"
        calendar_service.events().patch(
            calendarId='primary',
            eventId=event_id,
            body={'description': updated_description}
        ).execute()
        # 5. メール送信（送り先が指定されていれば）
        if mail_to:
            subject = f"予定: {event_title}"
            body_text = f"{event_description}\nGoogleカレンダー: {event_url}"
            send_mail_with_image(gmail_service, mail_to, subject, body_text, image_path)
        return {
            'event_url': event_url,
            'image_url': image_url,
            'image_path': image_path,
            'prompt_en': en_prompt
        }
    except HttpError as error:
        return {'error': str(error)}

# 既存のmain()は不要なので削除またはコメントアウト
# if __name__ == "__main__":
#     main()