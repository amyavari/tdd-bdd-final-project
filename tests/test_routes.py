######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_get_product(self):
        """It should Get a single Product"""
        #Create a new product
        test_product =self._create_products(1)[0]
        #Read sent product
        response=self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(data['name'],test_product.name)

    def test_get_product_not_found(self):
        """It should not Get any Product with wrong Id"""
        response=self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update a single Product"""
        #Create a new product
        test_product =self._create_products(1)[0]
        #Read sent product
        response=self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(data['name'],test_product.name)
        #Update name and check returned object name
        new_name="new name"
        test_product.name=new_name
        data=test_product.serialize()
        response=self.client.put(f"{BASE_URL}/{test_product.id}",json=data)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(data['name'],new_name)
        #Get product and check name
        response=self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(data['name'],new_name)

    def test_update_product_not_found(self):
        """It should not Update any Product that wrong Id"""
        test_product =self._create_products(1)[0]
        response=self.client.put(f"{BASE_URL}/0",json=test_product.serialize())
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
    
    def test_update_product_with_no_name(self):
        """It should not Update any Product without name"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        del new_product["name"]
        response = self.client.put(f"{BASE_URL}/{test_product.id}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_no_content_type(self):
        """It should not Update any Product with no Content-Type"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        response = self.client.put(f"{BASE_URL}/{test_product.id}", data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_product_wrong_content_type(self):
        """It should not Update any Product with wrong Content-Type"""
        test_product = self._create_products(1)[0]
        new_product = test_product.serialize()
        response = self.client.put(f"{BASE_URL}/{test_product.id}", data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    
    def test_delete_product(self):
        """It should Delete a single Product"""
        #Create a new product
        test_product =self._create_products(1)[0]
        #Read sent product
        response=self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        #Delete the product and check it not exist anymore
        response=self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        response=self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should not Delete any Product with wrong Id"""
        test_product =self._create_products(1)[0]
        response=self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

    def test_list_all_products(self):
        """It should list all products"""
        #Check every thing is empty
        response=self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),0)
        #Create new products
        test_products =self._create_products(5)
        #list all products
        response=self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),5)

    def test_list_all_products_by_name(self):
        """It should list all products by their Name"""
        #Check every thing is empty
        response=self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),0)
        #Create new products and read their names
        test_products =self._create_products(10)
        names=[]
        for product in test_products:
            names.append(product.name)
        first_name=test_products[0].name
        first_name_count=names.count(first_name)
        #list all products by name
        response=self.client.get(f"{BASE_URL}/name/{first_name}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),first_name_count)
        for product in data:
            self.assertEqual(product["name"],first_name)

    def test_list_all_products_by_name_empty(self):
        """It should not list any products with empty Name value"""
        test_products =self._create_products(10)

        response=self.client.get(f"{BASE_URL}/name/")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)


    def test_list_all_products_by_category(self):
        """It should list all products by their Category"""
        #Check every thing is empty
        response=self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),0)
        #Create new products and read their categories
        test_products =self._create_products(10)
        categories=[]
        for product in test_products:
            categories.append(product.category.name)
        first_category=test_products[0].category.name
        first_category_count=categories.count(first_category)
        #list all products by category
        response=self.client.get(f"{BASE_URL}/category/{first_category}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),first_category_count)
        for product in data:
            self.assertEqual(product["category"],first_category)
    
    def test_list_all_products_by_category_empty(self):
        """It should not list any products with empty Category value"""
        test_products =self._create_products(10)

        response=self.client.get(f"{BASE_URL}/category/")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
        response=self.client.get(f"{BASE_URL}/category/not_valid")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
    
    def test_list_all_products_by_availability(self):
        """It should list all products by their Availability"""
        #Check every thing is empty
        response=self.client.get(BASE_URL)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),0)
        #Create new products and read their categories
        test_products =self._create_products(10)
        availabilities=[]
        for product in test_products:
            availabilities.append(product.available)
        first_availability=test_products[0].available
        first_availability_count=availabilities.count(first_availability)
        #list all products by category
        response=self.client.get(f"{BASE_URL}/avalability/{first_availability}")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        data=response.get_json()
        self.assertEqual(len(data),first_availability_count)
        for product in data:
            self.assertEqual(product["available"],first_availability)
 
    def test_list_all_products_by_availability_empty(self):
        """It should not list any products with wrong Availability value"""
        test_products =self._create_products(10)

        response=self.client.get(f"{BASE_URL}/avalability/")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)
        response=self.client.get(f"{BASE_URL}/avalability/3")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
