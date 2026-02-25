import streamlit as st
import numpy as np
import pandas as pd
import io
import base64

# Required for Streamlit Cloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas

# -----------------------------------------
# GLOBAL CSS FOR FONTS, SLIDERS, CLEAN UI
# -----------------------------------------
st.markdown("""
<style>

/* Larger, darker text */
html, body, [class*="css"] {
    font-size: 18px !important;
    color: #222 !important;
}

/* Increase header size (H2) */
h2 {
    font-size: 30px !important;
    font-weight: 700 !important;
    color: #111 !important;
}

/* Wider sliders */
div.stSlider > div[data-baseweb="slider"] {
    width: 95% !important;
    padding-left: 5px;
    padding-right: 5px;
}

/* Larger slider handle */
div[data-baseweb="slider"] div[role="slider"] {
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
}

/* Add vertical space for slider grabbing */
div[data-baseweb="slider"] {
    padding-top: 12px !important;
    padding-bottom: 12px !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# PAGE TITLE
# -----------------------------------------
st.title("🔬 Interactive Screening Test Explorer")

st.write(
    "A complete teaching tool for exploring sensitivity, specificity, prevalence, predictive values, "
    "likelihood ratios, Bayesian inference, ROC curves, prevalence effects, and real-world case examples."
)

# -----------------------------------------
# PRESET TESTS
# -----------------------------------------
preset_tests = {
    "FIT": {"sens": 0.75, "spec": 0.95, "prev": 0.003},
    "FIT-DNA (Cologuard)": {"sens": 0.92, "spec": 0.87, "prev": 0.003},
    "Colonoscopy": {"sens": 0.95, "spec": 0.99, "prev": 0.01},
}

# -----------------------------------------
# MAIN TEST SETUP
# -----------------------------------------
st.header("⚙️ Test Setup")

test_choice = st.selectbox("Select Test Type:", ["FIT", "FIT-DNA (Cologuard)", "Colonoscopy", "Custom"])

# Defaults
if test_choice != "Custom":
    sens_default = preset_tests[test_choice]["sens"]
    spec_default = preset_tests[test_choice]["spec"]
else:
    sens_default = 0.80
    spec_default = 0.90

# -----------------------------------------
# SLIDERS
# -----------------------------------------
sens = st.slider("Sensitivity (%)", 1, 100, int(sens_default * 100)) / 100
spec = st.slider("Specificity (%)", 1, 100, int(spec_default * 100)) / 100
prev = st.slider("Prevalence (%)", 0.01, 40.0, 0.3) / 100  # up to 40%

population = 100000

# -----------------------------------------
# CORE CALCULATIONS
# -----------------------------------------
def calc_ppv(s, p, prev):
    return (s * prev) / ((s * prev) + (1 - p) * (1 - prev))

def calc_npv(s, p, prev):
    return (p * (1 - prev)) / ((p * (1 - prev)) + (1 - s) * prev)

ppv = calc_ppv(sens, spec, prev)
npv = calc_npv(sens, spec, prev)

# 2×2 counts
disease = population * prev
no_disease = population - disease

TP = sens * disease
FN = disease - TP
TN = spec * no_disease
FP = no_disease - TN

# -----------------------------------------
# COLLAPSIBLE: PPV & NPV (open by default)
# -----------------------------------------
with st.expander("📊 PPV & NPV", expanded=True):

    def interpret(v):
        if v >= 0.80: return "🟩 High"
        if v >= 0.40: return "🟨 Moderate"
        return "🟥 Low"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("PPV", f"{ppv*100:.2f}%")
        st.write(interpret(ppv))
    with col2:
        st.metric("NPV", f"{npv*100:.2f}%")
        st.write(interpret(npv))

# -----------------------------------------
# COLLAPSIBLE: 2x2 TABLE
# -----------------------------------------
with st.expander("🧪 2×2 Diagnostic Table"):

    st.write("This table shows TP, FP, FN, and TN counts in a population of 100,000.")

    table = pd.DataFrame({
        "Disease +": [f"{TP:.0f}", f"{FN:.0f}", f"{disease:.0f}"],
        "Disease –": [f"{FP:.0f}", f"{TN:.0f}", f"{no_disease:.0f}"],
        "Total": [f"{TP+FP:.0f}", f"{FN+TN:.0f}", f"{population}"]
    }, index=["Test +", "Test –", "Total"])

    st.table(table)

    csv = table.to_csv(index=True).encode()
    st.download_button("Download 2×2 Table (CSV)", csv, "2x2_table.csv")

# -----------------------------------------
# COLLAPSIBLE: LIKELIHOOD RATIOS
# -----------------------------------------
with st.expander("🧬 Likelihood Ratios (LR+ / LR–)"):

    LR_pos = sens / (1 - spec)
    LR_neg = (1 - sens) / spec

    st.write(f"**LR+ = {LR_pos:.2f}**")
    st.write(f"**LR– = {LR_neg:.2f}**")

    def lr_interpret(val, pos=True):
        if pos:
            if val > 10: return "🟩 Strong evidence for disease"
            elif val > 5: return "🟨 Moderate evidence"
            else: return "🟥 Weak evidence"
        else:
            if val < 0.1: return "🟩 Strong evidence against disease"
            elif val < 0.2: return "🟨 Moderate evidence"
            else: return "🟥 Weak evidence"

    st.write(lr_interpret(LR_pos, pos=True))
    st.write(lr_interpret(LR_neg, pos=False))

# -----------------------------------------
# COLLAPSIBLE: BAYESIAN POST-TEST PROBABILITY
# -----------------------------------------
with st.expander("🧮 Bayesian Post-Test Probability"):

    st.write("Choose whether the test result was positive or negative:")

    test_result = st.radio("Test Result:", ["Positive", "Negative"], horizontal=True)

    if test_result == "Positive":
        post = LR_pos * (prev / (1 - prev))
    else:
        post = LR_neg * (prev / (1 - prev))

    post_prob = post / (1 + post)

    st.metric("Post-Test Probability", f"{post_prob*100:.2f}%")

# -----------------------------------------
# COLLAPSIBLE: ROC CURVE
# -----------------------------------------
with st.expander("📈 ROC Curve"):

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.scatter(1 - spec, sens, s=120)
    ax.set_xlabel("1 – Specificity")
    ax.set_ylabel("Sensitivity")
    ax.set_title("ROC Space Position")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    st.pyplot(fig)

# -----------------------------------------
# COLLAPSIBLE: PREVALENCE EXPLORER
# -----------------------------------------
with st.expander("🌍 Prevalence Explorer"):

    ages = np.arange(20, 81)
    age_prev = (ages - 20) / 100  # simple model: increases with age

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ages, age_prev * 100)
    ax.set_xlabel("Age")
    ax.set_ylabel("Prevalence (%)")
    ax.set_title("How Disease Prevalence Rises with Age")
    st.pyplot(fig)

# -----------------------------------------
# COLLAPSIBLE: CASE EXAMPLES (C2)
# -----------------------------------------
with st.expander("👥 Case Examples"):

    st.write("Select a real-world scenario:")

    case = st.selectbox(
        "Choose Case Example:",
        [
            "Population Screening (FIT)",
            "Primary Care Symptomatic Patient",
            "High-Risk GI Clinic (FIT-DNA)",
            "Hospital Inpatient with Symptoms"
        ]
    )

    if case == "Population Screening (FIT)":
        sens = 0.75
        spec = 0.95
        prev = 0.003

    elif case == "Primary Care Symptomatic Patient":
        sens = 0.80
        spec = 0.90
        prev = 0.05

    elif case == "High-Risk GI Clinic (FIT-DNA)":
        sens = 0.92
        spec = 0.87
        prev = 0.12

    elif case == "Hospital Inpatient with Symptoms":
        sens = 0.95
        spec = 0.99
        prev = 0.25

    st.write(f"**Updated Sensitivity:** {sens*100:.1f}%")
    st.write(f"**Updated Specificity:** {spec*100:.1f}%")
    st.write(f"**Updated Prevalence:** {prev*100:.2f}%")

# -----------------------------------------
# COLLAPSIBLE: DOWNLOADS
# -----------------------------------------
with st.expander("📥 Downloads"):

    # ---- PDF ----
    if st.button("Download Summary as PDF"):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 800, "Screening Test Summary")
        c.drawString(100, 780, f"Sensitivity: {sens*100:.1f}%")
        c.drawString(100, 760, f"Specificity: {spec*100:.1f}%")
        c.drawString(100, 740, f"Prevalence: {prev*100:.2f}%")
        c.drawString(100, 720, f"PPV: {calc_ppv(sens, spec, prev)*100:.2f}%")
        c.drawString(100, 700, f"NPV: {calc_npv(sens, spec, prev)*100:.2f}%")
        c.save()
        st.download_button("Download PDF", data=buffer.getvalue(), file_name="summary.pdf", mime="application/pdf")

    # ---- PNG Graph ----
    fig2, ax2 = plt.subplots()
    ax2.plot([1, 2, 3], [1, 2, 3])
    png = io.BytesIO()
    fig2.savefig(png, format="png")
    st.download_button("Download Example Graph (PNG)", png.getvalue(), "graph.png", "image/png")
