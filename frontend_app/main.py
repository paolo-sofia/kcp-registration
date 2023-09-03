import datetime
import json
from enum import StrEnum
from hashlib import sha256
from typing import Any, Dict, List, Optional

import qrcode
import requests
import streamlit as st
from codicefiscale import codicefiscale

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}

class FormField(StrEnum):
    NOME = 'Nome'
    COGNOME = 'Cognome'
    CODICE_FISCALE = 'Codice Fiscale'
    DATA_NASCITA = 'Data di nascita'
    LUOGO_NASCITA = 'Luogo di nascita'
    LUOGO_RESIDENZA = 'Luogo di Residenza'
    VIA_RESIDENZA = 'Via di Residenza'
    NUM_TELEFONO = 'Numero di telefono'

class FormName(StrEnum):
    NOME = 'nome'
    COGNOME = 'cognome'
    DATA_NASCITA = 'data_nascita'
    LUOGO_NASCITA = 'luogo_nascita'
    PROVINCIA_NASCITA = 'provincia_nascita'
    CODICE_FISCALE = 'codice_fiscale'
    LUOGO_RESIDENZA = 'luogo_residenza'
    VIA_RESIDENZA = 'via_residenza'
    PROVINCIA_RESIDENZA = 'provincia_residenza'
    NUMERO_TELEFONO = 'numero_telefono'


def decodifica_codice_fiscale(cod_fiscale: str) -> Dict[str, Any]:
    if not codicefiscale.is_valid(cod_fiscale):
        st.error('Codice fiscale non valido, inserire codice fiscale corretto')
        return {}

    decoded_cod_fiscale: Dict[str, Any] = codicefiscale.decode(cod_fiscale)
    return {
        FormName.DATA_NASCITA: decoded_cod_fiscale.get('birthdate', datetime.datetime(1970, 1, 1)),
        FormName.LUOGO_NASCITA: decoded_cod_fiscale.get('birthplace', {}).get('name', ''),
        FormName.PROVINCIA_NASCITA: decoded_cod_fiscale.get('birthplace', {}).get('province', '')
    }


def regolamento_associativo_popup() -> bool:
    regolamento_associativo = """This is the privacy policy text.
    Please read the entire content carefully before proceeding.
    By clicking 'Accept', you acknowledge that you have read and understood the policy.
       """

    st.text_area("Regolamento Associativo ASD Motorart", regolamento_associativo, key="regolamento associativo_text_area", disabled=True)
    return st.checkbox("Ho letto ed accetto il Regolamento associativo")

def privacy_policy_popup() -> bool:
    privacy_policy = """This is the privacy policy text.
Please read the entire content carefully before proceeding.
By clicking 'Accept', you acknowledge that you have read and understood the policy.
   """

    st.text_area("Consenso del trattamento dei dati", privacy_policy, key="privacy_policy_text_area", disabled=True)
    return st.checkbox("Ho letto ed accetto la Privacy Policy")

def generate_and_show_qr_code(user: Dict[str, Any]) -> None:
    digest: str = sha256(json.dumps(user, sort_keys=True).encode('utf8')).hexdigest()
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
        and user_data.get(FormName.VIA_RESIDENZA)
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

def validate_child(child: Dict[str, str], child_min_date: datetime.date) -> bool:
    default_date: str = datetime.date.today().strftime('%Y-%m-%d')
    return bool(
        child.get('nome', '')
        and child.get('cognome', '')
        and datetime.datetime.strptime(child.get('data_nascita', default_date), '%Y-%m-%d') > child_min_date
        and codicefiscale.is_valid(child.get('codice_fiscale', ''))
    )

def validate_children(children: List[Dict[str, str]]) -> bool:
    child_min_date: datetime.datetime = datetime.datetime.now()
    child_min_date: datetime.datetime = datetime.datetime(child_min_date.year-18, child_min_date.month, child_min_date.day+1)

    return all(validate_child(child, child_min_date) for child in children)


def add_child() -> List[Dict[str, str]]:
    if 'children' not in st.session_state:
        print('children not in session state')
        st.session_state['children'] = []

    today: datetime = datetime.date.today()
    child_min_date = datetime.date(
        year=today.year - 18,
        month=today.month,
        day=today.day + 1
    )
    child_max_date: datetime.date = datetime.date(
        year=today.year - 7,
        month=child_min_date.month,
        day=child_min_date.day
    )
    st.subheader('Sezione Genitori')
    accept_child: bool = st.checkbox(label='Dichiaro di esercitare la potestà genitoriale sul/i minorenne/i registrato in quanto padre o madre dello stesso'
                                           ' (Consapevole delle conseguenze civili e penali delle dichiarazioni mendaci)')

    num_child: int = st.selectbox(label='Quanti figli devono guidare il kart?', options=list(range(20)), index=0)

    children: List[Dict[str, str]] = []
    for i in range(num_child):
        st.subheader(f'Dati Figlio {i+1}')

        child_name = st.text_input("Nome :red[*]", key=f'nome_figlio_{i}', disabled=not accept_child)
        child_surname = st.text_input("Cognome :red[*]", key=f'cognome_figlio_{i}', disabled=not accept_child)
        child_codice_fiscale = st.text_input("Codice fiscale figlio :red[*]", max_chars=16, key=f'cod_fiscale_figlio_{i}',
                                                   disabled=not accept_child)

        children.append({
            FormName.NOME       : " ".join([x.capitalize() for x in child_name]),
            FormName.COGNOME    : " ".join([x.capitalize() for x in child_surname]),
            FormName.DATA_NASCITA : str(st.date_input("Data di Nascita :red[*]", disabled=not accept_child,
                                             min_value=child_min_date, max_value=child_max_date,
                                             value=child_min_date, key=f'data_nascita_figlio_{i}')),
            FormName.CODICE_FISCALE: " ".join([x.upper() for x in child_codice_fiscale]),
        })

    return children

def registration_form():
    # with st.form('registration_form'):
    today: datetime.date = datetime.date.today()

    fiscal_code = st.text_input("Codice Fiscale :red[*]", max_chars=16)

    if fiscal_code:
        decoded_cod_fiscale: Dict[str, Any] = decodifica_codice_fiscale(fiscal_code)
        birth_place = st.text_input(
            label="Luogo di Nascita :red[*]",
            value=decoded_cod_fiscale.get(FormName.LUOGO_NASCITA, '')
        )
        # birth_province = st.text_input(
        #     label="Provincia di Nascita :red[*]",
        #     value=decoded_cod_fiscale.get('birth_province', '')
        # )
        birth_date = st.date_input(
            label="Data di Nascita :red[*]",
            value=decoded_cod_fiscale.get(FormName.DATA_NASCITA, datetime.datetime(1970, 1, 1)).date()
        )
    else:
        birth_place = st.text_input("Luogo di Nascita :red[*]")
        # birth_province = st.text_input("Provincia di Nascita :red[*]")
        birth_date = st.date_input("Data di Nascita :red[*]",
                                   min_value=datetime.date(today.year-100, 1, 1),
                                   value=datetime.date(1970,1,1),
                                   max_value=datetime.date(today.year-18, today.month, today.day))

    name = st.text_input("Nome :red[*]")
    surname = st.text_input("Cognome :red[*]")
    residence_place = st.text_input("Luogo di Residenza :red[*]")
    # residence_province = st.text_input("Provincia di Residenza :red[*]")
    residence_street = st.text_input("Via di Residenza :red[*]")
    phone_number = st.text_input('Numero di telefono')

    regolamento_associativo: bool = regolamento_associativo_popup()
    privacy_policy: bool = privacy_policy_popup()

    children: List[Dict[str,str]] = add_child()

    user_data = {
        FormName.CODICE_FISCALE     : fiscal_code.upper(),
        FormName.NOME               : " ".join([x.capitalize() for x in name.split()]),
        FormName.COGNOME            : " ".join([x.capitalize() for x in surname.split()]),
        FormName.DATA_NASCITA       : str(birth_date),
        FormName.LUOGO_NASCITA      : " ".join([x.capitalize() for x in birth_place.split()]),
        FormName.LUOGO_RESIDENZA    : " ".join([x.capitalize() for x in residence_place.split()]),
        FormName.VIA_RESIDENZA      : " ".join([x.capitalize() for x in residence_street.split()]),
        FormName.NUMERO_TELEFONO    : phone_number
    }

    data_validated: bool = validate_data(user_data) and validate_children(children)
    print(f'user validated {validate_data(user_data)}')
    print(f'children validated {validate_children(children)}')

    _, _, col, _, _ = st.columns(5)

    with col:
        register_button = st.button('Firma', disabled=not data_validated)

    if not register_button or not privacy_policy or not regolamento_associativo:
        return

    user_id: int = save_user_to_db(user_data)
    if not user_id:
        return

    children_ids: List[int] = save_children_to_db(children)
    if not children_ids:
        return

    children_removed: bool = remove_children_from_db(children_ids)
    if children_removed:
        return

    # flag_children_to_be_deleted(children)


def remove_children_from_db(children_id: List[int]) -> bool:
    response = requests.post("http://api:8000/remove_children/", json=children_id, headers=HEADERS)

    return response.status_code == 200


def save_children_to_db(children: List[Dict[str, str]]) -> Optional[List[int]]:
    response = requests.post("http://api:8000/add_children/", json=children, headers=HEADERS)

    return response.json() if response.status_code == 200 else None


def save_user_to_db(user_data: Dict[str, str]) -> Optional[int]:
    response = requests.post("http://api:8000/add_user/", json=user_data, headers=HEADERS)

    if response.status_code == 200:
        st.success("Utente registrato correttamente!")
        # generate_and_show_qr_code(user_data)
        return response.json().get('id', -1)

    st.error("Errore durante la registrazione, riprova.")
    return None


def handle_registered_user(response: Dict[str, Any]):
    if not response:
        st.error('Utente non registrato, registrati usando il form')
        return


def already_registered_form():
    st.markdown('#### Inserisci nome e cognome')
    with st.form('already_registered_form'):
        fiscal_code: str = st.text_input("Codice Fiscale")

        if not st.form_submit_button('Cerca', use_container_width=True):
            return

        try:
            response = requests.post("http://api:8000/user/", json={FormName.CODICE_FISCALE: fiscal_code.upper()},
                                     headers=HEADERS)

            if response.status_code == 200:
                handle_registered_user(response.json())
            else:
                st.error("Errore durante la ricerca, riprova.")
        except Exception:
            st.error("Errore durante la ricerca, riprova")

def main():
    st.title("User Registration")

    st.markdown('### Sei già registrato? Inserisci qui il tuo codice fiscale')
    already_registered_form()

    st.markdown('### Non sei registrato? Compila il form di registrazione')
    registration_form()


if __name__ == "__main__":
    main()
