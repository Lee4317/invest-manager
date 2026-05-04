import datetime
import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header

def get_advice(total_budget=550):
    # 1. 데이터 수집 (TQQQ 기준)
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(period="30d")
    if df.empty:
        return None
        
    current_price = df['Close'].iloc[-1]
    
    # RSI 계산 (상대강도지수)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    # 2. 날짜 관리
    today = datetime.date.today()
    cpi_date = datetime.date(2026, 5, 12)
    sell_date = datetime.date(2026, 5, 26)
    days_left = (sell_date - today).days

    # 3. 550달러 전액 투입 전략 로직
    if today < cpi_date:
        phase = "1단계: CPI 발표 전 눈치보기 (소액 매수)"
        base_amount = total_budget * 0.04  # 하루 약 $22
    elif today == cpi_date:
        phase = "중요: CPI 성적표 나오는 날 (비중 확대)"
        base_amount = total_budget * 0.15 # 약 $82 집중 투입
    else:
        phase = "2단계: 마무리 투입기 (5/26 매도 준비)"
        base_amount = total_budget * 0.08 # 하루 약 $44

    # 시장 상태에 따른 보정
    if rsi > 70:
        action = "🚨 과열! 오늘은 매수를 쉬고 내일 더 싸게 삽니다."
        final_amount = 0
    elif rsi < 35:
        action = "🔥 기회! 가격이 싸니 계획보다 20% 더 많이 삽니다."
        final_amount = base_amount * 1.2
    else:
        action = "✅ 정상 매수. 정해진 규칙대로 진행하세요."
        final_amount = base_amount

    # 마감 임박 처리
    if 0 < days_left <= 3:
        action = "🏁 전량 투입 단계! 남은 예산을 모두 매수합니다."
        final_amount = base_amount * 1.5

    return {
        "phase": phase, "action": action, "amount": round(final_amount, 2),
        "rsi": round(rsi, 2), "days": days_left, "price": round(current_price, 2)
    }

def send_naver_email(advice):
    # GitHub Secrets에서 아이디/비번 가져오기
    naver_id = os.environ.get('NAVER_ID')
    naver_pw = os.environ.get('NAVER_PW')
    
    if not naver_id or not naver_pw:
        print("오류: GitHub Secrets 환경변수(NAVER_ID, NAVER_PW)를 확인해주세요.")
        return

    smtp_server = "smtp.naver.com"
    smtp_port = 465
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 메일 본문
    msg_content = f"""
안녕하세요! 당신의 $550 투자 매니저입니다.
5월 26일 목표일을 향한 오늘의 행동 지침입니다.

--------------------------------------------------
[오늘의 행동] {advice['action']}
[권장 매수액] ${advice['amount']} (총 예산 $550 중)

분할 매수 가이드:
- TQQQ: ${round(advice['amount']/2, 2)}
- SOXL: ${round(advice['amount']/2, 2)}
--------------------------------------------------

[상세 브리핑]
1. 현재 단계: {advice['phase']}
2. 시장 열기(RSI): {advice['rsi']}
3. 현재 TQQQ 가격: ${advice['price']}
4. 목표일(5/26)까지: {advice['days']}일 남음

* 매니저의 한마디:
감정을 빼고 숫자대로만 움직이세요! 밤 10시 30분에 만나요.
    """

    msg = MIMEText(msg_content, _charset='utf-8')
    msg['Subject'] = Header(f"[{today_str}] 오늘의 $550 투자 지침 보고서", 'utf-8')
    msg['From'] = naver_id
    msg['To'] = naver_id # 본인 수신

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(naver_id, naver_pw)
            server.sendmail(naver_id, naver_id, msg.as_string())
        print(f"[{today_str}] 성공: 보고서 발송 완료.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    advice_result = get_advice()
    if advice_result:
        send_naver_email(advice_result)
