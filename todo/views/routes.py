from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta

api = Blueprint('api', __name__, url_prefix='/api/v1')

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}


TODO_PUT_FIELDS = {
    'title', 'description', 'completed', 'deadline_at'
}

TODO_POST_FIELDS = { 'id' } | TODO_PUT_FIELDS
TODO_POST_REQUIRED = { 'title' }

TODO_SERVER_FIELDS = {
    'created_at', 'updated_at'
}

TODO_ALL_FIELDS = TODO_POST_FIELDS | TODO_SERVER_FIELDS

def validate_todo_json(allowed_fields):
    if not request.json:
        return jsonify({'error': 'request missing json'}), 400
    extra_keys = set(request.json.keys()) - allowed_fields
    if extra_keys:
        return jsonify({'error': f'request contains unexpected keys: {extra_keys}'}), 400
    return None


@api.route('/health')
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query
    completed_flag = request.args.get('completed', False)
    if completed_flag:
        todos = todos.where(Todo.completed == True)

    window_flag = request.args.get('window', None)
    if window_flag is not None:
        try: window = int(window_flag)
        except ValueError: window = -1

        if window < 0:
            return jsonify({'error': 'window is not a valid integer: ' + window_flag}), 400

        future = datetime.now() + timedelta(days=window)
        todos = todos.where(Todo.deadline_at <= future)

    result = [todo.to_dict() for todo in todos.all()]
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    if err := validate_todo_json(TODO_POST_FIELDS):
        return err
    if missing := (TODO_POST_REQUIRED - set(request.json.keys())):
        return jsonify({'error': f'missing required fields: {missing}'}), 400
    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    # Adds a new record to the database or will update an existing record.
    db.session.add(todo)
    # Commits the changes to the database.
    # This must be called for the changes to be saved.
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if err := validate_todo_json(TODO_PUT_FIELDS):
        return err
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()
    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200


