import streamlit as st
import pandas as pd
import datetime
import os
from openpyxl import Workbook, load_workbook
from zipfile import BadZipFile

# Define file paths for persistence
INVENTORY_FILE = 'inventory.csv'
MENU_FILE = 'menu.csv'
SALES_FILE = 'sales.csv'
EXPENSES_FILE = 'expenses.csv'
REPORT_FILE = 'daily_report.csv'  # New report file for daily summaries
EXCEL_REPORT_FILE = 'daily_report.xlsx'  # Excel file for daily summaries

# Initialize global variables
inventory = {}
menu = {}
sales = pd.DataFrame()
expenses = pd.DataFrame()
milk_used_for_tea = 0.0


# Initialize inventory, menu, sales, and expenses from CSV files
def load_data():
    if os.path.exists(INVENTORY_FILE):
        inventory_df = pd.read_csv(INVENTORY_FILE, index_col=0).to_dict(orient='index')
    else:
        inventory_df = {}
        pd.DataFrame.from_dict(inventory_df, orient='index').to_csv(INVENTORY_FILE)

    if os.path.exists(MENU_FILE) and os.path.getsize(MENU_FILE) > 0:
        menu_df = pd.read_csv(MENU_FILE, index_col=0, on_bad_lines='skip').to_dict(orient='index')
        for key, value in menu_df.items():
            if isinstance(value['items'], str):
                menu_df[key]['items'] = eval(value['items'])
    else:
        menu_df = {
            'Beef and Ugali': {'items': {'BEEF': 0.1, 'UNGA': 0.2}, 'price': 150},
            'Liver and Ugali': {'items': {'LIVER': 0.1, 'UNGA': 0.2}, 'price': 200},
            'Ndengu and 2 Chapatis': {'items': {'NDENGU': 0.2, 'CHAPATI': 2}, 'price': 120},
            'Rice and Ndengu': {'items': {'RICE': 0.2, 'NDENGU': 0.2}, 'price': 120},
            'Rice and Beef': {'items': {'RICE': 0.2, 'BEEF': 0.1}, 'price': 150},
            'Matumbo and Ugali': {'items': {'MATUMBO': 0.1, 'UNGA': 0.2}, 'price': 120},
            'Sukuma and Ugali': {'items': {'SUKUMA': 0.2, 'UNGA': 0.2}, 'price': 120},
            'Cabbage and Ugali': {'items': {'CABBAGE': 0.2, 'UNGA': 0.2}, 'price': 120},
            'Fish and Ugali (200)': {'items': {'FISH': 1, 'UNGA': 0.2}, 'price': 200},
            'Fish and Ugali (250)': {'items': {'FISH': 1, 'UNGA': 0.2}, 'price': 250},
            'Chai and Chapati': {'items': {'MILK': 0.1, 'SUGAR': 0.05, 'CHAPATI': 1}, 'price': 50},
            'Special Chai': {'items': {'MILK': 0.25, 'SUGAR': 0.05}, 'price': 60},
            'Normal Tea': {'items': {'MILK': 0.1, 'SUGAR': 0.05}, 'price': 30},
            'Chapati': {'items': {'CHAPATI': 1}, 'price': 20},
            'Two Fried Eggs': {'items': {'EGGS': 2}, 'price': 80},
            'Fried Eggs and Ugali': {'items': {'EGGS': 2, 'UNGA': 0.2}, 'price': 130},
            'Two Slices of Bread': {'items': {'BREAD': 2}, 'price': 20},
            '300ml Soda': {'items': {'SODA': 1}, 'price': 60},
            'Mineral Water': {'items': {'MINERAL WATER': 1}, 'price': 30}
        }
        pd.DataFrame.from_dict(menu_df, orient='index').to_csv(MENU_FILE)

    sales_df = pd.read_csv(SALES_FILE, index_col=0) if os.path.exists(SALES_FILE) else pd.DataFrame(
        columns=['menu_item', 'quantity', 'total_price', 'payment_mode', 'date'])
    expenses_df = pd.read_csv(EXPENSES_FILE, index_col=0) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(
        columns=['item', 'quantity', 'total_cost', 'category', 'date'])

    return inventory_df, menu_df, sales_df, expenses_df


# Load initial data
inventory, menu, sales, expenses = load_data()


# Function to save data to CSV files
def save_data():
    pd.DataFrame.from_dict(inventory, orient='index').to_csv(INVENTORY_FILE)
    pd.DataFrame.from_dict(menu, orient='index').to_csv(MENU_FILE)
    sales.to_csv(SALES_FILE)
    expenses.to_csv(EXPENSES_FILE)


# Function to add a sale
def add_sale():
    st.markdown("### Log Sale")
    st.write("---")

    selected_combos = st.multiselect("Select Menu Items", options=list(menu.keys()))
    combo_quantities = {combo: st.number_input(f"Quantity of {combo}", min_value=1, value=1, key=combo)
                        for combo in selected_combos}

    payment_mode = st.selectbox("Payment Mode", options=['cash', 'till', 'pochi'])
    sale_date = st.date_input("Sale Date", value=datetime.date.today())

    total_price = sum(quantity * menu[combo]['price'] for combo, quantity in combo_quantities.items())
    st.markdown(f"**Total Price: {total_price} KES**")

    if st.button("Submit Sale"):
        global milk_used_for_tea  # To modify the milk usage

        for combo, quantity in combo_quantities.items():
            if combo == 'Chai and Chapati':
                milk_needed = 0.1 * quantity  # 0.1 liters per cup of tea
                if milk_used_for_tea + milk_needed > 1.0:
                    st.error("Not enough milk prepared for tea.")
                    return
                milk_used_for_tea += milk_needed

            for item, required_quantity in menu[combo]['items'].items():
                if item in inventory and inventory[item]['quantity'] < required_quantity * quantity:
                    st.warning(f"Warning: Not enough {item} in stock for {combo}. Proceeding with sale.")
                inventory[item]['quantity'] -= required_quantity * quantity

        global sales
        for combo, quantity in combo_quantities.items():
            if quantity > 0:  # Only log if the quantity is positive
                new_sale = pd.DataFrame({
                    'menu_item': [combo],
                    'quantity': [quantity],
                    'total_price': [quantity * menu[combo]['price']],
                    'payment_mode': [payment_mode],
                    'date': [sale_date]
                })
                sales = pd.concat([sales, new_sale], ignore_index=True)

        save_data()  # Save to CSV
        st.success(
            f"Sale logged for {', '.join([f'{quantity} x {combo}' for combo, quantity in combo_quantities.items()])}")


# Function to log an expense
def add_expense():
    global expenses
    st.markdown("### Log an Expense")
    st.write("---")
    category = st.selectbox("Expense Category", options=['restocking', 'bills', 'rent', 'taxes', 'other'])

    if category == 'restocking':
        item = st.text_input("Enter Item to Restock")
        quantity = st.number_input(f"Quantity of {item} to restock", min_value=1)
        unit = st.selectbox("Unit", options=['units', 'kg', 'litres'])
        total_cost = st.number_input("Total Restocking Cost", min_value=0.0, format="%.2f",
                                     value=float(quantity) * 0.0)  # Ensure value is a float
        expense_date = st.date_input("Restocking Date", value=datetime.date.today())

        if st.button("Submit Restocking Expense"):
            # Check if item is in inventory
            if item in inventory:
                inventory[item]['quantity'] += quantity
            else:
                # Add new item to inventory
                inventory[item] = {'quantity': quantity, 'unit': unit,
                                   'price_per_unit': total_cost / quantity if quantity > 0 else 0}
            new_expense = pd.DataFrame({
                'item': [item],
                'quantity': [quantity],
                'total_cost': [total_cost],
                'category': [category],
                'date': [expense_date]
            })
            expenses = pd.concat([expenses, new_expense], ignore_index=True)

            save_data()  # Save to CSV
            st.success(f"Restocked {quantity} units of {item}")

    else:
        item = st.text_input("Enter Expense Item")
        total_cost = st.number_input("Total Cost of Expense", min_value=0.0, format="%.2f")
        expense_date = st.date_input("Expense Date", value=datetime.date.today())

        if st.button("Submit Expense"):
            new_expense = pd.DataFrame({
                'item': [item],
                'quantity': [0],
                'total_cost': [total_cost],
                'category': [category],
                'date': [expense_date]
            })
            expenses = pd.concat([expenses, new_expense], ignore_index=True)

            save_data()  # Save to CSV
            st.success(f"Logged expense for {item} of KES {total_cost:.2f}")


# Function to view sales
def view_sales():
    st.markdown("### View Sales")
    st.write("---")
    if not sales.empty:
        st.dataframe(sales)
    else:
        st.warning("No sales recorded.")


# Function to view expenses
def view_expenses():
    st.markdown("### View Expenses")
    st.write("---")
    if not expenses.empty:
        st.dataframe(expenses)
    else:
        st.warning("No expenses recorded.")


# Function to view inventory
def view_inventory():
    st.markdown("### View Inventory")
    st.write("---")
    inventory_df = pd.DataFrame.from_dict(inventory, orient='index')
    st.dataframe(inventory_df)


# Function to generate a daily report
def generate_daily_report():
    st.markdown("### Generate Daily Report")
    st.write("---")
    report_date = st.date_input("Select Date for Report", value=datetime.date.today())

    if st.button("Generate Report"):
        daily_sales = sales[sales['date'] == str(report_date)]
        daily_expenses = expenses[expenses['date'] == str(report_date)]
        total_sales = daily_sales['total_price'].sum()
        total_expenses = daily_expenses['total_cost'].sum()
        profit = total_sales - total_expenses

        report_data = {
            'Date': [report_date],
            'Total Sales': [total_sales],
            'Total Expenses': [total_expenses],
            'Profit/Loss': [profit]
        }
        report_df = pd.DataFrame(report_data)

        # Create or load the daily report CSV
        if os.path.exists(REPORT_FILE):
            existing_report = pd.read_csv(REPORT_FILE)
            report_df = pd.concat([existing_report, report_df], ignore_index=True)

        report_df.to_csv(REPORT_FILE, index=False)
        st.success("Daily report generated successfully!")

        # Generate Excel report
        if os.path.exists(EXCEL_REPORT_FILE):
            with pd.ExcelWriter(EXCEL_REPORT_FILE, engine='openpyxl', mode='a') as writer:
                workbook = writer.book
                report_df.to_excel(writer, index=False, header=False, startrow=len(workbook.sheetnames) + 1)
        else:
            report_df.to_excel(EXCEL_REPORT_FILE, index=False)

        st.success("Excel report generated successfully!")


# Function to view daily reports
def view_daily_reports():
    st.markdown("### View Daily Reports")
    st.write("---")
    if os.path.exists(REPORT_FILE):
        reports = pd.read_csv(REPORT_FILE)
        st.dataframe(reports)
    else:
        st.warning("No reports found.")


# Streamlit layout
st.title("Restaurant Management System")

menu_options = ["Add Sale", "Add Expense", "View Sales", "View Expenses", "View Inventory", "Generate Daily Report",
                "View Daily Reports"]
selected_menu = st.sidebar.selectbox("Select an option", menu_options)

if selected_menu == "Add Sale":
    add_sale()
elif selected_menu == "Add Expense":
    add_expense()
elif selected_menu == "View Sales":
    view_sales()
elif selected_menu == "View Expenses":
    view_expenses()
elif selected_menu == "View Inventory":
    view_inventory()
elif selected_menu == "Generate Daily Report":
    generate_daily_report()
elif selected_menu == "View Daily Reports":
    view_daily_reports()
