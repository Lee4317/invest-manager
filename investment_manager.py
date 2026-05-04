import sys
import os
import datetime
import yfinance as yf
import smtplib
from email.message import EmailMessage

# 시스템 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

def get_advice():
    try:
        ticker = yf.Ticker("TQQQ")
        df = ticker.history(period="30d")
        if df.empty: return None
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
        
        return {
            "action": "BUY" if rsi < 50 else "HOLD",
            "rsi": round(rsi, 2),
            "price": round(df['Close'].iloc[-1], 2)
        }
    except:
        return None

def send_naver_email(advice):
    # ID/PW 가져오기
    n_id = os.environ.get('NAVER_ID', '').strip()
    n_pw = os.environ.get('NAVER_PW', '').strip()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # [중요] 한글을 1글자도 포함하지 않은 영문 메시지
    msg = EmailMessage()
    msg['Subject'] = f"Invest Report {today_str}"
    msg['From'] = n_id
    msg['To'] = n_id
    msg.set_content(f"Action: {advice['action']}\nRSI: {advice['rsi']}\nPrice: ${advice['price']}")

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            # 문자열을 명시적으로 영어(ascii)로 인코딩해서 전송
            server.login(n_id.encode('ascii').decode('ascii'), n_pw.encode('ascii').decode('ascii'))
            server.send_message(msg)
        print("Success")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    res = get_advice()
    if res:
        send_naver_email(res)
