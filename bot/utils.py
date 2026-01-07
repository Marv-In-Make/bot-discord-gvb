#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================
UTILS - Fonctions utilitaires Discord Bot Monster
================================================================
"""

import discord
from datetime import datetime, timedelta
from typing import Optional, List
import humanize

# ================================================================
# EMBEDS HELPERS
# ================================================================

def create_embed(
    title: str,
    description: str = "",
    color: discord.Color = discord.Color.blue(),
    fields: Optional[List[dict]] = None,
    footer: Optional[str] = None,
    timestamp: bool = True
) -> discord.Embed:
    """Créer embed Discord formaté"""
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow() if timestamp else None
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', 'Field'),
                value=field.get('value', 'Value'),
                inline=field.get('inline', False)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed

def success_embed(message: str, **kwargs) -> discord.Embed:
    """Embed succès vert"""
    return create_embed(
        title="✅ Succès",
        description=message,
        color=discord.Color.green(),
        **kwargs
    )

def error_embed(message: str, **kwargs) -> discord.Embed:
    """Embed erreur rouge"""
    return create_embed(
        title="❌ Erreur",
        description=message,
        color=discord.Color.red(),
        **kwargs
    )

def warning_embed(message: str, **kwargs) -> discord.Embed:
    """Embed warning orange"""
    return create_embed(
        title="⚠️ Attention",
        description=message,
        color=discord.Color.orange(),
        **kwargs
    )

# ================================================================
# FORMATAGE
# ================================================================

def format_datetime(dt: datetime, relative: bool = False) -> str:
    """Formater datetime en français"""
    if relative:
        return humanize.naturaltime(dt, when=datetime.utcnow())
    return dt.strftime('%d/%m/%Y %H:%M')

def format_duration(seconds: int) -> str:
    """Formater durée en heures/minutes"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}min"
    elif minutes > 0:
        return f"{int(minutes)}min {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def format_number(num: int) -> str:
    """Formater nombre avec séparateurs"""
    return f"{num:,}".replace(',', ' ')

# ================================================================
# PERMISSIONS
# ================================================================

def has_role(member: discord.Member, role_names: List[str]) -> bool:
    """Vérifier si membre a un des rôles"""
    member_roles = [role.name for role in member.roles]
    return any(role in member_roles for role in role_names)

def is_manager(member: discord.Member) -> bool:
    """Vérifier si membre est Manager ou Admin"""
    return has_role(member, ['Manager', 'Admin', 'Administrateur'])

def is_admin(member: discord.Member) -> bool:
    """Vérifier si membre est Admin"""
    return has_role(member, ['Admin', 'Administrateur'])

# ================================================================
# PARSING
# ================================================================

def parse_date(date_str: str) -> Optional[datetime]:
    """Parser date format JJ/MM ou JJ/MM/YYYY"""
    try:
        parts = date_str.split('/')
        if len(parts) == 2:  # JJ/MM
            day, month = int(parts[0]), int(parts[1])
            year = datetime.now().year
            return datetime(year, month, day)
        elif len(parts) == 3:  # JJ/MM/YYYY
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime(year, month, day)
    except:
        pass
    return None

def parse_user_mention(mention: str) -> Optional[int]:
    """Extraire user ID d'une mention Discord"""
    if mention.startswith('<@') and mention.endswith('>'):
        user_id = mention[2:-1]
        if user_id.startswith('!'):
            user_id = user_id[1:]
        try:
            return int(user_id)
        except:
            pass
    return None

# ================================================================
# PAGINATION
# ================================================================

async def paginate_embeds(
    ctx,
    embeds: List[discord.Embed],
    timeout: int = 60
):
    """Paginer une liste d'embeds avec boutons"""
    if not embeds:
        await ctx.send("Aucune donnée à afficher.")
        return
    
    if len(embeds) == 1:
        await ctx.send(embed=embeds[0])
        return
    
    # Ajouter numéro de page
    for i, embed in enumerate(embeds, 1):
        embed.set_footer(text=f"Page {i}/{len(embeds)}")
    
    # Envoyer première page
    message = await ctx.send(embed=embeds[0])
    
    # TODO: Ajouter boutons pagination
    # Nécessite discord.ui.View (voir doc discord.py)
