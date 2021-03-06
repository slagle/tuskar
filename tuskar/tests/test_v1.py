"""Base classes for API tests.
"""

from tuskar.tests import api
from tuskar.db.sqlalchemy import api as dbapi
from tuskar.api.controllers import v1


class TestRacks(api.FunctionalTest):

    test_rack = None
    db = dbapi.get_backend()

    def valid_rack_json(self, rack_json, test_rack=None):
        rack = None

        if test_rack is None:
            rack = self.test_rack
        else:
            rack = test_rack

        self.assertEqual(rack_json['id'], rack.id)
        self.assertEqual(rack_json['name'], rack.name)
        self.assertEqual(rack_json['slots'], rack.slots)
        self.assertEqual(rack_json['subnet'], rack.subnet)
        self.assertTrue(rack_json['nodes'])
        print rack.id
        print rack.nodes[0].id
        self.assertEqual(rack_json['nodes'][0]['id'],
                str(rack.nodes[0].id))
        self.assertTrue(rack_json['capacities'])
        self.assertEqual(rack_json['capacities'][0]['name'],
                rack.capacities[0].name)
        self.assertEqual(rack_json['capacities'][0]['value'],
                rack.capacities[0].value)
        self.assertTrue(rack_json['links'])
        self.assertEqual(rack_json['links'][0]['rel'], 'self')
        self.assertEqual(rack_json['links'][0]['href'],
                'http://localhost/v1/racks/' + str(rack.id))

    def setUp(self):
        """Create 'test_rack'"""

        super(TestRacks, self).setUp()
        self.test_rack = self.db.create_rack(
                v1.Rack(name='test-rack', slots=1,
                    subnet='10.0.0.0/24',
                    chassis=v1.Chassis(id='123'),
                    capacities=[v1.Capacity(name='cpu', value='10')],
                    nodes=[v1.Node(id='1')]
                    ))
        # FIXME: For some reason the 'self.test_rack' does not
        #        lazy-load the 'nodes' and other attrs when
        #        having more than 1 test method...
        #
        self.test_rack = self.db.get_rack(self.test_rack.id)

    def tearDown(self):
        self.db.delete_rack(self.test_rack.id)
        super(TestRacks, self).tearDown()

    def test_it_returns_single_rack(self):
        response = self.get_json('/racks/' + str(self.test_rack.id),
                expect_errors=True)

        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, "application/json")
        self.valid_rack_json(response.json)

    def test_it_returns_rack_list(self):
        response = self.get_json('/racks', expect_errors=True)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, "application/json")

        # The 'test_rack' is present in the racks listing:
        rack_json = filter(lambda r: r['id'] == self.test_rack.id,
                response.json)
        self.assertEqual(len(rack_json), 1)

        # And the Rack serialization is correct
        self.valid_rack_json(rack_json[0])

    def test_it_updates_rack(self):
        json = {
                'name': 'test-new-name'
            }
        response = self.put_json('/racks/' + str(self.test_rack.id),
                params=json, status=200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json['name'], json['name'])
        updated_rack = self.db.get_rack(self.test_rack.id)
        self.assertEqual(updated_rack.name, json['name'])

    def test_it_creates_and_deletes_new_rack(self):
        json = {
                'name': 'test-rack-create',
                'subnet': '127.0.0./24',
                'slots': '10',
                'capacities': [
                    {'name': 'memory', 'value': '1024'}
                ],
                'nodes': [
                    {'id': '1234567'},
                    {'id': '7891011'}
                ]
               }
        response = self.post_json('/racks', params=json, status=201)
        self.assertEqual(response.content_type, "application/json")

        self.assertTrue(response.json['id'])
        self.assertEqual(response.json['name'], json['name'])
        self.assertEqual(str(response.json['slots']), json['slots'])
        self.assertEqual(response.json['subnet'], json['subnet'])
        self.assertEqual(len(response.json['nodes']), 2)

        # Make sure we delete the Rack we just created
        self.db.delete_rack(response.json['id'])

    # FIXME(mfojtik): This test will fail because of Pecan bug, see:
    # https://github.com/tuskar/tuskar/issues/18
    #
    def test_it_returns_404_when_getting_unknown_rack(self):
        response = self.get_json('/racks/unknown',
                expect_errors=True,
                headers={"Accept":
                    "application/json"}
                )

        self.assertEqual(response.status_int, 404)

    # FIXME(mfojtik): This test will fail because of Pecan bug, see:
    # https://github.com/tuskar/tuskar/issues/18
    #
    def test_it_returns_404_when_deleting_unknown_rack(self):
        response = self.delete_json('/racks/unknown',
                expect_errors=True,
                headers={"Accept":
                    "application/json"}
                )

        self.assertEqual(response.status_int, 404)
