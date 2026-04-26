#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
import discord
from discord import app_commands
from discord.ext import commands
import ollama
import json
from datetime import datetime
import os
import time
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, level: str = "INFO"):
    """Print colored logs with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": Colors.OKBLUE,
        "SUCCESS": Colors.OKGREEN,
        "WARNING": Colors.WARNING,
        "ERROR": Colors.FAIL,
        "AI": Colors.OKCYAN,
        "TOOL": Colors.HEADER
    }
    color = colors.get(level, Colors.ENDC)
    print(f"{color}[{timestamp}] [{level}]{Colors.ENDC} {message}")

# ─────────────────────────────────────────────────────────────
# BOT INITIALIZATION
# ─────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─────────────────────────────────────────────────────────────
# DISCORD TOOL WRAPPER
# ─────────────────────────────────────────────────────────────

class DiscordTools:
    """Atomic Discord actions used by the AI agent."""

    def __init__(self, guild: discord.Guild, interaction: discord.Interaction):
        self.guild = guild
        self.interaction = interaction
        self.execution_log = []
        log(f"🔧 Tools initialized for guild: {guild.name}", "INFO")
        
    async def create_category(self, name: str) -> Dict:
        log(f"📁 Creating category: {name}", "TOOL")
        try:
            category = await self.guild.create_category(
                name=name, reason=f"Created by AI agent ({self.interaction.user})"
            )
            await asyncio.sleep(0.3)  # ← CRITICAL: Prevent heartbeat blocking
            
            result = {
                "success": True,
                "action": "create_category",
                "category_name": name,
                "category_id": category.id,
            }
            self.execution_log.append(result)
            log(f"✅ Category created: {name} (ID: {category.id})", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to create category {name}: {e}", "ERROR")
            return {"success": False, "action": "create_category", "error": str(e)}

    async def create_text_channel(self, name: str, category_name: str = None) -> Dict:
        log(f"📝 Creating text channel: {name} (Category: {category_name or 'None'})", "TOOL")
        try:
            category = (
                discord.utils.get(self.guild.categories, name=category_name)
                if category_name
                else None
            )
            channel = await self.guild.create_text_channel(
                name=name,
                category=category,
                reason=f"Created by AI agent ({self.interaction.user})",
            )
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "create_text_channel",
                "channel_name": name,
                "channel_id": channel.id,
            }
            self.execution_log.append(result)
            log(f"✅ Text channel created: #{name} (ID: {channel.id})", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to create text channel {name}: {e}", "ERROR")
            return {"success": False, "action": "create_text_channel", "error": str(e)}
    
    async def send_message_by_id(
        self, channel_id: int, content: str, embed_title: str = None) -> Dict:
        log(f"💬 Sending message to channel ID: {channel_id}", "TOOL")
        try:
            channel = self.guild.get_channel(int(channel_id))
            if not channel:
                log(f"❌ Channel ID not found: {channel_id}", "ERROR")
                return {
                    "success": False,
                    "action": "send_message_by_id",
                    "error": f"Channel ID {channel_id} not found",
                }
            if embed_title:
                embed = discord.Embed(title=embed_title, description=content, color=0x3498db)
                await channel.send(embed=embed)
                log(f"✅ Embed message sent to #{channel.name} (ID: {channel_id})", "SUCCESS")
            else:
                await channel.send(content)
                log(f"✅ Message sent to #{channel.name} (ID: {channel_id})", "SUCCESS")
            
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {"success": True, "action": "send_message_by_id", "channel_id": channel_id, "channel_name": channel.name}
            self.execution_log.append(result)
            return result
        except Exception as e:
            log(f"❌ Failed to send message to channel ID {channel_id}: {e}", "ERROR")
            return {"success": False, "action": "send_message_by_id", "error": str(e)}
    
    async def create_voice_channel(self, name: str, category_name: str = None) -> Dict:
        log(f"🔊 Creating voice channel: {name} (Category: {category_name or 'None'})", "TOOL")
        try:
            category = (
                discord.utils.get(self.guild.categories, name=category_name)
                if category_name
                else None
            )
            channel = await self.guild.create_voice_channel(
                name=name,
                category=category,
                reason=f"Created by AI agent ({self.interaction.user})",
            )
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "create_voice_channel",
                "channel_name": name,
                "channel_id": channel.id,
            }
            self.execution_log.append(result)
            log(f"✅ Voice channel created: {name} (ID: {channel.id})", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to create voice channel {name}: {e}", "ERROR")
            return {"success": False, "action": "create_voice_channel", "error": str(e)}
    
    async def delete_text_channel(self, channel_name: str = None, channel_id: str = None) -> Dict:
        """Delete a text channel by name or ID"""
        log(f"🗑️ Deleting channel: {channel_name or f'ID:{channel_id}'}", "TOOL")
        try:
            if channel_id:
                channel = self.guild.get_channel(int(channel_id))
            elif channel_name:
                channel = discord.utils.get(self.guild.text_channels, name=channel_name)
            else:
                log(f"❌ No channel name or ID provided", "ERROR")
                return {"success": False, "action": "delete_text_channel", "error": "No channel identifier provided"}
            
            if not channel:
                log(f"❌ Channel not found: {channel_name or channel_id}", "ERROR")
                return {
                    "success": False,
                    "action": "delete_text_channel",
                    "error": f"Channel {channel_name or channel_id} not found"
                }
            channel_info = f"#{channel.name} (ID: {channel.id})"
            await channel.delete(reason=f"Deleted by AI agent ({self.interaction.user})")
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "delete_text_channel",
                "channel_name": channel.name,
                "channel_id": str(channel.id)
            }
            self.execution_log.append(result)
            log(f"✅ Channel deleted: {channel_info}", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to delete channel: {e}", "ERROR")
            return {"success": False, "action": "delete_text_channel", "error": str(e)}
    
    async def delete_voice_channel(self, channel_name: str = None, channel_id: str = None) -> Dict:
        """Delete a voice channel by name or ID"""
        log(f"🗑️ Deleting voice channel: {channel_name or f'ID:{channel_id}'}", "TOOL")
        try:
            if channel_id:
                channel = self.guild.get_channel(int(channel_id))
            elif channel_name:
                channel = discord.utils.get(self.guild.voice_channels, name=channel_name)
            else:
                return {"success": False, "action": "delete_voice_channel", "error": "No channel identifier provided"}
            
            if not channel:
                log(f"❌ Voice channel not found: {channel_name or channel_id}", "ERROR")
                return {
                    "success": False,
                    "action": "delete_voice_channel",
                    "error": f"Channel {channel_name or channel_id} not found"
                }
            channel_info = f"{channel.name} (ID: {channel.id})"
            await channel.delete(reason=f"Deleted by AI agent ({self.interaction.user})")
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "delete_voice_channel",
                "channel_name": channel.name,
                "channel_id": str(channel.id)
            }
            self.execution_log.append(result)
            log(f"✅ Voice channel deleted: {channel_info}", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to delete voice channel: {e}", "ERROR")
            return {"success": False, "action": "delete_voice_channel", "error": str(e)}

    async def delete_category(self, category_name: str) -> Dict:
        """Delete a category and all channels inside it"""
        log(f"🗑️ Deleting category: {category_name}", "TOOL")
        try:
            category = discord.utils.get(self.guild.categories, name=category_name)
            if not category:
                log(f"❌ Category not found: {category_name}", "ERROR")
                return {
                    "success": False,
                    "action": "delete_category",
                    "error": f"Category {category_name} not found"
                }
            
            # Delete all channels in the category first
            for channel in category.channels:
                await channel.delete(reason=f"Category deletion by AI agent ({self.interaction.user})")
                await asyncio.sleep(0.3)  # ← CRITICAL
                log(f"  └─ Deleted channel: {channel.name}", "INFO")
            
            # Then delete the category
            await category.delete(reason=f"Deleted by AI agent ({self.interaction.user})")
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "delete_category",
                "category_name": category_name
            }
            self.execution_log.append(result)
            log(f"✅ Category deleted: {category_name}", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to delete category: {e}", "ERROR")
            return {"success": False, "action": "delete_category", "error": str(e)}

    async def delete_all_channels(self) -> Dict:
        """Delete ALL channels (batched to prevent heartbeat blocking)"""
        log(f"🗑️ DELETING ALL CHANNELS (batched)", "WARNING")
        try:
            deleted_count = 0
            command_channel_id = self.interaction.channel.id
            
            # Collect all channels to delete
            channels_to_delete = []
            for channel in self.guild.text_channels:
                if channel.id != command_channel_id:
                    channels_to_delete.append(channel)
            channels_to_delete.extend(self.guild.voice_channels)
            channels_to_delete.extend(self.guild.categories)
            
            # Delete in batches of 5 with delays
            batch_size = 5
            for i in range(0, len(channels_to_delete), batch_size):
                batch = channels_to_delete[i:i + batch_size]
                
                for channel in batch:
                    try:
                        await channel.delete(reason=f"Bulk deletion by AI agent ({self.interaction.user})")
                        await asyncio.sleep(0.3)  # ← CRITICAL
                        deleted_count = deleted_count + 1
                        log(f"  └─ Deleted: {channel.name}", "INFO")
                    except Exception as e:
                        log(f"  └─ Failed: {channel.name} - {e}", "WARNING")
                
                # Pause between batches
                if i + batch_size < len(channels_to_delete):
                    log(f"  ⏸️  Batch complete, pausing for heartbeat...", "INFO")
                    await asyncio.sleep(1)
            
            result = {
                "success": True,
                "action": "delete_all_channels",
                "deleted_count": deleted_count
            }
            self.execution_log.append(result)
            log(f"✅ Deleted {deleted_count} channels/categories total", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to delete all channels: {e}", "ERROR")
            return {"success": False, "action": "delete_all_channels", "error": str(e)}

    async def create_role(
        self, name: str, color: str = "default", permissions: str = "none"
    ) -> Dict:
        log(f"👥 Creating role: {name} (Permissions: {permissions}, Color: {color})", "TOOL")
        try:
            color_int = 0x99aab5 if color == "default" else int(color.replace("#", ""), 16)
            if permissions == "admin":
                perms = discord.Permissions(administrator=True)
            elif permissions == "moderator":
                perms = discord.Permissions(
                    manage_messages=True, kick_members=True, mute_members=True
                )
            else:
                perms = discord.Permissions.none()
            role = await self.guild.create_role(
                name=name,
                color=discord.Color(color_int),
                permissions=perms,
                reason=f"Created by AI agent ({self.interaction.user})",
            )
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "create_role",
                "role_name": name,
                "role_id": role.id,
            }
            self.execution_log.append(result)
            log(f"✅ Role created: @{name} (ID: {role.id})", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to create role {name}: {e}", "ERROR")
            return {"success": False, "action": "create_role", "error": str(e)}

    async def send_message(
        self, channel_name: str, content: str, embed_title: str = None
    ) -> Dict:
        log(f"💬 Sending message to: #{channel_name}", "TOOL")
        try:
            channel = discord.utils.get(self.guild.text_channels, name=channel_name)
            if not channel:
                log(f"❌ Channel not found: #{channel_name}", "ERROR")
                return {
                    "success": False,
                    "action": "send_message",
                    "error": f"Channel {channel_name} not found",
                }

            if embed_title:
                embed = discord.Embed(title=embed_title, description=content, color=0x3498db)
                await channel.send(embed=embed)
                log(f"✅ Embed message sent to #{channel_name}", "SUCCESS")
            else:
                await channel.send(content)
                log(f"✅ Message sent to #{channel_name}", "SUCCESS")

            await asyncio.sleep(0.3)  # ← CRITICAL

            result = {"success": True, "action": "send_message", "channel_name": channel_name}
            self.execution_log.append(result)
            return result
        except Exception as e:
            log(f"❌ Failed to send message to #{channel_name}: {e}", "ERROR")
            return {"success": False, "action": "send_message", "error": str(e)}

    async def set_channel_permissions(
        self, channel_name: str, role_or_everyone: str, can_send: bool = True, can_read: bool = True
    ) -> Dict:
        log(f"🔒 Setting permissions for #{channel_name} (Target: {role_or_everyone}, Send: {can_send}, Read: {can_read})", "TOOL")
        try:
            channel = discord.utils.get(self.guild.text_channels, name=channel_name)
            if not channel:
                log(f"❌ Channel not found: #{channel_name}", "ERROR")
                return {
                    "success": False,
                    "action": "set_permissions",
                    "error": f"Channel {channel_name} not found",
                }

            target = (
                self.guild.default_role
                if role_or_everyone.lower() == "everyone"
                else discord.utils.get(self.guild.roles, name=role_or_everyone)
            )
            if not target:
                log(f"❌ Role not found: {role_or_everyone}", "ERROR")
                return {
                    "success": False,
                    "action": "set_permissions",
                    "error": f"Role {role_or_everyone} not found",
                }

            await channel.set_permissions(target, send_messages=can_send, read_messages=can_read)
            await asyncio.sleep(0.3)  # ← CRITICAL
            
            result = {
                "success": True,
                "action": "set_channel_permissions",
                "channel_name": channel_name,
                "target": role_or_everyone,
            }
            self.execution_log.append(result)
            log(f"✅ Permissions set: #{channel_name} → {role_or_everyone}", "SUCCESS")
            return result
        except Exception as e:
            log(f"❌ Failed to set permissions for #{channel_name}: {e}", "ERROR")
            return {"success": False, "action": "set_permissions", "error": str(e)}

# ─────────────────────────────────────────────────────────────
# AI AGENT
# ─────────────────────────────────────────────────────────────

class DiscordAIAgent:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model

    def get_available_tools(self) -> List[Dict]:
        """Complete tool definitions for Ollama"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_category",
                    "description": "Create a category to organize channels",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Category name (e.g., 'General', 'Gaming')"
                            }
                        },
                        "required": ["name"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_text_channel",
                    "description": "Delete a text channel by name or ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_name": {
                                "type": "string",
                                "description": "Name of the channel to delete"
                            },
                            "channel_id": {
                                "type": "string",
                                "description": "ID of the channel to delete (takes priority over name)"
                            }
                        }
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_voice_channel",
                    "description": "Delete a voice channel by name or ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_name": {
                                "type": "string",
                                "description": "Name of the voice channel to delete"
                            },
                            "channel_id": {
                                "type": "string",
                                "description": "ID of the channel to delete"
                            }
                        }
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_category",
                    "description": "Delete a category and all channels inside it",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category_name": {
                                "type": "string",
                                "description": "Name of the category to delete"
                            }
                        },
                        "required": ["category_name"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_all_channels",
                    "description": "DELETE ALL CHANNELS in the server (except the command channel). Use only when explicitly requested.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_text_channel",
                    "description": "Create a text channel, optionally in a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Channel name (e.g., 'general-chat')"
                            },
                            "category_name": {
                                "type": "string",
                                "description": "Optional: category to place this channel in"
                            }
                        },
                        "required": ["name"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_voice_channel",
                    "description": "Create a voice channel, optionally in a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Voice channel name (e.g., 'Voice Chat')"
                            },
                            "category_name": {
                                "type": "string",
                                "description": "Optional: category to place this channel in"
                            }
                        },
                        "required": ["name"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_role",
                    "description": "Create a role with specified permissions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Role name (e.g., 'Admin', 'Moderator')"
                            },
                            "color": {
                                "type": "string",
                                "description": "Hex color without # (e.g., 'ff0000' for red) or 'default'"
                            },
                            "permissions": {
                                "type": "string",
                                "enum": ["none", "member", "moderator", "admin"],
                                "description": "Permission level"
                            }
                        },
                        "required": ["name"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_message",
                    "description": "Send a message to a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_name": {
                                "type": "string",
                                "description": "Target channel name"
                            },
                            "content": {
                                "type": "string",
                                "description": "Message content"
                            },
                            "embed_title": {
                                "type": "string",
                                "description": "Optional: title for embed (for rules, announcements)"
                            }
                        },
                        "required": ["channel_name", "content"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_channel_permissions",
                    "description": "Set permissions for a role in a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_name": {
                                "type": "string",
                                "description": "Target channel name"
                            },
                            "role_or_everyone": {
                                "type": "string",
                                "description": "Role name or 'everyone' for @everyone"
                            },
                            "can_send": {
                                "type": "boolean",
                                "description": "Can send messages"
                            },
                            "can_read": {
                                "type": "boolean",
                                "description": "Can read messages"
                            }
                        },
                        "required": ["channel_name", "role_or_everyone"]
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_message_by_id",
                    "description": "Send a message to a channel using its Discord ID (from mentions like <#123456>)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The numeric channel ID (extract from <#ID> format)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Message content"
                            },
                            "embed_title": {
                                "type": "string",
                                "description": "Optional: title for embed",
                            }
                        },
                        "required": ["channel_id", "content"]
                    },
                },
            },
        ]

    async def plan_and_execute(self, prompt: str, tools: DiscordTools, status_callback=None) -> Dict:
        log(f"🤖 AI Agent started with model: {self.model}", "AI")
        log(f"📝 User prompt: \"{prompt}\"", "AI")
        
        system_message = """You are a Discord server setup assistant.

Your job: Understand user requests and call the appropriate functions to set up their server.

RULES:
1. Always create categories BEFORE channels in those categories
2. Create roles BEFORE setting permissions that reference them
3. For rules channels: create channel → set read-only → send rules message
4. Be thorough - if user wants a "gaming server", include voice + text channels organized in categories

IMPORTANT - Discord Mentions:
- Channel mentions look like <#1234567890> - extract the numeric ID
- To send to existing channels, use send_message_by_id with just the numbers
- Example: <#1431882600804384810> → use channel_id="1431882600804384810"

Think step-by-step."""

        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]
        iteration = 0
        
        try:
            while iteration < 15:
                iteration = iteration + 1
                log(f"🔄 AI Iteration {iteration}/15", "AI")
                
                if status_callback:
                    await status_callback(f"AI thinking... iteration {iteration}")
                
                log(f"⏳ Calling Ollama API...", "AI")
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    tools=self.get_available_tools(),
                )
                
                msg = response.get("message", {})
                messages.append(msg)
                
                # Log AI's thinking
                if msg.get("content"):
                    content_preview = msg.get('content')[:150]
                    log(f"💭 AI thinking: {content_preview}...", "AI")
                
                tool_calls = msg.get("tool_calls", [])
                
                if not tool_calls:
                    log(f"✅ AI finished planning (no more tool calls needed)", "AI")
                    break
                
                log(f"🔧 AI requested {len(tool_calls)} tool call(s)", "AI")
                
                for idx, tool_call in enumerate(tool_calls, 1):
                    func_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]
                    
                    log(f"🛠️  Tool call {idx}/{len(tool_calls)}: {func_name}({args})", "TOOL")
                    
                    if status_callback:
                        await status_callback(f"Executing: {func_name}({args})")
                    
                    if hasattr(tools, func_name):
                        result = await getattr(tools, func_name)(**args)
                        messages.append({"role": "tool", "content": json.dumps(result)})
                        log(f"📊 Tool result: {result.get('success', False)} - {result.get('action', 'unknown')}", "INFO")
                    else:
                        log(f"❌ Function not found: {func_name}", "ERROR")
                        messages.append({
                            "role": "tool",
                            "content": json.dumps({"success": False, "error": f"Function {func_name} not found"})
                        })
                
                await asyncio.sleep(0.2)  # Small delay between AI iterations
            
            log(f"🎉 AI Agent completed successfully in {iteration} iteration(s)", "SUCCESS")
            log(f"📊 Total actions executed: {len(tools.execution_log)}", "INFO")
            
            return {
                "success": True,
                "iterations": iteration,
                "execution_log": tools.execution_log,
                "final_message": msg.get("content", "")
            }
        except Exception as e:
            log(f"💥 AI Agent failed with error: {e}", "ERROR")
            return {"success": False, "error": str(e), "execution_log": tools.execution_log}

# ─────────────────────────────────────────────────────────────
# DISCORD BOT COMMANDS
# ─────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log(f"🤖 Bot logged in as {bot.user} (ID: {bot.user.id})", "SUCCESS")
    log(f"🌐 Connected to {len(bot.guilds)} guild(s)", "INFO")
    for guild in bot.guilds:
        log(f"  └─ {guild.name} (ID: {guild.id}, Members: {guild.member_count})", "INFO")
    
    try:
        log(f"🔄 Syncing slash commands...", "INFO")
        synced = await bot.tree.sync()
        log(f"✅ Successfully synced {len(synced)} slash command(s)", "SUCCESS")
    except Exception as e:
        log(f"❌ Failed to sync commands: {e}", "ERROR")

@bot.tree.command(name="ai_setup", description="Use AI to create your Discord server structure")
@app_commands.describe(
    prompt="Describe your desired server (e.g., 'gaming server with voice channels')",
    model="Ollama model (default: qwen2.5:7b)"
)
async def ai_setup(interaction: discord.Interaction, prompt: str, model: str = "qwen2.5:7b"):
    log(f"📥 /ai_setup command received", "INFO")
    log(f"  └─ User: {interaction.user} (ID: {interaction.user.id})", "INFO")
    log(f"  └─ Guild: {interaction.guild.name} (ID: {interaction.guild.id})", "INFO")
    log(f"  └─ Prompt: \"{prompt}\"", "INFO")
    log(f"  └─ Model: {model}", "INFO")
    
    if not interaction.user.guild_permissions.administrator:
        log(f"❌ Permission denied - user lacks administrator permission", "WARNING")
        await interaction.response.send_message("❌ Admin permissions required.", ephemeral=True)
        return

    log(f"✅ Permission check passed", "SUCCESS")
    await interaction.response.defer(ephemeral=True)
    log(f"⏳ Interaction deferred, starting AI agent execution...", "INFO")
    
    # Start keepalive
    keepalive = KeepAlive()
    keepalive.start()
    
    try:
        tools = DiscordTools(interaction.guild, interaction)
        agent = DiscordAIAgent(model)
        status_msgs = []

        async def update_status(msg: str):
            status_msgs.append(f"• {msg}")
            if len(status_msgs) % 3 == 0:
                embed = discord.Embed(
                    title="🤖 AI Agent Working...",
                    description="\n".join(status_msgs[-6:]),
                    color=0xf39c12,
                )
                try:
                    await interaction.edit_original_response(embed=embed)
                except:
                    pass

        await update_status(f'Analyzing: "{prompt}"')
        result = await agent.plan_and_execute(prompt, tools, status_callback=update_status)

        log(f"📤 Building final response embed...", "INFO")
        
        if result["success"]:
            log(f"✅ Setup completed successfully", "SUCCESS")
            embed = discord.Embed(
                title="✅ Server Setup Complete!",
                description=f"Executed in {result['iterations']} AI iteration(s)",
                color=0x2ecc71,
            )
            embed.add_field(name="📝 Your Prompt", value=f"{prompt}", inline=False)
            
            # Summarize actions
            actions_summary = {}
            for log_entry in result["execution_log"]:
                action = log_entry["action"]
                actions_summary[action] = actions_summary.get(action, 0) + 1
            
            if actions_summary:
                summary_text = "\n".join([
                    f"• {action.replace('_', ' ').title()}: {count}"
                    for action, count in actions_summary.items()
                ])
                embed.add_field(name="📊 Actions Executed", value=summary_text, inline=False)
            
            if result.get("final_message"):
                embed.add_field(name="💬 AI Summary", value=result["final_message"][:1024], inline=False)
            
            embed.set_footer(text=f"Powered by {model} • Requested by {interaction.user.name}")
        else:
            log(f"❌ Setup failed: {result.get('error', 'Unknown error')}", "ERROR")
            embed = discord.Embed(
                title="❌ Setup Failed",
                description=result.get("error", "Unknown error"),
                color=0xe74c3c,
            )
            if result.get("execution_log"):
                log(f"⚠️ Partial execution: {len(result['execution_log'])} action(s) completed", "WARNING")
                embed.add_field(
                    name="⚠️ Partial Execution",
                    value=f"{len(result['execution_log'])} action(s) completed before error",
                    inline=False
                )
        
        await interaction.edit_original_response(embed=embed)
        log(f"✅ Response sent to Discord", "SUCCESS")
    
    finally:
        # Always stop keepalive, even if error occurs
        keepalive.stop()


@bot.tree.command(name="ai_models", description="List available Ollama models")
async def ai_models(interaction: discord.Interaction):
    log(f"📥 /ai_models command received from {interaction.user}", "INFO")
    
    try:
        log(f"🔍 Fetching models from Ollama...", "INFO")
        models = ollama.list()
        model_count = len(models.get("models", []))
        log(f"✅ Found {model_count} model(s)", "SUCCESS")
        
        embed = discord.Embed(title="🤖 Available AI Models", description="Models on your Ollama server", color=0x3498db)
        for model in models.get("models", [])[:10]:
            embed.add_field(
                name=f"• {model['name']}",
                value=f"Size: {model.get('size', 0)/1e9:.1f} GB",
                inline=True
            )
        embed.set_footer(text="Use these with /ai_setup model: parameter")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        log(f"✅ Model list sent to user", "SUCCESS")
    except Exception as e:
        log(f"❌ Failed to fetch models: {e}", "ERROR")
        await interaction.response.send_message(f"❌ Error connecting to Ollama: {e}\nMake sure Ollama is running!", ephemeral=True)

# ─────────────────────────────────────────────────────────────
# KEEPALIVE HELPER
# ─────────────────────────────────────────────────────────────

class KeepAlive:
    """Lightweight background task to keep Discord connection alive during long operations"""
    
    def __init__(self):
        self.running = False
        self.task = None
        self.ping_count = 0
    
    async def heartbeat(self):
        """Send periodic keepalive signals"""
        self.ping_count = 0
        while self.running:
            await asyncio.sleep(10)  # Every 10 seconds
            self.ping_count = ping_count + 1
            log(f"💓 Keepalive heartbeat #{self.ping_count}", "INFO")
    
    def start(self):
        """Start the keepalive task"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self.heartbeat())
            log(f"💚 Keepalive started", "SUCCESS")
    
    def stop(self):
        """Stop the keepalive task"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
            log(f"🛑 Keepalive stopped (sent {self.ping_count} heartbeats)", "INFO")
# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TOKEN = "MTQzMDkxMTE3MzAyMDA5NDYwNA.GWfjs1.hJWlhwkl2TgvsqKPPCe7AQM4SA1LO2dlKIwoXE"
    
    if not TOKEN:
        log("❌ DISCORD_BOT_TOKEN not found!", "ERROR")
        print("Create a .env file with: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    log("🚀 Starting bot...", "INFO")
    
    try:
        log("🔍 Checking Ollama connection...", "INFO")
        ollama.list()
        log("✅ Ollama connection verified", "SUCCESS")
    except Exception as e:
        log(f"⚠️ Ollama not reachable: {e}", "WARNING")
        log("Make sure Ollama is running: ollama serve", "WARNING")
    
    log("🔌 Connecting to Discord...", "INFO")
    bot.run(TOKEN)
