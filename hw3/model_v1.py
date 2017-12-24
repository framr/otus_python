# -*- coding: utf-8 -*-
"""
Autostorage/ValidatedField recipe is from Fluent Python by Luciano Ramalho (ch. 20, example 20-6)
"""

import re
import numbers
from datetime import datetime, timedelta
from abc import ABCMeta, abstractmethod


EMPTY_VALUES = (None, "", u"", [], (), {})
def empty(val):
    return val in EMPTY_VALUES


class AutoStorage(object):
    _counter = 0

    def __init__(self):
        _cls = self.__class__
        prefix = _cls.__name__
        index = _cls._counter
        self.storage_name = "_{}#{}".format(prefix, index)
        _cls._counter += 1

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return getattr(instance, self.storage_name, None)

    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value)


class ValidatedField(AutoStorage):
    __metaclass__ = ABCMeta

    def __init__(self, required=False, nullable=True):
        super(ValidatedField, self).__init__()
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        self.validate(instance, value)
        super(ValidatedField, self).__set__(instance, value)

    
    @abstractmethod
    def validate(self, instance, value):
        pass


class CharField(ValidatedField):
    def validate(self, instance, value):
        if not isinstance(value, unicode):
            raise ValueError("attribute should be unicode, while it is of type %s" % type(value))


class StrNumField(CharField):
    pass


class ArgumentsField(ValidatedField):
    def validate(self, instance, value):
        if not isinstance(value, dict):
            raise ValueError("arguments field should be dict")


class EmailField(CharField):
    def validate(self, instance, value):
        super(EmailField, self).validate(instance, value)
        if "@" not in value:
            raise ValueError("not a valid email address")


class PhoneField(ValidatedField):
    def validate(self, instance, value):
        super(PhoneField, self).validate(instance, value)
        value = unicode(value) if isinstance(value, numbers.Integral) else value
        if not isinstance(value, unicode) or len(value) != 11 or not value.startswith("7") or not value.isdigit():
            raise ValueError("not a valid phone")


class DateField(StrNumField):
    _RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

    def validate(self, instance, value):
        super(DateField, self).validate(instance, value)
        if not self._RE.match(value):
            raise ValueError("wrong date format")
            # check stuff with correct months/dates/etc via instantiating datetime
        dt = datetime.strptime(value, "%d.%m.%Y")


class BirthDayField(DateField):
    # for sure, we are not interested in the precision up to leap year stuff here
    MAX_AGE = timedelta(days=70 * 365.2425)

    def validate(self, instance, value):
        super(BirthDayField, self).validate(instance, value)
        dt = datetime.strptime(value, "%d.%m.%Y")
        if datetime.now() - dt > self.MAX_AGE:
            raise ValueError("wrong date")


class GenderField(ValidatedField):
    def validate(self, instance, value):
        if value not in (0, 1, 2):
            raise ValueError("malformed gender field")


class ClientIDsField(ValidatedField):
    def validate(self, instance, value):
        if not isinstance(value, list) or not all([isinstance(val, numbers.Integral) for val in value]):
            raise ValueError("wrong client ids")


class ValidatedRequestMeta(type):
    def __init__(cls, name, bases, attr_dict):
        super(ValidatedRequestMeta, cls).__init__(cls, name, bases, attr_dict)
        _fields = []
        _required = set()
        _nullable = set()
        for key, attr in attr_dict.iteritems():
            if isinstance(attr, ValidatedField):
                type_name = type(attr).__name__
                attr.storage_name = "_{}#{}".format(type_name, key)  # prettify automatic names
                _fields.append(key)
                if attr.required:
                    _required.add(key)
                if attr.nullable:
                    _nullable.add(key)
        setattr(cls, "_fields", _fields)
        setattr(cls, "_required", _required)
        setattr(cls, "_nullable", _nullable)


class ValidatedRequest(object):
    __metaclass__ = ValidatedRequestMeta

    def __init__(self):
        self._invalid_fields = {}
        self._set_fields = []

    @property
    def invalid_fields(self):
        return self._invalid_fields

    @property
    def fields(self):
        return self._fields

    @property
    def valid(self):
        return not self.invalid_fields

    @property
    def set_fields(self):
        return self._set_fields

    @property
    def validate_message(self):
        if self._invalid_fields:
            return "invalid fields %s" % ",".join(self._invalid_fields)
        else:
            return "fields OK"

    def parse_request(self, data):
        for field in self._fields:
            if field not in data:
                if field in self._required:
                    self._invalid_fields[field] = "Required field mising"
                continue
            if empty(field):
                if field not in self._nullable:
                    self._invalid_fields[field] = "Non-nullable field is empty"
            else:
                # currently we simply ignore empty fields
                try:
                    setattr(self, field, val)
                except ValueError as e:
                    self._invalid_fields[field] = e.message
                else:
                    self._set_fields.append(field)


class MethodRequest(ValidatedRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def __init__(self, request, context, store):
        super(MethodRequest, self).__init__()
        self._request = request
        self._context = context


class ClientsInterestsRequest(ValidatedRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def __init__(self, method_req, context, store):
        super(ClientsInterestsRequest, self).__init__()
        self._method_req = method_req
        self._store = store
        self._context = context

    def process(self):
        self._context.update({"has": len(self.client_ids)})
        res = {}
        for cid in self.client_ids:
            res[str(cid)] = get_interests(self._store, cid)
        return res


class OnlineScoreRequest(ValidatedFieldRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, method_req, context, store):
        super(OnlineScoreRequest, self).__init__()
        self._method_req = method_req
        self._store = store
        self._context = context

    def parse_request(self):
        super(OnlineScoreRequest, self).parse_request(self._method_req.arguments)

        valid = any(["phone" in self.set_fields and "email" in self.set_fields,
                     "first_name" in self.set_fields and "last_name" in self.set_fields,
                     "gender" in self.set_fields and "birthday" in self.set_fields])
        if not valid:
            self.invalid_fields["combo"] = ("at least one of pairs (phone, email), (first name, last name), "
                                           "(gender, birhday) should be set")

    @property
    def validate_message(self):
        return " ".join(["%s: %s" % (f, msg) for f, msg in self.invalid_fields.iteritems()])
        
    def process(self):
        self._context.update({"has": self.fields})
        if self._method_req.is_admin:
            return {"score": 42}
        score = get_score(self._store, self.phone, self.email, birthday=self.birthday, gender=self.gender,
                          first_name=self.first_name, last_name=self.last_name)
        return {"score": score}



