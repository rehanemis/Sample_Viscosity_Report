"""Viscosity Temperature Analysis - Streamlit app.

Enter the viscosity at 40 C and 100 C and the ASTM D341 line is drawn
automatically. Download the chart as a PNG (for the image box of the fillable
PDF form) or the full page as a PDF / PNG.
"""
import datetime
import re

import streamlit as st

import viscosity as vz

st.set_page_config(page_title="Viscosity Temperature Analysis",
                   page_icon="\U0001F6E2\uFE0F", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1400px;}
    .hdr {background:#0B4A8F; color:#fff; padding:18px 26px 10px 26px; border-radius:6px 6px 0 0;}
    .hdr h1 {color:#fff; margin:0; font-size:1.9rem; letter-spacing:0.5px;}
    .hdr p {margin:2px 0 6px 0; font-size:0.8rem; letter-spacing:2px; opacity:0.95;}
    .bar {background:#F28C1B; height:7px; border-radius:0 0 6px 6px; margin-bottom:18px;}
    h3 {color:#0B4A8F;}
    </style>
    <div class="hdr"><h1>VISCOSITY TEMPERATURE ANALYSIS</h1>
    <p>LUBRICANT VISCOSITY CHARACTERISTICS</p></div><div class="bar"></div>
    """,
    unsafe_allow_html=True,
)


def password_ok():
    """Optional password gate: set APP_PASSWORD in the app's Secrets to enable it."""
    try:
        expected = st.secrets.get("APP_PASSWORD", None)
    except Exception:
        expected = None
    if not expected:
        return True
    if st.session_state.get("auth_ok"):
        return True
    pw = st.text_input("Password", type="password")
    if pw:
        if pw == expected:
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


@st.cache_data(show_spinner=False)
def build_outputs(lubricant, iso_vg, vi, v40, v100, date_text, comments, ops):
    """Draw everything once per set of inputs and return the file contents."""
    a, b = vz.fit_line(v40, v100)
    ops = list(ops)
    info = dict(lubricant=lubricant, iso_vg=iso_vg, vi=vi, v40=v40, v100=v100,
                date=date_text, comments=comments)
    sub = lubricant if lubricant else ""
    return dict(
        a=a,
        b=b,
        preview=vz.fig_bytes(vz.chart_figure(a, b, v40, v100, ops, sub), "png", 120),
        chart_png=vz.fig_bytes(vz.chart_figure(a, b, v40, v100, ops, sub), "png", 300),
        report_pdf=vz.fig_bytes(vz.report_figure(info, a, b, ops), "pdf"),
        report_png=vz.fig_bytes(vz.report_figure(info, a, b, ops), "png", 200),
    )


if not password_ok():
    st.stop()

left, right = st.columns([1, 2.3], gap="large")

with left:
    st.markdown("### Lubricant details")
    lubricant = st.text_input("Lubricant", value="Hydraulic Oil ISO VG 46 (example)")
    c1, c2 = st.columns(2)
    iso_vg = c1.text_input("ISO VG", value="46")
    vi = c2.text_input("Viscosity Index (VI)", value="100",
                       help="Typed in from the data sheet or lab report. It does not change the line.")
    v40 = st.number_input("Viscosity at 40 \u00b0C (cSt)", min_value=0.0, value=46.0,
                          step=0.1, format="%.2f")
    v100 = st.number_input("Viscosity at 100 \u00b0C (cSt)", min_value=0.0, value=6.8,
                           step=0.1, format="%.2f")
    date = st.date_input("Date plotted", value=datetime.date.today())
    comments = st.text_area("Comments", value="", height=80)

    st.markdown("### Operating conditions")
    t1, t2, t3 = st.columns(3)
    t_min = t1.number_input("Minimum (\u00b0C)", min_value=-20.0, max_value=165.0,
                            value=10.0, step=1.0)
    t_norm = t2.number_input("Normal (\u00b0C)", min_value=-20.0, max_value=165.0,
                             value=50.0, step=1.0)
    t_max = t3.number_input("Maximum (\u00b0C)", min_value=-20.0, max_value=165.0,
                            value=80.0, step=1.0)
    st.caption("Example values are filled in. Replace them with your own.")

with right:
    err = vz.check_inputs(v40, v100)
    if err:
        st.error(err)
        st.stop()
    if None in (t_min, t_norm, t_max):
        st.error("Enter all three operating temperatures.")
        st.stop()
    if not (t_min <= t_norm <= t_max):
        st.warning("Operating temperatures should go from minimum to maximum.")

    ops = (("Minimum", t_min), ("Normal Operating", t_norm), ("Maximum", t_max))
    out = build_outputs(lubricant, iso_vg, vi, float(v40), float(v100),
                        date.strftime("%d-%b-%Y"), comments, ops)

    m1, m2, m3 = st.columns(3)
    m1.metric("Slope B", f"{out['b']:.4f}")
    m2.metric("Constant A", f"{out['a']:.4f}")
    m3.metric("Viscosity at normal temp.",
              f"{vz.viscosity_at(t_norm, out['a'], out['b']):,.1f} cSt")

    st.image(out["preview"])

    rows = [{"Condition": name, "Temperature (\u00b0C)": f"{t:g}",
             "Viscosity (cSt)": f"{vz.viscosity_at(t, out['a'], out['b']):,.1f}"}
            for name, t in ops]
    st.table(rows)

    base = re.sub(r"[^A-Za-z0-9_-]+", "_", lubricant).strip("_") or "viscosity"
    d1, d2, d3 = st.columns(3)
    d1.download_button("Chart PNG (for form)", out["chart_png"],
                       file_name=f"{base}_chart.png", mime="image/png")
    d2.download_button("Full report PDF", out["report_pdf"],
                       file_name=f"{base}_report.pdf", mime="application/pdf")
    d3.download_button("Full report PNG", out["report_png"],
                       file_name=f"{base}_report.png", mime="image/png")
    st.caption("Chart PNG is 11 x 7 inches at 300 dpi (aspect ratio 11:7). "
               "Make the image box in the PDF form the same shape so the chart is not stretched.")
