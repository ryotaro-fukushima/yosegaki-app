from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os

# .envファイルを読み込み
load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# アプリ初期化
app = App(token=SLACK_BOT_TOKEN)

# メモリ上に寄せ書きを保持
yosegaki_store = {}  # {thread_ts: [messages]}

# `/yosegaki` コマンド：寄せ書き開始
@app.command("/yosegaki")
def handle_yosegaki_command(ack, body, say):
    ack()
    user_id = body["user_id"]
    channel_id = body["channel_id"]

    # 開始メッセージを投稿（そのメッセージを基準スレッドに）
    result = say(
        text=f"🎉 <@{user_id}>さんが寄せ書きを始めました！このスレッドに自由にメッセージをどうぞ！"
    )
    thread_ts = result["ts"]
    yosegaki_store[thread_ts] = []

# メッセージイベントで寄せ書きを記録
@app.event("message")
def handle_message_events(body, event, logger):
    thread_ts = event.get("thread_ts")
    if not thread_ts:
        return

    if thread_ts in yosegaki_store and "text" in event:
        yosegaki_store[thread_ts].append(event["text"])
        logger.info(f"寄せ書き追加: {event['text']}")

# `/finish_yosegaki` コマンド：寄せ書きをまとめて表示
@app.command("/finish_yosegaki")
def handle_finish_command(ack, body, say):
    ack()
    thread_ts = body["text"].strip()
    if thread_ts in yosegaki_store:
        messages = yosegaki_store.pop(thread_ts)
        if messages:
            summary = "\n".join([f"・{m}" for m in messages])
            say(text=f"🎁 寄せ書きが完成しました！\n\n{summary}", thread_ts=thread_ts)
        else:
            say(text="⚠️ メッセージがまだありません。", thread_ts=thread_ts)
    else:
        say(text="❌ 対象のスレッドが見つかりません。thread_tsを確認してください。")

# アプリ起動
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
