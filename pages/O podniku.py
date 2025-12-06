import streamlit as st

st.set_page_config(page_title="O podniku – FixShop", layout="wide")

# --- HEADER S LOGOM ---
col1, col2 = st.columns([4, 1])
with col1:
    st.title("O podniku FixShop Bratislava")
with col2:
    st.image("fixshop.png", width= 150)  # môžeš meniť veľkosť

st.write("""
FixShop Bratislava je moderný špecializovaný servis mobilných telefónov, tabletov a počítačovej techniky s dôrazom na kvalitnú prácu, 
transparentné ceny a profesionálny prístup ku každému zákazníkovi.

Podnik vznikol ako rodinná firma so zámerom ponúknuť rýchly, spoľahlivý a odborný servis pre širokú verejnosť aj firemných klientov. 
FixShop ročne vybaví stovky servisných zásahov, pričom kladie dôraz na:

- odbornú diagnostiku  
- kvalitné náhradné diely  
- rýchly priebeh opráv  
- individuálny prístup k zákazníkovi  

V portfóliu služieb dominujú výmeny displejov, batérií, nabíjacích modulov, opravy matičných dosiek a bežná údržba zariadení. 
Zákazníci oceňujú stabilnú kvalitu, garanciu na prácu a férové ceny.
""")

st.subheader("Dodávatelia a používaný materiál")
st.write("""
FixShop spolupracuje s overenými dodávateľmi dielov z Európy aj Ázie, 
čo garantuje konzistentnú kvalitu komponentov a dostupnosť dielov pre najčastejšie modely na trhu.
""")

st.subheader("Tím a ľudské zdroje")
st.write("""
Servis zabezpečuje menší tím technikov so skúsenosťami v oblasti elektroniky a mikrolotovania.
Firma si zakladá na:

- pravidelnom školení technikov  
- zvyšovaní kvalifikácie v oblasti diagnostiky  
- internom systéme kontroly kvality  
""")

st.subheader("Vízia a hodnoty FixShopu")
st.write("""
Cieľom FixShopu je stať sa najspoľahlivejším lokálnym servisom v Bratislave, kde zákazník dostane profesionálny výsledok, 
jasné informácie a spravodlivú cenu.

FixShop stavia na hodnotách:

- **kvalita práce**  
- **rýchlosť a spoľahlivosť**  
- **čestnosť a transparentnosť**  
- **dlhodobé vzťahy so zákazníkmi**  
""")



