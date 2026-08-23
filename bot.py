import os
import requests
import json

# GitHub Secrets에서 텔레그램 정보 불러오기
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ==========================================
# 🎯 [내가 원하는 조건 설정]
# ==========================================
TARGET_MAX_PRICE = 3300   # 월 최대 요금 (3,300원 이하)
TARGET_MIN_DATA = 15      # 최소 기본 데이터 (15GB 이상)
TARGET_MIN_DURATION = 6   # 최소 할인 기간 (6개월 이상)
# ==========================================

def send_telegram_message(text):
    """텔레그램 메시지 발송 함수"""
    if not BOT_TOKEN or not CHAT_ID:
        print("토큰 또는 Chat ID 설정 누락")
        return False
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")
        return False

def check_mvno_plans():
    """알뜰폰 특가 요금제 조회 및 필터링"""
    print("알뜰폰 특가 요금제 탐색 시작...")
    
    api_url = "https://api.moyoplan.com/plans?page=1&amount=50"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    matched_plans = []
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            plans = data.get('data', {}).get('plans', [])
            
            for p in plans:
                name = p.get('name', '')
                carrier = p.get('carrier', {}).get('name', '통신사')
                price = p.get('regularPrice', 99999)
                duration = p.get('discountMonth', 0)
                data_gb = p.get('data', 0) / 1000
                plan_id = p.get('id', '')
                detail_url = f"https://www.moyoplan.com/plans/{plan_id}" if plan_id else "https://www.moyoplan.com"

                if price <= TARGET_MAX_PRICE and data_gb >= TARGET_MIN_DATA and duration >= TARGET_MIN_DURATION:
                    matched_plans.append({
                        "carrier": carrier,
                        "name": name,
                        "price": price,
                        "duration": duration,
                        "data": f"{int(data_gb)}GB",
                        "url": detail_url
                    })
    except Exception as e:
        print(f"API 수집 중 오류: {e}")

    if matched_plans:
        msg = f"🔥 <b>[알뜰폰 특가 요금제 알림]</b>\n"
        msg += f"설정 조건: {TARGET_MAX_PRICE}원 이하 / {TARGET_MIN_DATA}GB 이상 / {TARGET_MIN_DURATION}개월 이상\n\n"
        
        for idx, item in enumerate(matched_plans[:5], 1):
            msg += f"<b>{idx}. [{item['carrier']}] {item['name']}</b>\n"
            msg += f"💰 월 <b>{item['price']:,}원</b> ({item['duration']}개월 할인)\n"
            msg += f"📶 데이터: <b>{item['data']}</b>\n"
            msg += f"👉 <a href='{item['url']}'>상세보기 링크</a>\n\n"
            
        send_telegram_message(msg)
        print(f"발송 완료: {len(matched_plans)}건")
    else:
        print("조건에 맞는 신규 요금제가 없습니다.")

if __name__ == "__main__":
    check_mvno_plans()
