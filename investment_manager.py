import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def get_advice(total_budget=550):
    # 1. 데이터 수집 (시장의 기준이 되는 TQQQ 활용)
    ticker = yf.Ticker("TQQQ")
    # RSI 계산을 위해 충분한 데이터(20일분)를 가져옵니다.
    df = ticker.history(period="30d")
    current_price = df['Close'].iloc[-1]
    
    # 간이 RSI 지표 계산 (상대강도지수)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    # 2. 날짜 및 일정 관리
    today = datetime.date.today()
    cpi_date = datetime.date(2026, 5, 12)    # 중요 지표 발표일
    sell_date = datetime.date(2026, 5, 26)   # 약속된 전량 매도일
    days_left = (sell_date - today).days

    # 3. 비중 및 행동 결정 (550달러 전액 투입 전략)
    if today < cpi_date:
        phase = "1단계: CPI 발표 전 눈치보기 (조금씩 매수)"
        # 5월 12일 전까지는 하루에 예산의 약 4%씩 ($22 내외)
        base_amount = total_budget * 0.04 
    elif today == cpi_date:
        phase = "중요: CPI 성적표 나오는 날 (비중 확대)"
        # 지표 확인 후 결정을 위해 평소보다 더 많은 비중(15%) 할당
        base_amount = total_budget * 0.15
    else:
        phase = "2단계: 마무리 투입기 (5/26 매도 준비)"
        # 남은 예산을 매일 약 8%씩 나누어 투입
        base_amount = total_budget * 0.08

    # 시장 열기(RSI)에 따른 최종 매수 금액 보정
    if rsi > 70:
        action = "🚨 시장이 너무 뜨겁습니다! 오늘은 매수를 쉬고 내일 조금 더 싸게 삽니다."
        final_amount = 0
    elif rsi < 35:
        action = "🔥 기회입니다! 가격이 저렴하니 계획보다 20% 더 많이 삽니다."
        final_amount = base_amount * 1.2
    else:
        action = "✅ 정상 매수일입니다. 정해진 규칙대로 이동하세요."
        final_amount = base_amount

    # 판매일이 임박했다면(3일 전) 남은 예산을 전량 투입하도록 유도
    if 0 < days_left <= 3:
        action = "🏁 마무리 단계입니다. 남은 달러를 모두 주식으로 바꿉니다."
        final_amount = base_amount * 1.5

    return {
        "phase": phase,
        "action": action,
        "amount": round(final_amount, 2),
        "rsi": round(rsi, 2),
        "days": days_left,
        "price": round(current_price, 2)
    }

def send_naver_email(advice):
    # --- [필독] 네이버 설정 정보 ---
    smtp_server = "smtp.naver.com"
    smtp_port = 465
    
    # 본인의 정보로 수정하세요
    naver_id = "본인아이디@naver.com" 
    # 네이버 비밀번호 혹은 생성한 '애플리케이션 비밀번호'
    naver_pw = "네이버_비밀번호_또는_앱비밀번호" 
    
    receiver_email = "본인아이디@naver.com" 
    # ----------------------------

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 메일 본문 (초등학생도 이해하기 쉬운 매니저의 지침)
    msg_content = f"""
안녕하세요! 당신의 전담 투자 매니저입니다.
5월 26일 목표일을 향한 오늘의 행동 지침을 전달합니다.

--------------------------------------------------
[오늘의 행동] {advice['action']}
[권장 매수액] ${advice['amount']} (전체 $550 중 일부)

분할 매수 가이드:
- TQQQ: ${round(advice['amount']/2, 2)} 만큼 매수
- SOXL: ${round(advice['amount']/2, 2)} 만큼 매수
--------------------------------------------------

[상세 브리핑]
1. 현재 단계: {advice['phase']}
2. 시장 열기(RSI): {advice['rsi']} (70 이상 과열 / 30 이하 기회)
3. 현재 TQQQ 가격: ${advice['price']}
4. 목표일(5/26)까지: {advice['days']}일 남음

* 매니저의 한마디:
전체 자산의 33%가 들어가는 중요한 투자입니다. 
밤 10시 30분, 시장이 열리면 위 금액만큼 '기계적으로' 주문을 넣으세요.
오늘의 흔들림에 겁먹지 마세요! 우리는 3주 뒤를 봅니다.
    """

    msg = MIMEText(msg_content, _charset='utf-8')
    msg['Subject'] = Header(f"[{today_str}] 오늘의 $550 투자 지침 보고서", 'utf-8')
    msg['From'] = naver_id
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(naver_id, naver_pw)
            server.sendmail(naver_id, receiver_email, msg.as_string())
        print(f"[{today_str}] 성공: 매니저 보고서가 발송되었습니다.")
    except Exception as e:
        print(f"오류: 메일 발송에 실패했습니다. ({e})")

if __name__ == "__main__":
    # 1. 전략 계산
    advice_result = get_advice()
    # 2. 메일 발송
    send_naver_email(advice_result)
