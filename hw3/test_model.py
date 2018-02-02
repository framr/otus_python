#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from model_v1 import AutoStorage, ValidatedField, CharField, ArgumentsField, EmailField,\
        BirthDayField, GenderField, ClientIDsField, PhoneField, DateField, ValidatedRequest
from api import OnlineScoreRequest, ClientsInterestsRequest


def test_auto_storage():
    class T(object):
        auto = AutoStorage()
    t = T()
    t.auto = 1
    assert t.auto == 1
    t.auto = None
    assert t.auto is None

    t.auto = -1
    assert t.auto == -1

    t.auto = "abc"
    assert t.auto == "abc"

    t.auto = ""
    assert t.auto == ""

    t.auto = [1, 2, 3]
    assert t.auto == [1, 2, 3]

    t.auto = {1: 1, 2: 2, 3: 3}
    assert t.auto == {1: 1, 2: 2, 3: 3}


@pytest.fixture()
def req():
    class T(object):
        char = CharField(required=True, nullable=True)
        args = ArgumentsField(required=True, nullable=True)
        email = EmailField(required=False, nullable=True)
        bday = BirthDayField(required=False, nullable=True) 
        date = DateField(required=False, nullable=True)
        gender = GenderField(required=False, nullable=True)
        ids = ClientIDsField(required=True, nullable=False)
        phone = PhoneField(required=False, nullable=True)
    return T()


@pytest.mark.parametrize("value", [1, []])
def test_char_field_error_raises(value, req):
    with pytest.raises(ValueError):
        req.char = value


@pytest.mark.parametrize("value", [u"1", u"abc", u"abc", u""])
def test_char_field_valid(value, req):
    req.char = value
    assert req.char == value


@pytest.mark.parametrize("value", ["1", -1, 0, [], ()])
def test_arguments_field_error_raises(value, req):
    with pytest.raises(ValueError):
        req.args = value


@pytest.mark.parametrize("value", [{}, {1:1, 2:2, 3:3}, {"a": "b"}])
def test_arguments_field_valid(value, req):
    req.args = value
    assert req.args == value


@pytest.mark.parametrize("value", ["1", "", "myemail", "$$$", u"1", -1, 0, [], {}])
def test_email_field_error_raises(value, req):
    with pytest.raises(ValueError):
        req.email = value


@pytest.mark.parametrize("value", [u"@", u"xxx@yyy", u"1@", u"@1", u"xxx@yyy"])
def test_email_field_valid(value, req):
    req.email = value
    assert req.email == value


@pytest.mark.parametrize("value", ["1", "", "myemail", "$$$", u"1", -1, 0, [], {},
    "7-916-333-33-33", 49163333333])
def test_phone_field_error_raises(value, req):
    with pytest.raises(ValueError):
        req.phone = value


@pytest.mark.parametrize("value", [u"79163333333", u"79163333333", 79163333333])
def test_phone_field_valid(value, req):
    req.phone = value
    assert req.phone == value


@pytest.mark.parametrize("value", [u"27102000", u"2000.10.27", 27102000, u"27.10.1900"])
def test__bday_error_raises(value, req):
    with pytest.raises(ValueError):
        req.bday = value


@pytest.mark.parametrize("value", [u"27.10.2000", u"01.11.1980"])
def test__bday_valid(value, req):
    req.bday = value
    assert req.bday == value


@pytest.mark.parametrize("value", [u"27102000", u"2000.10.27", 27102000])
def test__date_error_raises(value, req):
    with pytest.raises(ValueError):
        req.date = value


@pytest.mark.parametrize("value", [u"27.10.2000", u"01.11.1980", u"27.10.1900"])
def test__date_valid(value, req):
    req.date = value
    assert req.date == value


@pytest.mark.parametrize("value", [-1, 3, 0.1, "abc"])
def test__gender_error_raises(value, req):
    with pytest.raises(ValueError):
        req.gender = value


@pytest.mark.parametrize("value", [0, 1, 2])
def test__gender_valid(value, req):
    req.gender = value
    assert req.gender == value


@pytest.mark.parametrize("value", [[""]])
def test__ids_error_raises(value, req):
    with pytest.raises(ValueError):
        req.ids = value


@pytest.mark.parametrize("value", [[0, 1, 2], []])
def test__ids_valid(value, req):
    req.ids = value
    assert req.ids == value


"""
@pytest.fixture()
def validated_req():
    class T(ValidatedRequest):
        first_name = CharField(required=False, nullable=True)
        last_name = CharField(required=False, nullable=True)
        email = EmailField(required=False, nullable=True)
        phone = PhoneField(required=False, nullable=True)
        birthday = BirthDayField(required=False, nullable=True)
        gender = GenderField(required=False, nullable=True)
    return T()


def test_validated_request():
    pass
"""
