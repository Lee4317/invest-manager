import sys
import os
import datetime
import yfinance as yf
import smtplib
from email.message import EmailMessage

# 시스템 출력 인코딩 강제 설정
sys.stdout.reconfigure(encoding='utf-8')

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
            action, final_amount = "매수 쉬어감", 0
        elif rsi < 35:
            action, final_amount = "추가 매수 기회", total_budget * 0.1
        else:
            action, final_amount = "정상 매수 진행", total_budget * 0.05

        return {
            "action": action, "amount": round(final_amount, 2),
            "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
        }
    except Exception:
        return None

def send_naver_email(advice):
    # Secrets 값 가져오기 (공백 제거)
    naver_id = os.environ.get('NAVER_ID', '').strip()
    naver_pw = os.environ.get('NAVER_PW', '').strip()
    
    if not naver_id or not naver_pw:
        print("Error: Secrets are empty")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # EmailMessage 사용 (한글 인코딩에 가장 강력함)
    msg = EmailMessage()
    msg['Subject'] = f"[Investment] {today_str} Report"
    msg['From'] = naver_id
    msg['To'] = naver_id
    
    # 본문 구성 (한글 포함)
    content = f"""
오늘의 지침: {advice['action']}
매수금액: ${advice['amount']}
현재 RSI: {advice['rsi']}
남은기간: {advice['days']}일
    """
    msg.set_content(content, charset='utf-8')

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(naver_id, naver_pw)
            server.send_message(msg)
        print(f"Success: Mail sent to {naver_id}")
    except Exception as e:
        # 에러 메시지 출력 시에도 인코딩 에러가 안 나도록 처리
        print(f"Error: {str(e).encode('utf-8', 'ignore')}")

if __name__ == "__main__":
    res = get_advice()
    if res:
        send_naver_email(res)
