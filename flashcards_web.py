import streamlit as st
import pandas as pd
import io

# Funktion för att ladda fil
def ladda_fil(uploaded_file):
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=";")

        if df.shape[1] < 2:
            st.error("Filen måste innehålla minst två kolumner.")
            return None
        if "Status" not in df.columns:
            df["Status"] = ""

        df["OriginalIndex"] = df.index
        return df
    return None

# Funktion för att spara status
def spara_status(df, index, status):
    df.at[index, "Status"] = status

# Funktion för att filtrera frågor
def filtrera_frågor(df, filter_status):
    if df is None:
        return []
    if filter_status == "Alla":
        return list(df.iterrows())
    elif filter_status == "Kan":
        return list(df[df["Status"] == 1].iterrows())
    elif filter_status == "Kan inte":
        return list(df[df["Status"] == 0].iterrows())
    elif filter_status == "Obesvarade":
        return list(df[df["Status"].isna() | (df["Status"] == "")].iterrows())
    return list(df.iterrows())

# Nytt: Hantera filuppladdning direkt
with st.sidebar:
    st.write("Ladda upp en Excel- eller CSV-fil med dina flashcards 📄")

    # Visa videon om ingen fil är uppladdad ännu
    if 'df' not in st.session_state or st.session_state['df'] is None:
        st.video("media/instruktion.mp4")  # 🟢 ändra till din videofil
    uploaded_file = st.file_uploader("Välj en Excel- eller CSV-fil", type=["xlsx", "csv"])

if 'senaste_filnamn' not in st.session_state:
    st.session_state['senaste_filnamn'] = None
if 'df' not in st.session_state:
    st.session_state['df'] = None

if uploaded_file and uploaded_file.name != st.session_state['senaste_filnamn']:
    df = ladda_fil(uploaded_file)
    if df is not None:
        st.session_state['df'] = df
        st.session_state['index'] = 0
        st.session_state['visar_svar'] = False
        st.session_state['filter_status'] = "Alla"
        st.session_state['senaste_filnamn'] = uploaded_file.name
        st.success("Filen laddades in! ✅")
        st.rerun()

if 'df' in st.session_state and st.session_state['df'] is not None:
    df = st.session_state['df']
    with st.sidebar:
        filter_alternativ = ["Alla", "Kan", "Kan inte", "Obesvarade"]
        st.session_state['filter_status'] = st.selectbox("Filter", filter_alternativ, index=filter_alternativ.index(st.session_state.get('filter_status', "Alla")))

        filtrerade_frågor = filtrera_frågor(df, st.session_state['filter_status'])

        with st.expander("\U0001F4CB Visa översikt över frågor"):
            for vis_index, (org_index, fråga) in enumerate(filtrerade_frågor):
                fråga_text = fråga.iloc[0] if not isinstance(fråga, pd.Series) else list(fråga.values)[0]
                status = fråga.get("Status", "")

                cols = st.columns([8, 2, 2])
                with cols[0]:
                    st.markdown(f"**{fråga_text}**")
                with cols[1]:
                    symbol = "✅" if status == 1 else "❌" if status == 0 else "❓"
                    st.markdown(f"<span style='font-size: 20px'>{symbol}</span>", unsafe_allow_html=True)
                with cols[2]:
                    if st.button("Visa", key=f"visa_{org_index}"):
                        st.session_state['index'] = vis_index
                        st.session_state['visar_svar'] = False
                        st.rerun()

    if filtrerade_frågor:
        org_index, aktuell_fråga = filtrerade_frågor[st.session_state['index']]
        fråge_text = aktuell_fråga.iloc[0] if not isinstance(aktuell_fråga, pd.Series) else list(aktuell_fråga.values)[0]
        svar_text = aktuell_fråga.iloc[1] if not isinstance(aktuell_fråga, pd.Series) else list(aktuell_fråga.values)[1]

        st.subheader(f"Fråga: {fråge_text}")

        status = aktuell_fråga.get("Status", "")
        symbol = "✅" if status == 1 else "❌" if status == 0 else "❓"
        st.markdown(f"<span style='font-size: 24px'>{symbol}</span>", unsafe_allow_html=True)

        if st.session_state['visar_svar']:
            st.info(f"Svar: {svar_text}")

        cols_nav = st.columns(3)
        with cols_nav[0]:
            if st.button("⬅️ Föregående"):
                st.session_state['index'] = max(0, st.session_state['index'] - 1)
                st.session_state['visar_svar'] = False
                st.rerun()
        with cols_nav[1]:
            if st.button("👀 Visa svar"):
                st.session_state['visar_svar'] = not st.session_state['visar_svar']
                st.rerun()
        with cols_nav[2]:
            if st.button("➡️ Nästa"):
                st.session_state['index'] = min(len(filtrerade_frågor) - 1, st.session_state['index'] + 1)
                st.session_state['visar_svar'] = False
                st.rerun()

        cols_status = st.columns(2)
        with cols_status[0]:
            is_active = status == 1
            if st.button("👍 Kan", key="kan"):
                ny_status = None if is_active else 1
                spara_status(df, org_index, ny_status)
                st.rerun()
        with cols_status[1]:
            is_active = status == 0
            if st.button("👎 Kan inte", key="kan_inte"):
                ny_status = None if is_active else 0
                spara_status(df, org_index, ny_status)
                st.rerun()

        progress_value = (st.session_state['index'] + 1) / len(filtrerade_frågor)
        st.progress(progress_value)
        st.markdown(f"**{st.session_state['index'] + 1} / {len(filtrerade_frågor)}**")

        spara_df = df.drop(columns=["OriginalIndex"], errors="ignore")
        if st.session_state['senaste_filnamn'].endswith(".csv"):
            csv_buffer = io.StringIO()
            spara_df.to_csv(csv_buffer, index=False, sep=";")
            if st.download_button(label="💾 Spara", data=csv_buffer.getvalue(), file_name="flashcards_med_status.csv", mime="text/csv"):
                st.success("Fil sparad som 'flashcards_med_status.csv'")
        else:
            excel_buffer = io.BytesIO()
            spara_df.to_excel(excel_buffer, index=False)
            if st.download_button(label="💾 Spara", data=excel_buffer.getvalue(), file_name="flashcards_med_status.xlsx"):
                st.success("Fil sparad som 'flashcards_med_status.xlsx'")

    else:
        st.info("Inga frågor att visa med det valda filtret.")
else:
    st.info("Välj en Excel- eller CSV-fil för att starta.")
