import streamlit as st
import numpy as np

# Required for Streamlit Cloud matplotlib rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------
# CUSTOM CSS FOR WIDER SLIDERS & LARGER HANDLES
# ---------------------------
st.markdown("""
<style>
/* Make sliders full width */
div.stSlider > div[data-baseweb="slider"] {
    width: 95% !important;
    padding-left: 10px;
    padding-right: 10px;
}

/* Make the slider handle (thumb) larger */
div[data-baseweb="slider"] div[role="slider"] {
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
}

/* Increase clickable area vertically */
div[data-baseweb="slider"] {
    padding-top: 15px;
    padding-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# PAGE TITLE
# ---------------------------
st.title("🔬 Interactive Screening Test Explorer")
st.write("Explore how sensitivity, specificity, and prevalence shape PPV, NPV, and diagnostic accuracy.")

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
    sens_default, spec_default = 0.80, 0.90  # default for custom

# ---------------------------
# SLIDERS
# ---------------------------
st.subheader("Test Parameters")

sens = st.slider("Sensitivity (%)", 1, 100, int(sens_default * 100),
    help="Probability the test is positive if the disease is present.") / 100

spec = st.slider("Specificity (%)", 1, 100, int(spec_default * 100),
    help="Probability the test is negative if the disease is absent.") / 100

prev = st.slider("Prevalence (%)", 0.01, 40.0, 0.3,
    help="Percent of the population with the disease.") / 100

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

# 2×2 table components
disease = population * prev
no_disease = population - disease

TP = sens * disease
FN = disease - TP
TN = spec * no_disease
FP = no_disease - TN

# ---------------------------
# COLOR CODING FUNCTION
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
st.subheader("Predictive Values")

colA, colB = st.columns(2)
with colA:
    st.metric("PPV (Positive Predictive Value)", f"{ppv_val*100:.2f}%")
    st.write(color_bar(ppv_val))
with colB:
    st.metric("NPV (Negative Predictive Value)", f"{npv_val*100:.2f}%")
    st.write(color_bar(npv_val))

# ---------------------------
# 2×2 DIAGNOSTIC TABLE (Flipped)
# ---------------------------
st.subheader("2×2 Diagnostic Table")

table_data = {
    "": ["Test +", "Test –", "Total"],
    "Disease +": [f"{TP:.0f}", f"{FN:.0f}", f"{disease:.0f}"],
    "Disease –": [f"{FP:.0f}", f"{TN:.0f}", f"{no_disease:.0f}"],
    "Total": [f"{TP+FP:.0f}", f"{FN+TN:.0f}", f"{population}"]
}

st.table(table_data)

# ---------------------------
# VISUAL GRAPHS WITH MARKERS
# ---------------------------
st.subheader("Visualizing PPV & NPV Across Prevalence")

prev_range = np.linspace(0.0001, 0.40, 400)
ppv_curve = ppv(sens, spec, prev_range)
npv_curve = npv(sens, spec, prev_range)

fig, ax = plt.subplots(1, 2, figsize=(14, 5))

# PPV graph
ax[0].plot(prev_range * 100, ppv_curve * 100)
ax[0].scatter(prev * 100, ppv_val * 100, s=80)
ax[0].set_title("PPV vs Prevalence")
ax[0].set_xlabel("Prelevance (%)")
ax[0].set_ylim(0, 100)

# NPV graph
ax[1].plot(prev_range * 100, npv_curve * 100)
ax[1].scatter(prev * 100, npv_val * 100, s=80)
ax[1].set_title("NPV vs Prevalence")
ax[1].set_xlabel("Prevalence (%)")
ax[1].set_ylim(0, 100)

st.pyplot(fig)

# ---------------------------
# PDF DOWNLOAD
# ---------------------------
import io
from reportlab.pdfgen import canvas

st.subheader("Export Summary")

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
    st.download_button("Download PDF", data=buffer.getvalue(),
                       file_name="summary.pdf", mime="application/pdf")
