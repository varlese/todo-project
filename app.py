from flask import Flask, render_template, request, redirect, url_for, jsonify, abort

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate

import sys, traceback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost:5432/todoapp'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#setting up the todo and todolist models

class Todo(db.Model):
	__tablename__ = 'todos'
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.String(), nullable=False)
	completed = db.Column(db.Boolean, default=False)
	list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

	def __repr__(self):
		return f'<Todo id="{self.id}" list_id="{self.list_id}" description="{self.description}">'

class TodoList(db.Model):
	__tablename__ = 'todolists'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(), nullable=False)
	todos = db.relationship('Todo', backref='list', lazy=True)

	def __repr__(self):
		return f'<List id="{self.id}" name="{self.name}">'

#create todo list

@app.route('/create-list', methods=['POST'])
def create_list():
	error = False
	body = {}
	try:
		name = request.get_json()['name']
		new_list = TodoList(name=name)
		db.session.add(new_list)
		db.session.commit()
		body['name'] = new_list.name
		body['id'] = new_list.id
	except:
		error = True
		db.session.rollback()
		exc_type, exc_value, exc_traceback = sys.exc_info()

		print("*** print_exception:")
		traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

	finally:
		db.session.close()
	if not error:
		return jsonify(body)
	else:
		abort(500)

#delete todo list

@app.route('/lists/<list_id>', methods=['DELETE'])
def delete_list(list_id):
	try:
		TodoList.query.filter_by(id=list_id).delete()
		db.session.commit()
	except:
		db.session.rollback()
	finally:
		db.session.close()
	return jsonify({ 'success': True })

#create todo item

@app.route('/create', methods=['POST'])
def create_todo():
	error = False
	body = {}
	try:
		description = request.get_json()['description']
		list_id = request.get_json()['list_id']
		todo = Todo(description=description)
		active_list = TodoList.query.get(list_id)
		todo.list = active_list
		db.session.add(todo)
		db.session.commit()
		body['description'] = todo.description
	except:
		error = True
		db.session.rollback()
		exc_type, exc_value, exc_traceback = sys.exc_info()

		print("*** print_exception:")
		traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)

	finally:
		db.session.close()
	if not error:
		return jsonify(body)
	else:
		abort(500)

#delete todo items

@app.route('/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
	try:
		Todo.query.filter_by(id=todo_id).delete()
		db.session.commit()
	except:
		db.session.rollback()
	finally:
		db.session.close()
	return jsonify({ 'success': True })

#change todo to completed

@app.route('/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
	try:
		completed = request.get_json()['completed']
		print('completed', completed)
		todo = Todo.query.get(todo_id)
		todo.completed = completed
		db.session.commit()
	except:
		db.session.rollback()
	finally:
		db.session.close()
	return redirect(url_for('index'))

#selects list id and related todos

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
	todos_in_list = Todo.query.filter_by(list_id=list_id).order_by('id').all()
	for todo in todos_in_list:
		print(todo)
	return render_template(
		'index.html',
		lists=TodoList.query.all(),
		active_list=TodoList.query.get(list_id),
		todos=todos_in_list
	)

#standard route to index.html

@app.route('/')
def index():
	return redirect(url_for('get_list_todos', list_id=1))
