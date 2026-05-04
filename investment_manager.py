import sys
import io

# 1. 실행 환경의 인코딩을 UTF-8로 강제 고정 (ASCII 에러 원천 차단)
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import datetime
import yfinance as yf
import smtplib
import os
from email.message import EmailMessage

def get_advice(total_budget=550):
    try:
        # TQQQ 데이터 수집
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

        # 투자 전략
        if today < cpi_date:
            phase, base_amount = "1단계: CPI 전 소액 매수", total_budget * 0.04
        elif today == cpi_date:
            phase, base_amount = "중요: CPI 발표일 비중 확대", total_budget * 0.15
        else:
            phase, base_amount = "2단계: 마무리 투입기", total_budget * 0.08

        # RSI 기반 보정
        if rsi > 70:
            action, final_amount = "🚨 과열! 매수 쉼", 0
        elif rsi < 35:
            action, final_amount = "🔥 기회! 추가 매수", base_amount * 1.2
        else:
            action, final_amount = "✅ 정상 매수", base_amount

        return {
            "phase": phase, "action": action, "amount": round(final_amount, 2),
            "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
        }
    except Exception as e:
        print(f"Data processing error: {e}")
        return None

def send_naver_email(advice):
    # 환경변수 읽기 및 공백 제거
    naver_id = os.environ.get('NAVER_ID', '').strip()
    naver_pw = os.environ.get('NAVER_PW', '').strip()
    
    if not naver_id or not naver_pw:
        print("❌ Error: NAVER_ID or NAVER_PW is missing in Secrets.")
        return

    smtp_server = "smtp.naver.com"
    smtp_port = 465
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 최신 EmailMessage 객체 사용
    msg = EmailMessage()
    msg['Subject'] = f"[{today_str}] 오늘의 $550 투자 지침 보고서"
    msg['From'] = naver_id
    msg['To'] = naver_id
    
    msg_content = f"""
안녕하세요! $550 투자 매니저입니다.
{today_str} 오늘의 행동 지침입니다.

--------------------------------------------------
[오늘의 행동] {advice['action']}
[권장 매수액] ${advice['amount']} (TQQQ/SOXL 반반)
--------------------------------------------------

[상세 데이터]
1. 투자 단계: {advice['phase']}
2. 시장 열기(RSI): {advice['rsi']}
3. 현재 TQQQ 가격: ${advice['price']}
4. 목표일(5/26)까지 {advice['days']}일 남았습니다.
    """
    msg.set_content(msg_content)

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(naver_id, naver_pw)
            server.send_message(msg)
        print(f"✅ Success: Email sent to {naver_id}")
    except Exception as e:
        # 에러 메시지 출력 시 발생할 수 있는 인코딩 문제도 방지
        error_msg = str(e).encode('utf-8', 'ignore').decode('utf-8')
        print(f"❌ Error: Failed to send email. ({error_msg})")

if __name__ == "__main__":
    result = get_advice()
    if result:
        send_naver_email(result)
    else:
        print("❌ Error: Could not generate investment advice.")
