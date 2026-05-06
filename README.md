# 💰 FINA - Financial Insights Navigation Assistant

**FINA** is a powerful, terminal-based personal finance management system designed to help users track daily expenses, monitor budgets, and gain actionable insights into their spending patterns through interactive visualizations and AI-powered analytics.

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Security Features](#-security-features)
- [File Structure](#-file-structure)
- [Technologies Used](#-technologies-used)
- [Screenshots](#-screenshots)
- [Development Team](#-development-team)
- [License](#-license)

---

## 🚀 Features

### Core Functionality
- **Multi-User Support**: Secure authentication system with encrypted passwords (SHA-256 hashing)
- **Expense Tracking**: Add, edit, and delete expense entries with categorization
- **Daily Budget Limits**: Set and monitor daily spending limits with real-time alerts
- **Visual Analytics**: Interactive graphs including pie charts, bar graphs, and line graphs
- **Data Export**: Export data to CSV with comprehensive formatting and summary statistics
- **PDF Reports**: Generate professional PDF reports with graphs and insights

### Advanced Features

#### 🔮 AI-Powered Budget Prediction
- Analyzes spending patterns from the last 30 days
- Predicts weekly and monthly spending based on historical data
- Identifies spending trends (increasing, decreasing, or stable)
- Provides budget health checks against daily limits

#### 💡 Smart Spending Advisor
- Personalized financial recommendations based on spending habits
- Identifies high-spending categories (alerts when >40% of budget)
- Detects frequent small purchases that accumulate
- Analyzes weekend vs. weekday spending patterns
- Provides actionable advice for budget optimization

#### 🔍 Advanced Search System
Search expenses by:
- **Category**: Find all transactions in specific categories
- **Date Range**: Filter expenses between specific dates
- **Amount Range**: Search by minimum and maximum amounts
- **Keywords**: Search descriptions and categories by keyword

#### 💾 Backup & Restore System
- Create timestamped backups of all financial data
- Restore from any previous backup
- View backup details (size, date, expense count)
- Delete old backups to save space
- Automatic corruption recovery

#### 📊 Graph Export Capabilities
- Export pie charts for any date with expenses
- Export bar graphs showing daily spending trends
- Export line graphs for specific categories
- High-resolution PNG output (300 DPI)
- Full PDF reports with multiple graphs and insights

#### 🧮 Financial Calculator
- Built-in calculator for quick financial computations
- Supports: addition, subtraction, multiplication, division, percentages, and exponents
- Calculation history tracking
- Use previous results with 'ans' keyword
- Percentage calculations (e.g., "15% of 1500")

### Security & Safety Features

#### 🔐 Enhanced Security
- **Password Hashing**: SHA-256 encryption for all stored passwords
- **Login Attempt Limiting**: Maximum 3 attempts before temporary lockout
- **Account Lockout**: 5-minute temporary lockout after failed attempts
- **Username Validation**: Prevents path traversal and injection attacks
- **Input Sanitization**: Protection against malicious input

#### 🛡️ Data Protection
- **JSON Corruption Recovery**: Automatic backup and recovery system
- **Atomic File Operations**: Prevents data loss during save operations
- **Input Validation**: Maximum length limits and type checking
- **Sanitized Filenames**: Protection against path traversal attacks

---

## 💻 System Requirements

### Required
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Terminal**: Any terminal with UTF-8 support

### Python Libraries
```bash
# Core Libraries (usually pre-installed)
json
os
csv
re
datetime
collections
shutil
hashlib

# Required External Libraries
matplotlib>=3.5.0

# Optional (for PDF reports)
reportlab>=3.6.0
```

---

## 📦 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/fina-budget-tracker.git
cd fina-budget-tracker
```

### Step 2: Install Dependencies
```bash
# Install required libraries
pip install matplotlib

# Install optional PDF support
pip install reportlab
```

### Step 3: Verify Installation
```bash
python login_system.py
```

---

## 📖 Usage Guide

### First-Time Setup

1. **Run the Application**
   ```bash
   python login_system.py
   ```

2. **Create an Account**
   - Select option `1` (Register New Account)
   - Enter a username (3-20 characters, letters/numbers/underscores/hyphens only)
   - Enter a password (minimum 4 characters)
   - Confirm your password

3. **Login**
   - Select option `2` (Login to Existing Account)
   - Enter your credentials

### Daily Usage

#### Adding Expenses
1. Select `1. Add Expense` from the main menu
2. Enter the amount spent
3. Choose or create a category (suggestions shown)
4. Add a brief description
5. System automatically alerts if daily limit is exceeded

#### Setting Daily Budget
1. Select `2. Set/Update Daily Limit`
2. Enter your daily spending limit
3. System will track and alert you when exceeded

#### Viewing Expenses
1. Select `3. View Expense History`
2. Interactive table displays in a graphical window
3. Shows all transactions with totals and daily limit comparison

#### Generating Graphs
1. Select `5. Generate Spending Graphs`
2. Choose graph type:
   - **Pie Chart**: Today's spending by category
   - **Bar Graph**: Daily spending trends over time
   - **Line Graph**: Category-specific spending trends

#### Exporting Graphs
1. From the graph menu, select `4. Export Graph as PNG`
2. Choose the graph type to export
3. For pie charts: select the date
4. For line graphs: select the category
5. High-resolution PNG saved to current directory

#### Using Search
1. Select `6. Search Expenses`
2. Choose search method:
   - By category
   - By date range
   - By amount range
   - By keyword (searches descriptions and categories)
3. View filtered results with totals

#### Budget Prediction
1. Select `7. Budget Prediction (AI Mode)`
2. View analysis of last 30 days:
   - Average daily spending
   - Spending trend (increasing/decreasing/stable)
   - 7-day and 30-day predictions
   - Top spending categories
   - Budget health check

#### Smart Spending Advisor
1. Select `8. Smart Spending Advisor`
2. Receive personalized insights:
   - High-spending category warnings
   - Frequent purchase alerts
   - Daily limit compliance status
   - Weekend vs. weekday analysis

### Data Management

#### Backup Your Data
1. Go to `9. Settings` → `4. Backup & Restore System`
2. Select `1. Create Backup`
3. Timestamped backup created in `/backups` folder

#### Restore from Backup
1. Go to Settings → Backup & Restore System
2. Select `2. Restore from Backup`
3. Choose backup from list
4. Type `RESTORE` to confirm
5. Data replaced with backup

#### Export to CSV
1. Go to `9. Settings`
2. Select `3. Export Data to CSV`
3. Comprehensive CSV file generated with:
   - Summary statistics
   - Category breakdown
   - Detailed transaction history
   - Metadata and report information

#### Generate PDF Report
1. Go to `9. Settings`
2. Select `5. Generate Full PDF Report`
3. Professional PDF created with:
   - Financial summary
   - Graphs (pie and bar charts)
   - Detailed expense table
   - Statistics and insights

### Admin Features

#### Custom Date Entries (For Testing/Demo)
1. Go to `9. Settings` → `6. Experimental Admin Settings`
2. Login: `username: admin`, `password: bsit1203`
3. Add expenses with custom dates for graph demonstrations

---

## 🔐 Security Features

### Authentication Security
| Feature | Description | Protection Against |
|---------|-------------|-------------------|
| **SHA-256 Password Hashing** | Passwords encrypted before storage | Password theft, database breach |
| **Login Attempt Limiting** | Max 3 failed attempts | Brute force attacks |
| **Temporary Lockout** | 5-minute lockout after failed attempts | Automated attacks |
| **Username Validation** | Alphanumeric + underscore/hyphen only | Path traversal, injection |

### Data Security
| Feature | Description | Protection Against |
|---------|-------------|-------------------|
| **Input Sanitization** | All inputs validated and sanitized | SQL injection, XSS |
| **Path Traversal Prevention** | Filenames sanitized | Directory traversal attacks |
| **JSON Corruption Recovery** | Auto-backup on corruption | Data loss |
| **Atomic File Operations** | Temp files → rename pattern | Partial writes, corruption |
| **Length Limits** | Max input lengths enforced | Buffer overflow, DoS |

### File Security
```
✅ User data isolated per username
✅ No plaintext passwords stored
✅ Automatic backup on corruption
✅ Sanitized filenames prevent path traversal
✅ Input validation prevents overflow
```

---

## 📁 File Structure

```
fina-budget-tracker/
│
├── login_system.py           # User authentication and registration
├── budget_tracker.py          # Main application logic
│
├── users.json                 # User credentials (encrypted)
├── login_attempts.json        # Login attempt tracking
├── budget_data_{username}.json # User-specific expense data
│
├── backups/                   # Backup directory
│   ├── backup_budget_data_{username}_{timestamp}.json
│   └── ...
│
├── FINA_Export_{timestamp}.csv       # CSV exports
├── FINA_PieChart_{date}_{timestamp}.png    # Graph exports
├── FINA_BarGraph_{timestamp}.png
├── FINA_LineGraph_{category}_{timestamp}.png
├── FINA_FullReport_{timestamp}.pdf   # PDF reports
│
└── README.md                  # This file
```

### Key Files Explained

#### `login_system.py`
- Handles user authentication
- Password hashing and validation
- Login attempt tracking
- Account lockout management
- Entry point for the application

#### `budget_tracker.py`
- Core expense tracking functionality
- Graph generation (matplotlib)
- Data analysis and predictions
- Search and filter capabilities
- Export functions (CSV, PNG, PDF)
- Backup and restore system

#### `users.json`
```json
{
  "username": {
    "password": "hashed_password_sha256",
    "created_at": "2025-01-15 10:30:45"
  }
}
```

#### `budget_data_{username}.json`
```json
{
  "daily_limit": 500.00,
  "expenses": [
    {
      "amount": 150.50,
      "category": "Food",
      "description": "Lunch at restaurant",
      "date": "2025-01-15",
      "timestamp": "2025-01-15 12:30:45"
    }
  ]
}
```

---

## 🛠️ Technologies Used

### Core Technologies
- **Python 3.8+**: Primary programming language
- **JSON**: Data storage and serialization
- **CSV**: Data export format

### Libraries & Frameworks

#### Data Visualization
- **Matplotlib 3.5+**: Graph generation (pie, bar, line charts)
- **Matplotlib GridSpec**: Advanced graph layouts

#### PDF Generation (Optional)
- **ReportLab 3.6+**: Professional PDF report creation
- Custom table styling and layouts

#### Security
- **hashlib**: SHA-256 password hashing
- **re (regex)**: Input validation and sanitization

#### Data Processing
- **datetime**: Date/time handling and formatting
- **collections.defaultdict**: Efficient data aggregation
- **shutil**: File operations and backups

---

## 📸 Screenshots

### Main Menu
```
==================================================================
💰 FINA: Terminal Based Financial Insights Navigation Assistant 💰
                      Logged in as: john_doe
==================================================================

📋 MAIN MENU
------------------------------------------------------------------
 1.  Add Expense
 2.  Set/Update Daily Limit
 3.  View Expense History (Table)
 4.  Smart Financial Insights (Monthly Summary)
 5.  Generate Spending Graphs
 6.  🔍 Search Expenses
 7.  🔮 Budget Prediction (AI Mode)
 8.  💡 Smart Spending Advisor
 9.  ⚙️  Settings (Edit, Delete, Export, Backup)
 10. 📖 About FINA
 11. 🧮 Calculator
 12. 🚪 Logout / Exit
------------------------------------------------------------------
```

### Budget Alert Example
```
==================================================================
💰 FINA: Terminal Based Financial Insights Navigation Assistant 💰
                      Logged in as: john_doe
------------------------------------------------------------------
  🚨 ⚠️  BUDGET ALERT: Daily Limit Exceeded! Spent ₱650.00 / Limit ₱500.00
==================================================================
```

### Graph Examples
- **Pie Chart**: Category breakdown with percentages
- **Bar Graph**: Daily spending trends with values
- **Line Graph**: Category-specific trends over time


---

## 👥 Development Team

**GROUP 2 - BSIT-1203**

| Name | Role |
|------|------|
| **Mark Droeid Mendoza** | Lead Developer |
| **Jhon Mark Unico** | Login Page Developer |
| **Pauleen Pusta** | Developer |
| **Jhared Louise Chavez** | Developer |
| **Chyzza Malou Edulza** | Developer |
| **Janeah Angeles** | Developer |
| **Ghinger Kaye Reyes** | Developer |

**Instructor**: Kyla Andes

**Academic Year**: 2025-2026

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **GUI Environment Required for Graphs**: Matplotlib requires a GUI backend. On headless servers, graphs are saved as files instead of displayed.
2. **Single Currency**: Currently hardcoded to Philippine Peso (₱). Multi-currency support planned for future releases.
3. **Local Storage Only**: Data stored locally in JSON files. Cloud sync planned for future versions.

### Compatibility Notes
- **Windows**: Full compatibility ✅
- **macOS**: Full compatibility ✅
- **Linux**: Full compatibility ✅ (may need X11 for graph display)
- **WSL**: Graphs save to files (no display) - use PNG export feature

---

## 📄 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025 GROUP 2 - BSIT-1203

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Support & Contact

### For Academic Inquiries
- **Institution**: Batangas State University - JPLPC Malvar Campus
- **Course**: BSIT-1203
- **Instructor**: Kyla Andes

### For Technical Support
- Open an issue on GitHub
- Contact: markdroeidmendoza@gmail.com

---

## 🙏 Acknowledgments

- **Instructor Kyla Andes** for guidance and support
- **Matplotlib** for powerful visualization capabilities
- **ReportLab** for PDF generation tools
- **Python Community** for excellent documentation
- All beta testers and early users

---

<div align="center">

**Built with ❤️ by GROUP 2. Spearheaded by Mark Droeid Mendoza**

*Making personal finance management accessible and intuitive*


</div>
