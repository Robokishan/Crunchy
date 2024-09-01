# -*- coding: utf-8 -*-
# refrence: https://github.com/johanlundberg/neo4j-django-tutorial/tree/master/neo4jtut/neo4jtut
from contextlib import contextmanager
from neo4j import GraphDatabase, basic_auth


class Neo4jDBSessionManager:
    def __init__(self, uri, username=None, password=None, encrypted=True):
        self.uri = uri
        self.driver = self._get_db_driver(uri, username, password, encrypted)

    @staticmethod
    def _get_db_driver(uri, username=None, password=None, encrypted=True, max_connection_pool_size=50):
        """
        :param uri: Bolt uri
        :type uri: str
        :param username: Neo4j username
        :type username: str
        :param password: Neo4j password
        :type password: str
        :param encrypted: Use TLS
        :type encrypted: Boolean
        :param max_pool_size: Maximum number of idle sessions
        :type max_pool_size: Integer
        :param trust: Trust cert on first use (0) or do not accept unknown cert (1)
        :type trust: Integer
        :return: Neo4j driver
        :rtype: neo4j.v1.session.Driver
        """
        return GraphDatabase.driver(uri, auth=basic_auth(username, password), encrypted=encrypted,
                                    max_connection_pool_size=max_connection_pool_size)

    @contextmanager
    def _session(self):
        session = self.driver.session()
        try:
            yield session
        except Exception as e:
            print(e)
            raise e
    session = property(_session)

    @contextmanager
    def _transaction(self):
        session = self.driver.session()
        transaction = session.begin_transaction()
        try:
            yield transaction
        except Exception as e:
            session.rollback_transaction()
            raise e
        else:
            session.commit_transaction()
    transaction = property(_transaction)