import streamlit as st
COLORS = {"Observation": "#1E88E5", "Forecast": "#8E44AD", "Model estimate": "#F39C12",
          "Official bulletin (imported)": "#2E9E5B", "Sample data": "#7F8C8D"}

def inject_css():
    st.markdown("""<style>
    [data-testid=stSidebar]{background:#0B1F3A} [data-testid=stSidebar] *{color:#fff}
    .re-card{background:#fff;border:1px solid #DCE6F2;border-radius:12px;padding:14px 16px;height:150px}
    .re-t{font-size:.85rem;color:#5B6B7F}.re-v{font-size:1.8rem;font-weight:700;color:#0B1F3A}
    .re-s{font-size:.8rem;color:#1F2A3A}.re-m{font-size:.7rem;color:#8795A8;margin-top:4px}
    .re-b{display:inline-block;padding:1px 8px;border-radius:10px;color:#fff;font-size:.65rem}
    </style>""", unsafe_allow_html=True)

def badge(cls):
    return f'<span class="re-b" style="background:{COLORS.get(cls, "#7F8C8D")}">{cls}</span>'

def card(title, value, sub, source, cls, valid=""):
    st.markdown(f'<div class="re-card"><div class="re-t">{title}</div><div class="re-v">{value}</div>'
                f'<div class="re-s">{sub}</div><div class="re-m">{badge(cls)} {source} {valid}</div></div>',
                unsafe_allow_html=True)
