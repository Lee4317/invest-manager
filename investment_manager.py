import sys
import os
import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 시스템 출력 환경 설정
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
        rsi = (100 - (100 / (1 + (df['Close'].diff().where(df['Close'].diff() > 0, 0).rolling(14).mean() / -df['Close'].diff().where(df['Close'].diff() < 0, 0).rolling(14).mean())))).iloc[-1]
        return {"action": "BUY" if rsi < 50 else "HOLD", "rsi": round(rsi, 2)}
    except:
        return {"action": "CHECK", "rsi": 0}

def send_naver_email(advice):
    # 환경변수 로드
    naver_id = os.environ.get('NAVER_ID', '').strip()
    naver_pw = os.environ.get('NAVER_PW', '').strip()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # 1. 모든 텍스트를 영문으로 구성 (한글 원천 배제)
    msg = MIMEText(f"RSI: {advice['rsi']}\nAction: {advice['action']}", 'plain', 'utf-8')
    msg['Subject'] = Header(f"Invest Report {today_str}", 'utf-8')
    msg['From'] = naver_id
    msg['To'] = naver_id

    try:
        # 2. SMTP 연결 (타임아웃 30초로 넉넉하게 설정)
        server = smtplib.SMTP_SSL("smtp.naver.com", 465, timeout=30)
        
        # 3. [핵심] 아이디와 비밀번호를 'latin-1'로 강제 인코딩
        # 이 방식은 @나 . 같은 기호는 물론, 웬만한 특수문자 에러를 모두 무시하고 서버로 전송합니다.
        server.login(naver_id.encode('latin-1').decode('latin-1'), 
                     naver_pw.encode('latin-1').decode('latin-1'))
        
        server.sendmail(naver_id, [naver_id], msg.as_string())
        server.quit()
        print(f"Success: Sent to {naver_id}")
    except Exception as e:
        # 에러 발생 시 상세 내용을 문자열로 출력
        print(f"Error Detail: {str(e)}")

if __name__ == "__main__":
    res = get_advice()
    send_naver_email(res)
