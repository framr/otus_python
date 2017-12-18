#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from model_v1 import AutoStorage, Validated, CharField, MISSING_FIELD, ArgumentsField, EmailField, GenderField,\
        BirthDayField, GenderField, ClientIDsField, PhoneField, DateField, ValidatedRequest
from api import OnlineScoreRequest, ClientsInterestsRequest


class TestAutoStorage(unittest.TestCase):
    def setUp(self):
        class T(object):
            auto = AutoStorage()
        self.t = T()

    def test_auto_storage(self):
        self.t.auto = 1
        self.assertEquals(self.t.auto, 1)
        self.t.auto = None
        self.assertIsNone(self.t.auto)


class TestValidatedField(unittest.TestCase):
    def test_required_not_nullable(self): 
        class T(object):
            val = Validated(required=True, nullable=False)
        self.t = T()
        
        self.t.val = 1
        self.assertEquals(self.t.val, 1)
        self.t.val = "abc"
        self.assertEquals(self.t.val, "abc")
        try:
            self.t.val = None
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.val = MISSING_FIELD
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.val = u""
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")

    def test_required_nullable(self): 
        class T(object):
            val = Validated(required=True, nullable=True)
        self.t = T()
        
        self.t.val = 1
        self.assertEquals(self.t.val, 1)
        self.t.val = "abc"
        self.assertEquals(self.t.val, "abc")
        self.t.val = None
        self.assertIsNone(self.t.val)
        try:
            self.t.val = MISSING_FIELD
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")

    def test_not_required_nullable(self): 
        class T(object):
            val = Validated(required=False, nullable=True)
        self.t = T()
        
        self.t.val = 1
        self.assertEquals(self.t.val, 1)
        self.t.val = "abc"
        self.assertEquals(self.t.val, "abc")
        self.t.val = None
        self.assertIsNone(self.t.val)
        self.t.val = MISSING_FIELD
        self.assertIsNone(self.t.val)

    def test_not_required_not_nullable(self): 
        class T(object):
            val = Validated(required=False, nullable=False)
        self.t = T()
        
        self.t.val = 1
        self.assertEquals(self.t.val, 1)
        self.t.val = "abc"
        self.assertEquals(self.t.val, "abc")
        try:
            self.t.val = None
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")

        self.t.val = MISSING_FIELD
        self.assertIsNone(self.t.val)


class TestCharField(unittest.TestCase):
    def test_none(self):
        class Test(object):
            char = CharField(required=True, nullable=True)
        self.t = Test()
        self.t.char = None
        self.assertIsNone(self.t.char)

    def test_valid_str(self):
        class Test(object):
            char = CharField(required=True, nullable=True)
        self.t = Test()
        self.t.char = u"abc"
        self.assertEquals(self.t.char, u"abc")
        self.t.char = u""
        self.assertEquals(self.t.char, "")

    def test_integer_raises(self):
        class Test(object):
            char = CharField(required=True, nullable=True)
        self.t = Test()
        try:
            self.t.char = 1
        except ValueError:
            print "ValueError raised"
        else:
            self.assertTrue(False, "ValueError ont raised")


class TestArgumentsField(unittest.TestCase):
    def test_valid_dict(self):
        class Test(object):
            args = ArgumentsField(required=True, nullable=True)
        self.t = Test()
        try:
            self.t.args = {}
        except ValueError:
            self.assertTrue(False, "ValueError raised on valid dict")
        try:
            self.t.args = {"1": 1, "2": 2}
        except ValueError:
            self.assertTrue(False, "ValueError raised on valid dict")

    def test_not_valid_raises(self):
        class Test(object):
            args = ArgumentsField(required=True, nullable=True)
        self.t = Test()
        try:
            self.t.args = ""
        except ValueError:
            pass
        else:
            self.assertTrue(False, "ValueError not raised")


class TestEmailField(unittest.TestCase):
    def test_valid_email(self):
        class Test(object):
            email = EmailField(required=False, nullable=True)
        self.t = Test()
        try:
            self.t.email = u""
            self.t.email = None
        except ValueError:
            self.assertTrue(False, "ValueError raised on valid empty email")
        try:
            self.t.email = u"xxx@mail.ru"
            self.assertEquals(self.t.email, u"xxx@mail.ru")
            self.t.email = u"yyy@otus-python.ru"
            self.assertEquals(self.t.email, u"yyy@otus-python.ru")
        except ValueError:
            self.assertTrue(False, "ValueError raised on valid email")

    def test_not_valid_email_raises(self):
        class Test(object):
            email = EmailField(required=False, nullable=True)
        self.t = Test()
        try:
            self.t.email = u"xxxmail.ru"
        except ValueError:
            print "ValueError raised on invalid email"
        else:
            self.assertTrue(False, "ValueError raised on valid email")
        try:
            self.t.email = 1
        except ValueError:
            print "ValueError raised on invalid email"
        else:
            self.assertTrue(False, "ValueError raised on valid email")


class TestPhoneField(unittest.TestCase):
    def test_valid_phone(self):
        class Test(object):
            phone = PhoneField(required=False, nullable=True)
        t = Test()
        try:
            t.phone = u"79163332222"
            self.assertEquals(t.phone, u"79163332222")
            t.phone = 79163332222
            self.assertEquals(t.phone, 79163332222)
        except ValueError:
            self.assertTrue(False, "ValueError raised on valid phone")

    def test_not_valid_phone_raises(self):
        class Test(object):
            phone = PhoneField(required=False, nullable=True)
        t = Test()
        try:
            t.phone = u"7916333222222222"
        except ValueError:
            print "ValueError raised on invalid phone"
        else:
            self.assertTrue(False, "ValueError not raised on invalid phone")
        try:
            t.phone = 7916333222222222
        except ValueError:
            print "ValueError raised on invalid phone"
        else:
            self.assertTrue(False, "ValueError not raised on invalid phone")
        try:
            t.phone = 7.111111111
        except ValueError:
            print "ValueError raised on invalid phone"
        else:
            self.assertTrue(False, "ValueError not raised on invalid phone")
        try:
            t.phone = u"7916333222a"
        except ValueError:
            print "ValueError raised on invalid phone"
        else:
            self.assertTrue(False, "ValueError not raised on invalid phone")


class TestBirthDayField(unittest.TestCase):
    def setUp(self):
        class Test(object):
            bday = BirthDayField(required=False, nullable=True)
        self.t = Test()
 
    def test_valid_bday(self):    
        self.t.bday = u"27.10.2000"
        self.assertEquals(self.t.bday, u"27.10.2000")
        self.t.bday = u"01.11.1980"
        self.assertEquals(self.t.bday, u"01.11.1980")

    def test_invalid_bday(self):
        try:
            self.t.bday = 27102000
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"27102000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"27-10-2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"00.10.2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"01.13.2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"01.00.2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised") 
        try:
            self.t.bday = u"lizard2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.bday = u"01.01.1900"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")


class TestDateField(unittest.TestCase):
    def setUp(self):
        class Test(object):
            date = DateField(required=False, nullable=True)
        self.t = Test()
 
    def test_valid_date(self):    
        self.t.date = u"27.10.2000"
        self.assertEquals(self.t.date, u"27.10.2000")
        self.t.date = u"01.11.1980"
        self.assertEquals(self.t.date, u"01.11.1980")

    def test_invalid_date(self):
        try:
            self.t.date = 27102000
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.date = u"27102000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.date = u"27-10-2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.date = u"00.10.2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.date = u"lizard2000"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")

class TestGenderField(unittest.TestCase):
    def setUp(self):
        class T(object):
            gender = GenderField(required=False, nullable=True)
        self.t = T()

    def test_valid_gender(self):
        self.t.gender = 0
        self.assertEquals(self.t.gender, 0)
        self.t.gender = 1
        self.assertEquals(self.t.gender, 1)
        self.t.gender = 2
        self.assertEquals(self.t.gender, 2)
    
    def test_invalid_gender(self):
        try:
            self.t.gender = -1
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.gender = 3
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
            self.t.gender = "1"
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")


class TestClientIDsField(unittest.TestCase):
    def setUp(self):
        class T(object):
            ids = ClientIDsField(required=True, nullable=False)
        self.t = T()

    def test_valid_clientids(self):
        self.t.ids = [0, 1, 2]
        self.assertEquals(self.t.ids, [0, 1, 2])
        self.t.ids = []
        self.assertEquals(self.t.ids, [])

    def test_invalid_clientids(self):
        try:
            self.t.ids = ["0", "1", "2"]
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")
        try:
             self.t.ids = {1:1, 2:2}
        except ValueError:
            print "Ok, ValueError raised"
        else:
            self.assertTrue(False, "ValueError not raised")


class TestValidatedRequest(unittest.TestCase):
    def setUp(self):
        class T(ValidatedRequest):
            first_name = CharField(required=False, nullable=True)
            last_name = CharField(required=False, nullable=True)
            email = EmailField(required=False, nullable=True)
            phone = PhoneField(required=False, nullable=True)
            birthday = BirthDayField(required=False, nullable=True)
            gender = GenderField(required=False, nullable=True)
        self.t = T()

    def test_find_validated_attrs(self): 
        self.assertEquals(sorted(self.t._find_validated_attrs()),
                          sorted("first_name last_name email phone birthday gender".split()))
        

if __name__ == "__main__":
    unittest.main()
