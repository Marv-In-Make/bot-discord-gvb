#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================
DISCORD BOT MONSTER - GVB-ÉLECTRICITÉ
================================================================
Version: 2.0 Monster Edition
Date: 2026-01-02
Author: Marvin Ansseau

Features:
- 20+ commandes Discord
- API REST FastAPI (15+ endpoints)
- PostgreSQL + Redis
- Cache intelligent
- Rate limiting
- Logging structuré
- Métriques Prometheus
- Webhooks entrants/sortants
- Backup automatique
- Modération automatique
================================================================
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any
import json

# Discord
import discord
from discord.ext import commands, tasks

# Database
import asyncpg
from redis import asyncio as aioredis

# API REST
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import uvicorn

# Monitoring
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

# Utilities
from dotenv import load_dotenv
import structlog

# ================================================================
# CONFIGURATION
# ================================================================

load_dotenv()

# Discord Config
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
BOT_NAME = os.getenv('BOT_NAME', 'GVBOT')

# PostgreSQL Config
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres_discord')
DB_PORT = int(os.getenv('POSTGRES_PORT', 5432))
DB_USER = os.getenv('POSTGRES_USER', 'gvb')
DB_PASS = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB', 'discord_gvb')

# Redis Config
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_discord')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASS = os.getenv('REDIS_PASSWORD')

# API Config
API_KEY = os.getenv('API_KEY')
API_PORT = int(os.getenv('API_PORT', 5000))

# Channels IDs
CHANNEL_PLANNING_HEBDO = int(os.getenv('CHANNEL_PLANNING_HEBDO', 0)) if os.getenv('CHANNEL_PLANNING_HEBDO') else None
CHANNEL_LOGS_BOT = int(os.getenv('CHANNEL_LOGS_BOT', 0)) if os.getenv('CHANNEL_LOGS_BOT') else None
CHANNEL_ANNONCES = int(os.getenv('CHANNEL_ANNONCES', 0)) if os.getenv('CHANNEL_ANNONCES') else None

# Webhooks Discord
WEBHOOK_LOGS_URL = os.getenv('WEBHOOK_LOGS_URL')
WEBHOOK_ALERTS_URL = os.getenv('WEBHOOK_ALERTS_URL')

# Monitoring
ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'false').lower() == 'true'
METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))

# ================================================================
# LOGGING STRUCTURÉ
# ================================================================

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

# ================================================================
# MÉTRIQUES PROMETHEUS
# ================================================================

if ENABLE_METRICS:
    # Compteurs
    METRIC_COMMANDS_TOTAL = Counter('discord_commands_total', 'Total commands executed', ['command'])
    METRIC_MESSAGES_TOTAL = Counter('discord_messages_total', 'Total messages logged')
    METRIC_API_REQUESTS_TOTAL = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
    
    # Histogrammes
    METRIC_COMMAND_DURATION = Histogram('discord_command_duration_seconds', 'Command execution time', ['command'])
    METRIC_API_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint'])
    
    # Gauges
    METRIC_GUILD_MEMBERS = Gauge('discord_guild_members_total', 'Total guild members')
    METRIC_DB_CONNECTIONS = Gauge('postgres_connections_active', 'Active PostgreSQL connections')

# ================================================================
# BOT DISCORD
# ================================================================

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    help_command=None,  # Custom help command
    case_insensitive=True
)

# Pools globaux
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None

# FastAPI app
api_app = FastAPI(title="GVBOT API", version="2.0")

# ================================================================
# DATABASE FUNCTIONS
# ================================================================

async def init_db():
    """Initialize PostgreSQL connection pool"""
    global db_pool
    
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("database_connected", host=DB_HOST, database=DB_NAME)
        
        # Test connexion
        async with db_pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            logger.info("postgres_version", version=version)
        
        if ENABLE_METRICS:
            METRIC_DB_CONNECTIONS.set(db_pool.get_size())
        
        return True
    
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False

async def close_db():
    """Close PostgreSQL connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("database_closed")

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    try:
        redis_client = await aioredis.from_url(
            f"redis://:{REDIS_PASS}@{REDIS_HOST}:{REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
            max_connections=10
        )
        
        # Test connexion
        await redis_client.ping()
        logger.info("redis_connected", host=REDIS_HOST)
        return True
    
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("redis_closed")

# ================================================================
# BOT EVENTS
# ================================================================

@bot.event
async def on_ready():
    """Bot démarré et connecté"""
    logger.info(
        "bot_ready",
        bot_name=bot.user.name,
        bot_id=bot.user.id,
        guilds=len(bot.guilds),
        latency_ms=round(bot.latency * 1000, 2)
    )
    
    # Init databases
    await init_db()
    await init_redis()
    
    # Load extensions
    await load_extensions()
    
    # Start background tasks
    update_stats_cache.start()
    post_weekly_planning.start()
    cleanup_old_data.start()
    
    # Update bot presence
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} serveurs | {BOT_PREFIX}help"
        ),
        status=discord.Status.online
    )
    
    # Update metrics
    if ENABLE_METRICS:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            METRIC_GUILD_MEMBERS.set(guild.member_count)
    
    # Log dans channel
    if CHANNEL_LOGS_BOT:
        channel = bot.get_channel(CHANNEL_LOGS_BOT)
        if channel:
            embed = discord.Embed(
                title="🤖 Bot Démarré",
                description=f"**{BOT_NAME}** est maintenant en ligne !",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Latence", value=f"{round(bot.latency * 1000)}ms")
            embed.add_field(name="Serveurs", value=len(bot.guilds))
            await channel.send(embed=embed)

@bot.event
async def on_message(message: discord.Message):
    """Log tous les messages dans PostgreSQL"""
    
    # Ignorer messages bot
    if message.author.bot:
        return
    
    try:
        # Log dans PostgreSQL
        async with db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO messages (
                    message_id, user_id, user_name, channel_id, 
                    channel_name, guild_id, content, is_bot, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''', 
                message.id,
                message.author.id,
                message.author.name,
                message.channel.id,
                getattr(message.channel, 'name', 'DM'),
                message.guild.id if message.guild else 0,
                message.content[:2000],  # Limit 2000 chars
                message.author.bot,
                message.created_at
            )
        
        if ENABLE_METRICS:
            METRIC_MESSAGES_TOTAL.inc()
    
    except Exception as e:
        logger.error("message_logging_failed", error=str(e), message_id=message.id)
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx: commands.Context, error):
    """Gestion globale erreurs commandes"""
    
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore silencieusement
    
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ Permissions insuffisantes : {error.missing_permissions}")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant : `{error.param.name}`\nUtilise `{BOT_PREFIX}help {ctx.command}` pour voir la syntaxe.")
    
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argument invalide. Utilise `{BOT_PREFIX}help {ctx.command}`.")
    
    else:
        logger.error(
            "command_error",
            command=ctx.command.name if ctx.command else "unknown",
            error=str(error),
            user=ctx.author.name
        )
        await ctx.send(f"❌ Erreur : {str(error)}")

# ================================================================
# EXTENSIONS (COGS)
# ================================================================

async def load_extensions():
    """Charger tous les modules cogs"""
    extensions = [
        'cogs.commands_equipe',    # !presence, !stats, !resume
        'cogs.commands_tasks',      # !tache, !taches, !done
        'cogs.commands_planning',   # !monplanning, !planifier
        'cogs.commands_admin',      # !auditserveur, !creerchantier
        'cogs.commands_moderation', # !warn, !timeout, !ban
    ]
    
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info("extension_loaded", extension=ext)
        except Exception as e:
            logger.error("extension_load_failed", extension=ext, error=str(e))

# ================================================================
# BACKGROUND TASKS
# ================================================================

@tasks.loop(hours=1)
async def update_stats_cache():
    """Mise à jour cache stats toutes les heures"""
    try:
        async with db_pool.acquire() as conn:
            # Update user_stats
            await conn.execute('''
                INSERT INTO user_stats (user_id, user_name, total_messages, messages_7d, messages_30d, updated_at)
                SELECT 
                    user_id,
                    user_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 ELSE 0 END),
                    NOW()
                FROM messages
                GROUP BY user_id, user_name
                ON CONFLICT (user_id)
                DO UPDATE SET
                    total_messages = EXCLUDED.total_messages,
                    messages_7d = EXCLUDED.messages_7d,
                    messages_30d = EXCLUDED.messages_30d,
                    updated_at = EXCLUDED.updated_at
            ''')
        
        logger.info("stats_cache_updated")
    
    except Exception as e:
        logger.error("stats_cache_update_failed", error=str(e))

@tasks.loop(time=time(6, 0))  # Lundi 6h00
async def post_weekly_planning():
    """Post planning hebdomadaire chaque lundi"""
    
    # Vérifier si aujourd'hui est lundi
    if datetime.now().weekday() != 0:
        return
    
    if not CHANNEL_PLANNING_HEBDO:
        return
    
    try:
        channel = bot.get_channel(CHANNEL_PLANNING_HEBDO)
        if not channel:
            return
        
        # Récupérer planning semaine
        async with db_pool.acquire() as conn:
            events = await conn.fetch('''
                SELECT user_name, chantier, type, date_debut, date_fin, notes
                FROM planning
                WHERE date_debut >= CURRENT_DATE
                  AND date_debut <= CURRENT_DATE + INTERVAL '7 days'
                ORDER BY date_debut, user_name
            ''')
        
        if not events:
            await channel.send("📅 Aucun événement prévu cette semaine.")
            return
        
        # Créer embed
        embed = discord.Embed(
            title=f"📅 Planning Semaine {datetime.now().strftime('%W')}",
            description=f"Du {datetime.now().strftime('%d/%m')} au {(datetime.now() + timedelta(days=7)).strftime('%d/%m')}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Grouper par jour
        events_by_day = {}
        for event in events:
            day = event['date_debut'].strftime('%A %d/%m')
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)
        
        # Ajouter fields
        for day, day_events in events_by_day.items():
            value = "\n".join([
                f"• **{e['user_name']}** : {e['chantier']} ({e['type']})"
                for e in day_events
            ])
            embed.add_field(name=day, value=value, inline=False)
        
        await channel.send(embed=embed)
        logger.info("weekly_planning_posted", events_count=len(events))
    
    except Exception as e:
        logger.error("weekly_planning_post_failed", error=str(e))

@tasks.loop(hours=24)
async def cleanup_old_data():
    """Nettoyage données anciennes (>1 an)"""
    try:
        async with db_pool.acquire() as conn:
            # Nettoyer vieux messages
            deleted = await conn.fetchval('SELECT cleanup_old_messages(365)')
            logger.info("old_data_cleaned", messages_deleted=deleted)
    
    except Exception as e:
        logger.error("cleanup_failed", error=str(e))

# ================================================================
# COMMANDES BASIQUES
# ================================================================

@bot.command(name='ping')
async def ping(ctx: commands.Context):
    """Pong! Latence bot"""
    latency_ms = round(bot.latency * 1000, 2)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latence : **{latency_ms}ms**",
        color=discord.Color.green() if latency_ms < 200 else discord.Color.orange()
    )
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx: commands.Context, command_name: Optional[str] = None):
    """Affiche l'aide des commandes"""
    
    if command_name:
        # Aide spécifique commande
        command = bot.get_command(command_name)
        if not command:
            await ctx.send(f"❌ Commande `{command_name}` introuvable.")
            return
        
        embed = discord.Embed(
            title=f"📖 Aide : {BOT_PREFIX}{command.name}",
            description=command.help or "Pas de description disponible.",
            color=discord.Color.blue()
        )
        
        if command.usage:
            embed.add_field(
                name="Utilisation",
                value=f"`{BOT_PREFIX}{command.name} {command.usage}`",
                inline=False
            )
        
        if command.aliases:
            embed.add_field(
                name="Alias",
                value=", ".join([f"`{a}`" for a in command.aliases]),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    else:
        # Aide générale
        embed = discord.Embed(
            title=f"🤖 {BOT_NAME} - Commandes",
            description=f"Préfixe : `{BOT_PREFIX}`",
            color=discord.Color.blue()
        )
        
        categories = {
            "👥 Équipe": ["presence", "stats", "resume"],
            "📋 Tâches": ["tache", "taches", "done"],
            "📅 Planning": ["monplanning", "planifier", "modifierplanning"],
            "🔧 Admin": ["auditserveur", "creerchantier", "archiverchantier"],
            "⚙️ Utilitaires": ["ping", "help", "info"]
        }
        
        for cat_name, commands_list in categories.items():
            commands_text = ", ".join([f"`{c}`" for c in commands_list])
            embed.add_field(name=cat_name, value=commands_text, inline=False)
        
        embed.set_footer(text=f"Utilise {BOT_PREFIX}help <commande> pour plus de détails")
        
        await ctx.send(embed=embed)

@bot.command(name='info')
async def info(ctx: commands.Context):
    """Informations sur le bot"""
    
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"ℹ️ {BOT_NAME}",
        description="Bot Discord GVB-Électricité",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Version", value="2.0 Monster", inline=True)
    embed.add_field(name="Latence", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Serveurs", value=len(bot.guilds), inline=True)
    
    if guild:
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    
    # Stats DB
    try:
        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow('SELECT * FROM stats_globales')
            embed.add_field(name="Messages", value=f"{stats['total_messages']:,}", inline=True)
            embed.add_field(name="Tâches actives", value=stats['tasks_todo'], inline=True)
            embed.add_field(name="Chantiers", value=stats['chantiers_actifs'], inline=True)
    except:
        pass
    
    embed.set_footer(text=f"Créé par Marvin Ansseau")
    
    await ctx.send(embed=embed)

# ================================================================
# API REST
# ================================================================

@api_app.get("/")
async def api_root():
    """Root API endpoint"""
    return {
        "service": "GVBOT API",
        "version": "2.0",
        "status": "online",
        "endpoints": [
            "/health",
            "/stats",
            "/api/discord/*",
            "/metrics" if ENABLE_METRICS else None
        ]
    }

@api_app.get("/health")
async def api_health():
    """Healthcheck endpoint"""
    
    # Check bot
    bot_ok = bot.is_ready()
    
    # Check DB
    db_ok = False
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        db_ok = True
    except:
        pass
    
    # Check Redis
    redis_ok = False
    try:
        await redis_client.ping()
        redis_ok = True
    except:
        pass
    
    status_code = 200 if (bot_ok and db_ok and redis_ok) else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == 200 else "unhealthy",
            "bot": "ok" if bot_ok else "error",
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "latency_ms": round(bot.latency * 1000, 2) if bot_ok else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@api_app.get("/stats")
async def api_stats(authorization: str = Header(None)):
    """Stats globales serveur"""
    
    # Vérifier API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow('SELECT * FROM stats_globales')
        
        return dict(stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_app.post("/api/discord/task")
async def api_create_task(request: Request, authorization: str = Header(None)):
    """Créer une tâche via API"""
    
    # Auth
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Parse body
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    user_id = data.get('user_id')
    assignee_id = data.get('assignee_id')
    description = data.get('description')
    chantier = data.get('chantier', '')
    
    if not all([user_id, assignee_id, description]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    try:
        async with db_pool.acquire() as conn:
            task_id = await conn.fetchval('''
                INSERT INTO tasks (user_id, user_name, assignee_id, assignee_name, description, chantier)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            ''', 
                int(user_id),
                data.get('user_name', 'API'),
                int(assignee_id),
                data.get('assignee_name', 'Unknown'),
                description,
                chantier
            )
        
        return {"success": True, "task_id": task_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Prometheus metrics endpoint
if ENABLE_METRICS:
    @api_app.get("/metrics")
    async def api_metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

# ================================================================
# MAIN
# ================================================================

async def run_api():
    """Run FastAPI server"""
    config = uvicorn.Config(
        api_app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Point d'entrée principal"""
    
    # Vérifier variables
    if not all([DISCORD_TOKEN, DB_PASS, REDIS_PASS, API_KEY]):
        logger.error("missing_env_vars", message="DISCORD_TOKEN, DB_PASS, REDIS_PASS, API_KEY requis")
        sys.exit(1)
    
    # Start API server
    api_task = asyncio.create_task(run_api())
    
    # Start bot
    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    finally:
        await close_db()
        await close_redis()
        api_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("bot_stopped", reason="KeyboardInterrupt")
    except Exception as e:
        logger.error("bot_crash", error=str(e))
        sys.exit(1)
