# Expense Tracker Remote MCP Server

A comprehensive expense tracking system built as a Model Context Protocol (MCP) server with SSE transport. Track, manage, and analyze your expenses with natural language date parsing and flexible categorization.

## Features

### 🔧 Tools

- **add_expense** - Add a new expense with flexible date parsing (supports "today", "yesterday", "Nov 27", etc.)
- **list_expenses** - List expenses with filtering by category, date range, and limit
- **update_expense** - Update any field of an existing expense
- **delete_expense** - Remove an expense from the database
- **summarize_expenses** - Get expense summaries by category with totals and percentages

### 📋 Resources

- **expense://categories** - Access predefined expense categories and subcategories

### 🎯 Key Capabilities

- Natural language date parsing ("today", "last week", "last 30 days", etc.)
- 20 predefined expense categories with detailed subcategories
- SQLite database for persistent storage
- Flexible filtering by date ranges and categories
- Comprehensive expense summaries with breakdowns

## Categories

The server includes 20 predefined categories:

- Food, Transport, Housing, Utilities, Health
- Education, Family/Kids, Entertainment, Shopping
- Subscriptions, Personal Care, Gifts/Donations
- Finance/Fees, Business, Travel, Home
- Pet, Taxes, Investments, Miscellaneous

Each category has specific subcategories for detailed tracking (see `categories.json`).

## Installation

```bash
pip install -e .
```

Or with uv:

```bash
uv pip install -e .
```

## Usage

### Run the Remote Server

```bash
python main.py
```

Or with uv:

```bash
uv run python main.py
```

The server will start on `http://0.0.0.0:8000` and be accessible via SSE transport.

### Development Mode

Test the server with MCP Inspector:

```bash
uv run fastmcp dev main.py
```

## Connecting to the Server

Configure your MCP client to connect to:

- **URL**: `http://localhost:8000/sse`
- **Transport**: SSE (Server-Sent Events)

## Example Usage

### Add an Expense

```python
add_expense(
    date="today",
    amount=45.50,
    category="food",
    subcategory="groceries",
    note="Weekly grocery shopping"
)
```

### List Recent Expenses

```python
list_expenses(limit=10, date_range="last week")
```

### Get Summary

```python
summarize_expenses(date_range="this month")
```

### Update an Expense

```python
update_expense(expense_id=5, amount=50.00, note="Updated amount")
```

## Database

### Database (FastMCP Cloud note)

On FastMCP Cloud the app runs on ephemeral storage. The server is configured to use a writable temp path when deployed on FastMCP Cloud:

- Database path used on FastMCP Cloud: `/tmp/expense_tracker.db`

The server will automatically initialize the database on startup (or on first tool call) using the included initialization logic.

Expenses are stored in SQLite with the following schema:

```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    note TEXT
)
```

## Dependencies

- fastmcp>=2.13.1
- aiosqlite>=0.20.0 (async SQLite database operations)
- python-dateutil>=2.8.2 (flexible date parsing)

## Technical Details

- Uses `aiosqlite` for asynchronous database operations
- All database operations are non-blocking
- SQLite database for persistent local storage
- Natural language date parsing with `python-dateutil`

## License

MIT
