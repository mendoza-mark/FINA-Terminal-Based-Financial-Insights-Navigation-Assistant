import json
import os
import csv
import re
from datetime import datetime, timedelta
from collections import defaultdict
import shutil

# Matplotlib with backend fallback for no-GUI environments
import matplotlib
try:
    import matplotlib.pyplot as plt
    matplotlib.use('TkAgg')  # Try GUI backend first
except:
    try:
        matplotlib.use('Agg')  # Fallback to non-GUI backend
        print("⚠️  Running in non-GUI mode. Graphs will be saved as files.")
    except:
        pass

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Default data file, but this will change based on who logs in!
DATA_FILE = 'budget_data.json'

# Constants for input validation
MAX_INPUT_LENGTH = 200
MAX_AMOUNT = 999999999.99
MAX_DESCRIPTION_LENGTH = 200

def set_user_file(username):
    """Changes the save file so each user has their own data."""
    global DATA_FILE
    # Sanitize username to prevent path traversal
    safe_username = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    DATA_FILE = f'budget_data_{safe_username}.json'


# --- QUALITY OF LIFE HELPER FUNCTIONS ---
def clear_screen():
    """Clears the terminal screen for a cleaner UI."""
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    """Pauses the program so the user can read messages before the screen clears."""
    input("\nPress Enter to continue...")


def get_float_input(prompt, allow_negative=False, max_value=MAX_AMOUNT):
    """Loops until the user enters a valid, non-negative number, preventing crashes."""
    while True:
        try:
            user_input = input(prompt).strip()
            
            # INPUT VALIDATION: Check length
            if len(user_input) > 50:
                print("❌ Input too long. Please enter a reasonable number.")
                continue
            
            value = float(user_input)
            
            if not allow_negative and value < 0:
                print("❌ Invalid input. Please enter a positive number.")
                continue
            
            # INPUT VALIDATION: Check for insane values
            if abs(value) > max_value:
                print(f"❌ Value too large. Maximum: {max_value:,.2f}")
                continue
            
            return value
        except ValueError:
            print("❌ Invalid input. Please enter numbers only (e.g., 100 or 150.50).")


def get_string_input(prompt, max_length=MAX_INPUT_LENGTH):
    """Gets string input with length validation."""
    while True:
        user_input = input(prompt).strip()
        
        if len(user_input) > max_length:
            print(f"❌ Input too long! Maximum {max_length} characters.")
            continue
        
        return user_input


def get_used_categories(data):
    """Returns a list of unique categories the user has used before."""
    categories = {exp["category"] for exp in data.get("expenses", [])}
    return sorted(list(categories))


# --- DATA HANDLING WITH ERROR HANDLING ---
def load_data():
    """Loads budget data from a JSON file with corruption handling."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
                # Ensure expenses are always sorted by date
                data["expenses"] = sorted(data.get("expenses", []), key=lambda x: x.get("date", ""))
                
                # Ensure all required fields exist
                if "daily_limit" not in data:
                    data["daily_limit"] = 0
                if "expenses" not in data:
                    data["expenses"] = []
                
                return data
        except json.JSONDecodeError:
            # JSON CORRUPTION HANDLER
            print("⚠️  WARNING: Budget data file is corrupted!")
            backup_file = f"{DATA_FILE}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.copy(DATA_FILE, backup_file)
                print(f"Corrupted file backed up as: {backup_file}")
            except:
                pass
            print("✅ Starting with fresh data.")
            pause()
            return {"daily_limit": 0, "expenses": []}
        except Exception as e:
            print(f"⚠️  Error loading data: {e}")
            return {"daily_limit": 0, "expenses": []}
    
    return {"daily_limit": 0, "expenses": []}


def save_data(data):
    """Saves budget data to a JSON file with error handling and auto-backup."""
    try:
        # Keep expenses sorted
        data["expenses"] = sorted(data.get("expenses", []), key=lambda x: x.get("date", ""))
        
        # Create temporary file first
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, 'w') as file:
            json.dump(data, file, indent=4)
        
        # If successful, replace original
        os.replace(temp_file, DATA_FILE)
        return True
    except Exception as e:
        print(f"⚠️  Error saving data: {e}")
        return False


# --- CORE FUNCTIONS ---
def get_today_total(data):
    """Calculates how much has been spent today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(exp["amount"] for exp in data["expenses"] if exp.get("date") == today)


def get_overspend_warning(data):
    """Returns a warning string if daily limit is exceeded, else returns empty string."""
    limit = data.get("daily_limit", 0)
    if limit > 0:
        today_total = get_today_total(data)
        if today_total > limit:
            return (f"⚠️  BUDGET ALERT: Daily Limit Exceeded! "
                    f"Spent ₱{today_total:.2f} / Limit ₱{limit:.2f}")
    return ""


def _draw_expense_table(ax, expenses, title="Expense Details"):
    """Helper: draws a formatted expense table on a given matplotlib axes."""
    ax.axis("off")
    if not expenses:
        ax.text(0.5, 0.5, "No expenses to display.", ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        return

    columns = ["Date", "Category", "Amount (₱)", "Description"]
    cell_text = [
        [exp.get('date', 'N/A'), exp.get('category', 'N/A'), 
         f"₱{exp.get('amount', 0):.2f}", exp.get('description', 'N/A')]
        for exp in expenses
    ]

    tbl = ax.table(cellText=cell_text, colLabels=columns,
                   loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.2, 1.5)

    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#4C72B0')
        elif row % 2 == 0:
            cell.set_facecolor('#EEF2FF')

    ax.set_title(title, fontsize=9, fontweight='bold', pad=5)


def set_daily_limit(data):
    clear_screen()
    print("=" * 60)
    print("              SET/UPDATE DAILY LIMIT")
    print("=" * 60)
    print(f"Current Daily Limit: ₱{data.get('daily_limit', 0):.2f}\n")

    new_limit = get_float_input("Enter new daily limit: ₱")
    data["daily_limit"] = new_limit
    
    if save_data(data):
        print(f"\n✅ Daily limit updated to ₱{new_limit:.2f}")
    else:
        print("\n❌ Failed to save. Please try again.")
    
    pause()


def add_expense(data):
    clear_screen()
    print("=" * 60)
    print("                   ADD EXPENSE")
    print("=" * 60)

    amount = get_float_input("Enter amount spent: ₱")

    # Smart Category Suggestion
    existing_cats = get_used_categories(data)
    if existing_cats:
        print(f"\nPrevious categories: {', '.join(existing_cats)}")

    category = get_string_input("Enter category (e.g. Food, Transpo): ", 50).title()
    desc = get_string_input("Enter short description: ", MAX_DESCRIPTION_LENGTH)

    today = datetime.now().strftime("%Y-%m-%d")

    # Create the expense entry
    expense = {
        "amount": amount,
        "category": category if category else "Uncategorized",
        "description": desc if desc else "No description",
        "date": today,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["expenses"].append(expense)
    
    if save_data(data):
        print(f"\n✅ Successfully added ₱{amount:.2f} for {expense['category']}!")
    else:
        print("\n❌ Failed to save expense.")
        pause()
        return

    # OVERSPENDING CHECK
    limit = data.get("daily_limit", 0)
    if limit > 0:
        today_total = get_today_total(data)
        if today_total > limit:
            print(f"\n⚠️  WARNING: Target Daily Limit Exceeded! ⚠️")
            print(f"Your limit is ₱{limit:.2f}, but you have spent ₱{today_total:.2f} today.")

    pause()


def view_expenses(data):
    """Displays the expense history as a graphical Matplotlib table."""
    clear_screen()
    print("=" * 60)
    print("                 EXPENSE HISTORY")
    print("=" * 60)

    if not data.get("expenses"):
        print("\nNo expenses recorded yet.")
        pause()
        return

    today_total = get_today_total(data)
    print("\nOpening Expense History table in a new window...")
    print("Please close the graphical window to return to the terminal.")

    try:
        columns = ["ID", "Date", "Category", "Amount", "Description"]
        cell_text = []

        for idx, exp in enumerate(data["expenses"]):
            cell_text.append([
                str(idx),
                exp.get('date', 'N/A'),
                exp.get('category', 'N/A'),
                f"₱{exp.get('amount', 0):.2f}",
                exp.get('description', 'N/A')
            ])

        fig_height = max(4, len(data["expenses"]) * 0.4)
        fig, ax = plt.subplots(figsize=(10, fig_height))

        ax.axis("off")
        ax.axis("tight")

        table = ax.table(cellText=cell_text, colLabels=columns,
                         loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#4C72B0')

        # Build title — include overspend warning if applicable
        warning = get_overspend_warning(data)
        title_lines = (
            f"Expense History List\n"
            f"Total Spent Today: ₱{today_total:.2f}  |  "
            f"Daily Limit: ₱{data.get('daily_limit', 0):.2f}"
        )
        if warning:
            title_lines += f"\n🚨 {warning}"

        plt.title(title_lines, fontweight="bold",
                  color='red' if warning else 'black')
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"\n⚠️  Could not display graph: {e}")
        print("Showing text version instead:\n")
        
        # Fallback to text display
        for idx, exp in enumerate(data["expenses"]):
            print(f"{idx}: {exp.get('date', 'N/A')} | {exp.get('category', 'N/A')} | "
                  f"₱{exp.get('amount', 0):.2f} | {exp.get('description', 'N/A')}")
        
        pause()


# --- 🆕 NEW FEATURE: SEARCH EXPENSES ---
def search_expenses(data):
    """Advanced search/filter functionality for expenses."""
    clear_screen()
    print("=" * 60)
    print("              🔍 SEARCH EXPENSES 🔍")
    print("=" * 60)
    
    if not data.get("expenses"):
        print("\nNo expenses to search.")
        pause()
        return
    
    print("\nSearch by:")
    print("1. Category")
    print("2. Date Range")
    print("3. Amount Range")
    print("4. Description (keyword)")
    print("5. Back to Main Menu")
    
    choice = input("\nSelect search type: ").strip()
    
    results = []
    
    if choice == '1':
        # Search by category
        categories = get_used_categories(data)
        if not categories:
            print("\nNo categories found.")
            pause()
            return
        
        print(f"\nAvailable categories: {', '.join(categories)}")
        search_cat = get_string_input("Enter category to search: ", 50).title()
        
        results = [exp for exp in data["expenses"] 
                  if exp.get("category", "").lower() == search_cat.lower()]
        
        search_desc = f"Category: {search_cat}"
    
    elif choice == '2':
        # Search by date range
        print("\nEnter date range (YYYY-MM-DD format)")
        start_date = get_string_input("Start date: ", 20)
        end_date = get_string_input("End date: ", 20)
        
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            
            results = [exp for exp in data["expenses"]
                      if start_date <= exp.get("date", "") <= end_date]
            
            search_desc = f"Date Range: {start_date} to {end_date}"
        except ValueError:
            print("\n❌ Invalid date format!")
            pause()
            return
    
    elif choice == '3':
        # Search by amount range
        min_amount = get_float_input("Minimum amount: ₱", allow_negative=False)
        max_amount = get_float_input("Maximum amount: ₱", allow_negative=False)
        
        results = [exp for exp in data["expenses"]
                  if min_amount <= exp.get("amount", 0) <= max_amount]
        
        search_desc = f"Amount Range: ₱{min_amount:.2f} to ₱{max_amount:.2f}"
    
    elif choice == '4':
        # Search by description keyword
        keyword = get_string_input("Enter keyword: ", 50).lower()
        
        results = [exp for exp in data["expenses"]
                  if keyword in exp.get("description", "").lower() or 
                  keyword in exp.get("category", "").lower()]
        
        search_desc = f"Keyword: {keyword}"
    
    elif choice == '5':
        return
    else:
        print("❌ Invalid choice.")
        pause()
        return
    
    # Display results
    clear_screen()
    print("=" * 60)
    print(f"          SEARCH RESULTS: {search_desc}")
    print("=" * 60)
    
    if not results:
        print("\n❌ No expenses found matching your search.")
        pause()
        return
    
    total = sum(exp.get("amount", 0) for exp in results)
    
    print(f"\nFound {len(results)} expense(s) | Total: ₱{total:.2f}\n")
    print("-" * 60)
    
    for idx, exp in enumerate(results, 1):
        print(f"{idx}. {exp.get('date', 'N/A')} | {exp.get('category', 'N/A')}")
        print(f"   ₱{exp.get('amount', 0):.2f} - {exp.get('description', 'N/A')}")
        print("-" * 60)
    
    pause()


# --- 🆕 NEW FEATURE: BUDGET PREDICTION (AI-ISH) ---
def budget_prediction(data):
    """Predicts future spending based on historical data."""
    clear_screen()
    print("=" * 60)
    print("          🔮 BUDGET PREDICTION (AI MODE) 🔮")
    print("=" * 60)
    
    if not data.get("expenses") or len(data["expenses"]) < 7:
        print("\n⚠️  Insufficient data for prediction!")
        print("Please add at least 7 days of expenses for accurate predictions.")
        pause()
        return
    
    # Calculate daily averages for the last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_expenses = [exp for exp in data["expenses"]
                      if exp.get("date", "") >= thirty_days_ago]
    
    if not recent_expenses:
        print("\n⚠️  No recent expenses found (last 30 days).")
        pause()
        return
    
    # Daily spending analysis
    daily_totals = defaultdict(float)
    for exp in recent_expenses:
        daily_totals[exp.get("date")] += exp.get("amount", 0)
    
    avg_daily_spend = sum(daily_totals.values()) / len(daily_totals) if daily_totals else 0
    
    # Category breakdown
    category_totals = defaultdict(float)
    for exp in recent_expenses:
        category_totals[exp.get("category", "Uncategorized")] += exp.get("amount", 0)
    
    # Calculate predictions
    weekly_prediction = avg_daily_spend * 7
    monthly_prediction = avg_daily_spend * 30
    
    # Trend analysis (comparing first half vs second half of recent data)
    mid_point = len(recent_expenses) // 2
    first_half_avg = sum(e.get("amount", 0) for e in recent_expenses[:mid_point]) / mid_point if mid_point > 0 else 0
    second_half_avg = sum(e.get("amount", 0) for e in recent_expenses[mid_point:]) / (len(recent_expenses) - mid_point) if (len(recent_expenses) - mid_point) > 0 else 0
    
    trend = "increasing" if second_half_avg > first_half_avg * 1.1 else \
            "decreasing" if second_half_avg < first_half_avg * 0.9 else "stable"
    
    # Display predictions
    print("\n📊 SPENDING ANALYSIS (Last 30 Days):")
    print(f"  • Days with expenses: {len(daily_totals)}")
    print(f"  • Total spent: ₱{sum(daily_totals.values()):.2f}")
    print(f"  • Average daily spend: ₱{avg_daily_spend:.2f}")
    print(f"  • Spending trend: {trend.upper()}")
    
    print("\n🔮 PREDICTIONS:")
    print(f"  • Next 7 days (week): ₱{weekly_prediction:.2f}")
    print(f"  • Next 30 days (month): ₱{monthly_prediction:.2f}")
    
    print("\n💡 TOP SPENDING CATEGORIES:")
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    for cat, amount in sorted_categories:
        percentage = (amount / sum(category_totals.values())) * 100 if sum(category_totals.values()) > 0 else 0
        print(f"  • {cat}: ₱{amount:.2f} ({percentage:.1f}%)")
    
    # Smart recommendations based on daily limit
    limit = data.get("daily_limit", 0)
    if limit > 0:
        print("\n⚠️  BUDGET HEALTH CHECK:")
        if avg_daily_spend > limit:
            overage = avg_daily_spend - limit
            print(f"  • You're spending ₱{overage:.2f}/day OVER your limit!")
            print(f"  • Monthly overspending projection: ₱{overage * 30:.2f}")
            print("  • ⚡ RECOMMENDATION: Review your top spending categories")
        elif avg_daily_spend > limit * 0.9:
            print(f"  • You're within 10% of your daily limit")
            print("  • Status: ⚠️  CAUTION - Monitor closely")
        else:
            remaining = limit - avg_daily_spend
            print(f"  • You're averaging ₱{remaining:.2f}/day UNDER your limit!")
            print(f"  • Monthly savings potential: ₱{remaining * 30:.2f}")
            print("  • Status: ✅ EXCELLENT - Keep it up!")
    
    pause()


# --- 🆕 NEW FEATURE: SMART SPENDING ADVICE ---
def smart_spending_advice(data):
    """Provides personalized financial advice based on spending patterns."""
    clear_screen()
    print("=" * 60)
    print("          💡 SMART SPENDING ADVISOR 💡")
    print("=" * 60)
    
    if not data.get("expenses") or len(data["expenses"]) < 3:
        print("\n⚠️  Not enough data to provide advice.")
        print("Add more expenses to receive personalized recommendations!")
        pause()
        return
    
    # Analyze spending patterns
    current_month = datetime.now().strftime("%Y-%m")
    month_expenses = [exp for exp in data["expenses"]
                     if exp.get("date", "").startswith(current_month)]
    
    if not month_expenses:
        print("\n⚠️  No expenses this month yet.")
        pause()
        return
    
    total_month_spent = sum(exp.get("amount", 0) for exp in month_expenses)
    
    # Category analysis
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    for exp in month_expenses:
        cat = exp.get("category", "Uncategorized")
        category_totals[cat] += exp.get("amount", 0)
        category_counts[cat] += 1
    
    # Generate advice
    advice_list = []
    
    # 1. Identify highest spending category
    if category_totals:
        top_category = max(category_totals, key=category_totals.get)
        top_amount = category_totals[top_category]
        top_percentage = (top_amount / total_month_spent) * 100 if total_month_spent > 0 else 0
        
        if top_percentage > 40:
            advice_list.append(
                f"⚠️  '{top_category}' accounts for {top_percentage:.1f}% of your spending "
                f"(₱{top_amount:.2f}). This is quite high! Consider:\n"
                f"   • Setting a specific limit for {top_category}\n"
                f"   • Finding cheaper alternatives\n"
                f"   • Tracking each {top_category} expense more carefully"
            )
    
    # 2. Frequent small purchases warning
    frequent_cats = {cat: count for cat, count in category_counts.items() if count >= 5}
    if frequent_cats:
        for cat, count in frequent_cats.items():
            avg_amount = category_totals[cat] / count
            advice_list.append(
                f"📍 You have {count} '{cat}' transactions this month "
                f"(avg ₱{avg_amount:.2f} each).\n"
                f"   Small frequent purchases add up! Consider:\n"
                f"   • Batch purchases to reduce frequency\n"
                f"   • Set a weekly limit for {cat}"
            )
    
    # 3. Compare to daily limit
    limit = data.get("daily_limit", 0)
    if limit > 0:
        days_in_month = len(set(exp.get("date") for exp in month_expenses))
        avg_daily = total_month_spent / days_in_month if days_in_month > 0 else 0
        
        if avg_daily > limit:
            advice_list.append(
                f"❌ Your average daily spending (₱{avg_daily:.2f}) exceeds your "
                f"limit (₱{limit:.2f})!\n"
                f"   Action items:\n"
                f"   • Review and cut unnecessary expenses\n"
                f"   • Increase your daily limit if it's unrealistic\n"
                f"   • Focus on your top spending category"
            )
        elif avg_daily > limit * 0.9:
            advice_list.append(
                f"⚠️  You're averaging ₱{avg_daily:.2f}/day (90%+ of your ₱{limit:.2f} limit).\n"
                f"   You're cutting it close! Stay vigilant."
            )
        else:
            advice_list.append(
                f"✅ Great job! You're averaging ₱{avg_daily:.2f}/day, well under "
                f"your ₱{limit:.2f} limit.\n"
                f"   Keep up the good work!"
            )
    
    # 4. Weekend vs weekday analysis
    weekend_expenses = []
    weekday_expenses = []
    for exp in month_expenses:
        try:
            date_obj = datetime.strptime(exp.get("date", ""), "%Y-%m-%d")
            if date_obj.weekday() >= 5:  # Saturday or Sunday
                weekend_expenses.append(exp)
            else:
                weekday_expenses.append(exp)
        except:
            pass
    
    if weekend_expenses and weekday_expenses:
        weekend_avg = sum(e.get("amount", 0) for e in weekend_expenses) / len(weekend_expenses)
        weekday_avg = sum(e.get("amount", 0) for e in weekday_expenses) / len(weekday_expenses)
        
        if weekend_avg > weekday_avg * 1.5:
            advice_list.append(
                f"🎉 Your weekend spending (₱{weekend_avg:.2f}/transaction) is "
                f"50%+ higher than weekdays (₱{weekday_avg:.2f}).\n"
                f"   Weekend splurges are fun, but watch out! Consider:\n"
                f"   • Setting a weekend budget\n"
                f"   • Planning free or low-cost weekend activities"
            )
    
    # Display all advice
    print(f"\n📊 Analysis Period: {datetime.now().strftime('%B %Y')}")
    print(f"Total Spent: ₱{total_month_spent:.2f} | Transactions: {len(month_expenses)}")
    print("\n" + "=" * 60)
    
    if advice_list:
        for i, advice in enumerate(advice_list, 1):
            print(f"\n💡 INSIGHT #{i}:")
            print(advice)
            print("-" * 60)
    else:
        print("\n✅ Your spending looks healthy! Keep tracking your expenses.")
    
    pause()


# --- MONTHLY INSIGHTS (ORIGINAL + ENHANCED) ---
def monthly_insights(data):
    """Calculates and displays a smart text-based dashboard for the current month."""
    clear_screen()
    print("=" * 60)
    print("         📊 SMART FINANCIAL INSIGHTS 📊")
    print("=" * 60)

    if not data.get("expenses"):
        print("\nNot enough data to generate insights. Add some expenses first!")
        pause()
        return

    current_month = datetime.now().strftime("%Y-%m")
    month_expenses = [exp for exp in data["expenses"]
                      if exp.get("date", "").startswith(current_month)]

    if not month_expenses:
        print(f"\nNo expenses recorded yet for this month "
              f"({datetime.now().strftime('%B %Y')}).")
        pause()
        return

    total_month_spent = sum(exp.get("amount", 0) for exp in month_expenses)

    # Find most expensive category
    category_totals = defaultdict(float)
    for exp in month_expenses:
        cat = exp.get("category", "Uncategorized")
        category_totals[cat] += exp.get("amount", 0)

    top_category = max(category_totals, key=category_totals.get)

    # Unique days spent
    days_active = len(set(exp.get("date") for exp in month_expenses))
    daily_average = (total_month_spent / days_active
                     if days_active > 0 else total_month_spent)

    print(f"\n📅 Insights for {datetime.now().strftime('%B %Y')}:")
    print(f"  • Total Spent This Month: ₱{total_month_spent:.2f}")
    print(f"  • Number of Transactions: {len(month_expenses)}")
    print(f"  • Highest Spending Area : "
          f"{top_category} (₱{category_totals[top_category]:.2f})")
    print(f"  • Daily Average Spend   : "
          f"₱{daily_average:.2f}/day (across {days_active} active days)")

    limit = data.get("daily_limit", 0)
    if limit > 0:
        if daily_average > limit:
            print("\n⚠️  Trend Warning: Your average daily spending "
                  "exceeds your daily limit!")
        else:
            print("\n✅ Great job! Your average spending is staying "
                  "under your daily limit.")

    pause()


# --- GRAPH GENERATION ---
def graph_menu(data):
    if not data.get("expenses"):
        clear_screen()
        print("\nNot enough data to generate graphs. Add some expenses first!")
        pause()
        return

    while True:
        clear_screen()
        print("=" * 60)
        print("                 GENERATE GRAPHS")
        print("=" * 60)
        print("1. Today's Expense Breakdown (Pie Chart)")
        print("2. Daily Spending Trend (Bar Graph)")
        print("3. Spending Trend by Category (Line Graph)")
        print("4. Export Graph as PNG")
        print("5. Back to Main Menu")

        choice = input("\nSelect an option: ").strip()

        if choice == '1':
            generate_pie_chart(data)
        elif choice == '2':
            generate_bar_graph(data)
        elif choice == '3':
            generate_line_graph(data)
        elif choice == '4':
            export_graph_menu(data)
        elif choice == '5':
            break
        else:
            print("❌ Invalid choice.")
            pause()


def generate_pie_chart(data, save_path=None):
    """Generates pie chart with optional save capability."""
    today = datetime.now().strftime("%Y-%m-%d")
    category_totals = defaultdict(float)
    today_expenses = []

    for exp in data.get("expenses", []):
        if exp.get("date") == today:
            cat = exp.get("category", "Uncategorized")
            category_totals[cat] += exp.get("amount", 0)
            today_expenses.append(exp)

    if not category_totals or sum(category_totals.values()) == 0:
        print(f"\nYou haven't spent anything today ({today}) yet!")
        if not save_path:
            pause()
        return None

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    # Dynamic figure height based on number of expense rows
    table_rows = len(today_expenses)
    fig_height = max(9, 6 + table_rows * 0.35)

    try:
        fig = plt.figure(figsize=(11, fig_height))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1],
                               figure=fig, hspace=0.55)

        # --- PIE CHART ---
        ax_pie = fig.add_subplot(gs[0])
        ax_pie.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        ax_pie.set_title(f"Today's Spending Breakdown ({today})", fontweight='bold')

        # --- OVERSPEND WARNING ---
        warning = get_overspend_warning(data)
        if warning:
            fig.text(0.5, 0.97, f"🚨 {warning}", ha='center', va='top',
                     color='red', fontweight='bold', fontsize=10,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE0E0',
                               edgecolor='red', alpha=0.8))

        # --- EXPENSE TABLE ---
        ax_tbl = fig.add_subplot(gs[1])
        _draw_expense_table(ax_tbl, today_expenses, "Today's Expense Details")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            print("\nPie chart generated! Close the image window to return to the terminal.")
            plt.show()
            return None
    except Exception as e:
        print(f"⚠️  Error generating pie chart: {e}")
        if not save_path:
            pause()
        return None


def generate_pie_chart_for_date(data, target_date, save_path=None):
    """Generates pie chart for a specific date with optional save capability."""
    category_totals = defaultdict(float)
    date_expenses = []

    for exp in data.get("expenses", []):
        if exp.get("date") == target_date:
            cat = exp.get("category", "Uncategorized")
            category_totals[cat] += exp.get("amount", 0)
            date_expenses.append(exp)

    if not category_totals or sum(category_totals.values()) == 0:
        print(f"\nNo expenses found for {target_date}!")
        if not save_path:
            pause()
        return None

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    total_spent = sum(amounts)

    # Dynamic figure height based on number of expense rows
    table_rows = len(date_expenses)
    fig_height = max(9, 6 + table_rows * 0.35)

    try:
        fig = plt.figure(figsize=(11, fig_height))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1],
                               figure=fig, hspace=0.55)

        # --- PIE CHART ---
        ax_pie = fig.add_subplot(gs[0])
        ax_pie.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        ax_pie.set_title(f"Spending Breakdown for {target_date}\nTotal: ₱{total_spent:.2f}", 
                        fontweight='bold')

        # --- EXPENSE TABLE ---
        ax_tbl = fig.add_subplot(gs[1])
        _draw_expense_table(ax_tbl, date_expenses, f"Expense Details - {target_date}")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            print("\nPie chart generated! Close the image window to return to the terminal.")
            plt.show()
            return None
    except Exception as e:
        print(f"⚠️  Error generating pie chart: {e}")
        if not save_path:
            pause()
        return None


def generate_bar_graph(data, save_path=None):
    """Generates bar graph with optional save capability."""
    daily_totals = defaultdict(float)
    for exp in data.get("expenses", []):
        date = exp.get("date")
        daily_totals[date] += exp.get("amount", 0)

    if not daily_totals:
        print("\nNo expense data available.")
        if not save_path:
            pause()
        return None

    sorted_dates = sorted(daily_totals.keys())
    amounts = [daily_totals[date] for date in sorted_dates]

    table_rows = len(data.get("expenses", []))
    fig_height = max(10, 7 + table_rows * 0.30)

    try:
        fig = plt.figure(figsize=(12, fig_height))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1],
                               figure=fig, hspace=0.55)

        # --- BAR CHART ---
        ax_bar = fig.add_subplot(gs[0])
        bars = ax_bar.bar(sorted_dates, amounts, color='skyblue')

        for bar in bars:
            yval = bar.get_height()
            ax_bar.text(bar.get_x() + bar.get_width() / 2, yval,
                        f'₱{yval:.2f}', ha='center', va='bottom', fontsize=8)

        ax_bar.set_xlabel('Date')
        ax_bar.set_ylabel('Total Spent (₱)')
        ax_bar.set_title('Daily Spending Trend', fontweight='bold')
        plt.setp(ax_bar.get_xticklabels(), rotation=45, ha='right')

        # --- OVERSPEND WARNING ---
        warning = get_overspend_warning(data)
        if warning:
            fig.text(0.5, 0.97, f"🚨 {warning}", ha='center', va='top',
                     color='red', fontweight='bold', fontsize=10,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE0E0',
                               edgecolor='red', alpha=0.8))

        # --- EXPENSE TABLE (all records) ---
        ax_tbl = fig.add_subplot(gs[1])
        _draw_expense_table(ax_tbl, data.get("expenses", []), "All Recorded Expenses")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            print("\nBar graph generated! Close the image window to return to the terminal.")
            plt.show()
            return None
    except Exception as e:
        print(f"⚠️  Error generating bar graph: {e}")
        if not save_path:
            pause()
        return None


def generate_line_graph(data, save_path=None):
    """Generates a line graph showing spending over time for a selected category."""
    categories = get_used_categories(data)
    if not categories:
        print("\nNo categories found. Add some expenses first!")
        if not save_path:
            pause()
        return None

    if not save_path:
        clear_screen()
        print("=" * 60)
        print("         LINE GRAPH BY CATEGORY")
        print("=" * 60)
        print("\nAvailable categories:\n")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")

        # Category selection with validation
        while True:
            try:
                choice = int(input("\nSelect a category number: "))
                if 1 <= choice <= len(categories):
                    selected_cat = categories[choice - 1]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(categories)}.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
    else:
        # For auto-export, use the first category
        selected_cat = categories[0]

    # Filter expenses for the selected category
    cat_expenses = [exp for exp in data.get("expenses", [])
                    if exp.get("category") == selected_cat]

    if not cat_expenses:
        print(f"\nNo expenses found for '{selected_cat}'.")
        if not save_path:
            pause()
        return None

    # Aggregate spending by date for the selected category
    daily_totals = defaultdict(float)
    for exp in cat_expenses:
        date = exp.get("date")
        daily_totals[date] += exp.get("amount", 0)

    sorted_dates = sorted(daily_totals.keys())
    amounts = [daily_totals[d] for d in sorted_dates]

    table_rows = len(cat_expenses)
    fig_height = max(10, 7 + table_rows * 0.30)

    try:
        fig = plt.figure(figsize=(12, fig_height))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1],
                               figure=fig, hspace=0.55)

        # --- LINE CHART ---
        ax_line = fig.add_subplot(gs[0])
        ax_line.plot(sorted_dates, amounts, marker='o', color='steelblue',
                     linewidth=2.5, markersize=9, label=selected_cat)
        ax_line.fill_between(sorted_dates, amounts, alpha=0.15, color='steelblue')

        for date, amt in zip(sorted_dates, amounts):
            ax_line.annotate(f'₱{amt:.2f}', (date, amt),
                             textcoords="offset points", xytext=(0, 12),
                             ha='center', fontsize=9, fontweight='bold')

        ax_line.set_xlabel('Date')
        ax_line.set_ylabel('Total Amount Spent (₱)')
        ax_line.set_title(f"Spending Trend for '{selected_cat}'",
                          fontweight='bold')
        ax_line.legend()
        plt.setp(ax_line.get_xticklabels(), rotation=45, ha='right')
        ax_line.grid(axis='y', linestyle='--', alpha=0.5)

        # --- OVERSPEND WARNING ---
        warning = get_overspend_warning(data)
        if warning:
            fig.text(0.5, 0.97, f"🚨 {warning}", ha='center', va='top',
                     color='red', fontweight='bold', fontsize=10,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE0E0',
                               edgecolor='red', alpha=0.8))

        # --- EXPENSE TABLE (filtered by category) ---
        ax_tbl = fig.add_subplot(gs[1])
        _draw_expense_table(ax_tbl, cat_expenses,
                            f"All '{selected_cat}' Expenses")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            print(f"\nLine graph for '{selected_cat}' generated! "
                  "Close the image window to return to the terminal.")
            plt.show()
            return None
    except Exception as e:
        print(f"⚠️  Error generating line graph: {e}")
        if not save_path:
            pause()
        return None


def generate_line_graph_for_category(data, selected_category, save_path=None):
    """Generates a line graph for a specific category with optional save capability."""
    # Filter expenses for the selected category
    cat_expenses = [exp for exp in data.get("expenses", [])
                    if exp.get("category") == selected_category]

    if not cat_expenses:
        print(f"\nNo expenses found for '{selected_category}'.")
        if not save_path:
            pause()
        return None

    # Aggregate spending by date for the selected category
    daily_totals = defaultdict(float)
    for exp in cat_expenses:
        date = exp.get("date")
        daily_totals[date] += exp.get("amount", 0)

    sorted_dates = sorted(daily_totals.keys())
    amounts = [daily_totals[d] for d in sorted_dates]
    total_spent = sum(amounts)

    table_rows = len(cat_expenses)
    fig_height = max(10, 7 + table_rows * 0.30)

    try:
        fig = plt.figure(figsize=(12, fig_height))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1],
                               figure=fig, hspace=0.55)

        # --- LINE CHART ---
        ax_line = fig.add_subplot(gs[0])
        ax_line.plot(sorted_dates, amounts, marker='o', color='steelblue',
                     linewidth=2.5, markersize=9, label=selected_category)
        ax_line.fill_between(sorted_dates, amounts, alpha=0.15, color='steelblue')

        for date, amt in zip(sorted_dates, amounts):
            ax_line.annotate(f'₱{amt:.2f}', (date, amt),
                             textcoords="offset points", xytext=(0, 12),
                             ha='center', fontsize=9, fontweight='bold')

        ax_line.set_xlabel('Date')
        ax_line.set_ylabel('Total Amount Spent (₱)')
        ax_line.set_title(f"Spending Trend for '{selected_category}'\nTotal: ₱{total_spent:.2f}",
                          fontweight='bold')
        ax_line.legend()
        plt.setp(ax_line.get_xticklabels(), rotation=45, ha='right')
        ax_line.grid(axis='y', linestyle='--', alpha=0.5)

        # --- EXPENSE TABLE (filtered by category) ---
        ax_tbl = fig.add_subplot(gs[1])
        _draw_expense_table(ax_tbl, cat_expenses,
                            f"All '{selected_category}' Expenses")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            return save_path
        else:
            print(f"\nLine graph for '{selected_category}' generated! "
                  "Close the image window to return to the terminal.")
            plt.show()
            return None
    except Exception as e:
        print(f"⚠️  Error generating line graph: {e}")
        if not save_path:
            pause()
        return None


# --- 🆕 NEW FEATURE: EXPORT GRAPHS AS PNG ---
def export_graph_menu(data):
    """Menu for exporting graphs as PNG files."""
    clear_screen()
    print("=" * 60)
    print("              📸 EXPORT GRAPH AS PNG")
    print("=" * 60)
    print("\n1. Export Pie Chart (Select Date)")
    print("2. Export Bar Graph (All Daily Trends)")
    print("3. Export Line Graph (Select Category)")
    print("4. Back to Graph Menu")
    
    choice = input("\n➤ Select graph type: ").strip()
    
    if choice == '4':
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if choice == '1':
            # Get available dates with expenses
            dates_with_expenses = sorted(set(exp.get("date") for exp in data.get("expenses", [])))
            
            if not dates_with_expenses:
                print("\n❌ No expenses found to export.")
                pause()
                return
            
            clear_screen()
            print("=" * 60)
            print("         SELECT DATE FOR PIE CHART EXPORT")
            print("=" * 60)
            print("\nAvailable dates:\n")
            
            for i, date in enumerate(dates_with_expenses, 1):
                # Count expenses for that date
                count = sum(1 for exp in data.get("expenses", []) if exp.get("date") == date)
                total = sum(exp.get("amount", 0) for exp in data.get("expenses", []) if exp.get("date") == date)
                print(f"  {i}. {date} ({count} transactions, ₱{total:.2f})")
            
            while True:
                try:
                    date_choice = int(input(f"\n➤ Select date number (1-{len(dates_with_expenses)}): "))
                    if 1 <= date_choice <= len(dates_with_expenses):
                        selected_date = dates_with_expenses[date_choice - 1]
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(dates_with_expenses)}.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
            
            filename = f"FINA_PieChart_{selected_date}_{timestamp}.png"
            result = generate_pie_chart_for_date(data, selected_date, save_path=filename)
            
            if result:
                print(f"\n✅ Pie chart exported successfully!")
                print(f"📁 File: {filename}")
                print(f"📅 Date: {selected_date}")
        
        elif choice == '2':
            filename = f"FINA_BarGraph_{timestamp}.png"
            result = generate_bar_graph(data, save_path=filename)
            if result:
                print(f"\n✅ Bar graph exported successfully!")
                print(f"📁 File: {filename}")
        
        elif choice == '3':
            categories = get_used_categories(data)
            if not categories:
                print("\n❌ No categories found.")
                pause()
                return
            
            clear_screen()
            print("=" * 60)
            print("       SELECT CATEGORY FOR LINE GRAPH EXPORT")
            print("=" * 60)
            print("\nAvailable categories:\n")
            
            for i, cat in enumerate(categories, 1):
                # Count expenses for that category
                count = sum(1 for exp in data.get("expenses", []) if exp.get("category") == cat)
                total = sum(exp.get("amount", 0) for exp in data.get("expenses", []) if exp.get("category") == cat)
                print(f"  {i}. {cat} ({count} transactions, ₱{total:.2f})")
            
            while True:
                try:
                    cat_choice = int(input(f"\n➤ Select category number (1-{len(categories)}): "))
                    if 1 <= cat_choice <= len(categories):
                        selected_category = categories[cat_choice - 1]
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(categories)}.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
            
            filename = f"FINA_LineGraph_{selected_category}_{timestamp}.png"
            result = generate_line_graph_for_category(data, selected_category, save_path=filename)
            
            if result:
                print(f"\n✅ Line graph exported successfully!")
                print(f"📁 File: {filename}")
                print(f"📊 Category: {selected_category}")
        
        else:
            print("❌ Invalid choice.")
    
    except Exception as e:
        print(f"⚠️  Export failed: {e}")
    
    pause()


# --- 🆕 NEW FEATURE: FULL PDF REPORT GENERATION ---
def generate_full_report(data):
    """Generates a comprehensive PDF report with graphs and insights."""
    if not PDF_AVAILABLE:
        clear_screen()
        print("=" * 60)
        print("              📄 PDF REPORT GENERATION")
        print("=" * 60)
        print("\n⚠️  PDF generation requires the 'reportlab' library.")
        print("\nTo enable this feature, install it using:")
        print("  pip install reportlab")
        pause()
        return
    
    clear_screen()
    print("=" * 60)
    print("          📄 GENERATE FULL PDF REPORT")
    print("=" * 60)
    
    if not data.get("expenses"):
        print("\n❌ No data available to generate report.")
        pause()
        return
    
    print("\n⏳ Generating comprehensive PDF report...")
    print("This may take a moment...\n")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"FINA_FullReport_{timestamp}.pdf"
        
        # Generate temporary graph images
        pie_path = f"temp_pie_{timestamp}.png"
        bar_path = f"temp_bar_{timestamp}.png"
        
        print("📊 Generating graphs...")
        generate_pie_chart(data, save_path=pie_path)
        generate_bar_graph(data, save_path=bar_path)
        
        # Create PDF
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4C72B0'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Title
        story.append(Paragraph("FINA Financial Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}",
                              styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Summary Section
        story.append(Paragraph("<b>FINANCIAL SUMMARY</b>", styles['Heading2']))
        
        current_month = datetime.now().strftime("%Y-%m")
        month_expenses = [exp for exp in data["expenses"]
                         if exp.get("date", "").startswith(current_month)]
        
        total_month = sum(exp.get("amount", 0) for exp in month_expenses)
        total_all_time = sum(exp.get("amount", 0) for exp in data["expenses"])
        
        summary_data = [
            ["Metric", "Value"],
            ["Daily Limit", f"₱{data.get('daily_limit', 0):.2f}"],
            ["Total Expenses (This Month)", f"₱{total_month:.2f}"],
            ["Total Expenses (All Time)", f"₱{total_all_time:.2f}"],
            ["Number of Transactions", str(len(data["expenses"]))],
            ["Report Date", datetime.now().strftime("%Y-%m-%d")]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4C72B0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * inch))
        
        # Add graphs
        if os.path.exists(pie_path):
            story.append(Paragraph("<b>Today's Spending Breakdown</b>", styles['Heading2']))
            story.append(Image(pie_path, width=6*inch, height=4*inch))
            story.append(PageBreak())
        
        if os.path.exists(bar_path):
            story.append(Paragraph("<b>Daily Spending Trend</b>", styles['Heading2']))
            story.append(Image(bar_path, width=6*inch, height=4*inch))
            story.append(PageBreak())
        
        # Expense Table
        story.append(Paragraph("<b>DETAILED EXPENSE LIST</b>", styles['Heading2']))
        
        expense_data = [["Date", "Category", "Amount", "Description"]]
        for exp in data["expenses"][-20:]:  # Last 20 expenses
            expense_data.append([
                exp.get('date', 'N/A'),
                exp.get('category', 'N/A'),
                f"₱{exp.get('amount', 0):.2f}",
                exp.get('description', 'N/A')[:30]  # Truncate long descriptions
            ])
        
        expense_table = Table(expense_data)
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4C72B0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(expense_table)
        
        # Build PDF
        doc.build(story)
        
        # Cleanup temporary files
        try:
            if os.path.exists(pie_path):
                os.remove(pie_path)
            if os.path.exists(bar_path):
                os.remove(bar_path)
        except:
            pass
        
        print(f"✅ PDF Report generated successfully!")
        print(f"📁 File: {pdf_filename}")
        
    except Exception as e:
        print(f"⚠️  Error generating PDF: {e}")
    
    pause()


# --- 🆕 NEW FEATURE: BACKUP & RESTORE SYSTEM ---
def backup_restore_menu(data):
    """Menu for backup and restore operations."""
    while True:
        clear_screen()
        print("=" * 60)
        print("          💾 BACKUP & RESTORE SYSTEM")
        print("=" * 60)
        print("\n1. Create Backup")
        print("2. Restore from Backup")
        print("3. List Available Backups")
        print("4. Delete Backup")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            create_backup(data)
        elif choice == '2':
            restore_backup()
        elif choice == '3':
            list_backups()
        elif choice == '4':
            delete_backup()
        elif choice == '5':
            break
        else:
            print("❌ Invalid choice.")
            pause()


def create_backup(data):
    """Creates a backup of current data."""
    clear_screen()
    print("=" * 60)
    print("                 CREATE BACKUP")
    print("=" * 60)
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{DATA_FILE}_{timestamp}.json"
        
        # Create backups directory if it doesn't exist
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Save backup
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"\n✅ Backup created successfully!")
        print(f"📁 Location: {backup_path}")
        print(f"📊 Total expenses backed up: {len(data.get('expenses', []))}")
        
    except Exception as e:
        print(f"\n⚠️  Backup failed: {e}")
    
    pause()


def restore_backup():
    """Restores data from a backup file."""
    clear_screen()
    print("=" * 60)
    print("              RESTORE FROM BACKUP")
    print("=" * 60)
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print("\n❌ No backups folder found.")
        pause()
        return
    
    # List available backups
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    
    if not backups:
        print("\n❌ No backup files found.")
        pause()
        return
    
    print("\nAvailable backups:\n")
    for i, backup in enumerate(backups, 1):
        # Extract timestamp from filename
        try:
            timestamp_str = backup.split('_')[-1].replace('.json', '')
            timestamp_obj = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            readable_date = timestamp_obj.strftime("%B %d, %Y %I:%M %p")
            print(f"  {i}. {backup}")
            print(f"     Created: {readable_date}")
        except:
            print(f"  {i}. {backup}")
    
    print()
    
    try:
        choice = int(input("Select backup number to restore (0 to cancel): "))
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(backups):
            selected_backup = backups[choice - 1]
            backup_path = os.path.join(backup_dir, selected_backup)
            
            # Confirm restoration
            print(f"\n⚠️  WARNING: This will REPLACE your current data with the backup!")
            confirm = input("Type 'RESTORE' to confirm: ").strip()
            
            if confirm == 'RESTORE':
                # Load backup data
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                
                # Save to current data file
                with open(DATA_FILE, 'w') as f:
                    json.dump(backup_data, f, indent=4)
                
                print(f"\n✅ Data restored successfully from backup!")
                print(f"📊 {len(backup_data.get('expenses', []))} expenses restored")
            else:
                print("\n❌ Restoration cancelled.")
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Invalid input.")
    except Exception as e:
        print(f"⚠️  Restoration failed: {e}")
    
    pause()


def list_backups():
    """Lists all available backups with details."""
    clear_screen()
    print("=" * 60)
    print("             AVAILABLE BACKUPS")
    print("=" * 60)
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print("\n❌ No backups folder found.")
        pause()
        return
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    
    if not backups:
        print("\n❌ No backup files found.")
        pause()
        return
    
    print(f"\nFound {len(backups)} backup(s):\n")
    print("-" * 60)
    
    for backup in backups:
        backup_path = os.path.join(backup_dir, backup)
        
        # Get file size
        size = os.path.getsize(backup_path)
        size_kb = size / 1024
        
        # Extract and format timestamp
        try:
            timestamp_str = backup.split('_')[-1].replace('.json', '')
            timestamp_obj = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            readable_date = timestamp_obj.strftime("%B %d, %Y %I:%M %p")
        except:
            readable_date = "Unknown date"
        
        # Try to load and get expense count
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
                expense_count = len(backup_data.get('expenses', []))
        except:
            expense_count = "Unknown"
        
        print(f"📁 {backup}")
        print(f"   Created: {readable_date}")
        print(f"   Size: {size_kb:.2f} KB")
        print(f"   Expenses: {expense_count}")
        print("-" * 60)
    
    pause()


def delete_backup():
    """Deletes a selected backup file."""
    clear_screen()
    print("=" * 60)
    print("                DELETE BACKUP")
    print("=" * 60)
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print("\n❌ No backups folder found.")
        pause()
        return
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    
    if not backups:
        print("\n❌ No backup files found.")
        pause()
        return
    
    print("\nAvailable backups:\n")
    for i, backup in enumerate(backups, 1):
        print(f"  {i}. {backup}")
    
    print()
    
    try:
        choice = int(input("Select backup number to DELETE (0 to cancel): "))
        
        if choice == 0:
            return
        
        if 1 <= choice <= len(backups):
            selected_backup = backups[choice - 1]
            backup_path = os.path.join(backup_dir, selected_backup)
            
            # Confirm deletion
            print(f"\n⚠️  Are you sure you want to delete '{selected_backup}'?")
            confirm = input("Type 'DELETE' to confirm: ").strip()
            
            if confirm == 'DELETE':
                os.remove(backup_path)
                print(f"\n✅ Backup deleted successfully!")
            else:
                print("\n❌ Deletion cancelled.")
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Invalid input.")
    except Exception as e:
        print(f"⚠️  Deletion failed: {e}")
    
    pause()


# --- CALCULATOR (ORIGINAL - UNCHANGED) ---
def calculator():
    """A simple terminal-based financial calculator."""
    history = []
    last_result = None

    while True:
        clear_screen()
        print("=" * 68)
        print("                    FINANCIAL CALCULATOR")
        print("=" * 68)
        print("\n  Format : [number] [operator] [number]\n")
        print("  Operators:")
        print("    +  Addition        -  Subtraction")
        print("    *  Multiply        /  Division")
        print("    %  Percentage      ^  Power/Exponent\n")
        print("  Note  : '%' means 'rate% of number'")
        print("          e.g.  1500 % 12  →  12% of ₱1500\n")
        print("  'ans' : Use last result  |  'history': View log")
        print("  'exit': Return to main menu")
        print("-" * 68)

        if last_result is not None:
            print(f"  Last Result: ₱{last_result:,.2f}")

        print()
        raw = input("  Calc > ").strip()

        if not raw:
            continue

        if raw.lower() == 'exit':
            print("\n  Returning to main menu...")
            pause()
            break

        if raw.lower() == 'history':
            clear_screen()
            print("=" * 60)
            print("            CALCULATION HISTORY")
            print("=" * 60)
            if history:
                for i, entry in enumerate(history, 1):
                    print(f"  {i:>3}. {entry}")
            else:
                print("\n  No calculations yet.")
            pause()
            continue

        # Replace 'ans' keyword with the last result
        if 'ans' in raw.lower():
            if last_result is None:
                print("\n  ❌ No previous result to reference yet.")
                pause()
                continue
            raw = raw.lower().replace('ans', str(last_result))

        # Parse: single number [operator] single number
        pattern = r'^\s*(-?[\d.]+)\s*([+\-*/%^])\s*(-?[\d.]+)\s*$'
        match = re.match(pattern, raw)

        if not match:
            print("\n  ❌ Unrecognized format.")
            print("     Try: 1500 + 300  |  800 * 1.12  |  2000 % 10")
            pause()
            continue

        try:
            a = float(match.group(1))
            op = match.group(2)
            b = float(match.group(3))

            if op == '+':
                result = a + b
                label = f"₱{a:,.2f} + ₱{b:,.2f}"
            elif op == '-':
                result = a - b
                label = f"₱{a:,.2f} - ₱{b:,.2f}"
            elif op == '*':
                result = a * b
                label = f"₱{a:,.2f} × {b}"
            elif op == '/':
                if b == 0:
                    print("\n  ❌ Cannot divide by zero!")
                    pause()
                    continue
                result = a / b
                label = f"₱{a:,.2f} ÷ {b}"
            elif op == '%':
                result = a * (b / 100)
                label = f"{b}% of ₱{a:,.2f}"
            elif op == '^':
                result = a ** b
                label = f"₱{a:,.2f} ^ {b}"
            else:
                print("\n  ❌ Unknown operator.")
                pause()
                continue

            print(f"\n  ✅  {label}  =  ₱{result:,.2f}")
            history.append(f"{label} = ₱{result:,.2f}")
            last_result = result
            pause()

        except OverflowError:
            print("\n  ❌ Result is too large to compute.")
            pause()
        except Exception as e:
            print(f"\n  ❌ Calculation error: {e}")
            pause()


# --- ADMIN / SETTINGS FEATURES ---
def export_to_csv(data):
    """Exports the JSON expense data to a professionally formatted CSV file."""
    if not data.get("expenses"):
        print("\n❌ No data available to export.")
        pause()
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FINA_Export_{timestamp}.csv"

    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # HEADER SECTION
            writer.writerow(["=" * 80])
            writer.writerow(["FINA - FINANCIAL INSIGHTS NAVIGATION ASSISTANT"])
            writer.writerow(["EXPENSE REPORT - COMPREHENSIVE DATA EXPORT"])
            writer.writerow(["=" * 80])
            writer.writerow([])
            
            # METADATA SECTION
            writer.writerow(["REPORT INFORMATION"])
            writer.writerow(["-" * 80])
            writer.writerow(["Generated Date:", datetime.now().strftime("%B %d, %Y")])
            writer.writerow(["Generated Time:", datetime.now().strftime("%I:%M:%S %p")])
            writer.writerow(["Total Records:", len(data["expenses"])])
            writer.writerow(["Daily Limit:", f"₱{data.get('daily_limit', 0):,.2f}"])
            writer.writerow([])
            
            # SUMMARY STATISTICS
            total_amount = sum(exp.get("amount", 0) for exp in data["expenses"])
            avg_amount = total_amount / len(data["expenses"]) if data["expenses"] else 0
            
            # Category breakdown
            category_totals = defaultdict(float)
            for exp in data["expenses"]:
                category_totals[exp.get("category", "Uncategorized")] += exp.get("amount", 0)
            
            top_category = max(category_totals, key=category_totals.get) if category_totals else "N/A"
            top_category_amount = category_totals.get(top_category, 0)
            
            # Date range
            dates = sorted([exp.get("date", "") for exp in data["expenses"]])
            date_range_start = dates[0] if dates else "N/A"
            date_range_end = dates[-1] if dates else "N/A"
            
            writer.writerow(["SUMMARY STATISTICS"])
            writer.writerow(["-" * 80])
            writer.writerow(["Total Amount Spent:", f"₱{total_amount:,.2f}"])
            writer.writerow(["Average Per Transaction:", f"₱{avg_amount:,.2f}"])
            writer.writerow(["Highest Spending Category:", f"{top_category} (₱{top_category_amount:,.2f})"])
            writer.writerow(["Date Range:", f"{date_range_start} to {date_range_end}"])
            writer.writerow(["Number of Categories:", len(category_totals)])
            writer.writerow([])
            
            # CATEGORY BREAKDOWN
            writer.writerow(["SPENDING BY CATEGORY"])
            writer.writerow(["-" * 80])
            writer.writerow(["Category", "Total Amount", "Percentage", "Transaction Count"])
            
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            for cat, amount in sorted_categories:
                count = sum(1 for exp in data["expenses"] if exp.get("category") == cat)
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                writer.writerow([cat, f"₱{amount:,.2f}", f"{percentage:.1f}%", count])
            
            writer.writerow([])
            writer.writerow([])
            
            # DETAILED TRANSACTION LIST
            writer.writerow(["DETAILED TRANSACTION HISTORY"])
            writer.writerow(["=" * 80])
            writer.writerow(["Date", "Category", "Amount", "Description", "Time Recorded"])
            writer.writerow(["-" * 80])
            
            for exp in data["expenses"]:
                writer.writerow([
                    exp.get("date", "N/A"),
                    exp.get("category", "N/A"),
                    f"₱{exp.get('amount', 0):,.2f}",
                    exp.get("description", "N/A"),
                    exp.get("timestamp", "N/A")
                ])
            
            writer.writerow([])
            writer.writerow(["=" * 80])
            writer.writerow(["END OF REPORT"])
            writer.writerow(["=" * 80])
            writer.writerow([])
            writer.writerow(["Generated by FINA - Financial Insights Navigation Assistant"])
            writer.writerow(["Developed by GROUP 2 | BSIT-1203"])
        
        print(f"\n✅ Data successfully exported to: {filename}")
        print(f"📊 Total records: {len(data['expenses'])}")
        print(f"💰 Total amount: ₱{total_amount:,.2f}")
        print("\n📁 You can open this file in:")
        print("   • Microsoft Excel")
        print("   • Google Sheets")
        print("   • Any spreadsheet application")
        
    except Exception as e:
        print(f"\n❌ Failed to export data: {e}")
    
    pause()


def admin_settings(data):
    clear_screen()
    print("=" * 60)
    print("           ADMIN AUTHENTICATION")
    print("=" * 60)

    uname = get_string_input("Username: ", 50)
    pwd = get_string_input("Password: ", 50)

    if uname == "admin" and pwd == "bsit1203":
        print("\n✅ Access Granted. Entering Experimental Admin Mode...")
        pause()

        while True:
            clear_screen()
            print("=" * 60)
            print("      🛠️  EXPERIMENTAL ADMIN MENU 🛠️")
            print("=" * 60)
            print("1. Add Expense (Custom Date - For Graph Demo)")
            print("2. Back to Settings")

            choice = input("\nSelect an option: ").strip()

            if choice == '1':
                add_custom_date_expense(data)
            elif choice == '2':
                break
            else:
                print("❌ Invalid choice.")
                pause()
    else:
        print("\n❌ Access Denied. Invalid Admin Credentials.")
        pause()


def add_custom_date_expense(data):
    clear_screen()
    print("=" * 60)
    print("        ADD EXPENSE (CUSTOM DATE)")
    print("=" * 60)
    print("Note: This bypasses the daily limit warning for demo purposes.\n")

    amount = get_float_input("Enter amount spent: ₱")
    category = get_string_input("Enter category (e.g. Food, Transpo): ", 50).title()
    desc = get_string_input("Enter short description: ", MAX_DESCRIPTION_LENGTH)

    while True:
        date_str = get_string_input("Enter custom date (YYYY-MM-DD): ", 20)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-05-15).")

    expense = {
        "amount": amount,
        "category": category if category else "Uncategorized",
        "description": desc if desc else "Admin Demo Entry",
        "date": date_str,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["expenses"].append(expense)
    
    if save_data(data):
        print(f"\n✅ Successfully injected ₱{amount:.2f} for "
              f"{expense['category']} on {date_str}!")
    else:
        print("\n❌ Failed to save expense.")
    
    pause()


def settings_menu(data):
    while True:
        clear_screen()
        print("=" * 60)
        print("                    SETTINGS")
        print("=" * 60)
        print("1. Edit an Expense")
        print("2. Remove Expenses")
        print("3. Export Data to CSV (Excel)")
        print("4. Backup & Restore System")
        print("5. Generate Full PDF Report")
        print("6. Experimental Admin Settings")
        print("7. Back to Main Menu")

        choice = input("\nSelect an option: ").strip()

        if choice == '1':
            if not data.get("expenses"):
                print("\nNo expenses to edit.")
                pause()
                continue

            view_expenses(data)
            try:
                idx = int(input(
                    "\nEnter the ID number (from the table) of the expense to edit: "))
                if 0 <= idx < len(data["expenses"]):
                    new_amt = get_float_input("Enter corrected amount: ₱")
                    new_cat = get_string_input("Enter corrected category: ", 50).title()
                    data["expenses"][idx]["amount"] = new_amt
                    data["expenses"][idx]["category"] = (
                        new_cat if new_cat else "Uncategorized")
                    
                    if save_data(data):
                        print("✅ Expense updated successfully!")
                    else:
                        print("❌ Failed to save changes.")
                else:
                    print("❌ Invalid ID.")
            except ValueError:
                print("❌ Invalid input. Please enter a whole number for the ID.")
            pause()

        elif choice == '2':
            if not data.get("expenses"):
                print("\nNo expenses to remove.")
                pause()
                continue

            print("\n--- REMOVE EXPENSES ---")
            print("1. Remove a specific expense")
            print("2. Clear ALL expenses")
            rem_choice = input("Select an option: ").strip()

            if rem_choice == '1':
                view_expenses(data)
                try:
                    idx = int(input(
                        "\nEnter the ID number (from the table) of the expense to remove: "))
                    if 0 <= idx < len(data["expenses"]):
                        removed = data["expenses"].pop(idx)
                        if save_data(data):
                            print(f"✅ Removed expense: ₱{removed.get('amount', 0):.2f} "
                                  f"for {removed.get('category', 'N/A')}.")
                        else:
                            print("❌ Failed to save changes.")
                    else:
                        print("❌ Invalid ID.")
                except ValueError:
                    print("❌ Invalid input.")
            elif rem_choice == '2':
                confirm = input(
                    "⚠️  Are you sure you want to delete ALL expenses? "
                    "This cannot be undone! (y/n): ").strip().lower()
                if confirm == 'y':
                    data["expenses"].clear()
                    if save_data(data):
                        print("✅ All expenses have been completely cleared.")
                    else:
                        print("❌ Failed to save changes.")
                else:
                    print("Action cancelled.")
            else:
                print("❌ Invalid choice.")
            pause()

        elif choice == '3':
            export_to_csv(data)

        elif choice == '4':
            backup_restore_menu(data)
            # Reload data after potential restore
            data = load_data()

        elif choice == '5':
            generate_full_report(data)

        elif choice == '6':
            admin_settings(data)

        elif choice == '7':
            break
        else:
            print("❌ Invalid choice.")
            pause()


# --- ABOUT PAGE ---
def about_page():
    clear_screen()
    current_date = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().strftime("%Y")

    print("=" * 68)
    print(" " * 26 + "ABOUT FINA")
    print("=" * 68)
    print(" PROJECT NAME : FINA (Terminal Based Financial Insights")
    print("                Navigation Assistant)")
    print(f" COMPILED     : {current_date} ({current_year})")
    print("-" * 68)
    print(" DESCRIPTION  : FINA is a lightweight, Python-based terminal")
    print("                application designed to help users track")
    print("                daily expenses, monitor budgeting limits,")
    print("                and gain visual insights into their spending")
    print("                patterns using interactive data graphs.")
    print("-" * 68)
    print(" 🆕 NEW FEATURES:")
    print("    • Budget Prediction (AI-powered analytics)")
    print("    • Smart Spending Advisor (Personalized tips)")
    print("    • Advanced Search & Filter")
    print("    • Backup & Restore System")
    print("    • PNG/PDF Export Capabilities")
    print("    • Full PDF Report Generation")
    print("    • Enhanced Security (Password hashing, login limits)")
    print("-" * 68)
    print(" DEVELOPED BY : GROUP 2")
    print("                * Mark Droeid Mendoza")
    print("                * Jhon Mark Unico")
    print("                * Pauleen Pusta")
    print("                * Jhared Louise Chavez")
    print("                * Chyzza Malou Edulza")
    print("                * Janeah Angeles")
    print("                * Ghinger Kaye Reyes")
    print("-" * 68)
    print(" INSTRUCTOR   : * Kyla Andes")
    print("=" * 68)
    pause()


# --- MAIN MENU LOOP ---
def main(username="User"):
    set_user_file(username)
    data = load_data()

    while True:
        clear_screen()
        data = load_data()  # Refresh data at the top of each loop

        print("=" * 68)
        print(" 💰 FINA: Terminal Based Financial Insights Navigation Assistant 💰")
        print(f"                      Logged in as: {username}")

        # --- OVERSPEND WARNING BANNER ---
        warning = get_overspend_warning(data)
        if warning:
            print("-" * 68)
            print(f"  🚨 {warning}")

        print("=" * 68)
        print("\n📋 MAIN MENU")
        print("-" * 68)
        print(" 1.  Add Expense")
        print(" 2.  Set/Update Daily Limit")
        print(" 3.  View Expense History (Table)")
        print(" 4.  Smart Financial Insights (Monthly Summary)")
        print(" 5.  Generate Spending Graphs")
        print(" 6.  🔍 Search Expenses")
        print(" 7.  🔮 Budget Prediction (AI Mode)")
        print(" 8.  💡 Smart Spending Advisor")
        print(" 9.  ⚙️  Settings (Edit, Delete, Export, Backup)")
        print(" 10. 📖 About FINA")
        print(" 11. 🧮 Calculator")
        print(" 12. 🚪 Logout / Exit")
        print("-" * 68)

        choice = input("\n➤ Choose an option (1-12): ").strip()

        if choice == '1':
            add_expense(data)
        elif choice == '2':
            set_daily_limit(data)
        elif choice == '3':
            view_expenses(data)
        elif choice == '4':
            monthly_insights(data)
        elif choice == '5':
            graph_menu(data)
        elif choice == '6':
            search_expenses(data)
        elif choice == '7':
            budget_prediction(data)
        elif choice == '8':
            smart_spending_advice(data)
        elif choice == '9':
            settings_menu(data)
        elif choice == '10':
            about_page()
        elif choice == '11':
            calculator()
        elif choice == '12':
            print("\n💾 Saving data... Logging out. Goodbye!")
            save_data(data)
            break
        else:
            print("\n❌ Invalid choice. Please select a number between 1 and 12.")
            pause()


if __name__ == "__main__":
    main("Guest")