import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText

def get_advice(total_budget=550):
    today = datetime.date.today()
    cpi_date = datetime.date(2026, 5, 12)
    sell_date = datetime.date(2026, 5, 26)
    
    # 1. 남은 평일 계산 (대략적)
    days_to_sell = (sell_date - today).days
    
    # 2. 시장 지표 (TQQQ 기준)
    ticker = yf.Ticker("TQQQ")
    # ... (RSI 계산 로직 동일) ...

    # 3. 비중에 따른 매수 금액 설정
    if today < cpi_date:
        # CPI 전에는 천천히 (전체의 약 4%씩)
        daily_amount = total_budget * 0.04 
    elif today == cpi_date:
        # CPI 당일은 승부 (전체의 15%)
        daily_amount = total_budget * 0.15
    else:
        # CPI 이후 마무리 (남은 예산 배분)
        daily_amount = total_budget * 0.08

    # 4. RSI에 따른 행동 보정
    if rsi > 75: # 너무 과열됨
        action = "🚨 과열! 오늘 매수는 쉬고 내일 좀 더 저렴하게 삽니다."
        final_amount = 0
    elif rsi < 35: # 기회!
        action = "🔥 기회! 계획보다 20% 더 많이 삽니다."
        final_amount = daily_amount * 1.2
    else:
        action = "✅ 정상 매수. 약속된 금액만큼 진행하세요."
        final_amount = daily_amount

    return {
        "amount": round(final_amount, 2),
        "action": action,
        "rsi": round(rsi, 2),
        "phase": "CPI 전" if today < cpi_date else "CPI 후/마무리"
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
