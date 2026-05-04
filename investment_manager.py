import sys
import os
import datetime
import yfinance as yf
import smtplib
import base64
from email.mime.text import MIMEText
from email.header import Header

# 파이썬 실행 환경의 인코딩을 강제로 UTF-8로 고정
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

def get_advice(total_budget=550):
    try:
        ticker = yf.Ticker("TQQQ")
        df = ticker.history(period="30d")
        if df.empty: return None
        
        current_price = df['Close'].iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        today = datetime.date.today()
        days_left = (datetime.date(2026, 5, 26) - today).days

        # 모든 텍스트를 영어로 구성 (인코딩 에러 원천 차단)
        action = "BUY" if rsi < 50 else "HOLD"
        amount = total_budget * 0.05 if rsi < 50 else 0

        return {
            "action": action, "amount": round(amount, 2),
            "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
        }
    except:
        return None

def send_naver_email(advice):
    # Secrets 값을 가져와서 앞뒤 공백을 제거하고 바이트로 변환
    raw_id = os.environ.get('NAVER_ID', '').strip()
    raw_pw = os.environ.get('NAVER_PW', '').strip()
    
    if not raw_id or not raw_pw:
        print("Error: Empty Secrets")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # 메일 본문 및 제목 (전부 영어로 구성)
    subject = f"Report {today_str}"
    body = f"Action: {advice['action']}\nAmount: ${advice['amount']}\nRSI: {advice['rsi']}"

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = raw_id
    msg['To'] = raw_id

    try:
        # SMTP 서버 연결
        server = smtplib.SMTP_SSL("smtp.naver.com", 465, timeout=20)
        
        # [핵심] 로그인 정보를 보낼 때 ASCII 에러를 피하기 위해 바이트 단위로 명시적 전달
        server.login(raw_id.encode('ascii'), raw_pw.encode('ascii'))
        
        server.sendmail(raw_id, [raw_id], msg.as_string())
        server.quit()
        print(f"✅ Success: Mail sent to {raw_id}")
    except Exception as e:
        # 에러가 나더라도 어떤 에러인지 영어로만 출력
        print(f"❌ SMTP Error: {repr(e)}")

if __name__ == "__main__":
    res = get_advice()
    if res:
        send_naver_email(res)
