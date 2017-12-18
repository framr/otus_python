# -*- coding: utf-8 -*-
"""
Autostorage/Validated recipe is from Fluent Python by Luciano Ramalho (ch. 20, example 20-6)
"""
 
import re
import numbers
#import abc
import inspect
from datetime import datetime, timedelta
from logging import exception

MISSING_FIELD = type("MissingField", (), {})()


def nonempty(val):
    if val is None or (isinstance(val, unicode) and not val):
        return False
    return True


def defined(val):
    if val is None or val is MISSING_FIELD:
        return False
    return True


def missing(val):
    return val is MISSING_FIELD


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
            return getattr(instance, self.storage_name)
    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value)


class Validated(AutoStorage):
    def __init__(self, required=False, nullable=True):
        super(Validated, self).__init__()
        self._required = required
        self._nullable = nullable

    def __set__(self, instance, value):
        self.validate(instance, value)
        if value is MISSING_FIELD:
            value = None
        super(Validated, self).__set__(instance, value)

    def validate(self, instance, value):
        if self._required and missing(value):
            raise ValueError("attribute is mandatory")
        if not self._nullable:
            if not nonempty(value):
                raise ValueError("attribute is not nullable")


class CharField(Validated):
    def validate(self, instance, value):
        super(CharField, self).validate(instance, value)
        if defined(value) and not isinstance(value, unicode):
            raise ValueError("attribute should be unicode, while it is of type %s" % type(value))


class StrNumField(CharField):
    pass


class ArgumentsField(Validated):
    def validate(self, instance, value):
        super(ArgumentsField, self).validate(instance, value)
        if defined(value) and not isinstance(value, dict):
            raise ValueError("arguments field should be dict")


class EmailField(CharField):
    def validate(self, instance, value):
        super(EmailField, self).validate(instance, value)
        if nonempty(value) and "@" not in value:
            raise ValueError("not a valid email address")


class PhoneField(Validated):
    def validate(self, instance, value):
        super(PhoneField, self).validate(instance, value)
        if nonempty(value):
            value = unicode(value) if isinstance(value, numbers.Integral) else value
            if not isinstance(value, unicode) or len(value) != 11 or not value.startswith("7") or not value.isdigit():
                raise ValueError("not a valid phone")


class DateField(StrNumField):
    _RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
    def validate(self, instance, value):
        super(DateField, self).validate(instance, value)
        if nonempty(value):
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
        # we are 
        if datetime.now() - dt > self.MAX_AGE:
            raise ValueError("wrong date")


class GenderField(Validated):
    def validate(self, instance, value):
        super(GenderField, self).validate(instance, value)
        if defined(value) and value not in (0, 1, 2):
            raise ValueError("malformed gender field")


class ClientIDsField(Validated):
    def validate(self, instance, value):
        super(ClientIDsField, self).validate(instance, value)
        if defined(value) and (not isinstance(value, list) or not all([isinstance(val, numbers.Integral) for val in value])):
            raise ValueError("wrong client ids")


class ValidatedRequest(object):
    def __init__(self):
        self._fields = []
        self._invalid_fields = []
    
    @classmethod
    def _find_validated_attrs(_cls):
        res = []
        for klass in inspect.getmro(_cls):
            for key, attr in klass.__dict__.iteritems():
                if isinstance(attr, Validated):
                    res.append(key)
        return res

    @property
    def invalid_fields(self):
        return self._invalid_fields

    @property
    def fields(self):
        return self._fields

    @property
    def validate_message(self):
        if self._invalid_fields:
            return "invalid fields %s" % ",".join(self._invalid_fields)
        else:
            return "fields OK"

    def parse_request(self, data):
        self._invalid_field = []
        self._fields = []
        for field in self.__class__._find_validated_attrs():
            try:
                val = data.get(field, MISSING_FIELD)
                setattr(self, field, val)
                if val is not MISSING_FIELD:
                    self._fields.append(field)
            except ValueError:
                exception("error setting attr %s" % field)
                self._invalid_fields.append(field)

        if self._invalid_fields:
            raise ValueError("error validating fields")


