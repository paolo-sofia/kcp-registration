import json
import logging
import time
from enum import StrEnum
from hashlib import sha256
from typing import Any, Dict, List, Optional

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
    regolamento_associativo = """This is the privacy policy text.
    Please read the entire content carefully before proceeding.
    By clicking 'Accept', you acknowledge that you have read and understood the policy.
       """

    st.text_area(
        label="Regolamento Associativo ASD Motorart",
        key="regolamento associativo_text_area",
        value=regolamento_associativo,
        disabled=True,
    )
    return st.checkbox(label="Ho letto ed accetto il Regolamento associativo")


def privacy_policy_popup() -> bool:
    privacy_policy = """This is the privacy policy text.
Please read the entire content carefully before proceeding.
By clicking 'Accept', you acknowledge that you have read and understood the policy.
   """

    st.text_area("Consenso del trattamento dei dati", privacy_policy, key="privacy_policy_text_area", disabled=True)
    return st.checkbox("Ho letto ed accetto la Privacy Policy")


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
    default_date: str = pendulum.today().date().strftime("%Y-%m-%d")
    return bool(
        child.get(FormName.NOME, "")
        and child.get(FormName.COGNOME, "")
        and pendulum.from_format(child.get(FormName.DATA_NASCITA, default_date), "YYYY-MM-DD",
                                 tz="Europe/Rome").date() > child_min_date
        and codicefiscale.is_valid(child.get(FormName.CODICE_FISCALE, "")),
    )


def validate_children(children: List[Dict[str, str]]) -> bool:
    child_min_date: pendulum.Date = pendulum.today(DEFAULT_TIMEZONE).today().subtract(years=18).add(days=1)

    return all(validate_child(child, child_min_date) for child in children)


def add_child() -> List[Dict[str, str]]:
    if "children" not in st.session_state:
        print("children not in session state")
        st.session_state["children"] = []

    today: pendulum.datetime = pendulum.today(DEFAULT_TIMEZONE)

    child_min_date: pendulum.date = today.subtract(years=18).add(days=1).date()
    child_max_date: pendulum.date = today.subtract(years=6).date()

    st.subheader("Sezione Genitori")
    accept_child: bool = st.checkbox(
        label="Dichiaro di esercitare la potestà genitoriale sul/i minorenne/i registrato in quanto padre o madre dello stesso"
              " (Consapevole delle conseguenze civili e penali delle dichiarazioni mendaci)")

    num_child: int = st.selectbox(label="Quanti figli devono guidare il kart?", options=list(range(20)), index=0)

    children: List[Dict[str, str]] = []
    for i in range(num_child):
        st.subheader(f"Dati Figlio {i + 1}")

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
            label="Codice fiscale figlio :red[*]",
            max_chars=16,
            key=f"cod_fiscale_figlio_{i}",
            disabled=not accept_child,
        )

        children.append({
            str(FormName.NOME): " ".join([x.capitalize() for x in child_name.split()]),
            str(FormName.COGNOME): " ".join([x.capitalize() for x in child_surname.split()]),
            str(FormName.DATA_NASCITA): str(st.date_input("Data di Nascita :red[*]", disabled=not accept_child,
                                                          min_value=child_min_date, max_value=child_max_date,
                                                          value=child_min_date, key=f"data_nascita_figlio_{i}")),
            str(FormName.CODICE_FISCALE): child_codice_fiscale.upper(),
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
    }
    update_user_data(user_data)

    data_validated: bool = validate_data(user_data) and validate_children(children) and regolamento_associativo \
                           and privacy_policy

    _, _, col, _, _ = st.columns(5)

    with col:
        register_button = st.button("Firma", disabled=not data_validated)

    if not register_button or not privacy_policy or not regolamento_associativo:
        return

    if st.session_state.renew:
        parent_id: Optional[int] = renew_user(user_data)
    else:
        parent_id: Optional[int] = save_user_to_db(user_data)
    if not parent_id:
        return

    st.write(f"parent_id {parent_id}")
    st.write(f"Children {children}")
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

    st.write(f"Before clearing session\n{st.session_state}")
    clear_session_state()
    st.write(f"After clearing session\n{st.session_state}")
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
    st.write(user_data)

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

    if check_if_user_needs_renew(response.get(FormName.DATA_REGISTRAZIONE), response.get(FormName.DATA_NASCITA)):
        st.warning("Hai effettuato la registrazione più di un anno fa, ricompila il modulo per favore")
        return schemas.User(**response)

    st.success("Sei già registrato, grazie e buon divertimento")
    return None


def already_registered_form() -> Optional[schemas.User]:
    st.markdown("#### Inserisci nome e cognome")
    with st.form("already_registered_form"):
        fiscal_code: str = st.text_input("Codice Fiscale")

        if not st.form_submit_button("Cerca", use_container_width=True):
            return None

        try:
            response = requests.get(f"{API_BASE_URL}/users/{fiscal_code.upper()}", headers=HEADERS)
            st.write(response.json())
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


def check_if_user_needs_renew(data_registrazione: str, data_nascita: str) -> bool:
    data_registrazione: pendulum.datetime = pendulum.from_format(data_registrazione, "YYYY-MM-DD", tz=DEFAULT_TIMEZONE)
    data_nascita: pendulum.datetime = pendulum.from_format(data_nascita, "YYYY-MM-DD", tz=DEFAULT_TIMEZONE)

    is_default_renew: bool = pendulum.now(tz=DEFAULT_TIMEZONE).diff(data_registrazione).days > 365
    is_minor_at_date: bool = check_if_minor_at_date(data_nascita, data_registrazione)
    is_minor_today: bool = check_if_minor_at_date(data_nascita, pendulum.today(tz=DEFAULT_TIMEZONE))

    return is_default_renew or (is_minor_at_date and not is_minor_today)


def main():
    st.title("User Registration")

    st.markdown("### Sei già registrato? Inserisci qui il tuo codice fiscale")
    user_to_renew = already_registered_form()
    if user_to_renew:
        st.session_state.renew = True
        update_user_data(user_to_renew.model_dump())

    st.markdown("### Non sei registrato? Compila il form di registrazione")
    registration_form(user_to_renew=user_to_renew)


if __name__ == "__main__":
    main()
