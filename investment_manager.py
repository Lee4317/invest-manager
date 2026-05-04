import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText

def get_advice(total_budget=550):
    # 1. 데이터 수집 (TQQQ 기준)
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(period="20d")
    current_price = df['Close'][-1]
    
    # RSI 계산
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    # 2. 날짜 관리
    today = datetime.date.today()
    cpi_date = datetime.date(2026, 5, 12)
    sell_date = datetime.date(2026, 5, 26)
    days_to_go = (sell_date - today).days

    # 3. 비중 및 행동 결정
    if today < cpi_date:
        phase = "1단계: CPI 발표 전 눈치보기 (소액 매수)"
        base_amount = total_budget * 0.04 # 하루 약 $22
    else:
        phase = "2단계: CPI 이후 추세 매매 (비중 확대)"
        base_amount = total_budget * 0.08 # 하루 약 $44

    if rsi > 70:
        action = "⚠️ 관망 (시장이 너무 과열되었습니다. 오늘은 사지 마세요!)"
        amount = 0
    elif rsi < 40:
        action = "✅ 적극 매수 (가격이 매력적입니다. 계획보다 더 사도 좋습니다.)"
        amount = base_amount * 1.2
    else:
        action = "🆗 계획대로 매수 (차분하게 비중을 채워가세요.)"
        amount = base_amount

    return {
        "phase": phase, "action": action, "amount": round(amount, 2),
        "rsi": round(rsi, 2), "days": days_to_go, "price": round(current_price, 2)
    }

def send_email(advice):
    # 본인 메일 설정 (기존 뉴스봇 설정과 동일하게)
    sender = "본인메일@gmail.com"
    receiver = "받을메일@gmail.com"
    password = "구글앱비밀번호" 

    msg_content = f"""
    ### 📊 550달러 챌린지: 오늘의 투자 지침 ###
    
    1. 현재 단계: {advice['phase']}
    2. 오늘의 행동: {advice['action']}
    3. **매수 권장 금액: ${advice['amount']}** (TQQQ/SOXL 반반 추천)
    
    - 현재 TQQQ 가격: ${advice['price']}
    - 시장 열기(RSI): {advice['rsi']}
    - 5월 26일 판매까지: {advice['days']}일 남음
    
    * 매니저의 한마디: 감정을 빼고 숫자대로만 움직이세요!
    """
    
    msg = MIMEText(msg_content)
    msg['Subject'] = f"[{today}] 오늘의 투자 행동 지침입니다."
    msg['From'] = sender
    msg['To'] = receiver

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

if __name__ == "__main__":
    advice_data = get_advice()
    send_email(advice_data)
