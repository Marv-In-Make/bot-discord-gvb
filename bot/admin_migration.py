#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================
ADMIN MIGRATION - Module administration serveur Discord
================================================================
"""

import discord
from discord.ext import commands
from datetime import datetime
import json
from typing import Optional

class AdminMigration(commands.Cog):
    """Module d'administration serveur Discord"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='auditserveur')
    @commands.has_permissions(administrator=True)
    async def audit_server(self, ctx: commands.Context):
        """Audite la structure complète du serveur"""
        
        await ctx.send("🔍 Audit en cours...")
        
        guild = ctx.guild
        
        audit_data = {
            'guild_name': guild.name,
            'guild_id': guild.id,
            'audit_date': datetime.utcnow().isoformat(),
            'member_count': guild.member_count,
            'categories': [],
            'channels': [],
            'roles': []
        }
        
        # Catégories et channels
        for category in guild.categories:
            cat_data = {
                'name': category.name,
                'id': category.id,
                'position': category.position,
                'channels': []
            }
            
            for channel in category.channels:
                cat_data['channels'].append({
                    'name': channel.name,
                    'id': channel.id,
                    'type': str(channel.type),
                    'position': channel.position
                })
            
            audit_data['categories'].append(cat_data)
        
        # Channels sans catégorie
        for channel in guild.channels:
            if channel.category is None:
                audit_data['channels'].append({
                    'name': channel.name,
                    'id': channel.id,
                    'type': str(channel.type)
                })
        
        # Rôles
        for role in guild.roles:
            if role.name != "@everyone":
                audit_data['roles'].append({
                    'name': role.name,
                    'id': role.id,
                    'color': str(role.color),
                    'permissions': role.permissions.value,
                    'members_count': len(role.members)
                })
        
        # Créer fichier JSON
        filename = f"audit_serveur_{guild.id}_{datetime.now().strftime('%Y%m%d')}.json"
        json_str = json.dumps(audit_data, indent=2, ensure_ascii=False)
        
        # Embed résumé
        embed = discord.Embed(
            title="📋 Audit Serveur",
            description=f"**{guild.name}**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Catégories", value=len(audit_data['categories']), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Rôles", value=len(audit_data['roles']), inline=True)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        
        await ctx.send(embed=embed)
        
        # Envoyer fichier
        with open(f'/tmp/{filename}', 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        await ctx.send(file=discord.File(f'/tmp/{filename}', filename=filename))
    
    @commands.command(name='creerchantier')
    @commands.has_permissions(manage_channels=True)
    async def create_chantier(self, ctx: commands.Context, nom: str):
        """Créer un channel chantier dans la catégorie CHANTIERS ACTIFS"""
        
        guild = ctx.guild
        
        # Chercher catégorie "CHANTIERS ACTIFS"
        category = discord.utils.get(guild.categories, name="CHANTIERS ACTIFS")
        
        if not category:
            await ctx.send("❌ Catégorie 'CHANTIERS ACTIFS' introuvable.")
            return
        
        # Vérifier si channel existe déjà
        existing = discord.utils.get(category.channels, name=nom.lower())
        if existing:
            await ctx.send(f"❌ Le channel #{nom.lower()} existe déjà.")
            return
        
        # Créer channel
        try:
            channel = await guild.create_text_channel(
                name=nom.lower(),
                category=category,
                topic=f"Chantier {nom.capitalize()}"
            )
            
            embed = discord.Embed(
                title="✅ Chantier créé",
                description=f"Channel {channel.mention} créé avec succès.",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
            # Log dans PostgreSQL (si disponible)
            try:
                async with self.bot.db_pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO chantiers (nom, channel_id, status, created_at)
                        VALUES ($1, $2, 'actif', NOW())
                    ''', nom.lower(), channel.id)
            except:
                pass
        
        except Exception as e:
            await ctx.send(f"❌ Erreur création channel : {str(e)}")
    
    @commands.command(name='archiverchantier')
    @commands.has_permissions(administrator=True)
    async def archive_chantier(self, ctx: commands.Context, nom: str):
        """Archiver un channel chantier"""
        
        guild = ctx.guild
        
        # Chercher channel
        category_actifs = discord.utils.get(guild.categories, name="CHANTIERS ACTIFS")
        channel = discord.utils.get(category_actifs.channels, name=nom.lower()) if category_actifs else None
        
        if not channel:
            await ctx.send(f"❌ Channel #{nom.lower()} introuvable dans CHANTIERS ACTIFS.")
            return
        
        # Chercher catégorie archives
        category_archives = discord.utils.get(guild.categories, name="CHANTIERS ARCHIVÉS")
        if not category_archives:
            await ctx.send("❌ Catégorie 'CHANTIERS ARCHIVÉS' introuvable.")
            return
        
        try:
            year = datetime.now().year
            new_name = f"{year}-{nom.lower()}"
            
            # Renommer et déplacer
            await channel.edit(
                name=new_name,
                category=category_archives,
                sync_permissions=True
            )
            
            # Permissions lecture seule (optionnel)
            # await channel.set_permissions(guild.default_role, send_messages=False)
            
            embed = discord.Embed(
                title="📦 Chantier archivé",
                description=f"Channel renommé en **#{new_name}** et déplacé vers archives.",
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
            
            # Update DB
            try:
                async with self.bot.db_pool.acquire() as conn:
                    await conn.execute('''
                        UPDATE chantiers 
                        SET status = 'archivé', archived_at = NOW()
                        WHERE channel_id = $1
                    ''', channel.id)
            except:
                pass
        
        except Exception as e:
            await ctx.send(f"❌ Erreur archivage : {str(e)}")

async def setup(bot):
    """Setup hook pour charger le Cog"""
    await bot.add_cog(AdminMigration(bot))
