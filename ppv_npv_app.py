import streamlit as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.write("App Loaded!")  # Debug line

st.title("🔍 Interactive Sn / Sp / Prevalence → PPV & NPV Calculator")

# Sliders
sens = st.slider("Sensitivity (%)", 1, 100, 75) / 100
spec = st.slider("Specificity (%)", 1, 100, 95) / 100
prev = st.slider("Prevalence (%)", 0.01, 20.0, 0.3) / 100

# Functions
def ppv(sens, spec, prev):
    return (sens * prev) / ((sens * prev) + ((1 - spec) * (1 - prev)))

def npv(sens, spec, prev):
    return (spec * (1 - prev)) / ((spec * (1 - prev)) + ((1 - sens) * prev))

ppv_val = ppv(sens, spec, prev)
npv_val = npv(sens, spec, prev)

st.metric("PPV", f"{ppv_val*100:.2f}%")
st.metric("NPV", f"{npv_val*100:.2f}%")

# Graphs
prev_range = np.linspace(0.0001, 0.2, 400)
ppv_curve = ppv(sens, spec, prev_range)
npv_curve = npv(sens, spec, prev_range)

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# PPV graph
ax[0].plot(prev_range * 100, ppv_curve * 100)
ax[0].axvline(prev * 100, linestyle="--")
ax[0].set_title("PPV vs Prevalence")
ax[0].set_xlabel("Prevalence (%)")
ax[0].set_ylabel("PPV (%)")
ax[0].set_ylim(0, 100)

# NPV graph
ax[1].plot(prev_range * 100, npv_curve * 100)
ax[1].axvline(prev * 100, linestyle="--")
ax[1].set_title("NPV vs Prevalence")
ax[1].set_xlabel("Prevalence (%)")
ax[1].set_ylabel("NPV (%)")
ax[1].set_ylim(0, 100)

st.pyplot(fig)
