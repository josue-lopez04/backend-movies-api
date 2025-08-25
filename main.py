# main.py - Movies Service
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId
import jwt
import datetime
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración
MONGO_URI = os.environ.get('MONGO_URI', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
PORT = int(os.environ.get('PORT', 8080))

# Conexión a MongoDB
client = None
db = None
movies_collection = None

def connect_to_mongodb():
    """Conectar a MongoDB con manejo de errores"""
    global client, db, movies_collection
    
    if not MONGO_URI:
        logger.warning("MONGO_URI not configured - running in demo mode")
        return False
    
    try:
        logger.info("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client.moviesdb
        movies_collection = db.movies
        logger.info("Successfully connected to MongoDB")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False

mongodb_connected = connect_to_mongodb()

# Datos demo para cuando MongoDB no está disponible
DEMO_MOVIES = [
    {
        '_id': '1',
        'title': 'The Shawshank Redemption',
        'year': 1994,
        'genre': 'Drama',
        'director': 'Frank Darabont',
        'rating': 9.3,
        'description': 'Two imprisoned men bond over years.'
    },
    {
        '_id': '2',
        'title': 'The Godfather',
        'year': 1972,
        'genre': 'Crime',
        'director': 'Francis Ford Coppola',
        'rating': 9.2,
        'description': 'The aging patriarch of a crime dynasty.'
    }
]

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Movies API',
        'status': 'running',
        'mongodb': 'connected' if mongodb_connected else 'demo mode',
        'endpoints': ['/health', '/api/movies', '/api/movies/<id>']
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Movies API',
        'timestamp': datetime.datetime.now().isoformat(),
        'mongodb': 'connected' if mongodb_connected else 'demo mode',
        'port': PORT
    }), 200

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Obtener todas las películas"""
    try:
        if not mongodb_connected:
            return jsonify({
                'movies': DEMO_MOVIES,
                'count': len(DEMO_MOVIES),
                'mode': 'demo'
            }), 200
        
        movies = list(movies_collection.find())
        for movie in movies:
            movie['_id'] = str(movie['_id'])
        
        return jsonify({
            'movies': movies,
            'count': len(movies)
        }), 200
    except Exception as e:
        logger.error(f"Error getting movies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    """Obtener película por ID"""
    try:
        if not mongodb_connected:
            movie = next((m for m in DEMO_MOVIES if m['_id'] == movie_id), None)
            if not movie:
                return jsonify({'error': 'Movie not found'}), 404
            return jsonify(movie), 200
        
        try:
            movie = movies_collection.find_one({'_id': ObjectId(movie_id)})
        except InvalidId:
            return jsonify({'error': 'Invalid movie ID format'}), 400
            
        if not movie:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie['_id'] = str(movie['_id'])
        return jsonify(movie), 200
    except Exception as e:
        logger.error(f"Error getting movie: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/seed', methods=['POST'])
def seed_movies():
    """Poblar base de datos con películas de ejemplo"""
    if not mongodb_connected:
        return jsonify({
            'message': 'Database not connected - using demo data',
            'movies': DEMO_MOVIES
        }), 200
    
    try:
        movies_collection.delete_many({})
        
        sample_movies = [
            {
                'title': 'The Shawshank Redemption',
                'year': 1994,
                'genre': 'Drama',
                'director': 'Frank Darabont',
                'rating': 9.3,
                'description': 'Two imprisoned men bond over years.'
            },
            {
                'title': 'The Godfather',
                'year': 1972,
                'genre': 'Crime',
                'director': 'Francis Ford Coppola',
                'rating': 9.2,
                'description': 'The aging patriarch of a crime dynasty.'
            },
            {
                'title': 'The Dark Knight',
                'year': 2008,
                'genre': 'Action',
                'director': 'Christopher Nolan',
                'rating': 9.0,
                'description': 'Batman faces the Joker.'
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
        logger.error(f"Error seeding: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Movies Service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)