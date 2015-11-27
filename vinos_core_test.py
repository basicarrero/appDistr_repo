#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-
u"""
vinos_core test
"""
import unittest
import json
import os
from vinos_core import app, db


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_01_Wines(self):
        try:
            os.remove('db.sqlite')
        except OSError:
            pass
        db.create_all()
        # Create
        wine_1 = {
           'name': "lambrusco",
           'grade': 9,
           'price': 5.99,
           'bottle': 1
           }
        response = self.app.post('/wines',
                                 data=json.dumps(wine_1),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        global id_lambrusco
        id_lambrusco = json.loads(response.data)['created']
        wine_2 = {
           'name': "mosto",
           'grade': 7,
           'price': 3.5
           }
        response = self.app.post('/wines',
                                 data=json.dumps(wine_2),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        global id_mosto
        id_mosto = json.loads(response.data)['created']

        # Update
        wine_1['price'] = 10
        response = self.app.put('/wines' + '/' + id_lambrusco,
                                data=json.dumps(wine_1),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(self.app.get('/wines' + '/' + id_lambrusco).data)
        self.assertEqual(data['price'], wine_1['price'])
        id_lambrusco = data['id']

        # Show by type
        response = self.app.get('/wines/byType/azul')
        self.assertEqual(response.status_code, 404)
        response = self.app.get('/wines/byType/tinto')
        data = json.loads(response.data)
        self.assertEqual(data['red'], ["lambrusco"])
        response = self.app.get('/wines/byType/blanco')
        data = json.loads(response.data)
        self.assertEqual(data['white'], ["mosto"])

        # Delete
        response = self.app.delete('/wines/' + id_mosto)
        self.assertEqual(response.status_code, 200)

        # Get
        response = self.app.get('/wines/' + id_lambrusco)
        data = json.loads(response.data)
        self.assertEqual(data['id'], id_lambrusco)

        # Get unlisted
        response = self.app.get('/wines/jk35')
        self.assertEqual(response.status_code, 404)

        # Get All
        response = self.app.get('/wines')
        data = json.loads(response.data)
        self.assertEqual(data['wines'][0]['name'], "lambrusco")

        # Delete All
        response = self.app.delete('/wines')
        self.assertEqual(response.status_code, 200)

        # Put new
        response = self.app.put('/wines' + '/' + id_lambrusco,
                                data=json.dumps(wine_1),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        id_lambrusco = json.loads(response.data)['created']

        # Bad one
        response = self.app.post('/wines',
                                 data=json.dumps({'price': 2}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_02_Users(self):
        # Create
        user_1 = {
           'email': "basicarrero@hotmail.com",
           'pass': "prueba",
           }
        response = self.app.post('/clients',
                                 data=json.dumps(user_1),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        user_2 = {
           'email': "jonero@gmail.com",
           'pass': "prueba",
           }
        response = self.app.post('/clients',
                                 data=json.dumps(user_2),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.app.post('/clients',
                                 data=json.dumps(user_2),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        user_3 = {
           'email': "dummy@gmail.com",
           'pass': "prueba",
           }
        response = self.app.put('/clients/' + user_3['email'],
                                data=json.dumps(user_3),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Bad one
        response = self.app.post('/clients',
                                 data=json.dumps({'pass': "prueba"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # Get All
        response = self.app.get('/clients')
        self.assertEqual(response.status_code, 200)

        # Update
        user_1['phone'] = "690413234"
        response = self.app.put('/clients/' + user_1['email'],
                                data=json.dumps(user_1),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(self.app.get('/clients/' + user_1['email']).data)
        self.assertEqual(data['phone'], user_1['phone'])

        # Delete
        response = self.app.delete('/clients/jonero@gmail.com')
        self.assertEqual(response.status_code, 200)

        # Get unlisted
        response = self.app.delete('/clients/juan@gmail.com')
        self.assertEqual(response.status_code, 404)

    def test_03_Cart(self):
        # Create
        response = self.app.post('/clients/basicarrero@hotmail.com',
                                 data=json.dumps({"name": "my_cart"}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        id_cart = data['created']['id']

        # Add other
        itemLst = {"items": [id_lambrusco]}
        response = self.app.put('/clients/basicarrero@hotmail.com/carts/myOtherCart',
                                data=json.dumps(itemLst),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Add unlisted wine
        itemLst = {"items": [id_lambrusco, 'unknow']}
        response = self.app.put('/clients/basicarrero@hotmail.com/carts/' + id_cart,
                                data=json.dumps(itemLst),
                                content_type='application/json')
        self.assertEqual(response.status_code, 404)

        # Add to cart
        itemLst = {"items": [id_lambrusco]}
        response = self.app.put('/clients/basicarrero@hotmail.com/carts/' + id_cart,
                                data=json.dumps(itemLst),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Get
        response = self.app.get('/clients/basicarrero@hotmail.com/carts/' + id_cart)
        data = json.loads(response.data)
        self.assertEqual(data['items'], [id_lambrusco])

        # Update unlisted item
        response = self.app.put('/clients/basicarrero@hotmail.com/carts/' +
                                id_cart + '/item/' + id_mosto)
        self.assertEqual(response.status_code, 404)

        # Delete item
        response = self.app.delete('/clients/basicarrero@hotmail.com/carts/' +
                                   id_cart + '/item/' + id_lambrusco)
        self.assertEqual(response.status_code, 200)

        # Update item
        response = self.app.put('/clients/basicarrero@hotmail.com/carts/' +
                                id_cart + '/item/' + id_lambrusco)
        self.assertEqual(response.status_code, 200)

        # Delete cart
        response = self.app.delete('/clients/basicarrero@hotmail.com/carts/' + id_cart)
        self.assertEqual(response.status_code, 200)

        # Missed client
        response = self.app.delete('/clients/pepe@hotmail.com/carts/kjsdfh')
        self.assertEqual(response.status_code, 404)

        # Missed client_2
        response = self.app.delete('/clients/pepe@hotmail.com/carts/kjsdfh/item/dasf')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
