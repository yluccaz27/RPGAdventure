"""
Ponto de entrada do servidor Flask para o RPG Engine.
Inicia a aplicação definida em app.py.
"""
from app import app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
