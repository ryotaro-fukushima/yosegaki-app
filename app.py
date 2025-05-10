from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os

# .envファイルを読み込み
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
print("SLACK_BOT_TOKEN:", SLACK_BOT_TOKEN)
print("SLACK_APP_TOKEN:", SLACK_APP_TOKEN)

# アプリ初期化
app = App(token=SLACK_BOT_TOKEN)

# メモリ上に寄せ書きを保持
yosegaki_store = {}  # {thread_ts: [messages]}

# ユーザーごとの最新スレッドを記録
user_threads = {}  # {user_id: thread_ts}

@app.command("/yosegaki")
def handle_yosegaki_command(ack, body, say):
    ack()
    user_id = body["user_id"]
    result = say(
        text=f"🎉 <@{user_id}>さんが寄せ書きを始めました！このスレッドに自由にメッセージをどうぞ！"
    )
    thread_ts = result["ts"]
    yosegaki_store[thread_ts] = []
    user_threads[user_id] = thread_ts  # ← 追加
    print(f"🧵 保存した thread_ts: {thread_ts} for user {user_id}")


# メッセージイベントで寄せ書きを記録
@app.event("message")
def handle_message_events(body, event, say, client):
    thread_ts = event.get("thread_ts") or event.get("ts")
    user_id = event.get("user")
    text = event.get("text")

    # 対象スレッドに記録
    if thread_ts in yosegaki_store and user_id and text:
        # ユーザー名を取得
        user_info = client.users_info(user=user_id)
        display_name = user_info["user"]["profile"].get("display_name") or user_info["user"]["real_name"]

        # 形式：名前：メッセージ
        yosegaki_store[thread_ts].append(f"{display_name}：{text}")
        print(f"📩 寄せ書き追加: {display_name}：{text}")


# `/finish_yosegaki` コマンド：寄せ書きをまとめて表示
@app.command("/finish_yosegaki")
def handle_finish_command(ack, body, say):
    ack()
    user_id = body["user_id"]
    thread_ts = user_threads.get(user_id)

    if not thread_ts:
        say("⚠️ 寄せ書きを開始していないか、thread_ts が見つかりません。")
        return

    messages = yosegaki_store.pop(thread_ts, [])
    if messages:
        summary = "\n".join([f"・{m}" for m in messages])
        say(text=f"🎁 寄せ書きが完成しました！\n\n{summary}", thread_ts=thread_ts)
    else:
        say(text="⚠️ メッセージがまだありません。", thread_ts=thread_ts)

# アプリ起動
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

# @app.event("*")
# def handle_all_events(body, event=None, logger=None):
#     print("📦 何かイベントを受信しました")
#     print("body:", body)
