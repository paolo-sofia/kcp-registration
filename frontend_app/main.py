import json
import logging
import time
from enum import StrEnum
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple

import pendulum
import qrcode
import requests
import streamlit as st
from codicefiscale import codicefiscale

from database import schemas

logger = next(logging.getLogger(name) for name in logging.root.manager.loggerDict)

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}

API_BASE_URL: str = "http://api:8000"
DEFAULT_TIMEZONE: str = "Europe/Rome"

activity_cols: Dict[str, str] = {
    "kart": "Kart non agonistico",
    "moto": "Motociclismo non agonistico",
    "altro": "Frequentazione spazi associativi a scopo ludico/ricreativo (Non sportivo)",
}

tipo_utente_cols: Dict[str, str] = {
    "socio": "Socio/a",
    "tesserato": "Tesserato/a",
}


class FormName(StrEnum):
    NOME = "nome"
    COGNOME = "cognome"
    DATA_NASCITA = "data_nascita"
    LUOGO_NASCITA = "luogo_nascita"
    PROVINCIA_NASCITA = "provincia_nascita"
    CODICE_FISCALE = "codice_fiscale"
    LUOGO_RESIDENZA = "luogo_residenza"
    VIA_RESIDENZA = "via_residenza"
    PROVINCIA_RESIDENZA = "provincia_residenza"
    TELEFONO = "telefono"
    DATA_REGISTRAZIONE = "data_registrazione"
    REGOLAMENTO_ASSOCIATIVO = "regolamento_associativo"
    PRIVACY_POLICY = "privacy_policy"
    TIPO_UTENTE = "tipo_utente"
    ATTIVITA = "attivita"


def decodifica_codice_fiscale(cod_fiscale: str) -> Dict[str, Any]:
    if not codicefiscale.is_valid(cod_fiscale):
        st.error("Codice fiscale non valido, inserire codice fiscale corretto")
        return {}

    decoded_cod_fiscale: Dict[str, Any] = codicefiscale.decode(cod_fiscale)
    return {
        FormName.DATA_NASCITA: decoded_cod_fiscale.get("birthdate", pendulum.datetime(1970, 1, 1, tz=DEFAULT_TIMEZONE)),
        FormName.LUOGO_NASCITA: decoded_cod_fiscale.get("birthplace", {}).get("name", ""),
        FormName.PROVINCIA_NASCITA: decoded_cod_fiscale.get("birthplace", {}).get("province", ""),
    }


def regolamento_associativo_popup() -> bool:
    regolamento_associativo = f"""Il/La sottoscritto/a
- dichara di aver letto e compreso in ogni dettaglio il regolamento associativo {pendulum.now(DEFAULT_TIMEZONE).year} per le predette attività, predisposto dalla stessa asd motorart
- di aver compreso che i soci ordinari rispondono in prima persona delle azioni compiute all'interno degli spazi associativi ed in particolare nell'utilizzo dei kart/moto/mini-moto e che gli istruttori sportivi rispondono nei limiti di quanto previsto dal regolamento associativo {pendulum.now(DEFAULT_TIMEZONE).year} ovvero per quanto direttamente connesso alle direttive impartite secondo la corretta disciplina sportiva.
- chiede di utilizzare la copertura assicurativa base (così indicata nella polizza assicurativa dell'asd visionata insieme al regolamento associativo) versando per la quota associativa la somma di €__
- chiede di utilizzare la copertura assicurativa integrativa (che prevede l'abbattimento delle franchigie e l'innalzamento dei rimborsi così come indicato nella polizza assicurativa dell'asd visionata insieme al regolamento associativo) versando la somma integrativa di € __
- il sottoscritto allega alla sottoscritta il certificato di idionetá alla pratica sportiva non agonistica
- il sottoscritto dichiara sotto la propria responsabilitá (consapevole delle conseguenze civili/penali delle dichiarazioni mendaci) di possedere il certificato - si impegna all'invio telematico.
- chiede di essere informato via mail/sms/whatsapp e altri mezzi di comunicazione sulle attività dell'associazione
"""

    with st.expander("Dichiarazione di responsabilita'", expanded=False):
        st.markdown(regolamento_associativo)
        return st.checkbox(label="Ho letto ed accetto il Regolamento associativo")


def privacy_policy_popup() -> bool:
    privacy_policy = """INFORMATIVA ex art. 13 del REGOLAMENTO (UE) 2016/679
Gentile Signore/a, gentile socio/a, GENTILE GENITORE DEL/LA MINORENNE desideriamo informarLa, in qualità di Titolari del trattamento, che il Regolamento UE/2016/679 Generai Data Protection Regulation (G.D.P.R.), di immediata applicazione anche in Italia, prevede la tutela delle persone e di altri soggetti rispetto al trattamento dei dati personali. Secondo la normativa indicata, tale trattamento sarà improntato ai principi di correttezza, liceità, trasparenza e tutela della Sua riservatezza e dei Suoi diritti. Ai sensi dell'articolo 13 del G.D.P.R., pertanto, Le fornisco le seguenti informazioni:
1. I dati personali anagrafici e di recapiti, da Lei forniti verranno trattati per le seguenti finalità basate sul Suo consenso e sul legittimo interesse della scrivente ASD: inserimento nel libro dei soci e tesseramento ASC ed ogni altro utilizzo attinente ai suddetti rapporti associativi e di tesseramento sportivo. 2. Base giuridica di tale operazione sono l'art. 36 del C.C., la normativa fiscale relativa agli enti non commerciali, in particolare l'art. 148 del T.U.I.R., l'art. 4 del D.P.R. 633/72 e l'art. 90 della Legge 289/2002, nonché le norme del CONI e dell'A.S.C. relative al tesseramento e alla partecipazione alle attività organizzate da tali enti o con la loro partecipazione. 3. I legittimi interessi del titolare del trattamento perseguiti con tale attività sono una chiara e corretta applicazione delle disposizioni statutarie sull'ordinamento interno e l'amministrazione dell'associazione, la possibilità di usufruire delle agevolazioni fiscali spettanti all'associazione, la possibilità di partecipare alle attività organizzate dagli enti citati al precedente punto l. 4. Il trattamento sarà effettuato con le seguenti modalità: su schede manuali, realizzate anche con l'ausilio di mezzi elettronici, conservate in luoghi chiusi, la cui chiave è detenuta dal Presidente e dagli incaricati dell' amministrazione, ovvero in maniera informatizzata, su un PC detenuto esclusivamente dal Presidente dell'associazione che è attrezzato adeguatamente contro i rischi infornatici (firewall, antivirus, backup periodico dei dati); autorizzati ad accedere a tali dati sono il presidente e gli incaricati da quest'ultimo ai fini dell'amministrazione. Ai sensi dell'art.4 n. 2del G.D.P.R, il trattamento dei dati personali potrà consistere nella raccolta, registrazione, organizzazione, consultazione, elaborazione, modificazione, selezione, estrazione, raffronto, utilizzo, interconnessione, blocco, comunicazione, cancellazione e distruzione dei dati. 5. I dati personali saranno conservati per tutto il tempo indispensabile a una corretta tenuta del libro dei soci e/o per procedere alle formalità richieste dalle Federazioni Sportive e/o gli Enti di Promozione Sportiva cui siamo affiliati: tale termine è determinato dal codice civile, dalla normativa fiscale e dalle norme e regolamenti del CONI e del l'A.S.C. cui siamo affiliati. La verifica sulla obsolescenza dei dati oggetto di trattamento rispetto alle finalità perle quali sono stati raccolti e trattati viene effettuata periodicamente.
6. Il conferimento dei dati è obbligatorio per il raggiungimento delle finalità dello statuto dell'Associazione ed è quindi indispensabile per consentirci di accogliere la sua domanda di ammissione a socio e/o per il tesseramento presso i soggetti indicati al punto precedente; l'eventuale rifiuto a fornirli comporta l'impossibilità di accogliere la Sua domanda di iscrizione e/o tesseramento, non essendo in tale ipotesi possibile instaurare l'indicato rapporto associativo e/o di tesseramento presso gli enti cui l'Associazione è affiliata. 7. I dati anagrafici potranno essere comunicati esclusivamente all'A.S.C..; tutti i dati non saranno comunicati ad altri soggetti, né saranno oggetto di diffusione. 8. Il trattamento non riguarderà dati personali rientranti nel novero dei dati "sensibili", vale a dire "i dati personali idonei a rivelare l'origine razziale ed etnica, le convinzioni religiose, filosofiche o di altro genere, le opinioni politiche, l'adesione a partiti, sindacati, associazioni od organizzazioni a carattere religioso, filosofico, politico o sindacale, nonché i dati personali idonei a rivelare lo stato di salute e la vita sessuale". I dati sanitari sono conservati a cura del medico incaricato degli accertamenti inerenti all'idoneità sportiva, medico che provvede in proprio al loro trattamento. 9. Il titolare del trattamento è ANDREA PALAZZO, legale rappresentante della ASD MOTORART con sede in c/da MONTADA, n° 18 - TRECCHINA (PZ), contattabile all' indirizzo mail: palazzo.and@gmail.com. IO. Il responsabile del trattamento è l'incaricato ANDREA PALAZZO contattabile all'indirizzo mail predetto. In ogni momento Lei potrà esercitare i Suoi diritti di conoscere i dati che La riguardano, sapere come sono stati acquisiti, verificare se sono esatti, completi, aggiornati e ben custoditi, di ricevere i dati in un formato strutturato, di uso comune e leggibile da dispositivo automatico, di revocare il consenso eventualmente prestato relativamente al trattamento dei Suoi dati in qualsiasi momento ed opporsi in tutto od in parte, all' utilizzo degli stessi come sanciti dagli artt. da 15 a 20 del G.D.P.R. Tali diritti possono essere esercitati attraverso specifica istanza da indirizzare tramite raccomandata - o PEC- al Titolare del trattamento. 11. Lei ha in diritto di revocare il consenso in qualsiasi momento senza pregiudicare la liceità del trattamento basata sul consenso prestato prima della revoca. Tale diritto potrà essere esercitato inviando la revoca del consenso all' indirizzo e-mail indicato nei precedenti punti.12. Lei ha il diritto di proporre reclamo al Garante per la protezione dei dati personali ovvero a alla diversa autorità di controllo che dovesse essere istituita dal Decreto previsto della Legge Comunitaria n.163/2017 13. Non esiste alcun processo decisionale automatizzato, né alcuna attività di profilazione di cui all'articolo 22, paragrafi I e 4 del G.D.P.R.
Il/La sottoscritto/a autorizza nel contempo il trattamento dei dati inseriti nella presente comunicazione e modulistica.
   """
    with st.expander("Consenso al trattamento dei dati", expanded=False):
        st.markdown(privacy_policy)
        return st.checkbox("Ho letto ed accetto la Privacy Policy")


def show_regolamento_associativo() -> None:
    regolamento_associativo = """
1. L'accesso agli spazi associativi (pista di kart/moto, paddock etc...) è consentito esclusivamente ai soci in regola con il tesseramento per anno 2022, previa ammissione da parte del Direttivo e a suo insindacabile giudizio;
2. Prima e dopo il predetto tesseramento è possibile un periodo di training per (l'utilizzo dei veicoli mediante professionisti convenzionati con |'ASD allo scopo di apprendere la guida sicura all'interno del circuito. Tali professionisti applicheranno il loro codice deontologiche e le loro tariffe. La responsabilità professionale di tali sessioni di apprendimento ricade sul professionista e sull'allievo in base alla normativa vigente;
3. I soci e gli allievi delle sessioni di apprendimento seguono le indicazioni in materia di sicurezza e di ordine negli spazi associativi, in particolare della pista di Go-Kart, del Presidente e del Direttivo: coloro i quali non si attengano alle indicazioni predette possono essere inibiti dall'utilizzo delle attrezzature con effetto immediato e, ricorrendo le condizioni previste dallo Statuto associativo dell'ASD, possono essere espulsi dalla stessa associazione.
A) PISTA GO-KART
1. Per l'accesso alla pista e per l'utilizzo dei veicoli è previsto il versamento di un contributo in base al tempo di utilizzo effettivo: tale contributo è volontario, in quanto il socio può decidere volontariamente se utilizzare o meno gli spazi associativi per quanto tempo decida lui stesso, ma a condizione di versare il contributo deciso dal Direttivo ed esposto nelle comunicazioni visibili all'ingresso degli spazi associativi;
2. All'interno della pista e degli ambienti di utilizzo delle attrezzature del kartodromo il socio è tenuto a rispettare le REGOLE DI COMPORTAMENTO - in particolare:
	- è vietato arrecare danno alle altre automobili mediante contatto
	volontario o negligente
	- è vietato guidare sotto l'effetto di alcool o droghe
	- è obbligatorio utilizzare l'abbigliamento idoneo per la guida
	- è vietato accedere ai box a velocità sostenuta e comunque superiore
	a quella prevista dalla segnaletica accessoria
	- è obbligatorio arrestare la propria guida nell'eventualità di FERMO
	PISTA, ovvero di veicoli fermi per motivi tecnici o di sicurezza
	- è vietato scendere dal proprio veicolo qualora dovesse arrestarsi
	- è OBBLIGATORIO nella maniera più assoluta INDOSSARE IL CASCO
	BEN ALLACCIATO
	- IL MATERIALE E LE ATTREZZATURE PER L'UTILIZZO DEI KART DEVONO ESSERE RESTITUITI LADDOVE SIANO STATI PRELEVATI
    """
    with st.expander("Leggi il regolamento associativo", expanded=False):
        st.write(regolamento_associativo)


def generate_and_show_qr_code(user: Dict[str, Any]) -> None:
    digest: str = sha256(json.dumps(user, sort_keys=True).encode("utf8")).hexdigest()
    img = qrcode.make(digest)
    st.image(img)


def validate_data(user_data: Dict[str, Any]) -> bool:
    validated: bool = bool(
        user_data.get(FormName.NOME)
        and user_data.get(FormName.COGNOME)
        and user_data.get(FormName.DATA_NASCITA)
        and user_data.get(FormName.LUOGO_NASCITA)
        and user_data.get(FormName.CODICE_FISCALE)
        and user_data.get(FormName.LUOGO_RESIDENZA)
        and user_data.get(FormName.VIA_RESIDENZA),
    )

    if not validated:
        return validated

    for gender in ["M", "F"]:
        test_fiscal_code: str = codicefiscale.encode(
            lastname=user_data.get(FormName.COGNOME),
            firstname=user_data.get(FormName.NOME),
            gender=gender,
            birthdate=user_data.get(FormName.DATA_NASCITA),
            birthplace=user_data.get(FormName.LUOGO_NASCITA),
        )[:-5].upper()

        if test_fiscal_code == user_data.get(FormName.CODICE_FISCALE)[:-5]:
            return True

    return False


def validate_child(child: Dict[str, str], child_min_date: pendulum.Date) -> bool:
    st.error(f"child min date {child_min_date} {type(child_min_date)}")
    default_date: str = pendulum.today().date().strftime("%Y-%m-%d")
    st.error(f"child date {child.get(FormName.DATA_NASCITA, default_date)}")
    data_nascita: pendulum.date = pendulum.from_format(child.get(FormName.DATA_NASCITA, default_date), "YYYY-MM-DD",
                                                       tz="Europe/Rome").date()
    st.error(f"computed date {data_nascita} {type(data_nascita)}")

    return bool(
        child.get(FormName.NOME, "")
        and child.get(FormName.COGNOME, "")
        and data_nascita > child_min_date
        and codicefiscale.is_valid(child.get(FormName.CODICE_FISCALE, "")),
    )


def validate_children(children: List[Dict[str, str]]) -> bool:
    child_min_date: pendulum.Date = pendulum.today(DEFAULT_TIMEZONE).subtract(years=18).add(days=1).date()

    return all(validate_child(child, child_min_date) for child in children)


def add_child() -> List[Dict[str, str]]:
    if "children" not in st.session_state:
        print("children not in session state")
        st.session_state["children"] = []

    today: pendulum.datetime = pendulum.today(DEFAULT_TIMEZONE)

    child_min_date: pendulum.date = today.subtract(years=18).add(days=1).date()
    child_max_date: pendulum.date = today.subtract(years=6).date()

    st.subheader("Sezione Genitori", divider="red")
    accept_child: bool = st.checkbox(
        label="Dichiaro di esercitare la potestà genitoriale sul/i minorenne/i registrato in quanto padre o madre dello stesso"
              " (Consapevole delle conseguenze civili e penali delle dichiarazioni mendaci)")

    num_child: int = st.selectbox(label="Quanti figli devono guidare il kart?", options=list(range(20)), index=0)

    children: List[Dict[str, str]] = []
    for i in range(num_child):
        st.subheader(f"Dati Figlio/a {i + 1}", divider="red")

        child_name = st.text_input(
            label="Nome :red[*]",
            key=f"nome_figlio_{i}",
            disabled=not accept_child,
        )
        child_surname = st.text_input(
            label="Cognome :red[*]",
            key=f"cognome_figlio_{i}",
            disabled=not accept_child,
        )
        child_codice_fiscale = st.text_input(
            label="Codice fiscale figlio/a :red[*]",
            max_chars=16,
            key=f"cod_fiscale_figlio_{i}",
            disabled=not accept_child,
        )

        data_nascita_figlio = st.date_input(
            label="Data di Nascita :red[*]",
            disabled=not accept_child,
            min_value=child_min_date,
            max_value=child_max_date,
            value=child_min_date,
            key=f"data_nascita_figlio_{i}")

        child_type: str = st.radio(
            label="Tipologia ammissione figlio/a",
            options=["tesserato", "socio"],
            index=0,
            key="child_type",
            format_func=tipo_utente_cols.get,
        )

        child_activity: str = st.radio(
            label="Tipologia attivita' figlio/a",
            options=["kart", "moto", "altro"],
            key="child_activity",
            format_func=activity_cols.get,
            index=0,
        )

        children.append({
            str(FormName.NOME): " ".join([x.capitalize() for x in child_name.split()]),
            str(FormName.COGNOME): " ".join([x.capitalize() for x in child_surname.split()]),
            str(FormName.DATA_NASCITA): str(data_nascita_figlio),
            str(FormName.CODICE_FISCALE): child_codice_fiscale.upper(),
            str(FormName.TIPO_UTENTE): child_type,
            str(FormName.ATTIVITA): child_activity,
        })

    return children


def clear_session_state() -> None:
    fields_to_clear: List[str] = [
        FormName.NOME,
        FormName.COGNOME,
        FormName.CODICE_FISCALE,
        FormName.DATA_NASCITA,
        FormName.LUOGO_NASCITA,
        FormName.VIA_RESIDENZA,
        FormName.LUOGO_RESIDENZA,
        FormName.LUOGO_RESIDENZA,
        FormName.DATA_REGISTRAZIONE,
        FormName.TELEFONO,
        "children",
        "renew",
    ]

    for variable in fields_to_clear:
        if variable in st.session_state:
            del st.session_state[variable]


def update_user_data(json_data: Dict[str, str]) -> None:
    for field in schemas.UserBase.model_fields:
        value = json_data.get(field, "")

        if field not in st.session_state or st.session_state[field] != value:
            st.session_state[field] = value


def registration_form(user_to_renew: schemas.User = None):
    if "renew" not in st.session_state or not st.session_state.renew:
        st.session_state["renew"] = bool(user_to_renew)

    if st.session_state.renew:
        default_values = {
            FormName.CODICE_FISCALE: st.session_state[FormName.CODICE_FISCALE] or "",
            FormName.NOME: st.session_state[FormName.NOME] or "",
            FormName.COGNOME: st.session_state[FormName.COGNOME] or "",
            FormName.DATA_NASCITA: st.session_state[FormName.DATA_NASCITA] or pendulum.date(1970, 1, 1),
            FormName.LUOGO_NASCITA: st.session_state[FormName.LUOGO_NASCITA] or "",
            FormName.LUOGO_RESIDENZA: st.session_state[FormName.LUOGO_RESIDENZA] or "",
            FormName.VIA_RESIDENZA: st.session_state[FormName.VIA_RESIDENZA] or "",
            FormName.TELEFONO: st.session_state[FormName.TELEFONO] or "",
        }
        update_user_data(default_values)
    else:
        default_values = {
            FormName.CODICE_FISCALE: "",
            FormName.NOME: "",
            FormName.COGNOME: "",
            FormName.DATA_NASCITA: pendulum.date(1970, 1, 1),
            FormName.LUOGO_NASCITA: "",
            FormName.LUOGO_RESIDENZA: "",
            FormName.VIA_RESIDENZA: "",
            FormName.TELEFONO: "",
        }

    # with st.form('registration_form'):
    today: pendulum.date = pendulum.today().date()
    with st.container():
        show_regolamento_associativo()

        fiscal_code = st.text_input(
            label="Codice Fiscale :red[*]",
            max_chars=16,
            disabled=st.session_state.renew,
            value=default_values[FormName.CODICE_FISCALE],
        )

        if fiscal_code:
            decoded_cod_fiscale: Dict[str, Any] = decodifica_codice_fiscale(fiscal_code)
            birth_place = st.text_input(
                label="Luogo di Nascita :red[*]",
                value=decoded_cod_fiscale.get(FormName.LUOGO_NASCITA, ""),
                disabled=st.session_state.renew,
            )
            birth_date = st.date_input(
                label="Data di Nascita :red[*]",
                value=decoded_cod_fiscale.get(FormName.DATA_NASCITA,
                                              pendulum.datetime(1970, 1, 1, tz=DEFAULT_TIMEZONE)).date(),
                min_value=today.replace(year=today.year - 100),
                max_value=today.replace(year=today.year - 18),
                disabled=st.session_state.renew,
            )
        else:
            birth_place = st.text_input(
                label="Luogo di Nascita :red[*]",
                disabled=st.session_state.renew,
                value=default_values[FormName.LUOGO_NASCITA],
            )
            birth_date = st.date_input(
                label="Data di Nascita :red[*]",
                value=default_values[FormName.DATA_NASCITA],
                min_value=today.replace(year=today.year - 100),
                max_value=today.replace(year=today.year - 18),
                disabled=st.session_state.renew,
            )

        name = st.text_input(
            label="Nome :red[*]",
            disabled=st.session_state.renew,
            value=default_values[FormName.NOME],
        )
        surname = st.text_input(
            label="Cognome :red[*]",
            disabled=st.session_state.renew,
            value=default_values[FormName.COGNOME],
        )
        residence_place = st.text_input(
            label="Luogo di Residenza :red[*]",
            disabled=False,
            value=default_values[FormName.LUOGO_RESIDENZA],
        )
        residence_street = st.text_input(
            label="Via di Residenza :red[*]",
            disabled=False,
            value=default_values[FormName.VIA_RESIDENZA],
        )
        phone_number = st.text_input(
            label="Numero di telefono",
            disabled=False,
            value=default_values[FormName.TELEFONO],
        )

        user_type: str = st.radio(
            label="Tipologia ammissione",
            options=["tesserato", "socio"],
            format_func=tipo_utente_cols.get,
        )

        user_activity: str = st.radio(
            label="Tipologia attivita'",
            options=["kart", "moto", "altro"],
            format_func=activity_cols.get,
            index=0,
        )

        regolamento_associativo: bool = regolamento_associativo_popup()
        privacy_policy: bool = privacy_policy_popup()

        children: List[Dict[str, str]] = add_child()

        user_data = {
            str(FormName.CODICE_FISCALE): fiscal_code.upper(),
            str(FormName.NOME): " ".join([x.capitalize() for x in name.split()]),
            str(FormName.COGNOME): " ".join([x.capitalize() for x in surname.split()]),
            str(FormName.DATA_NASCITA): str(birth_date),
            str(FormName.LUOGO_NASCITA): " ".join([x.capitalize() for x in birth_place.split()]),
            str(FormName.LUOGO_RESIDENZA): " ".join([x.capitalize() for x in residence_place.split()]),
            str(FormName.VIA_RESIDENZA): " ".join([x.capitalize() for x in residence_street.split()]),
            str(FormName.TELEFONO): phone_number,
            str(FormName.TIPO_UTENTE): user_type,
            str(FormName.ATTIVITA): user_activity,
        }
        update_user_data(user_data)

        data_validated: bool = validate_data(user_data) and validate_children(children) and regolamento_associativo \
                               and privacy_policy

        register_button = st.columns(5)[2].button(
            label="Firma",
            disabled=not data_validated,
            type="primary",
            use_container_width=True,
        )

        if not register_button or not privacy_policy or not regolamento_associativo:
            return

        if st.session_state.renew:
            parent_id: Optional[int] = renew_user(user_data)
        else:
            parent_id: Optional[int] = save_user_to_db(user_data)
        if not parent_id:
            return

        if not children:
            clear_session_state()
            time.sleep(2)
            st.experimental_rerun()
            return

        children_ids: List[int] = save_children_to_db(children, parent_id)
        if not children_ids:
            st.write("error saving children")
            if not remove_children_from_db(children_ids):
                st.write("error removing children")
                return
            return

        clear_session_state()
        time.sleep(2)
        st.experimental_rerun()


def remove_children_from_db(children_id: List[int]) -> bool:
    response = requests.delete(f"{API_BASE_URL}/childrens/", json=children_id, headers=HEADERS)

    return response.status_code == 200


def save_children_to_db(children: List[Dict[str, str]], parent_id: int) -> Optional[List[int]]:
    response = requests.post(
        url=f"{API_BASE_URL}/childrens/{parent_id}",
        json=children,
        headers=HEADERS,
    )

    return response.json() if response.status_code == 200 else None


def save_user_to_db(user_data: Dict[str, str]) -> Optional[int]:
    user_data = {str(k): str(v) for k, v in user_data.items()}
    response = requests.post(f"{API_BASE_URL}/users", json=user_data, headers=HEADERS, params={})
    if response.status_code == 200:
        st.success("Utente registrato correttamente!")

        return response.json().get("id", -1)

    st.error("Errore durante la registrazione, riprova.")
    return None


def renew_user(user_data: Dict[str, str]) -> Optional[int]:
    response = requests.put(f"{API_BASE_URL}/users/", json=user_data)
    if response.status_code == 200:
        st.success("Utente aggiornato correttamente!")
        return response.json()

    st.error("Errore durante l'aggiornamento dell'utente, riprova.")
    return None


def handle_registered_user(response: Dict[str, Any]) -> Optional[schemas.User]:
    if not response:
        st.error("Utente non registrato, registrati usando il form")
        return None

    default_renew, minor_renew = check_if_user_needs_renew(response.get(FormName.DATA_REGISTRAZIONE),
                                                           response.get(FormName.DATA_NASCITA))
    if default_renew:
        st.warning("Hai effettuato la registrazione più di un anno fa, ricompila il modulo per favore")
        return schemas.User(**response)
    elif minor_renew:
        st.warning("Quando hai effettuato la registrazione eri minorenne, ricompila il modulo per favore")
        return schemas.User(**response)

    st.success("Sei già registrato, grazie e buon divertimento")
    return None


def already_registered_form() -> Optional[schemas.User]:
    with st.form("already_registered_form"):
        st.markdown("#### Controllo utente registrato")
        fiscal_code: str = st.text_input("Codice Fiscale")
        if not st.columns(5)[2].form_submit_button("Cerca", use_container_width=True, type="secondary"):
            return None

        try:
            response = requests.get(f"{API_BASE_URL}/users/{fiscal_code.upper()}", headers=HEADERS)
            if response.status_code == 200:
                return handle_registered_user(response.json())
            else:
                st.error("Errore durante la ricerca, riprova.")
        except Exception as e:
            st.error(f"Errore durante la ricerca, riprova {e}")
    return None


def check_if_minor_at_date(data_nascita: pendulum.datetime, other_date: pendulum.datetime) -> bool:
    if other_date.year - data_nascita.year < 18:
        return True

    if other_date.month - data_nascita.month < 0:
        return True

    if other_date.day - data_nascita.day < 0:
        return True
    return False


def check_if_user_needs_renew(data_registrazione: str, data_nascita: str) -> Tuple[bool, bool]:
    data_registrazione: pendulum.datetime = pendulum.from_format(data_registrazione, "YYYY-MM-DD", tz=DEFAULT_TIMEZONE)
    data_nascita: pendulum.datetime = pendulum.from_format(data_nascita, "YYYY-MM-DD", tz=DEFAULT_TIMEZONE)

    is_default_renew: bool = pendulum.now(tz=DEFAULT_TIMEZONE).diff(data_registrazione).days > 365
    is_minor_at_date: bool = check_if_minor_at_date(data_nascita, data_registrazione)
    is_minor_today: bool = check_if_minor_at_date(data_nascita, pendulum.today(tz=DEFAULT_TIMEZONE))

    return is_default_renew, is_minor_at_date and not is_minor_today


def prettify_link(link: str, text: str) -> str:
    return f'<a href="{link}" style="color : #fb2029;"> {text}</a>'


def social_media_icons():
    st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <a href="https://www.instagram.com/kartcircuitpalazzo_trecchina/" target="_blank"><img width="40" height="40" src="https://img.icons8.com/office/50/instagram-new.png" alt="instagram-new"/></a>
        <a href="https://www.facebook.com/kartodromo.palazzo" target="_blank"><img width="40" height="40" src="https://img.icons8.com/color/40/facebook-new.png" alt="facebook-new"/></a>
        <a href="https://github.com/paolo-sofia/kcp-registration" target="_blank"><img width="40" height="40" src="https://img.icons8.com/color-glass/50/github--v1.png" alt="github--v1"/></a>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="KCP Registrazione",
        page_icon="data/img/kcp_logo_small.png",
        layout="centered",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://kartodromopalazzo.it/",
            "Report a bug": "https://github.com/paolo-sofia/kcp-registration/issues",
            "About": "# This is a header. This is an *extremely* cool app!",
        },
    )
    with st.columns(3)[1]:
        st.image(
            image="frontend_app/data/img/kcp_logo_small.png",
            use_column_width="auto",
            width=250,
        )
    st.title("KCP - Registrazione utente")

    st.markdown(f"""
##### Benvenuto al kart circuit Palazzo
Per poter continuare devi compilare il modulo di registrazione.
- Se sei gia' stato qui', inserisci nel {prettify_link('#controllo-utente-registrato', 'form seguente')} il tuo codice fiscale per confermare che sei gia' registrato
- Se non sei mai stato qui', devi compilare il {prettify_link('#form-di-registrazione', 'form in basso')}. Se sei un genitore, inserisci i tuoi dati nel form, mentre nella parte {prettify_link('#sezione-genitori', 'Sezione genitori')}, inserisci i dati dei figli che devono fare il giro sui kart
    """, unsafe_allow_html=True)

    user_to_renew = already_registered_form()
    if user_to_renew:
        st.session_state.renew = True
        update_user_data(user_to_renew.model_dump())

    st.subheader("Form di registrazione", divider="red")
    registration_form(user_to_renew=user_to_renew)

    st.markdown("---")
    social_media_icons()


if __name__ == "__main__":
    main()
