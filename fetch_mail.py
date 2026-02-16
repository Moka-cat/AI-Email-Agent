from imap_tools import MailBox, AND, MailMessageFlags
import requests
import time
import os
import imaplib
import ssl
from dotenv import load_dotenv



# 加载环境变量 (推荐方式)
load_dotenv()

# 配置信息 (也可以直接填在这里测试，但在生产环境中请使用环境变量)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.qq.com") # 例如: imap.gmail.com
EMAIL_USER = os.getenv("EMAIL_USER", "xxx@qq.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "xx")

API_URL = "http://127.0.0.1:8000/api/v1/process_email"

# ... 之前的代码保持不变 ...

def fetch_and_process():
    print(f"🔌 Connecting to {IMAP_SERVER}...")
    
    try:
        # 1. 建立连接
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            print("👀 Checking for UNSEEN emails (Batch of 10)...")
            print("-" * 20)
            for f in mailbox.folder.list():
                print(f.name)
            print("-" * 20)
            # 2. [关键修改] limit=10 
            # 每次只拉取 10 封，避免连接时间过长被服务器踢掉
            # bulk=True 会预取数据，减少交互次数，提升稳定性
            emails = mailbox.fetch(AND(seen=False), limit=10, bulk=True)
            
            count = 0
            for msg in emails:
                count += 1
                print(f"\n📨 [{count}] Processing: {msg.subject[:30]}...")
                
                payload = {
                    "id": msg.uid,
                    "subject": msg.subject,
                    "sender": msg.from_,
                    "body": msg.text or msg.html or ""
                }
                
                try:
                    # 设置 API 超时，防止卡死 IMAP 连接
                    response = requests.post(API_URL, json=payload, timeout=60)
                    
                    if response.status_code == 200:
                        data = response.json()
                        category = data.get('classification', 'unknown')
                        print(f"   🤖 Judgment: {category}")
                        
                        mailbox.flag(msg.uid, MailMessageFlags.SEEN, True)

                        if category == "spam":
                            print(f"   🗑️ Moving to Trash...")
                            # QQ邮箱的垃圾箱通常叫 "Deleted Messages" 或 "Trash"
                            # 如果报错找不到文件夹，请打印 mailbox.folder.list() 查看
                            mailbox.move(msg.uid, "Deleted Messages")
                        elif category == "reply_needed":
                            print(f"   ✨ Needs reply! (Draft generated)")
                            
                            # === 新增：打印草稿内容 ===
                            draft_content = data.get('draft')
                            if draft_content:
                                print(f"\n{'='*20} 🤖 AI Draft Reply {'='*20}")
                                print(draft_content)
                                print(f"{'='*56}\n")

                            # === 存入草稿箱 ===
                            if draft_content:
                                from email.mime.text import MIMEText
                                
                                # 1. 构建邮件对象
                                new_msg = MIMEText(draft_content, 'plain', 'utf-8')
                                new_msg['Subject'] = "Re: " + msg.subject
                                new_msg['To'] = msg.from_ or "unknown"
                                # 你的邮箱地址
                                new_msg['From'] = "xx@qq.com" 

                                print(f"   👉 Saving to 'Drafts'...")

                                import time
                            from imaplib import Time2Internaldate

                            print(f"   👉 Saving to 'Drafts' (Using Raw IMAP)...")

                            try:
                                # [终极必杀技]
                                # 我们直接调用底层的 client.append，绕过 imap_tools 的 Bug
                                # 参数含义: 文件夹名, 标记(设为已读), 时间(现在), 邮件内容
                                mailbox.client.append("Drafts", "(\\Seen)", Time2Internaldate(time.time()), new_msg.as_bytes())
                                
                                print("   ✅ 成功！草稿已保存！(绕过了库的 Bug)")
                                
                            except Exception as e:
                                print(f"   ❌ 保存失败: {e}")
                            
                    else:
                        print(f"   ❌ API Error: {response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    print(f"   ❌ API Connection Failed: {e}")
            
            if count == 0:
                print("   💤 No new emails.")
            else:
                print(f"   ✅ Batch finished. Processed {count} emails.")

    # 3. [关键修改] 捕获连接断开错误，防止脚本崩溃
    except (imaplib.IMAP4.abort, ssl.SSLEOFError, ConnectionResetError) as e:
        print(f"⚠️  Connection dropped by server (Normal for long sessions): {e}")
        print("   ♻️  Will reconnect in next cycle...")
    except Exception as e:
        print(f"💥 Unexpected Error: {e}")

if __name__ == "__main__":
    print("🚀 Mail Poller Started (Batch Mode)")
    while True:
        fetch_and_process()
        # 休息 5 秒再进行下一次轮询，给服务器喘息时间
        print("⏳ Cooling down for 5s...")
        time.sleep(5)