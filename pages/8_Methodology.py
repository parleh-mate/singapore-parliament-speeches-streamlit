import streamlit as st

st.title("Metholodogy")

st.warning("Under construction.")

explainer = """
Data displayed on this website originates from the Singapore Parliament website. It is supplemented with member information, which is available from Wikipedia.

Want to learn more? See source code:
* Data pipeline: [singapore-parliament-speeches](https://github.com/jeremychia/singapore-parliament-speeches) (Github).
* Data modelling with dbt: [singapore-parliament-speeches-dbt](https://github.com/jeremychia/singapore-parliament-speeches-dbt) (Github).
* Streamlit app (_this_): [singapore-parliament-speeches-streamlit](https://github.com/jeremychia/singapore-parliament-speeches-streamlit) (Github).
* Data visualisation: [Looker Studio Dashboard](https://lookerstudio.google.com/u/1/reporting/e41e239f-a88a-45b9-b133-5c91bb1f3f13/page/p_jniba4ngfd).
"""

st.write(explainer)