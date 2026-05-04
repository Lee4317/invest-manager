import sys
import os
import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 1. 시스템 출력 인코딩 강제 설정 (한글 깨짐 방지)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

def get_advice():
    try:
        ticker = yf.Ticker("TQQQ")
        df = ticker.history(period="30d")
        if df.empty: return None
        
        # RSI 계산
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        return {
            "action": "BUY" if rsi < 50 else "HOLD",
            "rsi": round(rsi, 2),
            "price": round(df['Close'].iloc[-1], 2)
        }
    except:
        return {"action": "CHECK", "rsi": 0, "price": 0}

def send_naver_email(advice):
    # 2. Secrets 로드 및 공백 제거
    naver_id = os.environ.get('NAVER_ID', '').strip()
    naver_pw = os.environ.get('NAVER_PW', '').strip()
    
    if not naver_id or not naver_pw:
        print("❌ Error: Secrets are empty.")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 3. 메일 구성 (최대한 단순한 영문 위주)
    msg = MIMEText(f"RSI: {advice['rsi']}\nPrice: ${advice['price']}\nAction: {advice['action']}", 'plain', 'utf-8')
    msg['Subject'] = Header(f"Invest Report {today_str}", 'utf-8')
    msg['From'] = naver_id
    msg['To'] = naver_id

    try:
        # 4. SMTP 서버 연결
        server = smtplib.SMTP_SSL("smtp.naver.com", 465, timeout=20)
        
        # [핵심 해결책] 아이디와 비번을 '글자'가 아닌 '바이트 데이터'로 강제 변환하여 로그인
        # 이렇게 하면 position 1-5 에러를 일으키는 인코딩 과정을 건너뜁니다.
        server.login(naver_id.encode('utf-8'), naver_pw.encode('utf-8'))
        
        server.sendmail(naver_id, [naver_id], msg.as_string())
        server.quit()
        print(f"✅ Success: Mail sent to {naver_id}")
    except Exception as e:
        # 에러 발생 시 상세 내용을 안전하게 출력
        print(f"❌ Error Detail: {repr(e)}")

if __name__ == "__main__":
    res = get_advice()
    send_naver_email(res)
