import discord
from discord.ext import commands
import os
import asyncio
from flask import Flask  # Para mantener el bot 24/7
import google.generativeai as genai  # Librería de Google Gemini

# ------ CONFIGURACIÓN DEL BOT ------
TARGET_CHANNEL_ID = 1372765754621038593
NOT_ALLOWED_MESSAGE = "Hola, soy el bot de IA de Novacraft. Solo puedo conversar en este canal. Por favor, ve al canal designado para hablar conmigo."

# ------ FLASK PARA MANTENER EL BOT ENCENDIDO ------
app = Flask('')

@app.route('/')
def home():
    return "¡El bot de Novacraft está vivo y coleando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    from threading import Thread
    t = Thread(target=run)
    t.start()

# ------ CONFIGURACIÓN DEL BOT DE DISCORD ------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=None, intents=intents)

@bot.event
async def on_ready():
    print(f'¡Bot {bot.user} de Novacraft ha iniciado sesión!')
    print(f'El bot solo responderá en el canal con ID: {TARGET_CHANNEL_ID}')
    print('-----------------------------------------')
    await bot.change_presence(activity=discord.Game(name="¡Pensando en Novacraft!"))

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    query = message.content.strip()
    if not query:
        return

    async with message.channel.typing():
        try:
            GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
            if not GEMINI_API_KEY:
                await message.channel.send("Lo siento, la clave API de Gemini no está configurada. No puedo responder en este momento.")
                print("ERROR: GEMINI_API_KEY no encontrada en Replit Secrets.")
                return

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            response = model.generate_content(query)

            if response.candidates and response.candidates[0].content:
                response_text = response.candidates[0].content.parts[0].text
                if len(response_text) > 2000:
                    for chunk in [response_text[i:i+1999] for i in range(0, len(response_text), 1999)]:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response_text)
            else:
                await message.channel.send("Lo siento, no pude generar una respuesta para eso. Intenta preguntar de otra manera.")

        except Exception as e:
            print(f"Error al interactuar con Gemini API: {e}")
            if "Resource exhausted" in str(e) or "quota" in str(e).lower():
                await message.channel.send(f"He alcanzado mi límite de uso por ahora. Inténtalo de nuevo más tarde. ({e})")
            else:
                await message.channel.send(f"Ups... ocurrió un error: {e}")

# ------ INICIO DEL BOT Y MANTENIMIENTO 24/7 ------
async def main_loop():
    keep_alive()  # Activa el servidor web
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    if not DISCORD_TOKEN:
        print("ERROR: El TOKEN de Discord no fue encontrado. Agrégalo en Replit Secrets.")
        return
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main_loop())
    except discord.errors.LoginFailure:
        print("ERROR: Fallo al iniciar sesión. ¿Tu TOKEN de bot es correcto?")
    except Exception as e:
        print(f"Error inesperado al iniciar el bot: {e}")