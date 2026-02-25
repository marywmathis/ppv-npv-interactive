import streamlit as st
import numpy as np

# Required for Streamlit Cloud matplotlib rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------
# PAGE TITLE
# ---------------------------
st.title("🔬 Interactive Screening Test Explorer")
st.write("Use this dashboard to explore how sensitivity, specificity, and prevalence shape PPV, NPV, and 2×2 tables for screening tests.")

# ---------------------------
# PRESET TEST OPTIONS
# ---------------------------
test_choice = st.selectbox(
    "Select Test Type:",
    ["FIT", "FIT-DNA (Cologuard)", "Colonoscopy", "Custom"]
)

preset_values = {
    "FIT": (0.75, 0.95),
    "FIT-DNA (Cologuard)": (0.92, 0.87),
    "Colonoscopy": (0.95, 0.99)
}

if test_choice in preset_values:
    sens_default, spec_default = preset_values[test_choice]
else:
    sens_default, spec_default = 0.80, 0.90

# ---------------------------
# SLIDERS
# ---------------------------
st.subheader("Test Parameters")

sens = st.slider("Sensitivity (%)", 1, 100, int(sens_default * 100), help="Probability test is positive if disease is present.") / 100
spec = st.slider("Specificity (%)", 1, 100, int(spec_default * 100), help="Probability test is negative if disease is absent.") / 100
prev = st.slider("Prevalence (%)", 0.01, 20.0, 0.3, help="Percent of population with the disease.") / 100

population = 100000  # fixed population

# ---------------------------
# CORE FUNCTIONS
# ---------------------------
def ppv(sens, spec, prev):
    return (sens * prev) / ((sens * prev) + (1 - spec) * (1 - prev))

def npv(sens, spec, prev):
    return (spec * (1 - prev)) / ((spec * (1 - prev)) + (1 - sens) * prev)

# Calculations
ppv_val = ppv(sens, spec, prev)
npv_val = npv(sens, spec, prev)

# 2x2 calculations
disease = population * prev
no_disease = population - disease

TP = sens * disease
FN = disease - TP
TN = spec * no_disease
FP = no_disease - TN

# ---------------------------
# COLOR CODING
# ---------------------------
def color_bar(value):
    if value >= 0.80:
        return "🟩 High"
    elif value >= 0.40:
        return "🟨 Moderate"
    else:
        return "🟥 Low"

# ---------------------------
# DISPLAY RESULTS
# ---------------------------
st.subheader("Results")

colA, colB = st.columns(2)
with colA:
    st.metric("PPV (Positive Predictive Value)", f"{ppv_val*100:.2f}%")
    st.write(color_bar(ppv_val))
with colB:
    st.metric("NPV (Negative Predictive Value)", f"{npv_val*100:.2f}%")
    st.write(color_bar(npv_val))

# ---------------------------
# 2×2 TABLE
# ---------------------------
st.subheader("2×2 Diagnostic Table")

st.table({
    "": ["Disease +", "Disease –", "Total"],
    "Test +": [f"{TP:.0f}", f"{FP:.0f}", f"{TP+FP:.0f}"],
    "Test –": [f"{FN:.0f}", f"{TN:.0f}", f"{FN+TN:.0f}"],
    "Total": [f"{disease:.0f}", f"{no_disease:.0f}", f"{population}"]
})

# ---------------------------
# GRAPHS WITH ANIMATED POINTS
# ---------------------------
st.subheader("Visualizing PPV & NPV Across Prevalence")

prev_range = np.linspace(0.0001, 0.20, 400)
ppv_curve = ppv(sens, spec, prev_range)
npv_curve = npv(sens, spec, prev_range)

fig, ax = plt.subplots(1, 2, figsize=(14, 5))

# PPV graph
ax[0].plot(prev_range * 100, ppv_curve * 100)
ax[0].scatter(prev * 100, ppv_val * 100, s=80)
ax[0].set_title("PPV vs Prevalence")
ax[0].set_xlabel("Prevalence (%)")
ax[0].set_ylim(0, 100)

# NPV graph
ax[1].plot(prev_range * 100, npv_curve * 100)
ax[1].scatter(prev * 100, npv_val * 100, s=80)
ax[1].set_title("NPV vs Prevalence")
ax[1].set_xlabel("Prevalence (%)")
ax[1].set_ylim(0, 100)

st.pyplot(fig)

# ---------------------------
# PDF DOWNLOAD (simple text summary)
# ---------------------------

import io
from reportlab.pdfgen import canvas

if st.button("Download Summary as PDF"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 800, "Screening Test Summary")
    c.drawString(100, 780, f"Test Type: {test_choice}")
    c.drawString(100, 760, f"Sensitivity: {sens*100:.1f}%")
    c.drawString(100, 740, f"Specificity: {spec*100:.1f}%")
    c.drawString(100, 720, f"Prevalence: {prev*100:.2f}%")
    c.drawString(100, 700, f"PPV: {ppv_val*100:.2f}%")
    c.drawString(100, 680, f"NPV: {npv_val*100:.2f}%")
    c.save()
    st.download_button("Download PDF", data=buffer.getvalue(), file_name="summary.pdf", mime="application/pdf")
