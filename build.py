import streamlit as st

# Set responsive page layout
st.set_page_config(page_title="Biller", layout="wide", initial_sidebar_state="collapsed")

# Initialize persistent memory block for items
if "item_ledger" not in st.session_state:
    st.session_state["item_ledger"] = []

st.title("⚡ Biller")

# ==========================================
# SECTION 1: TAX & DISCOUNT INPUTS
# ==========================================
col_tax, col_discount = st.columns(2)

with col_tax:
    tax_rate = st.number_input(
        "Tax %", 
        min_value=0.0, 
        max_value=100.0, 
        value=5.0, 
        step=0.5, 
        format="%.1f"
    )

with col_discount:
    discount_rate = st.number_input(
        "Discount %", 
        min_value=0.0, 
        max_value=100.0, 
        value=0.0, 
        step=1.0, 
        format="%.1f"
    )

st.markdown("---")

# ==========================================
# SECTION 2: ROSTER CONFIGURATION
# ==========================================
st.subheader("👥 Roster")

num_people = st.number_input(
    "Number of People", 
    min_value=1, 
    max_value=12, 
    value=4, 
    step=1
)

use_custom_names = st.toggle("Use Custom Names", value=False)

if use_custom_names:
    custom_names_raw = st.text_input(
        "Names (separated by commas)", 
        value="",
        placeholder="AC, TK, SB",
        help="Type names separated by commas."
    )
    parsed_names = [name.strip() for name in custom_names_raw.split(",") if name.strip()]
    
    # Pad with generic identifiers if entered names are fewer than the total count
    people_pool = []
    for i in range(int(num_people)):
        if i < len(parsed_names):
            people_pool.append(parsed_names[i])
        else:
            people_pool.append(f"Person {i+1}")
else:
    people_pool = [f"Person {i+1}" for i in range(int(num_people))]

st.markdown("---")

# ==========================================
# SECTION 3: ADD ITEMS FORM
# ==========================================
st.subheader("🍽️ Add Items")

with st.form(key="item_form", clear_on_submit=True):
    col_name, col_price = st.columns([2, 1])
    
    with col_name:
        item_name = st.text_input("Item Name", placeholder="e.g., Chicken Tikka, Salad")
    
    with col_price:
        item_price = st.number_input("Price (₹)", min_value=0.0, step=1.0, format="%.2f")
    
    split_protocol = st.radio(
        "Split Method", 
        ["Split Equally", "Personalized"], 
        horizontal=True
    )
    
    # Render selection box only if personalized logic is flagged
    if split_protocol == "Personalized":
        chosen_consumers = st.multiselect(
            "Shared by:", 
            options=people_pool,
            default=people_pool
        )
    else:
        chosen_consumers = people_pool
    
    submit_transaction = st.form_submit_button(label="Add to Bill")

# Process state mutations
if submit_transaction:
    if item_price <= 0:
        st.error("Price must be greater than ₹0.00")
    elif not chosen_consumers:
        st.error("Select at least one person")
    else:
        transaction_payload = {
            "name": item_name.strip() if item_name.strip() else f"Item #{len(st.session_state['item_ledger']) + 1}",
            "price": item_price,
            "consumers": chosen_consumers
        }
        st.session_state["item_ledger"].append(transaction_payload)
        st.success(f"Added {transaction_payload['name']}!")

st.markdown("---")

# ==========================================
# SECTION 4: BALANCES & AUDIT TRAIL
# ==========================================
col_balances, col_audit = st.columns([1, 1])

individual_balances = {person: 0.0 for person in people_pool}
audit_table_data = []

# Core math processing engine
for index, record in enumerate(st.session_state["item_ledger"]):
    active_consumers = [c for c in record["consumers"] if c in individual_balances]
    
    if not active_consumers:
        continue
        
    base_value = record["price"]
    
    # Calculate compounded tax followed by discount
    taxed_value = base_value * (1 + (tax_rate / 100))
    net_final_value = taxed_value * (1 - (discount_rate / 100))
    
    per_capita_cost = net_final_value / len(active_consumers)
    
    for consumer in active_consumers:
        individual_balances[consumer] += per_capita_cost
        
    audit_table_data.append({
        "Item": record["name"],
        "Base (₹)": f"₹{base_value:.2f}",
        "Final (₹)": f"₹{net_final_value:.2f}",
        "Shared By": ", ".join(active_consumers)
    })

with col_balances:
    st.subheader("💳 Total Owed")
    for individual in people_pool:
        debt_amount = individual_balances.get(individual, 0.0)
        st.metric(label=individual, value=f"₹{debt_amount:.2f}")

with col_audit:
    st.subheader("📋 Bill Audit")
    if audit_table_data:
        st.dataframe(audit_table_data, use_container_width=True, hide_index=True)
    else:
        st.info("No items added yet.")

# ==========================================
# SECTION 5: SYSTEM STATE CONTROL
# ==========================================
st.markdown("---")
if st.button("Reset Bill", type="primary", use_container_width=True):
    st.session_state["item_ledger"] = []
    st.rerun()