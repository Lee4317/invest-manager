import sys
import os
import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 시스템 출력 인코딩 강제 설정
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
        cpi_date = datetime.date(2026, 5, 12)
        sell_date = datetime.date(2026, 5, 26)
        days_left = (sell_date - today).days

        if rsi > 70:
            action = "Overheated - Wait"
            amount = 0
        elif rsi < 35:
            action = "Opportunity - Buy More"
            amount = total_budget * 0.1
        else:
            action = "Normal Buy"
            amount = total_budget * 0.05

        return {
            "action": action, "amount": round(amount, 2),
            "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
        }
    except Exception:
        return None

def send_naver_email(advice):
    naver_id = os.environ.get('NAVER_ID', '').strip()
    naver_pw = os.environ.get('NAVER_PW', '').strip()
    
    if not naver_id or not naver_pw:
        print("Error: Secrets are empty")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # [핵심] 제목과 본문을 Header와 MIMEText로 각각 UTF-8 처리
    subject = f"[{today_str}] Investment Guide Report"
    body = f"""
Today's Action: {advice['action']}
Amount: ${advice['amount']}
Market RSI: {advice['rsi']}
Current Price: ${advice['price']}
Days Left: {advice['days']}
    """

    # 메일 객체 생성 (전통적인 MIMEText 방식이 때로는 가장 안전합니다)
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = naver_id
    msg['To'] = naver_id

    try:
        # SMTP 서버 연결 시 타임아웃 추가
        with smtplib.SMTP_SSL("smtp.naver.com", 465, timeout=20) as server:
            server.login(naver_id, naver_pw)
            server.sendmail(naver_id, [naver_id], msg.as_string())
        print(f"Success: Mail sent to {naver_id}")
    except Exception as e:
        # 에러 메시지에서 ASCII 에러가 나는 것을 방지하기 위해 repr 사용
        print(f"Error occurred: {repr(e)}")

if __name__ == "__main__":
    res = get_advice()
    if res:
        send_naver_email(res)
    else:
        print("Error: Could not generate advice")
