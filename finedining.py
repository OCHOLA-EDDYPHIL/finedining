import streamlit as st
import pandas as pd
import datetime
import os

# Define file paths for persistence
INVENTORY_FILE = 'inventory.csv'
MENU_FILE = 'menu.csv'
SALES_FILE = 'sales.csv'
EXPENSES_FILE = 'expenses.csv'


# Initialize inventory, menu, sales, and expenses from CSV files
def load_data():
    if os.path.exists(INVENTORY_FILE):
        inventory_df = pd.read_csv(INVENTORY_FILE, index_col=0).to_dict(orient='index')
    else:
        inventory_df = {
            # 'rice': {'quantity': 50, 'unit': 'kg', 'price_per_unit': 100},
            # 'chicken': {'quantity': 20, 'unit': 'kg', 'price_per_unit': 250},
            'soda': {'quantity': 10, 'unit': 'bottles - 300ml', 'price_per_unit': 60}
        }
        pd.DataFrame.from_dict(inventory_df, orient='index').to_csv(INVENTORY_FILE)

    if os.path.exists(MENU_FILE):
        menu_df = pd.read_csv(MENU_FILE, index_col=0).to_dict(orient='index')
    else:
        menu_df = {
            'Combo 1': {'items': {'BEEF': 1, 'UGALI': 1}, 'price': 150},
            'Combo 2': {'items': {'LIVER': 0.5, 'UGALI': 1}, 'price': 200},
            'Combo 3': {'items': {'NDENGU': 1, 'CHAPATI': 2}, 'price': 120}
        }
        pd.DataFrame.from_dict(menu_df, orient='index').to_csv(MENU_FILE)

    sales_df = pd.read_csv(SALES_FILE, index_col=0) if os.path.exists(SALES_FILE) else pd.DataFrame(
        columns=['combo', 'quantity', 'total_price', 'payment_mode', 'date'])
    expenses_df = pd.read_csv(EXPENSES_FILE, index_col=0) if os.path.exists(EXPENSES_FILE) else pd.DataFrame(
        columns=['item', 'quantity', 'total_cost', 'category', 'date'])

    return inventory_df, menu_df, sales_df, expenses_df


# Load initial data
inventory = {}
menu = {}
sales = pd.DataFrame()
expenses = pd.DataFrame()

inventory, menu, sales, expenses = load_data()


# Function to save data to CSV files
def save_data():
    pd.DataFrame.from_dict(inventory, orient='index').to_csv(INVENTORY_FILE)
    pd.DataFrame.from_dict(menu, orient='index').to_csv(MENU_FILE)
    sales.to_csv(SALES_FILE)
    expenses.to_csv(EXPENSES_FILE)


# Function to add a sale
def add_sale():
    st.subheader("Log Sale")
    combo = st.selectbox("Select Menu Item (Combo)", options=list(menu.keys()))
    quantity = st.number_input(f"Quantity of {combo}", min_value=1, value=1)
    payment_mode = st.selectbox("Payment Mode", options=['cash', 'till', 'pochi'])
    sale_date = st.date_input("Sale Date", value=datetime.date.today())

    total_price = quantity * menu[combo]['price']
    st.write(f"Total Price: {total_price}")

    if st.button("Submit Sale"):
        # Update inventory based on menu items sold
        for item, required_quantity in menu[combo]['items'].items():
            if inventory[item]['quantity'] < required_quantity * quantity:
                st.error(f"Not enough {item} in stock.")
                return
            inventory[item]['quantity'] -= required_quantity * quantity

        # Record the sale
        new_sale = pd.DataFrame({
            'combo': [combo],
            'quantity': [quantity],
            'total_price': [total_price],
            'payment_mode': [payment_mode],
            'date': [sale_date]
        })
        global sales
        sales = pd.concat([sales, new_sale], ignore_index=True)

        save_data()  # Save to CSV
        st.success(f"Sale logged for {quantity} x {combo}")


# Function to log an expense
def add_expense():
    global expenses
    st.subheader("Log Expense")
    category = st.selectbox("Expense Category", options=['restocking', 'bills', 'rent', 'taxes', 'other'])

    if category == 'restocking':
        item = st.text_input("Enter Item to Restock")
        quantity = st.number_input(f"Quantity of {item} to restock", min_value=1)
        unit = st.selectbox("Unit", options=['units', 'kg', 'litres'])
        total_cost = st.number_input("Total Restocking Cost", min_value=0.0, format="%.2f",
                                     value=float(quantity) * 0.0)  # Ensure value is a float
        expense_date = st.date_input("Restocking Date", value=datetime.date.today())

        if st.button("Submit Restocking Expense", key="restocking"):
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
        item = st.text_input("Define Expense Item")
        total_cost = st.number_input(f"Total Cost for {category.capitalize()}", min_value=0.0, format="%.2f")
        expense_date = st.date_input("Expense Date", value=datetime.date.today())

        if st.button(f"Submit {category.capitalize()} Expense", key=category):
            new_expense = pd.DataFrame({
                'item': [item],
                'quantity': [0],
                'total_cost': [total_cost],
                'category': [category],
                'date': [expense_date]
            })
            expenses = pd.concat([expenses, new_expense], ignore_index=True)

            save_data()  # Save to CSV
            st.success(f"{category.capitalize()} expense logged")


# Function to calculate daily profit/loss
def calculate_profit_loss(date):
    total_sales = sales[sales['date'] == date]['total_price'].sum()
    total_expenses = expenses[expenses['date'] == date]['total_cost'].sum()
    return total_sales - total_expenses


# Function to display inventory
def display_inventory():
    st.subheader("Current Inventory")
    inventory_df = pd.DataFrame.from_dict(inventory, orient='index')
    st.dataframe(inventory_df)


# Function to display menu
def display_menu():
    st.subheader("Menu")
    menu_df = pd.DataFrame(menu).T
    st.dataframe(menu_df)


# Function to display sales
def display_sales():
    st.subheader("Sales")
    st.dataframe(sales)


# Function to display expenses
def display_expenses():
    st.subheader("Expenses")
    st.dataframe(expenses)


# Function to display and download spreadsheet report
def generate_spreadsheet():
    st.subheader("Generate Spreadsheet Report")
    inventory_df = pd.DataFrame.from_dict(inventory, orient='index')

    # Write to Excel file
    with pd.ExcelWriter('restaurant_report.xlsx') as writer:
        inventory_df.to_excel(writer, sheet_name='Inventory')
        sales.to_excel(writer, sheet_name='Sales')
        expenses.to_excel(writer, sheet_name='Expenses')

    if os.path.exists('restaurant_report.xlsx'):
        with open('restaurant_report.xlsx', 'rb') as file:
            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name='restaurant_report.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        st.success("Spreadsheet report generated and ready for download")


# Main App
st.title("Restaurant Inventory, Sales, and Expense Management System")

st.sidebar.title("Menu")
option = st.sidebar.selectbox("Select an option",
                              ["View Inventory", "View Menu", "Log Sale", "Log Expense", "View Sales", "View Expenses",
                               "Generate Spreadsheet", "Daily Profit/Loss"])

if option == "View Inventory":
    display_inventory()
elif option == "View Menu":
    display_menu()
elif option == "Log Sale":
    add_sale()
elif option == "Log Expense":
    add_expense()
elif option == "View Sales":
    display_sales()
elif option == "View Expenses":
    display_expenses()
elif option == "Generate Spreadsheet":
    generate_spreadsheet()
elif option == "Daily Profit/Loss":
    st.subheader("Calculate Daily Profit/Loss")
    selected_date = st.date_input("Select Date", value=datetime.date.today())
    profit_loss = calculate_profit_loss(selected_date)
    st.write(f"Profit/Loss for {selected_date}: {profit_loss}")
