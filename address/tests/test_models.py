from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from address.models import Country, State, Locality, Address, AddressField, Municipality
from address.models import to_python


class AddressModelTestCase(TestCase):
    fixtures = ["models.json"]

    def setUp(self):
        self.au = Country.objects.get(code="AU")
        self.be = Country.objects.get(code="BE")
        self.nz = Country.objects.get(code="NZ")
        self.uk = Country.objects.get(code="UK")
        self.au_vic = self.au.states.get(code="VIC")
        self.au_qld = self.au.states.get(name="Queensland")
        self.au_tas = self.au.states.get(code="TAS")
        self.au_empty = self.au.states.get(name="")
        self.uk_vic = self.uk.states.get(code="VIC")
        self.au_vic_nco = self.au_vic.localities.get(name="Northcote", postal_code="3070")
        self.au_vic_mel = self.au_vic.localities.get(name="Melbourne", postal_code="3000")
        self.au_vic_ftz = self.au_vic.localities.get(name="Fitzroy")
        self.au_vic_empty = self.au_vic.localities.get(name="")
        self.uk_vic_mel = self.uk_vic.localities.get(name="Melbourne", postal_code="3000")


class CountryTestCase(AddressModelTestCase):
    def test_ordering(self):
        qs = Country.objects.all()
        self.assertEqual(qs.count(), 4)
        self.assertEqual(qs[0].code, "AU")
        self.assertEqual(qs[1].code, "BE")
        self.assertEqual(qs[2].code, "NZ")
        self.assertEqual(qs[3].code, "UK")

    def test_unique_name(self):
        self.assertRaises(IntegrityError, Country.objects.create, name="Australia", code="**")


class StateTestCase(AddressModelTestCase):
    def test_required_country(self):
        self.assertRaises(IntegrityError, State.objects.create)

    def test_ordering(self):
        qs = State.objects.all()
        self.assertEqual(qs.count(), 6)
        self.assertEqual(qs[0].name, "")
        self.assertEqual(qs[1].name, "Queensland")
        self.assertEqual(qs[2].name, "Tasmania")
        self.assertEqual(qs[3].name, "Victoria")
        self.assertEqual(qs[4].name, "Oost-Vlaanderen")
        self.assertEqual(qs[5].name, "Victoria")

    def test_unique_name_country(self):
        State.objects.create(name="Tasmania", country=self.uk)
        self.assertRaises(IntegrityError, State.objects.create, name="Tasmania", country=self.au)


class MunicipalityTestCase(AddressModelTestCase):
    def test_ordering(self):
        qs = Municipality.objects.all()
        self.assertEquals(qs.count(), 6)
        self.assertEqual(qs[0].name, "Gold Coast")
        self.assertEqual(qs[0].state.name, "Queensland")
        self.assertEqual(qs[1].name, "")
        self.assertEqual(qs[1].state.code, "VIC")
        self.assertEqual(qs[2].name, "City of Darebin")
        self.assertEqual(qs[2].state.code, "VIC")
        self.assertEqual(qs[3].name, "City of Melbourne")
        self.assertEqual(qs[3].state.code, "VIC")
        self.assertEqual(qs[4].name, "City of Yarra")
        self.assertEqual(qs[4].state.code, "VIC")
        self.assertEqual(qs[5].name, "")
        self.assertEqual(qs[5].state.code, "VOV")

    def test_required_state(self):
        self.assertRaises(IntegrityError, Municipality.objects.create, name="test")

    def test_unique_name_state(self):
        self.assertRaises(IntegrityError, Municipality.objects.create, name="City of Melbourne", state=self.au_vic)


class LocalityTestCase(AddressModelTestCase):
    def test_required_state(self):
        self.assertRaises(IntegrityError, Locality.objects.create)

    def test_ordering(self):
        qs = Locality.objects.all()
        self.assertEqual(qs.count(), 5)
        self.assertEqual(qs[0].name, "")
        self.assertEqual(qs[1].name, "Fitzroy")
        self.assertEqual(qs[2].name, "Melbourne")
        self.assertEqual(qs[3].name, "Northcote")
        self.assertEqual(qs[4].name, "Melbourne")

    def test_unicode(self):
        self.assertEqual(str(self.au_vic_mel), "Melbourne, City of Melbourne, Victoria 3000, Australia")
        self.assertEqual(str(self.au_vic_ftz), "Fitzroy, City of Yarra, Victoria, Australia")
        self.assertEqual(str(self.au_vic_empty), "Victoria, Australia")


class AddressTestCase(AddressModelTestCase):
    def setUp(self):
        super().setUp()
        self.ad1 = Address.objects.create(
            street_number="1",
            route="Some Street",
            locality=self.au_vic_mel,
            raw="1 Some Street, Victoria, Melbourne",
        )
        self.ad2 = Address.objects.create(
            street_number="10",
            route="Other Street",
            locality=self.au_vic_mel,
            raw="10 Other Street, Victoria, Melbourne",
        )
        self.ad3 = Address.objects.create(
            street_number="1",
            route="Some Street",
            locality=self.au_vic_nco,
            raw="1 Some Street, Northcote, Victoria",
        )
        self.ad_empty = Address.objects.create(locality=self.au_vic_nco, raw="Northcote, Victoria")

    def test_required_raw(self):
        obj = Address.objects.create()
        self.assertRaises(ValidationError, obj.clean)

    def test_ordering(self):
        qs = Address.objects.all()
        self.assertEqual(qs.count(), 4)
        self.assertEqual(qs[0].route, "Other Street")
        self.assertEqual(qs[1].route, "Some Street")
        self.assertEqual(qs[2].route, "")
        self.assertEqual(qs[3].route, "Some Street")

    # def test_unique_street_address_locality(self):
    #     Address.objects.create(street_number='10', route='Other Street', locality=self.au_vic_nco)
    #     self.assertRaises(
    #         IntegrityError, Address.objects.create,
    #         street_number='10', route='Other Street', locality=self.au_vic_mel
    #     )

    def test_unicode(self):
        self.assertEqual(str(self.ad1), "1 Some Street, Melbourne, City of Melbourne, Victoria 3000, Australia")
        self.assertEqual(str(self.ad_empty), "Northcote, City of Darebin, Victoria 3070, Australia")


class AddressFieldTestCase(TestCase):
    class TestModel(object):
        address = AddressField()

    def setUp(self):
        self.ad1_dict = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "postal_code": "3070",
            "state": "Victoria",
            "state_code": "VIC",
            "country": "Australia",
            "country_code": "AU",
        }
        self.test = self.TestModel()

    def test_assignment_from_dict(self):
        self.test.address = to_python(self.ad1_dict)
        self.assertEqual(self.test.address.raw, self.ad1_dict["raw"])
        self.assertEqual(self.test.address.street_number, self.ad1_dict["street_number"])
        self.assertEqual(self.test.address.route, self.ad1_dict["route"])
        self.assertEqual(self.test.address.locality.name, self.ad1_dict["locality"])
        self.assertEqual(self.test.address.locality.postal_code, self.ad1_dict["postal_code"])
        self.assertEqual(self.test.address.locality.state.name, self.ad1_dict["state"])
        self.assertEqual(self.test.address.locality.state.code, self.ad1_dict["state_code"])
        self.assertEqual(self.test.address.locality.state.country.name, self.ad1_dict["country"])
        self.assertEqual(self.test.address.locality.state.country.code, self.ad1_dict["country_code"])

    def test_assignment_from_dict_no_country(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "state": "Victoria",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, "")
        self.assertEqual(self.test.address.route, "")
        self.assertEqual(self.test.address.locality, None)

    def test_assignment_from_dict_no_state(self):
        ad = {
            "raw": "Somewhere",
            "locality": "Northcote",
            "country": "Australia",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, "")
        self.assertEqual(self.test.address.route, "")
        self.assertEqual(self.test.address.locality, None)

    def test_assignment_from_dict_no_locality(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "state": "Victoria",
            "country": "Australia",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, "")
        self.assertEqual(self.test.address.route, "")
        self.assertEqual(self.test.address.locality, None)

    def test_assignment_from_dict_only_address(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, ad["street_number"])
        self.assertEqual(self.test.address.route, ad["route"])
        self.assertEqual(self.test.address.locality, None)

    def test_assignment_from_dict_duplicate_country_code(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "state": "Victoria",
            "country": "Australia",
            "country_code": "Australia",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, "1")
        self.assertEqual(self.test.address.route, "Somewhere Street")
        self.assertEqual(self.test.address.locality.name, "Northcote")
        self.assertEqual(self.test.address.locality.state.name, "Victoria")
        self.assertEqual(self.test.address.locality.state.country.name, "Australia")
        self.assertEqual(self.test.address.locality.state.country.code, "")

    def test_assignment_from_dict_duplicate_state_code(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "state": "Victoria",
            "state_code": "Victoria",
            "country": "Australia",
        }
        self.test.address = to_python(ad)
        self.assertEqual(self.test.address.raw, ad["raw"])
        self.assertEqual(self.test.address.street_number, "1")
        self.assertEqual(self.test.address.route, "Somewhere Street")
        self.assertEqual(self.test.address.locality.name, "Northcote")
        self.assertEqual(self.test.address.locality.state.name, "Victoria")
        self.assertEqual(self.test.address.locality.state.code, "Victoria")
        self.assertEqual(self.test.address.locality.state.country.name, "Australia")

    def test_assignment_from_dict_invalid_country_code(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "state": "Victoria",
            "country": "Australia",
            "country_code": "Something else",
        }
        self.assertRaises(ValueError, to_python, ad)

    def test_assignment_from_dict_invalid_state_code(self):
        ad = {
            "raw": "1 Somewhere Street, Northcote, Victoria 3070, VIC, AU",
            "street_number": "1",
            "route": "Somewhere Street",
            "locality": "Northcote",
            "state": "Victoria",
            "state_code": "Something",
            "country": "Australia",
        }
        # This is invalid because state codes are expected to have a max of 8 characters
        self.assertRaises(ValueError, to_python, ad)

    def test_assignment_from_string(self):
        self.test.address = to_python(self.ad1_dict["raw"])
        self.assertEqual(self.test.address.raw, self.ad1_dict["raw"])

    # def test_save(self):
    #     self.test.address = self.ad1_dict
    #     self.test.save()
    #     test = self.TestModel.objects.all()[0]
    #     self.assertEqual(test.address.raw, self.ad1_dict['raw'])
    #     self.assertEqual(test.address.street_number, self.ad1_dict['street_number'])
    #     self.assertEqual(test.address.route, self.ad1_dict['route'])
    #     self.assertEqual(test.address.locality.name, self.ad1_dict['locality'])
    #     self.assertEqual(test.address.locality.postal_code, self.ad1_dict['postal_code'])
    #     self.assertEqual(test.address.locality.state.name, self.ad1_dict['state'])
    #     self.assertEqual(test.address.locality.state.code, self.ad1_dict['state_code'])
    #     self.assertEqual(test.address.locality.state.country.name, self.ad1_dict['country'])
    #     self.assertEqual(test.address.locality.state.country.code, self.ad1_dict['country_code'])
