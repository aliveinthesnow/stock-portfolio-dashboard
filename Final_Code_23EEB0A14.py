import sys
import requests
from bs4 import BeautifulSoup
from tkinter import Tk, Label, Entry, Button, messagebox, StringVar, Toplevel
from tkinter.ttk import Treeview
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.dates as mdates

def calculate_ema(prices, period):
    ema = []
    multiplier = 2 / (period + 1)
    ema.append(prices[0])
    for price in prices[1:]:
        ema_value = (price - ema[-1]) * multiplier + ema[-1]
        ema.append(ema_value)
    return ema
def calculate_macd(prices):
    ema_8 = calculate_ema(prices, 9)
    ema_20 = calculate_ema(prices, 20)
    macd_line = []
    for i in range(len(ema_8)):
        macd_line.append(ema_8[i] - ema_20[i])
    return macd_line, ema_8, ema_20
def get_stock_price_in_inr(symbol):
    try:
        url = f"https://www.google.com/finance/quote/{symbol}:NSE"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        price_element = soup.find('div', {'class': 'YMlKec fxKbKc'})
        price_inr = price_element.text.replace('₹', '').replace(',', '').strip() if price_element else None
        return float(price_inr) if price_inr else None
    except Exception:
        messagebox.showerror("Oh No!", f"Didn't find the data online for {symbol}\n")
        return None
def get_last_30_days_prices(symbol):
    try:
        stock = yf.Ticker(symbol + ".NS") #NSE stocks have .NS suffix
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Fetch last 30 days data
        hist = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        return hist['Close'].tolist(), hist.index.strftime('%Y-%m-%d').tolist()
    except Exception:
        messagebox.showerror("Oops", f"Didn't really find anything for {symbol}\n")
        return None, None
class StockMarketDashboard(Tk):
    def __init__(self):
        super().__init__()
        self.title('Stock Market Dashboard (INR)')
        self.geometry('900x700')
        self.portfolio = {}  #mad an empty portfolio dictionary
        self.initUI()
    def initUI(self):
        Label(self, text="Enter Stock Symbol (NSE):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_symbol = Entry(self)
        self.entry_symbol.grid(row=0, column=1)
        Label(self, text="Enter Number of Shares:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_shares = Entry(self)
        self.entry_shares.grid(row=1, column=1)
        #buttons
        Button(self, text="Get Price", command=self.display_stock_price).grid(row=0, column=2, padx=10)
        Button(self, text="Add Stock", command=self.add_stock_to_portfolio).grid(row=1, column=2, padx=10)
        Button(self, text="Delete Stock", command=self.delete_stock_from_portfolio).grid(row=1, column=3,
                                                                                         padx=10)
        Button(self, text="Show Last 30 Days Prices", command=self.display_last_30_days_prices).grid(row=2, column=0,
                                                                                                   columnspan=3,
                                                                                                   pady=10)
        Button(self, text="Show Last 30 Days Chart", command=self.show_last_30_days_chart).grid(row=3, column=0,
                                                                                              columnspan=3, pady=10)
        #stock price
        self.label_price = Label(self, text="", font=('Arial', 16))
        self.label_price.grid(row=4, column=0, columnspan=4, pady=10)
        #portfolio
        self.portfolio_table = Treeview(self, columns=("symbol", "shares", "price", "total"), show='headings')
        self.portfolio_table.heading("symbol", text="Symbol")
        self.portfolio_table.heading("shares", text="Shares")
        self.portfolio_table.heading("price", text="Price (INR)")
        self.portfolio_table.heading("total", text="Total Value (INR)")
        self.portfolio_table.grid(row=5, column=0, columnspan=4, pady=10)
        #total value
        self.total_value_var = StringVar()
        self.total_value_var.set("Total Portfolio Value: ₹0.00")
        self.label_total_value = Label(self, textvariable=self.total_value_var, font=('Arial', 14))
        self.label_total_value.grid(row=6, column=0, columnspan=4, pady=10)
        Button(self, text="Visualize Portfolio", command=self.visualize_portfolio).grid(row=7, column=0, columnspan=4,
                                                                                        pady=10)
    def display_stock_price(self):
        symbol = self.entry_symbol.get().upper()
        price_inr = get_stock_price_in_inr(symbol)
        if price_inr:
            self.label_price.config(text=f"Current Price: ₹{price_inr}")
        else:
            self.label_price.config(text="Price Not Found")
    def add_stock_to_portfolio(self):
        symbol = self.entry_symbol.get().upper()
        shares_text = self.entry_shares.get()
        if (symbol == False or shares_text.isdigit() == False):
            messagebox.showwarning("Input Error", "Enter a valid stock symbol and number of shares.")
            return
        shares = int(shares_text)
        price_inr = get_stock_price_in_inr(symbol)
        if price_inr is None:
            messagebox.showwarning("Error", "Could not fetch stock price.")
            return
        if symbol in self.portfolio:
            self.portfolio[symbol]['shares'] += shares  # Update the number of shares
        else:
            self.portfolio[symbol] = {'shares': shares, 'price': price_inr}
        self.update_portfolio_table()
        self.calculate_total_value()
    def update_portfolio_table(self):
        #clear the table before updating
        for item in self.portfolio_table.get_children():
            self.portfolio_table.delete(item)

        for symbol, data in self.portfolio.items():
            total_value = data['shares'] * data['price']
            self.portfolio_table.insert("", "end",
                                        values=(symbol, data['shares'], f"₹{data['price']:.2f}", f"₹{total_value:.2f}"))
    #2f rounds off to 2 dec places
    def calculate_total_value(self):
        total_value = 0
        for data in self.portfolio.values():
            total_value = total_value + (data['shares'] * data['price'])
        self.total_value_var.set(f"Total Portfolio Value: ₹{total_value:.2f}")
    def visualize_portfolio(self):
        #visualization waali window
        visualization_window = Toplevel(self)
        visualization_window.title("Portfolio Visualization")
        visualization_window.geometry("600x400")
        #data for piechart
        symbols = list(self.portfolio.keys())
        sizes = [self.portfolio[symbol]['shares'] * self.portfolio[symbol]['price'] for symbol in symbols]
        #matplotlib figure
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=symbols, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')#standard code, used for ensuring it is a circle
        #standard code to embed the figure into window
        canvas = FigureCanvasTkAgg(fig, master=visualization_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def display_last_30_days_prices(self):
        symbol = self.entry_symbol.get().upper()
        #take current price
        current_price = get_stock_price_in_inr(symbol)
        current_date = datetime.now().strftime('%Y-%m-%d')
        #30 days ke historical prices
        prices, dates = get_last_30_days_prices(symbol)

        if prices:
            #append current date and price to the lists
            prices.append(current_price)
            dates.append(current_date)
            #new window data dikhane ke liye
            history_window = Toplevel(self)
            history_window.title(f"Last 30 Days Prices for {symbol}")
            history_window.geometry("300x600")

            for i in range(len(dates)):
                date = dates[i]
                price = prices[i]
                Label(history_window, text=f"{date}: ₹{price:.2f}").pack()
        else:
            messagebox.showerror("Error", f"Could not retrieve price data for {symbol}.")
    def show_last_30_days_chart(self):
        symbol = self.entry_symbol.get().upper()
        current_price = get_stock_price_in_inr(symbol)
        current_date = datetime.now().strftime('%Y-%m-%d')
        #historical price 30 days waala
        prices, dates = get_last_30_days_prices(symbol)

        if prices:
            #adding current date and time to list
            prices.append(current_price)
            dates.append(current_date)
            macd_line, ema_8, ema_20 = calculate_macd(prices) #macd waala data
            chart_window = Toplevel(self)
            chart_window.title(f"Price & MACD Chart for {symbol}")
            chart_window.geometry("600x650")
            #making figure
            fig = Figure(figsize=(6, 6))
            #prices and ema made on subplot
            ax1 = fig.add_subplot(211)
            ax1.plot(dates, prices, marker='o', linestyle='-', color='blue', label="Price")
            ax1.plot(dates, ema_8, marker='', linestyle='-', color='green', label="EMA 9")
            ax1.plot(dates, ema_20, marker='', linestyle='-', color='red', label="EMA 20")
            ax1.set_title(f"Last 30 Days Prices for {symbol}")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price in Rupees")
            ax1.grid(True)
            ax1.legend()

            #for only day instead of pura date format
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
            #macd on bottom plot
            ax2 = fig.add_subplot(212)
            ax2.plot(dates, macd_line, marker='', linestyle='-', color='purple', label="MACD Line")
            ax2.axhline(0, color='gray', linewidth=1)  # Add a zero line for MACD
            ax2.set_title("MACD Indicator")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("MACD Value")
            ax2.grid(True)
            ax2.legend()

            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d"))

            #embed code
            canvas = FigureCanvasTkAgg(fig, master=chart_window)
            canvas.draw()
            canvas.get_tk_widget().pack()
        else:
            messagebox.showerror("Error", f"Could not retrieve price data for {symbol}.")
    def delete_stock_from_portfolio(self):
        symbol = self.entry_symbol.get().upper()
        shares_text = self.entry_shares.get()
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

            #edge case if all shares delete ya entire stock remove
        self.portfolio[symbol]['shares'] -= shares_to_delete
        if self.portfolio[symbol]['shares'] == 0:
            del self.portfolio[symbol]
            
        self.update_portfolio_table()
        self.calculate_total_value()
        messagebox.showinfo("Success", f"Deleted {shares_to_delete} shares of {symbol} from portfolio.")

if __name__ == '__main__':
    app = StockMarketDashboard()
    app.mainloop()
