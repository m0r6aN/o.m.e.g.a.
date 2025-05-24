"""
Tests for the enhanced dependency tracking module.

This test suite validates the functionality of the DependencyResolver class
for proper cross-file dependency mapping.
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from enhanced_dependency_tracking import DependencyResolver
from omega.core.models.analysis_models import Component, Dependency

# Sample repository structure for testing
SAMPLE_REPO = {
    'app.py': '''
from flask import Flask, request, jsonify
from db import get_user, create_user
from utils.helpers import validate_input

app = Flask(__name__)

@app.route('/users/<user_id>')
def user_detail(user_id):
    user = get_user(user_id)
    return jsonify(user)

@app.route('/users', methods=['POST'])
def user_create():
    data = request.json
    if validate_input(data):
        user = create_user(data)
        return jsonify(user), 201
    return jsonify({"error": "Invalid input"}), 400
''',
    'db.py': '''
import sqlite3
from models import User

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['name'], user_data['email'])
    return None

def create_user(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO users (name, email) VALUES (?, ?)',
        (data['name'], data['email'])
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_user(user_id)
''',
    'models.py': '''
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
''',
    'utils/helpers.py': '''
def validate_input(data):
    if not data:
        return False
    if not 'name' in data or not 'email' in data:
        return False
    if not '@' in data['email']:
        return False
    return True

def format_response(data):
    return {
        'status': 'success',
        'data': data
    }
'''
}

class TestDependencyResolver:
    """Test suite for the DependencyResolver class."""
    
    @pytest.fixture
    def sample_components_dependencies(self):
        """Create a sample set of components and dependencies for testing."""
        components = [
            Component(type="file", name="app.py", path="app.py"),
            Component(type="file", name="db.py", path="db.py"),
            Component(type="file", name="models.py", path="models.py"),
            Component(type="file", name="helpers.py", path="utils/helpers.py"),
            
            Component(type="function", name="user_detail", path="app.py:user_detail"),
            Component(type="function", name="user_create", path="app.py:user_create"),
            Component(type="function", name="get_user", path="db.py:get_user"),
            Component(type="function", name="create_user", path="db.py:create_user"),
            Component(type="function", name="get_db_connection", path="db.py:get_db_connection"),
            Component(type="function", name="validate_input", path="utils/helpers.py:validate_input"),
            Component(type="function", name="format_response", path="utils/helpers.py:format_response"),
            
            Component(type="class", name="User", path="models.py:User"),
            Component(type="function", name="to_dict", path="models.py:User.to_dict"),
        ]
        
        dependencies = [
            # app.py imports
            Dependency(source="app.py", target="flask"),
            Dependency(source="app.py", target="db"),
            Dependency(source="app.py", target="utils.helpers"),
            
            # app.py function calls
            Dependency(source="app.py:user_detail", target="get_user"),
            Dependency(source="app.py:user_create", target="validate_input"),
            Dependency(source="app.py:user_create", target="create_user"),
            
            # db.py imports
            Dependency(source="db.py", target="sqlite3"),
            Dependency(source="db.py", target="models"),
            
            # db.py function calls
            Dependency(source="db.py:get_user", target="get_db_connection"),
            Dependency(source="db.py:create_user", target="get_db_connection"),
            Dependency(source="db.py:create_user", target="get_user"),
            Dependency(source="db.py:get_user", target="User"),
        ]
        
        return components, dependencies
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary directory with sample files."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a repo structure
            os.makedirs(os.path.join(temp_dir, 'utils'))
            
            # Create files
            for path, content in SAMPLE_REPO.items():
                file_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)
    
    def test_dependency_resolution(self, sample_components_dependencies, temp_repo):
        """Test that dependencies are correctly resolved."""
        components, dependencies = sample_components_dependencies
        
        resolver = DependencyResolver(temp_repo, components, dependencies)
        resolved_deps = resolver.resolve()
        
        # Check that we have resolved dependencies
        assert len(resolved_deps) >= len(dependencies), "Should have at least as many resolved as raw dependencies"
        
        # Check specific resolutions
        targets = [dep.target for dep in resolved_deps]
        
        # Import resolutions
        assert any(t == "db.py" for t in targets), "Should resolve 'db' import to db.py"
        assert any(t == "models.py" for t in targets), "Should resolve 'models' import to models.py"
        assert any(t == "utils/helpers.py" for t in targets), "Should resolve 'utils.helpers' import to utils/helpers.py"
        
        # Function call resolutions
        assert any(t == "db.py:get_user" for t in targets), "Should resolve 'get_user' call to db.py:get_user"
        assert any(t == "db.py:create_user" for t in targets), "Should resolve 'create_user' call to db.py:create_user"
        assert any(t == "utils/helpers.py:validate_input" for t in targets), "Should resolve 'validate_input' call to utils/helpers.py:validate_input"
        
        # Class references
        assert any(t == "models.py:User" for t in targets), "Should resolve 'User' reference to models.py:User"
    
    def test_import_mapping(self, sample_components_dependencies, temp_repo):
        """Test that import statements are correctly mapped to file paths."""
        components, dependencies = sample_components_dependencies
        
        resolver = DependencyResolver(temp_repo, components, dependencies)
        resolver._build_mappings()
        
        # Check module mappings
        assert "db" in resolver.module_mapping, "'db' should be in module mapping"
        assert resolver.module_mapping["db"] == "db.py", "'db' should map to db.py"
        
        assert "models" in resolver.module_mapping, "'models' should be in module mapping"
        assert resolver.module_mapping["models"] == "models.py", "'models' should map to models.py"
        
        # Check import mappings
        assert "utils.helpers" in resolver.import_mapping, "'utils.helpers' should be in import mapping"
        assert resolver.import_mapping["utils.helpers"] == "utils/helpers.py", "'utils.helpers' should map to utils/helpers.py"
    
    def test_function_mapping(self, sample_components_dependencies, temp_repo):
        """Test that function names are correctly mapped to their paths."""
        components, dependencies = sample_components_dependencies
        
        resolver = DependencyResolver(temp_repo, components, dependencies)
        resolver._build_mappings()
        
        # Check function mappings
        assert "get_user" in resolver.function_mapping, "'get_user' should be in function mapping"
        assert "db.py:get_user" in resolver.function_mapping["get_user"], "'get_user' should map to db.py:get_user"
        
        assert "validate_input" in resolver.function_mapping, "'validate_input' should be in function mapping"
        assert "utils/helpers.py:validate_input" in resolver.function_mapping["validate_input"], "'validate_input' should map to utils/helpers.py:validate_input"
    
    def test_class_mapping(self, sample_components_dependencies, temp_repo):
        """Test that class names are correctly mapped to their paths."""
        components, dependencies = sample_components_dependencies
        
        resolver = DependencyResolver(temp_repo, components, dependencies)
        resolver._build_mappings()
        
        # Check class mappings
        assert "User" in resolver.class_mapping, "'User' should be in class mapping"
        assert "models.py:User" in resolver.class_mapping["User"], "'User' should map to models.py:User"
    
    def test_resolve_import_dependencies(self, sample_components_dependencies, temp_repo):
        """Test resolving dependencies from import statements."""
        components, dependencies = sample_components_dependencies
        
        # Create a new dependency for testing
        import_dep = Dependency(source="app.py", target="db")
        
        resolver = DependencyResolver(temp_repo, components, [import_dep])
        resolver._build_mappings()
        
        resolved = resolver._resolve_dependency(import_dep)
        
        # Check that the import was resolved to a file path
        assert len(resolved) == 1, "Should have one resolved dependency"
        assert resolved[0].source == "app.py", "Source should remain the same"
        assert resolved[0].target == "db.py", "Target should be resolved to db.py"
    
    def test_resolve_function_dependencies(self, sample_components_dependencies, temp_repo):
        """Test resolving dependencies from function calls."""
        components, dependencies = sample_components_dependencies
        
        # Create a new dependency for testing
        func_dep = Dependency(source="app.py:user_detail", target="get_user")
        
        resolver = DependencyResolver(temp_repo, components, [func_dep])
        resolver._build_mappings()
        
        resolved = resolver._resolve_dependency(func_dep)
        
        # Check that the function call was resolved to a function path
        assert len(resolved) == 1, "Should have one resolved dependency"
        assert resolved[0].source == "app.py:user_detail", "Source should remain the same"
        assert resolved[0].target == "db.py:get_user", "Target should be resolved to db.py:get_user"
    
    def test_resolve_class_dependencies(self, sample_components_dependencies, temp_repo):
        """Test resolving dependencies from class references."""
        components, dependencies = sample_components_dependencies
        
        # Create a new dependency for testing
        class_dep = Dependency(source="db.py:get_user", target="User")
        
        resolver = DependencyResolver(temp_repo, components, [class_dep])
        resolver._build_mappings()
        
        resolved = resolver._resolve_dependency(class_dep)
        
        # Check that the class reference was resolved to a class path
        assert len(resolved) == 1, "Should have one resolved dependency"
        assert resolved[0].source == "db.py:get_user", "Source should remain the same"
        assert resolved[0].target == "models.py:User", "Target should be resolved to models.py:User"
    
    def test_complex_resolution_chain(self, sample_components_dependencies, temp_repo):
        """Test resolving a complex chain of dependencies."""
        components, dependencies = sample_components_dependencies
        
        # Create dependency chain: app.py:user_create -> db.py:create_user -> db.py:get_user -> models.py:User
        dep_chain = [
            Dependency(source="app.py:user_create", target="create_user"),
            Dependency(source="db.py:create_user", target="get_user"),
            Dependency(source="db.py:get_user", target="User")
        ]
        
        resolver = DependencyResolver(temp_repo, components, dep_chain)
        resolved_deps = resolver.resolve()
        
        # Extract sources and targets for easier assertion
        resolved_pairs = [(d.source, d.target) for d in resolved_deps]
        
        # Check each link in the chain
        assert ("app.py:user_create", "db.py:create_user") in resolved_pairs, "First link should be resolved"
        assert ("db.py:create_user", "db.py:get_user") in resolved_pairs, "Second link should be resolved"
        assert ("db.py:get_user", "models.py:User") in resolved_pairs, "Third link should be resolved"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
