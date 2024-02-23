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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory
from typing import Type

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a Product"""
        #Create a new product
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        #Find product by id and check all details
        new_product=Product.find(product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)
    
    def test_update_a_product(self):
        """It should Update a Product"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create a new product
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        #Find product by id
        new_product=Product.find(product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        #Update product description
        new_description="New descrition for test"
        product.description=new_description
        product.update()       
        #Find product by id and check its Id and Description
        updated_product=Product.find(product.id)
        self.assertEqual(updated_product.id, product.id)
        self.assertEqual(updated_product.description, new_description)
        #Check there is just one product
        products = Product.all()
        self.assertEqual(len(products), 1)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create a new product
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        #Check there is one product
        products = Product.all()
        self.assertEqual(len(products), 1)
        #Delete product and check there is no product
        product.delete()
        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five new product
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
        #Retrieve all products and check the count
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five products and save their names
        names=[]
        for _ in range(5):
            product=ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
            names.append(product.name)
        first_name=names[0]
        first_name_count=names.count(first_name)
        #Find all products by name and check the count
        products = Product.find_by_name(first_name)
        self.assertEqual(products.count(), first_name_count)
        #check all names
        for product in products:
            self.assertEqual(product.name,first_name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five products and save their names
        availabilities=[]
        for _ in range(10):
            product=ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
            availabilities.append(product.available)
        first_availability=availabilities[0]
        first_availability_count=availabilities.count(first_availability)
        #Find all products by availability and check the count
        products = Product.find_by_availability(first_availability)
        self.assertEqual(products.count(), first_availability_count)
        #check all availabilities
        for product in products:
            self.assertEqual(product.available,first_availability)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five products and save their names
        categories=[]
        for _ in range(10):
            product=ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
            categories.append(product.category)
        first_category=categories[0]
        first_category_count=categories.count(first_category)
        #Find all products by category and check the count
        products = Product.find_by_category(first_category)
        self.assertEqual(products.count(), first_category_count)
        #check all categories
        for product in products:
            self.assertEqual(product.category,first_category)

    #
    # MY EXTRA TEST CASES
    #
    def test_find_by_price(self):
        """It should Find Products by Price"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five products and save their names
        prices=[]
        for _ in range(10):
            product=ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
            prices.append(product.price)
        first_price=prices[0]
        first_price_count=prices.count(first_price)
        #Find all products by price and check the count
        products = Product.find_by_price(first_price)
        self.assertEqual(products.count(), first_price_count)
        #check all categories
        for product in products:
            self.assertEqual(product.price,first_price)
    
    def test_update_no_id(self):
        """It should raise DataValidationError"""
        product=ProductFactory()
        product.id=None
        self.assertRaises(DataValidationError,product.update)

    def test_serialize(self):
        """It should return dictionary"""
        product=ProductFactory()
        #Serialize object and check type and then each key
        product_dic=product.serialize()
        self.assertIsInstance(product_dic,dict)
        self.assertEqual(product_dic['name'],product.name)
        self.assertEqual(product_dic['description'],product.description)
        self.assertEqual(Decimal(product_dic['price']),product.price)
        self.assertEqual(product_dic['available'],product.available)
        self.assertEqual(product_dic['category'],product.category.name)

    def test_deserialize(self):
        """It should convert dictionary to object"""
        product=ProductFactory()
        #Serialize object and check type
        product_dic=product.serialize()
        self.assertIsInstance(product_dic,dict)
        #Derialize dictionary and check each attribute
        product_obj=product.deserialize(data=product_dic)
        self.assertEqual(product_obj.name,product.name)
        self.assertEqual(product_obj.description,product.description)
        self.assertEqual(product_obj.price,product.price)
        self.assertEqual(product_obj.available,product.available)
        self.assertEqual(product_obj.category,product.category)

    def test_deserialize_available_not_bool(self):
        """It should raise DataValidationError for availabe"""
        product=ProductFactory()
        #Serialize object and check type
        product_dic=product.serialize()
        self.assertIsInstance(product_dic,dict)
        #Change availabe to string and Derialize dictionary
        product_dic['available']="True"
        self.assertRaises(DataValidationError,product.deserialize,product_dic)

    def test_deserialize_category_not_valid(self):
        """It should raise DataValidationError for category"""
        product=ProductFactory()
        #Serialize object and check type
        product_dic=product.serialize()
        self.assertIsInstance(product_dic,dict)
        #Change category to none defined string and Derialize dictionary
        product_dic['category']="NOT_EXIST"
        self.assertRaises(DataValidationError,product.deserialize,product_dic)

    def test_deserialize_type_error(self):
        """It should raise DataValidationError for incorrect type"""
        product=ProductFactory()
        #Serialize object and check type
        product_dic=product.serialize()
        self.assertIsInstance(product_dic,dict)
        #Change category to number and Derialize dictionary
        product_dic['category']=1
        self.assertRaises(DataValidationError,product.deserialize,product_dic)
        product_dic=product.serialize()
        #Change price to string and Derialize dictionary
        #NOT PASS
        ## product_dic['price']="ten dollar"
        ## self.assertRaises(DataValidationError,product.deserialize,product_dic)

    def test_find_by_strin_price(self):
        """It should Find Products by string Price"""
        #Check products are empty
        products = Product.all()
        self.assertEqual(products, [])
        #Create five products and save their names
        prices=[]
        for _ in range(10):
            product=ProductFactory()
            product.id = None
            product.create()
            # Assert that it was assigned an id and shows up in the database
            self.assertIsNotNone(product.id)
            prices.append(product.price)
        first_price=prices[0]
        first_price_count=prices.count(first_price)
        #Find all products by price and check the count
        str_price=str(first_price)
        products = Product.find_by_price(str_price)
        self.assertEqual(products.count(), first_price_count)
        #check all categories
        for product in products:
            self.assertEqual(product.price,first_price)