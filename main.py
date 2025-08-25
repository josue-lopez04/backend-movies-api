from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuración
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://admin:Movies2024Secure!@movies-cluster.xxxxx.mongodb.net/moviesdb?retryWrites=true&w=majority')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')

# Conexión a MongoDB
client = MongoClient(MONGO_URI)
db = client.moviesdb
movies_collection = db.movies

def verify_token():
    """Verificar token en headers"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return decoded
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Movies API',
        'timestamp': datetime.datetime.now().isoformat()
    }), 200

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Obtener todas las películas"""
    try:
        # Verificar autenticación (opcional)
        # user = verify_token()
        # if not user:
        #     return jsonify({'error': 'Unauthorized'}), 401
        
        movies = list(movies_collection.find())
        for movie in movies:
            movie['_id'] = str(movie['_id'])
        
        return jsonify({
            'movies': movies,
            'count': len(movies)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    """Obtener película por ID"""
    try:
        movie = movies_collection.find_one({'_id': ObjectId(movie_id)})
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie['_id'] = str(movie['_id'])
        return jsonify(movie), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies', methods=['POST'])
def create_movie():
    """Crear nueva película"""
    try:
        # Verificar autenticación
        user = verify_token()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        movie = {
            'title': data['title'],
            'year': data.get('year', 2024),
            'genre': data.get('genre', 'Unknown'),
            'director': data.get('director', 'Unknown'),
            'rating': data.get('rating', 0),
            'description': data.get('description', ''),
            'created_at': datetime.datetime.utcnow(),
            'created_by': user['email']
        }
        
        result = movies_collection.insert_one(movie)
        movie['_id'] = str(result.inserted_id)
        
        return jsonify(movie), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<movie_id>', methods=['PUT'])
def update_movie(movie_id):
    """Actualizar película"""
    try:
        user = verify_token()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        data['updated_at'] = datetime.datetime.utcnow()
        data['updated_by'] = user['email']
        
        result = movies_collection.update_one(
            {'_id': ObjectId(movie_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Movie not found'}), 404
        
        return jsonify({'message': 'Movie updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """Eliminar película"""
    try:
        user = verify_token()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        result = movies_collection.delete_one({'_id': ObjectId(movie_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Movie not found'}), 404
        
        return jsonify({'message': 'Movie deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/seed', methods=['POST'])
def seed_movies():
    """Poblar base de datos con películas de ejemplo"""
    try:
        # Limpiar colección
        movies_collection.delete_many({})
        
        # Películas de ejemplo
        sample_movies = [
            {
                'title': 'The Shawshank Redemption',
                'year': 1994,
                'genre': 'Drama',
                'director': 'Frank Darabont',
                'rating': 9.3,
                'description': 'Two imprisoned men bond over a number of years.'
            },
            {
                'title': 'The Godfather',
                'year': 1972,
                'genre': 'Crime',
                'director': 'Francis Ford Coppola',
                'rating': 9.2,
                'description': 'The aging patriarch of an organized crime dynasty.'
            },
            {
                'title': 'The Dark Knight',
                'year': 2008,
                'genre': 'Action',
                'director': 'Christopher Nolan',
                'rating': 9.0,
                'description': 'Batman faces the Joker.'
            },
            {
                'title': 'Pulp Fiction',
                'year': 1994,
                'genre': 'Crime',
                'director': 'Quentin Tarantino',
                'rating': 8.9,
                'description': 'Various interconnected stories in LA.'
            },
            {
                'title': 'Forrest Gump',
                'year': 1994,
                'genre': 'Drama',
                'director': 'Robert Zemeckis',
                'rating': 8.8,
                'description': 'Life story of a simple man with a low IQ.'
            }
        ]
        
        for movie in sample_movies:
            movie['created_at'] = datetime.datetime.utcnow()
            movies_collection.insert_one(movie)
        
        return jsonify({
            'message': 'Database seeded',
            'count': len(sample_movies)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)