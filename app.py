#%%

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO
import time
from datetime import datetime


today = datetime.today().strftime("%Y.%m.%d")
my_header = {'user-agent': 'Mozilla/5.0'}
url_incom = 'https://finance.naver.com/item/sise_day.naver?code=005930&page='

tables = pd.concat([
    pd.read_html(StringIO(requests.get(url_incom + str(p), headers=my_header).text))[0]
    for p in range(1, 11)
])
time.sleep(0.3)

tables.dropna(inplace=True)
tables.rename(columns={'날짜': 'date', '고가': 'highest_price', '저가': 'lowest_price'}, inplace=True)
tables.drop(['전일비', '거래량', '시가', '종가'], axis=1, inplace=True)
tables['median_price'] = (tables['highest_price'] + tables['lowest_price']) / 2
tables.drop(['highest_price', 'lowest_price'], axis=1, inplace=True)

tables['month'] = tables['date'].str[0:7]
tables.set_index('date', inplace=True)
tables.sort_index(inplace=True)
month_avg = tables.groupby('month')['median_price'].mean()
tables.drop(['month'], axis=1, inplace=True)

day_dict = tables['median_price'].to_dict()
month_dict = month_avg.to_dict()


st.title("📈 삼성전자 주가 분석 & 매매 이력 추적")

# --- 초기 현금 입력 ---
initial_cash = st.number_input("현재 보유 현금을 입력하세요", min_value=0, value=1000000, step=10000)

# --- 구매/판매 입력 ---
st.subheader("🟢 매매 이력 입력")
buy_dict, sell_dict = {}, {}

with st.expander("주식 구매 이력 입력"):
    add_buy = st.checkbox("구매 이력 추가")
    if add_buy:
        dates_buy = st.multiselect("구매 날짜 선택", list(day_dict.keys()))
        for d in dates_buy:
            qty = st.number_input(f"{d} 구매 수량", min_value=0, step=1)
            if qty > 0:
                buy_dict[d] = qty

with st.expander("🔴 주식 판매 이력 입력"):
    add_sell = st.checkbox("판매 이력 추가")
    if add_sell:
        dates_sell = st.multiselect("판매 날짜 선택", list(day_dict.keys()))
        for d in dates_sell:
            qty = st.number_input(f"{d} 판매 수량", min_value=0, step=1)
            if qty > 0:
                sell_dict[d] = qty

# -----------------------
# 계산 로직
# -----------------------
buy_total = sum(day_dict[d] * q for d, q in buy_dict.items())
sell_total = sum(day_dict[d] * q for d, q in sell_dict.items())
total_buy_qty = sum(buy_dict.values())
total_sell_qty = sum(sell_dict.values())
quantity_all = total_buy_qty - total_sell_qty
current_value = day_dict.get(today, list(day_dict.values())[-1]) * quantity_all

avg_buy_price = buy_total / total_buy_qty if total_buy_qty > 0 else 0
realized_profit = sum([sell_dict[d] * (day_dict[d] - avg_buy_price) for d in sell_dict])
total_eval = current_value + realized_profit
current_profit_rate = ((total_eval - buy_total) / buy_total * 100) if buy_total > 0 else 0
total_asset = initial_cash + total_eval

# -----------------------
# 결과 출력
# -----------------------
st.subheader("📊 결과 요약")
st.write(f"**총 매입 금액**: {buy_total:,.0f}원")
st.write(f"**실현 손익**: {realized_profit:,.0f}원")
st.write(f"**현재 평가액**: {current_value:,.0f}원")
st.write(f"**현재 수익률**: {current_profit_rate:.2f}%")
st.write(f"**추정 총자산**(보유 현금 포함): {total_asset:,.0f}원")

# -----------------------
# 그래프 시각화
# -----------------------
st.subheader("📉 주가 그래프")
dates = [datetime.strptime(d, "%Y.%m.%d") for d in day_dict.keys()]
prices = list(day_dict.values())

plt.figure(figsize=(12, 6))
plt.plot(dates, prices, label="Median Price", linewidth=2)

if buy_dict:
    buy_dates = [datetime.strptime(d, "%Y.%m.%d") for d in buy_dict.keys()]
    buy_prices = [day_dict[d] for d in buy_dict.keys()]
    plt.scatter(buy_dates, buy_prices, color="green", marker="^", s=100, label="Buy")

if sell_dict:
    sell_dates = [datetime.strptime(d, "%Y.%m.%d") for d in sell_dict.keys()]
    sell_prices = [day_dict[d] for d in sell_dict.keys()]
    plt.scatter(sell_dates, sell_prices, color="red", marker="v", s=100, label="Sell")

plt.title("Stock Price with Buy/Sell Points")
plt.xlabel("Date")
plt.ylabel("Price (KRW)")
plt.legend()
plt.grid(True)
st.pyplot(plt)
# %%
