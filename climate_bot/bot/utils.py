from pathlib import Path

CHAT_IDS_FILE = Path("chat_ids.txt")


def save_chat_id(chat_id: int):
    chat_ids = get_all_chat_ids()
    if chat_id not in chat_ids:
        with open(CHAT_IDS_FILE, "a") as f:
            f.write(f"{chat_id}\n")


def get_all_chat_ids():
    if not CHAT_IDS_FILE.exists():
        return set()
    with open(CHAT_IDS_FILE, "r") as f:
        return set(int(line.strip()) for line in f if line.strip())