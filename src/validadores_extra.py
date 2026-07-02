"""
Validadores de dados extraídos (CPF, data, email)
"""

import re
from datetime import datetime


def validar_cpf(cpf_str):
    cpf = re.sub(r"[^\d]", "", cpf_str)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False, "CPF deve ter 11 dígitos"

    for n in range(9, 11):
        soma = sum(int(cpf[i]) * ((n + 1) - i) for i in range(n))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[n]):
            return False, "CPF inválido"

    return True, "CPF válido"


def validar_data(data_str):
    formatos = [
        ("%d/%m/%Y", "DD/MM/AAAA"),
        ("%d-%m-%Y", "DD-MM-AAAA"),
        ("%Y-%m-%d", "AAAA-MM-DD"),
        ("%d %m %Y", "DD MM AAAA"),
        ("%d/%m/%y", "DD/MM/AA"),
    ]

    data_str = data_str.strip()

    for fmt, desc in formatos:
        try:
            dt = datetime.strptime(data_str, fmt)
            if dt.year < 1900 or dt.year > 2100:
                return False, f"Ano fora do intervalo (1900-2100)"
            return True, desc
        except ValueError:
            continue

    if re.match(r"^\d{1,2}[\/\- ]\d{1,2}[\/\- ]\d{2,4}$", data_str):
        return False, "Data fora do intervalo válido"
    return False, "Formato não reconhecido (use DD/MM/AAAA)"


def validar_email(email_str):
    padrao = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if re.match(padrao, email_str.strip()):
        return True, "Email válido"
    return False, "Email inválido"


def validar_telefone(tel_str):
    digitos = re.sub(r"[^\d]", "", tel_str)
    if len(digitos) < 8:
        return False, "Telefone deve ter ao menos 8 dígitos"
    return True, "Telefone válido"


def sugerir_validacao(placeholder_lower):
    if "cpf" in placeholder_lower:
        return "cpf"
    if any(p in placeholder_lower for p in ["data", "nascimento", "dt_", "dtnasc"]):
        return "data"
    if any(p in placeholder_lower for p in ["email", "e-mail", "mail"]):
        return "email"
    if any(p in placeholder_lower for p in ["telefone", "tel", "fone", "celular"]):
        return "telefone"
    return None


def validar_campo(placeholder, valor):
    tipo = sugerir_validacao(placeholder.lower())
    if not tipo or not valor.strip():
        return True, ""

    if tipo == "cpf":
        ok, msg = validar_cpf(valor)
    elif tipo == "data":
        ok, msg = validar_data(valor)
    elif tipo == "email":
        ok, msg = validar_email(valor)
    elif tipo == "telefone":
        ok, msg = validar_telefone(valor)
    else:
        return True, ""

    return ok, msg
