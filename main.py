from fastmcp import FastMCP
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any
import os
from dateutil import parser
import json

# Create a FastMCP server instance
mcp = FastMCP("Expense Tracker Server")

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")


async def init_database():
    """Initialize the SQLite database with the expenses table."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                note TEXT
            )
        """)
        await conn.commit()


# MCP Resource: Expense Categories
@mcp.resource("expense://categories")
def get_categories_resource() -> str:
    """Provides the list of available expense categories and their subcategories.
    
    This resource exposes the categories.json file as an MCP resource,
    allowing clients to access the predefined expense categories and subcategories.
    """
    try:
        with open(CATEGORIES_PATH, 'r') as f:
            categories = json.load(f)
        
        # Format as a readable string
        result = "📋 Available Expense Categories and Subcategories:\n\n"
        
        for category, subcategories in categories.items():
            # Format category name (replace underscores with spaces, title case)
            formatted_category = category.replace('_', ' ').title()
            result += f"🔹 {formatted_category}:\n"
            
            for subcat in subcategories:
                formatted_subcat = subcat.replace('_', ' ').title()
                result += f"   • {formatted_subcat}\n"
            result += "\n"
        
        return result
    except FileNotFoundError:
        return "❌ Error: categories.json file not found"
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON in categories.json"
    except Exception as e:
        return f"❌ Error loading categories: {str(e)}"


@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> str:
    """Add a new expense to the tracker database.
    
    This tool records a new expense with all relevant details including the date,
    amount spent, category classification, optional subcategory, and notes.
    The date can be in various formats including natural language.
    
    Args:
        date: Date of the expense in any common format (e.g., "2025-11-27", "27th November 2025", "Nov 27, 2025", "today")
        amount: Amount of money spent (e.g., 45.50)
        category: Main category of the expense (e.g., "Food", "Transport", "Entertainment")
        subcategory: Optional subcategory for more detailed classification (e.g., "Groceries", "Gas")
        note: Optional notes or description about the expense
    
    Returns:
        Confirmation message with the expense ID and details
    """
    try:
        # Parse date flexibly using dateutil
        parsed_date = parser.parse(date, fuzzy=True)
        formatted_date = parsed_date.strftime("%Y-%m-%d")
        
        # Connect to database
        async with aiosqlite.connect(DB_PATH) as conn:
            # Insert expense
            cursor = await conn.execute("""
                INSERT INTO expenses (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
            """, (formatted_date, amount, category, subcategory, note))
            
            expense_id = cursor.lastrowid
            await conn.commit()
        
        return f"✅ Expense added successfully!\nID: {expense_id}\nDate: {formatted_date}\nAmount: ${amount:.2f}\nCategory: {category}" + (f"\nSubcategory: {subcategory}" if subcategory else "") + (f"\nNote: {note}" if note else "")
    
    except (ValueError, parser.ParserError):
        return "❌ Error: Could not parse the date. Please provide a valid date (e.g., '2025-11-27', '27th November 2025', or 'today')"
    except Exception as e:
        return f"❌ Error adding expense: {str(e)}"


@mcp.tool()
async def list_expenses(
    limit: int = 10,
    category: str = "",
    date_range: str = "",
    start_date: str = "",
    end_date: str = ""
) -> str:
    """List expenses from the tracker database with optional filtering.
    
    This tool retrieves and displays expenses from the database. You can filter by
    category and date range using natural language or specific dates.
    
    Args:
        limit: Maximum number of expenses to return (default: 10, use 0 for all)
        category: Filter by specific category (optional, e.g., "Food")
        date_range: Natural language date range (optional, e.g., "last week", "last month", "this year", "last 7 days", "last 30 days", "today", "yesterday", "this week", "this month")
        start_date: Filter expenses from this date onwards (optional, any date format like "2025-11-27" or "Nov 27")
        end_date: Filter expenses up to this date (optional, any date format)
    
    Returns:
        Formatted list of expenses with all details, or a message if no expenses found
    """
    try:
        from datetime import timedelta
        
        # Parse date_range if provided
        parsed_start = None
        parsed_end = None
        
        if date_range:
            today = datetime.now()
            date_range_lower = date_range.lower().strip()
            
            if date_range_lower in ["today"]:
                parsed_start = today.strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["yesterday"]:
                yesterday = today - timedelta(days=1)
                parsed_start = yesterday.strftime("%Y-%m-%d")
                parsed_end = yesterday.strftime("%Y-%m-%d")
            elif date_range_lower in ["this week"]:
                start_of_week = today - timedelta(days=today.weekday())
                parsed_start = start_of_week.strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last week"]:
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                end_of_last_week = start_of_last_week + timedelta(days=6)
                parsed_start = start_of_last_week.strftime("%Y-%m-%d")
                parsed_end = end_of_last_week.strftime("%Y-%m-%d")
            elif date_range_lower in ["this month"]:
                parsed_start = today.replace(day=1).strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last month"]:
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                parsed_start = last_month_start.strftime("%Y-%m-%d")
                parsed_end = last_month_end.strftime("%Y-%m-%d")
            elif date_range_lower in ["this year"]:
                parsed_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last year"]:
                last_year = today.year - 1
                parsed_start = f"{last_year}-01-01"
                parsed_end = f"{last_year}-12-31"
            elif "last" in date_range_lower and "days" in date_range_lower:
                # Handle "last X days"
                try:
                    days = int(''.join(filter(str.isdigit, date_range_lower)))
                    start = today - timedelta(days=days)
                    parsed_start = start.strftime("%Y-%m-%d")
                    parsed_end = today.strftime("%Y-%m-%d")
                except:
                    pass
        
        # Parse start_date and end_date if provided
        if start_date and not parsed_start:
            parsed_start = parser.parse(start_date, fuzzy=True).strftime("%Y-%m-%d")
        
        if end_date and not parsed_end:
            parsed_end = parser.parse(end_date, fuzzy=True).strftime("%Y-%m-%d")
        
        # Build query with filters
        query = "SELECT id, date, amount, category, subcategory, note FROM expenses WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if parsed_start:
            query += " AND date >= ?"
            params.append(parsed_start)
        
        if parsed_end:
            query += " AND date <= ?"
            params.append(parsed_end)
        
        query += " ORDER BY date DESC, id DESC"
        
        if limit > 0:
            query += " LIMIT ?"
            params.append(limit)
        
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(query, params)
            expenses = await cursor.fetchall()
        
        if not expenses:
            return "📭 No expenses found matching the criteria."
        
        # Format output
        date_info = ""
        if date_range:
            date_info = f" ({date_range})"
        elif parsed_start and parsed_end:
            date_info = f" ({parsed_start} to {parsed_end})"
        elif parsed_start:
            date_info = f" (from {parsed_start})"
        elif parsed_end:
            date_info = f" (up to {parsed_end})"
        
        result = f"📊 Found {len(expenses)} expense(s){date_info}:\n\n"
        total = 0
        
        for exp in expenses:
            exp_id, date, amount, cat, subcat, note = exp
            total += amount
            result += f"ID: {exp_id} | Date: {date} | Amount: ${amount:.2f}\n"
            result += f"Category: {cat}"
            if subcat:
                result += f" > {subcat}"
            result += "\n"
            if note:
                result += f"Note: {note}\n"
            result += "-" * 50 + "\n"
        
        result += f"\n💰 Total: ${total:.2f}"
        
        return result
    
    except Exception as e:
        return f"❌ Error listing expenses: {str(e)}"


@mcp.tool()
async def update_expense(
    expense_id: int,
    date: str = "",
    amount: float = 0,
    category: str = "",
    subcategory: str = "",
    note: str = ""
) -> str:
    """Update an existing expense in the tracker database.
    
    This tool allows you to modify any field of an existing expense.
    Only provide the fields you want to change - empty/zero values will be ignored.
    
    Args:
        expense_id: The ID of the expense to update (required, get this from list_expenses)
        date: New date for the expense (optional, any date format like "2025-11-27" or "Nov 27")
        amount: New amount (optional, e.g., 45.50)
        category: New category (optional, e.g., "Food")
        subcategory: New subcategory (optional, e.g., "Groceries")
        note: New note/description (optional)
    
    Returns:
        Confirmation message with updated expense details, or error if expense doesn't exist
    """
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # First check if the expense exists
            cursor = await conn.execute("SELECT id, date, amount, category, subcategory, note FROM expenses WHERE id = ?", (expense_id,))
            expense = await cursor.fetchone()
            
            if not expense:
                return f"❌ Error: No expense found with ID {expense_id}"
            
            # Get current values
            old_id, old_date, old_amount, old_category, old_subcategory, old_note = expense
            
            # Build update query for fields that are provided
            updates = []
            params = []
            
            if date:
                # Parse date flexibly
                parsed_date = parser.parse(date, fuzzy=True)
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                updates.append("date = ?")
                params.append(formatted_date)
            
            if amount > 0:
                updates.append("amount = ?")
                params.append(amount)
            
            if category:
                updates.append("category = ?")
                params.append(category)
            
            if subcategory is not None and subcategory != "":
                updates.append("subcategory = ?")
                params.append(subcategory)
            
            if note is not None and note != "":
                updates.append("note = ?")
                params.append(note)
            
            # Check if there's anything to update
            if not updates:
                return "⚠️ No fields provided to update. Please specify at least one field to change."
            
            # Execute update
            params.append(expense_id)
            query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
            await conn.execute(query, params)
            await conn.commit()
            
            # Fetch updated expense
            cursor = await conn.execute("SELECT id, date, amount, category, subcategory, note FROM expenses WHERE id = ?", (expense_id,))
            updated = await cursor.fetchone()
        
        # Format output
        upd_id, upd_date, upd_amount, upd_category, upd_subcategory, upd_note = updated
        
        result = f"✅ Expense updated successfully!\n\n"
        result += f"ID: {upd_id}\n"
        result += f"Date: {upd_date}" + (f" (was: {old_date})" if date and old_date != upd_date else "") + "\n"
        result += f"Amount: ${upd_amount:.2f}" + (f" (was: ${old_amount:.2f})" if amount > 0 and old_amount != upd_amount else "") + "\n"
        result += f"Category: {upd_category}" + (f" (was: {old_category})" if category and old_category != upd_category else "") + "\n"
        if upd_subcategory:
            result += f"Subcategory: {upd_subcategory}\n"
        if upd_note:
            result += f"Note: {upd_note}\n"
        
        return result
    
    except (ValueError, parser.ParserError):
        return "❌ Error: Could not parse the date. Please provide a valid date format."
    except Exception as e:
        return f"❌ Error updating expense: {str(e)}"


@mcp.tool()
async def delete_expense(expense_id: int) -> str:
    """Delete an expense from the tracker database.
    
    This tool permanently removes an expense record from the database.
    Use this when you need to remove an incorrectly added expense or
    clean up old records.
    
    Args:
        expense_id: The ID of the expense to delete (you can get this from list_expenses)
    
    Returns:
        Confirmation message if successful, or error message if the expense doesn't exist
    """
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # First check if the expense exists
            cursor = await conn.execute("SELECT id, date, amount, category FROM expenses WHERE id = ?", (expense_id,))
            expense = await cursor.fetchone()
            
            if not expense:
                return f"❌ Error: No expense found with ID {expense_id}"
            
            # Delete the expense
            await conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            await conn.commit()
        
        exp_id, date, amount, category = expense
        return f"✅ Expense deleted successfully!\nID: {exp_id}\nDate: {date}\nAmount: ${amount:.2f}\nCategory: {category}"
    
    except Exception as e:
        return f"❌ Error deleting expense: {str(e)}"


@mcp.tool()
async def summarize_expenses(
    date_range: str = "",
    start_date: str = "",
    end_date: str = "",
    category: str = ""
) -> str:
    """Summarize expenses with totals grouped by category.
    
    This tool provides a summary of expenses showing total amounts spent per category.
    You can filter by date range using natural language or specific dates, and optionally
    filter by a specific category to see its subcategory breakdown.
    
    Args:
        date_range: Natural language date range (optional, e.g., "last week", "last month", "this year", "last 30 days")
        start_date: Filter expenses from this date onwards (optional, any date format)
        end_date: Filter expenses up to this date (optional, any date format)
        category: Show details for specific category only (optional, e.g., "Food")
    
    Returns:
        Summary of expenses by category with totals and percentages
    """
    try:
        from datetime import timedelta
        
        # Parse date_range if provided (same logic as list_expenses)
        parsed_start = None
        parsed_end = None
        
        if date_range:
            today = datetime.now()
            date_range_lower = date_range.lower().strip()
            
            if date_range_lower in ["today"]:
                parsed_start = today.strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["yesterday"]:
                yesterday = today - timedelta(days=1)
                parsed_start = yesterday.strftime("%Y-%m-%d")
                parsed_end = yesterday.strftime("%Y-%m-%d")
            elif date_range_lower in ["this week"]:
                start_of_week = today - timedelta(days=today.weekday())
                parsed_start = start_of_week.strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last week"]:
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                end_of_last_week = start_of_last_week + timedelta(days=6)
                parsed_start = start_of_last_week.strftime("%Y-%m-%d")
                parsed_end = end_of_last_week.strftime("%Y-%m-%d")
            elif date_range_lower in ["this month"]:
                parsed_start = today.replace(day=1).strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last month"]:
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                parsed_start = last_month_start.strftime("%Y-%m-%d")
                parsed_end = last_month_end.strftime("%Y-%m-%d")
            elif date_range_lower in ["this year"]:
                parsed_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
                parsed_end = today.strftime("%Y-%m-%d")
            elif date_range_lower in ["last year"]:
                last_year = today.year - 1
                parsed_start = f"{last_year}-01-01"
                parsed_end = f"{last_year}-12-31"
            elif "last" in date_range_lower and "days" in date_range_lower:
                try:
                    days = int(''.join(filter(str.isdigit, date_range_lower)))
                    start = today - timedelta(days=days)
                    parsed_start = start.strftime("%Y-%m-%d")
                    parsed_end = today.strftime("%Y-%m-%d")
                except:
                    pass
        
        # Parse start_date and end_date if provided
        if start_date and not parsed_start:
            parsed_start = parser.parse(start_date, fuzzy=True).strftime("%Y-%m-%d")
        
        if end_date and not parsed_end:
            parsed_end = parser.parse(end_date, fuzzy=True).strftime("%Y-%m-%d")
        
        async with aiosqlite.connect(DB_PATH) as conn:
            # Build query
            if category:
                # Show subcategory breakdown for specific category
                query = """
                    SELECT subcategory, SUM(amount) as total, COUNT(*) as count
                    FROM expenses 
                    WHERE category = ?
                """
                params = [category]
                
                if parsed_start:
                    query += " AND date >= ?"
                    params.append(parsed_start)
                
                if parsed_end:
                    query += " AND date <= ?"
                    params.append(parsed_end)
                
                query += " GROUP BY subcategory ORDER BY total DESC"
                
                cursor = await conn.execute(query, params)
                results = await cursor.fetchall()
                
                if not results:
                    return f"📭 No expenses found for category '{category}' in the specified period."
                
                # Calculate total for this category
                grand_total = sum(row[1] for row in results)
                
                # Format output
                date_info = ""
                if date_range:
                    date_info = f" ({date_range})"
                elif parsed_start and parsed_end:
                    date_info = f" ({parsed_start} to {parsed_end})"
                elif parsed_start:
                    date_info = f" (from {parsed_start})"
                elif parsed_end:
                    date_info = f" (up to {parsed_end})"
                
                result = f"📊 Summary for '{category}'{date_info}:\n\n"
                
                for subcat, total, count in results:
                    percentage = (total / grand_total * 100) if grand_total > 0 else 0
                    subcat_name = subcat if subcat else "(No subcategory)"
                    result += f"  {subcat_name}:\n"
                    result += f"    💰 ${total:.2f} ({percentage:.1f}%) - {count} expense(s)\n"
                    result += "-" * 50 + "\n"
                
                result += f"\n🔢 Total for '{category}': ${grand_total:.2f}"
                
            else:
                # Show all categories
                query = """
                    SELECT category, SUM(amount) as total, COUNT(*) as count
                    FROM expenses 
                    WHERE 1=1
                """
                params = []
                
                if parsed_start:
                    query += " AND date >= ?"
                    params.append(parsed_start)
                
                if parsed_end:
                    query += " AND date <= ?"
                    params.append(parsed_end)
                
                query += " GROUP BY category ORDER BY total DESC"
                
                cursor = await conn.execute(query, params)
                results = await cursor.fetchall()
                
                if not results:
                    return "📭 No expenses found in the specified period."
                
                # Calculate grand total
                grand_total = sum(row[1] for row in results)
                
                # Format output
                date_info = ""
                if date_range:
                    date_info = f" ({date_range})"
                elif parsed_start and parsed_end:
                    date_info = f" ({parsed_start} to {parsed_end})"
                elif parsed_start:
                    date_info = f" (from {parsed_start})"
                elif parsed_end:
                    date_info = f" (up to {parsed_end})"
                
                result = f"📊 Expense Summary by Category{date_info}:\n\n"
                
                for cat, total, count in results:
                    percentage = (total / grand_total * 100) if grand_total > 0 else 0
                    result += f"{cat}:\n"
                    result += f"  💰 ${total:.2f} ({percentage:.1f}%) - {count} expense(s)\n"
                    result += "-" * 50 + "\n"
                
                result += f"\n🔢 Grand Total: ${grand_total:.2f}"
        
        return result
    
    except Exception as e:
        return f"❌ Error summarizing expenses: {str(e)}"


if __name__ == "__main__":
    import asyncio
    
    # Initialize database on startup
    asyncio.run(init_database())
    
    # Run the server as a remote MCP server with SSE transport
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
