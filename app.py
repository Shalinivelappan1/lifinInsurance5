import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# =====================================================
# Page Config
# =====================================================
st.set_page_config(page_title="LiFin Insurance Lab", layout="wide")
st.title("🛡️ LiFin Insurance Lab — Developed by Prof.Shalini Velappan, IIM Trichy")

st.caption("""
This is a **teaching simulator** for reasoning about insurance using:
- Expected value (NPV)
- Utility / protection logic
- Duration, discounting, and risk transfer

It is **not** an actuarial pricing engine.
""")

# =====================================================
# Helper: Break-even finder
# =====================================================
def find_break_even(x_vals, y_vals):
    y = np.array(y_vals)
    idx = np.argmin(np.abs(y))
    return x_vals[idx], y_vals[idx]

# =====================================================
# Sidebar: Personal Profile
# =====================================================
st.sidebar.header("👤 Personal Profile")

age = st.sidebar.slider("Current Age", 18, 65, 30)
gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
smoker = st.sidebar.selectbox("Smoker?", ["No", "Yes"])
health = st.sidebar.selectbox("Health Condition", ["Good", "Average", "Poor"])
dependents = st.sidebar.number_input("Number of Dependents", 0, 6, 2)
discount_rate = st.sidebar.slider("Your Discount Rate / Opportunity Cost (%)", 1.0, 20.0, 8.0)

with st.sidebar.expander("ℹ️ What is the discount rate?"):
    st.markdown("""
This is your **opportunity cost of capital**:
- What you believe you can earn elsewhere (equity, business, etc.)
- It reflects **time preference + risk preference**
- A higher discount rate makes **long-duration policies look worse**
""")

# =====================================================
# Sidebar: Policy A
# =====================================================
st.sidebar.header("📜 Policy A")

policyA_type = st.sidebar.selectbox("Policy A Type", ["Term Insurance", "Whole Life"])
termA = st.sidebar.slider("Policy A Term (years)", 5, 80, 30)
coverA = st.sidebar.number_input("Policy A Cover (₹)", value=5_000_000, step=500_000)
premA = st.sidebar.number_input("Policy A Annual Premium (₹)", value=20_000, step=1_000)

st.sidebar.markdown("**Policy A Riders**")
accA = st.sidebar.checkbox("Accidental Death Rider (50% extra cover)", value=False)
ciA = st.sidebar.checkbox("Critical Illness Rider (30% lump sum)", value=False)
disA = st.sidebar.checkbox("Disability / Income Replacement Rider", value=False)
wopA = st.sidebar.checkbox("Waiver of Premium Rider", value=False)

# =====================================================
# Sidebar: Policy B
# =====================================================
st.sidebar.header("📜 Policy B")

policyB_type = st.sidebar.selectbox("Policy B Type", ["Term Insurance", "Whole Life"])
termB = st.sidebar.slider("Policy B Term (years)", 5, 80, 40)
coverB = st.sidebar.number_input("Policy B Cover (₹)", value=7_500_000, step=500_000)
premB = st.sidebar.number_input("Policy B Annual Premium (₹)", value=35_000, step=1_000)

st.sidebar.markdown("**Policy B Riders**")
accB = st.sidebar.checkbox("B: Accidental Death Rider", value=True)
ciB = st.sidebar.checkbox("B: Critical Illness Rider", value=True)
disB = st.sidebar.checkbox("B: Disability / Income Replacement Rider", value=False)
wopB = st.sidebar.checkbox("B: Waiver of Premium Rider", value=False)

# =====================================================
# Explanations of Riders
# =====================================================
with st.expander("ℹ️ What do these riders do?"):
    st.markdown("""
**Accidental Death:** Pays extra if death is accidental.  
**Critical Illness:** Pays a lump sum on diagnosis of major illness.  
**Disability / Income Replacement:** If disability occurs before age 60, pays an income-like benefit for a few years.  
**Waiver of Premium:** If disability/CI occurs before age 55, future premiums are waived but coverage continues.

Conceptually:
- Disability rider protects **your income**
- Waiver of premium protects **the survival of the policy**
""")

# =====================================================
# Mortality Model (Teaching Approximation)
# =====================================================
def base_mortality(age, year, gender):
    current_age = age + year
    base = 0.0015 if gender == "Female" else 0.002
    slope = 0.00025
    p = base + slope * max(current_age - 30, 0)
    return min(p, 0.25)

def risk_multiplier(smoker, health):
    m = 1.0
    if smoker == "Yes":
        m *= 1.5
    if health == "Average":
        m *= 1.3
    elif health == "Poor":
        m *= 1.8
    return m

# =====================================================
# NPV Engine
# =====================================================
def insurance_npv(age, term, coverage, premium, discount_rate, gender, smoker, health,
                  accidental, critical, disability, wop, policy_type):

    r = discount_rate / 100
    pv_benefit = 0
    pv_premium = 0
    survival = 1.0
    mult = risk_multiplier(smoker, health)

    effective_term = term if policy_type == "Term Insurance" else 100

    for t in range(1, effective_term + 1):
        p_death = base_mortality(age, t, gender) * mult

        payout = coverage
        if accidental:
            payout *= 1.5

        expected_payout = survival * p_death * payout

        # Critical illness: 10% chance, pays 30% of cover
        if critical:
            expected_payout += survival * 0.10 * 0.3 * coverage

        # Disability income: only before age 60, pays 20% of cover for 5 years (simplified)
        if disability and (age + t) < 60:
            expected_payout += survival * 0.05 * 0.2 * coverage

        pv_benefit += expected_payout / ((1 + r) ** t)

        # Waiver of premium: if triggered before age 55, premiums drop by 100% (simplified expectation)
        effective_premium = premium
        if wop and (age + t) < 55 and t > 10:
            effective_premium = 0.0

        if policy_type == "Term Insurance" and t <= term:
            pv_premium += effective_premium / ((1 + r) ** t)
        elif policy_type == "Whole Life" and t <= 60:
            pv_premium += effective_premium / ((1 + r) ** t)

        survival *= (1 - p_death)

    return pv_benefit - pv_premium

# =====================================================
# Compute NPVs
# =====================================================
npvA = insurance_npv(age, termA, coverA, premA, discount_rate, gender, smoker, health, accA, ciA, disA, wopA, policyA_type)
npvB = insurance_npv(age, termB, coverB, premB, discount_rate, gender, smoker, health, accB, ciB, disB, wopB, policyB_type)

utilA = coverA * max(dependents, 1) / (abs(npvA) + 1)
utilB = coverB * max(dependents, 1) / (abs(npvB) + 1)

# =====================================================
# Dashboard
# =====================================================
st.subheader("📊 Policy Comparison Dashboard")

with st.expander("ℹ️ What do NPV and Utility mean?"):
    st.markdown("""
**NPV (Expected Value View):**
- Financial value of the contract under probabilities and discounting
- Usually **negative** for good insurance (because insurer must survive and make profit)

**Utility (Protection View):**
- A proxy for **how much financial ruin is avoided**
- High cover with manageable cost = high utility
""")

c1, c2 = st.columns(2)
with c1:
    st.markdown("### 🅰️ Policy A")
    st.metric("NPV (₹)", f"{npvA:,.0f}")
    st.metric("Utility Score", f"{utilA:,.1f}")

with c2:
    st.markdown("### 🅱️ Policy B")
    st.metric("NPV (₹)", f"{npvB:,.0f}")
    st.metric("Utility Score", f"{utilB:,.1f}")

# =====================================================
# Decision Summary Table
# =====================================================
st.markdown("## 📋 Decision Summary Table")

summary = {
    "Metric": [
        "NPV (₹)", "Utility Score", "Cover (₹)", "Premium (₹)",
        "Accidental Rider", "Critical Illness Rider", "Disability Rider", "Waiver of Premium"
    ],
    "Policy A": [
        f"{npvA:,.0f}", f"{utilA:,.1f}", f"{coverA:,.0f}", f"{premA:,.0f}",
        accA, ciA, disA, wopA
    ],
    "Policy B": [
        f"{npvB:,.0f}", f"{utilB:,.1f}", f"{coverB:,.0f}", f"{premB:,.0f}",
        accB, ciB, disB, wopB
    ]
}

st.table(summary)

# =====================================================
# Charts Section
# =====================================================
st.markdown("## 📚 Learning from Comparison Charts")

st.markdown("""
🟩 **Green region** = NPV ≥ 0 (financially acceptable)  
🟥 **Red region** = NPV < 0 (financial cost — but may still be optimal for protection)
""")

# -------- NPV vs Term --------
st.subheader("1️⃣ NPV vs Term")

terms = np.arange(5, 81)
npvA_terms = [insurance_npv(age, t, coverA, premA, discount_rate, gender, smoker, health, accA, ciA, disA, wopA, policyA_type) for t in terms]
npvB_terms = [insurance_npv(age, t, coverB, premB, discount_rate, gender, smoker, health, accB, ciB, disB, wopB, policyB_type) for t in terms]

beA_x, beA_y = find_break_even(terms, npvA_terms)
beB_x, beB_y = find_break_even(terms, npvB_terms)

plt.figure()
plt.plot(terms, npvA_terms, label="Policy A")
plt.plot(terms, npvB_terms, label="Policy B")
plt.axhline(0)

plt.fill_between(terms, npvA_terms, 0, where=(np.array(npvA_terms) >= 0), color="green", alpha=0.15)
plt.fill_between(terms, npvA_terms, 0, where=(np.array(npvA_terms) < 0), color="red", alpha=0.15)

plt.scatter([beA_x], [beA_y]); plt.scatter([beB_x], [beB_y])
plt.axvline(beA_x, linestyle="--", alpha=0.5); plt.axvline(beB_x, linestyle="--", alpha=0.5)

plt.legend(); plt.title("NPV vs Term"); plt.xlabel("Years"); plt.ylabel("NPV")
st.pyplot(plt.gcf()); plt.clf()

with st.expander("💡 How to think about this (MBA hint)"):
    st.markdown("""
- Look for **crossing points**: which policy dominates at short vs long horizons?
- Long horizons suffer from **discounting dominating probability**.
- This is a **duration** problem, not a simple cost problem.
""")

# -------- NPV vs Premium --------
st.subheader("2️⃣ NPV vs Premium")

premiumsA = np.linspace(0.3 * premA, 2.5 * premA, 25)
premiumsB = np.linspace(0.3 * premB, 2.5 * premB, 25)

npvA_prem = [insurance_npv(age, termA, coverA, p, discount_rate, gender, smoker, health, accA, ciA, disA, wopA, policyA_type) for p in premiumsA]
npvB_prem = [insurance_npv(age, termB, coverB, p, discount_rate, gender, smoker, health, accB, ciB, disB, wopB, policyB_type) for p in premiumsB]

beA_x, beA_y = find_break_even(premiumsA, npvA_prem)
beB_x, beB_y = find_break_even(premiumsB, npvB_prem)

plt.figure()
plt.plot(premiumsA, npvA_prem, label="Policy A")
plt.plot(premiumsB, npvB_prem, label="Policy B")
plt.axhline(0)

plt.fill_between(premiumsA, npvA_prem, 0, where=(np.array(npvA_prem) >= 0), color="green", alpha=0.15)
plt.fill_between(premiumsA, npvA_prem, 0, where=(np.array(npvA_prem) < 0), color="red", alpha=0.15)

plt.scatter([beA_x], [beA_y]); plt.scatter([beB_x], [beB_y])
plt.axvline(beA_x, linestyle="--", alpha=0.5); plt.axvline(beB_x, linestyle="--", alpha=0.5)

plt.legend(); plt.title("NPV vs Premium"); plt.xlabel("Annual Premium (₹)"); plt.ylabel("NPV")
st.pyplot(plt.gcf()); plt.clf()

with st.expander("💡 How to think about this (MBA hint)"):
    st.markdown("""
- The zero crossing is the **maximum acceptable premium**.
- Steeper curves = **higher sensitivity to mispricing**.
- This is a **pricing discipline** problem.
""")

# -------- NPV vs Discount Rate --------
st.subheader("3️⃣ NPV vs Discount Rate")

rates = np.linspace(1, 20, 25)

npvA_rates = [insurance_npv(age, termA, coverA, premA, r, gender, smoker, health, accA, ciA, disA, wopA, policyA_type) for r in rates]
npvB_rates = [insurance_npv(age, termB, coverB, premB, r, gender, smoker, health, accB, ciB, disB, wopB, policyB_type) for r in rates]

beA_x, beA_y = find_break_even(rates, npvA_rates)
beB_x, beB_y = find_break_even(rates, npvB_rates)

plt.figure()
plt.plot(rates, npvA_rates, label="Policy A")
plt.plot(rates, npvB_rates, label="Policy B")
plt.axhline(0)

plt.fill_between(rates, npvA_rates, 0, where=(np.array(npvA_rates) >= 0), color="green", alpha=0.15)
plt.fill_between(rates, npvA_rates, 0, where=(np.array(npvA_rates) < 0), color="red", alpha=0.15)

plt.scatter([beA_x], [beA_y]); plt.scatter([beB_x], [beB_y])
plt.axvline(beA_x, linestyle="--", alpha=0.5); plt.axvline(beB_x, linestyle="--", alpha=0.5)

plt.legend(); plt.title("NPV vs Discount Rate"); plt.xlabel("Discount Rate (%)"); plt.ylabel("NPV")
st.pyplot(plt.gcf()); plt.clf()

with st.expander("💡 How to think about this (MBA hint)"):
    st.markdown("""
- The zero crossing is the **implied internal rate of return** of the policy.
- Long-duration policies are **more sensitive to discount rate**.
- This is an **opportunity cost of capital** problem.
""")

# =====================================================
# Assignment Submission
# =====================================================
st.markdown("## 📝 Assignment Submission")

student_name = st.text_input("Student Name")
student_id = st.text_input("Student ID / Roll No")

q1 = st.text_area("1) Which policy would you choose and why?")
q2 = st.text_area("2) What did you learn from the three NPV curves?")
q3 = st.text_area("3) Why can a negative NPV policy still be a good decision?")
q4 = st.text_area("4) Which curve (Term / Premium / Discount Rate) changed your thinking the most? Why?")
q5 = st.text_area("5) In your own words: explain the difference between a 'bad investment' and a 'good insurance product'.")

if st.button("📄 Generate Submission File"):
    content = f"""
LiFin Insurance Lab Submission
Date: {datetime.now()}

Name: {student_name}
ID: {student_id}

NPV Policy A: {npvA}
NPV Policy B: {npvB}

Q1: {q1}

Q2: {q2}

Q3: {q3}

Q4: {q4}

Q5: {q5}
"""
    st.download_button("⬇️ Download Submission", content, file_name=f"{student_name}_insurance_assignment.txt")

# =====================================================
# Footer
# =====================================================
st.markdown("""
---
⚠️ This is a **pedagogical simulator**, not an actuarial pricing system.
""")
