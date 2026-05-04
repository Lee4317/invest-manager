import datetime
import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr # 안전한 주소 형식을 위해 추가

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

        if today < cpi_date:
            phase, base_amount = "1단계: CPI 전 소액 매수", total_budget * 0.04
        elif today == cpi_date:
            phase, base_amount = "중요: CPI 발표일 비중 확대", total_budget * 0.15
        else:
            phase, base_amount = "2단계: 마무리 투입기", total_budget * 0.08

        if rsi > 70:
            action, final_amount = "🚨 과열! 오늘 매수 쉼", 0
        elif rsi < 35:
            action, final_amount = "🔥 기회! 20% 추가 매수", base_amount * 1.2
        else:
            action, final_amount = "✅ 정상 매수 진행", base_amount

        if 0 < days_left <= 3:
            action, final_amount = "🏁 전량 투입 단계", base_amount * 1.5

        return {
            "phase": phase, "action": action, "amount": round(final_amount, 2),
            "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
        }
    except Exception as e:
        print(f"데이터 수집 중 오류: {e}")
        return None

def send_naver_email(advice):
    naver_id = os.environ.get('NAVER_ID')
    naver_pw = os.environ.get('NAVER_PW')
    
    if not naver_id or not naver_pw:
        print("❌ 오류: NAVER_ID 또는 NAVER_PW 환경변수를 찾을 수 없습니다.")
        return

    smtp_server = "smtp.naver.com"
    smtp_port = 465
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 메일 본문 구성 (한글이 깨지지 않도록 설정)
    msg_content = f"""
안녕하세요! $550 투자 매니저입니다.
{today_str} 오늘의 행동 지침을 전달합니다.

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

    # MIMEText 생성 시 'utf-8' 명시
    msg = MIMEText(msg_content, 'plain', 'utf-8')
    
    # 제목 인코딩 에러 방지 (Header 클래스 사용)
    msg['Subject'] = Header(f"[{today_str}] 오늘의 $550 투자 지침 보고서", 'utf-8')
    
    # 보낸 사람/받는 사람 설정 (이메일 주소만 깔끔하게 전달)
    msg['From'] = naver_id
    msg['To'] = naver_id 

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(naver_id, naver_pw)
            server.sendmail(naver_id, [naver_id], msg.as_string())
        print(f"✅ [{today_str}] 메일 발송 성공!")
    except Exception as e:
        print(f"❌ 오류: 메일 발송에 실패했습니다. ({e})")

if __name__ == "__main__":
    result = get_advice()
    if result:
        send_naver_email(result)
