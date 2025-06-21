import sys
import requests
from bs4 import BeautifulSoup
from tkinter import Tk, Label, Entry, Button, messagebox, StringVar, Toplevel
from tkinter.ttk import Treeview
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import matplotlib.pyplot as plt
#import time
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def calculate_ema(prices, period):
    ema = []
    multiplier = 2 / (period + 1)
    ema.append(prices[0])
    for price in prices[1:]:
        ema_value = (price - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_value)
    return ema

def calculate_macd(prices):
    ema_8 = calculate_ema(prices, 8)
    ema_20 = calculate_ema(prices, 20)
    macd_line = [ema_8[i] - ema_20[i] for i in range(len(ema_8))]
    return macd_line, ema_8, ema_20

def get_stock_price_in_inr(symbol):
    for suffix in [":NSE", ":BOM"]:
        try:
            url = f"https://www.google.com/finance/quote/{symbol}{suffix}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            price_element = soup.find('div', {'class': 'YMlKec fxKbKc'})
            price_inr = price_element.text.replace('₹', '').replace(',', '').strip() if price_element else None
            if price_inr:
                return float(price_inr)
        except:
            continue
    messagebox.showerror("Oh No!", f"Couldn't fetch price for {symbol} (NSE & BSE)")
    return None

def get_last_30_days_prices(symbol):
    try:
        data = yf.download(symbol + ".NS", period="1mo", interval="1d", auto_adjust=True)
        if data is None or data.empty:
            raise ValueError("No data returned")
        if 'Close' not in data.columns:
            raise ValueError("No 'Close' column in data")
        close = data['Close']
        # If close is a DataFrame for some reason, pick first column
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        #  close should be a series
        prices = close.values.tolist()   # list of floats
        dates = [dt.strftime('%Y-%m-%d') for dt in close.index]
        return prices, dates
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch last 30 days prices for {symbol}: {e}")
        return None, None

class StockMarketDashboard(Tk):
    def __init__(self):
        super().__init__()
        self.title('Stock Market Dashboard (INR)')
        self.geometry('900x700')
        self.portfolio = {}
        self.initUI()

    def initUI(self):
        Label(self, text="Enter Stock Symbol (NSE):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_symbol = Entry(self)
        self.entry_symbol.grid(row=0, column=1)

        Label(self, text="Enter Number of Shares: ").grid(row=1, column=0, padx=10, pady=10)
        self.entry_shares = Entry(self)
        self.entry_shares.grid(row=1, column=1)

        Button(self, text="Get Price", command=self.display_stock_price).grid(row=0, column=2, padx=10)
        Button(self, text="Add Stock", command=self.add_stock_to_portfolio).grid(row=1, column=2, padx=10)
        Button(self, text="Delete Stock", command=self.delete_stock_from_portfolio).grid(row=1, column=3, padx=10)
        Button(self, text="Show Last 30 Days Prices", command=self.display_last_30_days_prices).grid(row=2, column=0, columnspan=3, pady=10)
        Button(self, text="Show Last 30 Days Chart", command=self.show_last_30_days_chart).grid(row=3, column=0, columnspan=3, pady=10)

        self.label_price = Label(self, text="", font=('Arial', 16))
        self.label_price.grid(row=4, column=0, columnspan=4, pady=10)

        self.portfolio_table = Treeview(self, columns=("symbol", "shares", "price", "total"), show='headings')
        self.portfolio_table.heading("symbol", text="Symbol")
        self.portfolio_table.heading("shares", text="Shares")
        self.portfolio_table.heading("price", text="Price (INR)")
        self.portfolio_table.heading("total", text="Total Value (INR)")
        self.portfolio_table.grid(row=5, column=0, columnspan=4, pady=10)

        self.total_value_var = StringVar()
        self.total_value_var.set("Total Portfolio Value: ₹0.00")
        self.label_total_value = Label(self, textvariable=self.total_value_var, font=('Arial', 14))
        self.label_total_value.grid(row=6, column=0, columnspan=4, pady=10)

        Button(self, text="Visualize Portfolio", command=self.visualize_portfolio).grid(row=7, column=0, columnspan=4, pady=10)

    def display_stock_price(self):
        symbol = self.entry_symbol.get().upper().strip()
        price_inr = get_stock_price_in_inr(symbol)
        if price_inr is not None:
            self.label_price.config(text=f"Current Price: ₹{price_inr}")
        else:
            self.label_price.config(text="Price Not Found")

    def add_stock_to_portfolio(self):
        symbol = self.entry_symbol.get().upper().strip()
        shares_text = self.entry_shares.get().strip()
        if not symbol or not shares_text.isdigit():
            messagebox.showwarning("Input Error", "Enter a valid stock symbol and number of shares.")
            return
        shares = int(shares_text)
        price_inr = get_stock_price_in_inr(symbol)
        if price_inr is None:
            messagebox.showwarning("Error", "Could not fetch stock price.")
            return
        if symbol in self.portfolio:
            self.portfolio[symbol]['shares'] += shares
        else:
            self.portfolio[symbol] = {'shares': shares, 'price': price_inr}
        self.update_portfolio_table()
        self.calculate_total_value()

    def update_portfolio_table(self):
        for item in self.portfolio_table.get_children():
            self.portfolio_table.delete(item)
        for symbol, data in self.portfolio.items():
            total_value = data['shares'] * data['price']
            self.portfolio_table.insert("", "end", values=(symbol, data['shares'], f"₹{data['price']:.2f}", f"₹{total_value:.2f}"))

    def calculate_total_value(self):
        total_value = sum(data['shares'] * data['price'] for data in self.portfolio.values())
        self.total_value_var.set(f"Total Portfolio Value: ₹{total_value:.2f}")

    def visualize_portfolio(self):
        win = Toplevel(self)
        win.title("Portfolio Visualization")
        win.geometry("600x400")
        symbols = list(self.portfolio.keys())
        sizes = [self.portfolio[s]['shares'] * self.portfolio[s]['price'] for s in symbols]
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=symbols, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def display_last_30_days_prices(self):
        symbol = self.entry_symbol.get().upper().strip()
        current_price = get_stock_price_in_inr(symbol)
        current_date = datetime.now().strftime('%Y-%m-%d')
        prices, dates = get_last_30_days_prices(symbol)
        if prices:
            if current_price is not None:
                prices.append(current_price)
                dates.append(current_date)
            win = Toplevel(self)
            win.title(f"Last 30 Days Prices for {symbol}")
            win.geometry("300x600")
            for i in range(len(dates)):
                price = prices[i]
                try:
                    text = f"{dates[i]}: ₹{float(price):.2f}"
                except Exception:
                    text = f"{dates[i]}: {price}"
                Label(win, text=text).pack(pady=2)
        else:
            messagebox.showerror("Error", f"Could not retrieve price data for {symbol}.")

    def show_last_30_days_chart(self):
        symbol = self.entry_symbol.get().upper().strip()
        current_price = get_stock_price_in_inr(symbol)
        current_date = datetime.now().strftime('%Y-%m-%d')
        prices, dates = get_last_30_days_prices(symbol)
        if prices:
            if current_price is not None:
                prices.append(current_price)
                dates.append(current_date)
            # Ensure all prices are floats
            clean_prices = []
            for p in prices:
                try:
                    clean_prices.append(float(p))
                except Exception:
                    clean_prices.append(0.0)
            macd_line, ema_8, ema_20 = calculate_macd(clean_prices)
            win = Toplevel(self)
            win.title(f"Price & MACD Chart for {symbol}")
            win.geometry("600x600")
            fig = Figure(figsize=(6, 6))
            ax1 = fig.add_subplot(211)
            ax1.plot(dates, clean_prices, 'b-o', label="Price")
            ax1.plot(dates, ema_8, 'g-', label="EMA 8")
            ax1.plot(dates, ema_20, 'r-', label="EMA 20")
            ax1.set_title(f"Last 30 Days Prices for {symbol}")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price (INR)")
            ax1.grid(True)
            ax1.legend()
            for label in ax1.get_xticklabels():
                label.set_rotation(45)
                label.set_horizontalalignment('right')
            ax2 = fig.add_subplot(212)
            ax2.plot(dates, macd_line, 'purple')
            ax2.axhline(0, color='gray', linewidth=1)
            ax2.set_title("MACD Indicator")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("MACD Value")
            ax2.grid(True)
            ax2.legend(["MACD Line"])
            for label in ax2.get_xticklabels():
                label.set_rotation(45)
                label.set_horizontalalignment('right')
            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.draw()
            canvas.get_tk_widget().pack()
        else:
            messagebox.showerror("Error", f"Could not retrieve price data for {symbol}.")

    def delete_stock_from_portfolio(self):
        symbol = self.entry_symbol.get().upper().strip()
        shares_text = self.entry_shares.get().strip()
        if not symbol or not shares_text.isdigit():
            messagebox.showwarning("Input Error", "Enter a valid stock symbol and number of shares.")
            return
        shares_to_delete = int(shares_text)
        if symbol not in self.portfolio:
            messagebox.showwarning("Error", "Stock not found in the portfolio.")
            return
        if self.portfolio[symbol]['shares'] < shares_to_delete:
            messagebox.showwarning("Error", "Not enough shares to delete.")
            return
        self.portfolio[symbol]['shares'] -= shares_to_delete
        if self.portfolio[symbol]['shares'] == 0:
            del self.portfolio[symbol]
        self.update_portfolio_table()
        self.calculate_total_value()
        messagebox.showinfo("Success", f"Deleted {shares_to_delete} shares of {symbol} from portfolio.")

if __name__ == '__main__':
    app = StockMarketDashboard()
    app.mainloop()
