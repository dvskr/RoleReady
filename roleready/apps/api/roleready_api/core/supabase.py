"""
Supabase client configuration for RoleReady API
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'your-anon-key')

def get_supabase_client() -> Client:
    """
    Get Supabase client instance
    For development, this returns a mock client
    """
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception:
        # Return a mock client for development
        return MockSupabaseClient()

class MockSupabaseClient:
    """
    Mock Supabase client for development and testing
    """
    
    def table(self, table_name: str):
        return MockTable(table_name)

class MockTable:
    """
    Mock table for development
    """
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    def select(self, *args, **kwargs):
        return MockQuery(self.table_name, 'select', args, kwargs)
    
    def insert(self, data):
        return MockQuery(self.table_name, 'insert', data)
    
    def update(self, data):
        return MockQuery(self.table_name, 'update', data)
    
    def delete(self):
        return MockQuery(self.table_name, 'delete')
    
    def eq(self, column: str, value):
        return MockQuery(self.table_name, 'eq', (column, value))
    
    def rpc(self, function_name: str, params: dict = None):
        return MockQuery(self.table_name, 'rpc', (function_name, params))

class MockQuery:
    """
    Mock query for development
    """
    
    def __init__(self, table_name: str, operation: str, data=None, kwargs=None):
        self.table_name = table_name
        self.operation = operation
        self.data = data
        self.kwargs = kwargs or {}
    
    def execute(self):
        """
        Mock execute method that returns appropriate mock data
        """
        if self.operation == 'select':
            return MockResult([])
        elif self.operation == 'insert':
            # Mock successful insert
            mock_data = self.data if isinstance(self.data, dict) else self.data[0] if isinstance(self.data, list) else {}
            mock_data['id'] = 'mock-id-123'
            mock_data['created_at'] = '2024-01-01T00:00:00Z'
            return MockResult([mock_data])
        elif self.operation == 'update':
            # Mock successful update
            return MockResult([self.data])
        elif self.operation == 'delete':
            # Mock successful delete
            return MockResult([])
        elif self.operation == 'rpc':
            # Mock RPC call
            function_name, params = self.data
            if function_name == 'create_team':
                return MockResult('team-mock-id-123')
            elif function_name == 'invite_team_member':
                return MockResult(True)
            elif function_name == 'get_team_analytics':
                return MockResult([])
            else:
                return MockResult([])
        else:
            return MockResult([])
    
    def eq(self, column: str, value):
        return self
    
    def order(self, column: str, desc: bool = False):
        return self
    
    def limit(self, count: int):
        return self
    
    def single(self):
        return self

class MockResult:
    """
    Mock result object
    """
    
    def __init__(self, data):
        self.data = data
        self.count = len(data) if isinstance(data, list) else 1 if data else 0
