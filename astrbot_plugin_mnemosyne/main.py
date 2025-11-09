"""
Mnemosyne - AstrBot 长期记忆插件
基于 RAG (检索增强生成) 技术和 Milvus 向量数据库实现
为 AI 赋予持久记忆能力，构建个性化对话体验
"""

import os
import json
import time
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

# 导入 AstrBot 插件框架
from astrbot import plugin, event, api
from astrbot.utils import logger

# 导入 Milvus 客户端
from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema

class MnemosynePlugin(plugin.Plugin):
    """Mnemosyne 长期记忆插件"""
    
    def __init__(self):
        super().__init__()
        self.name = "Mnemosyne"
        self.version = "1.0.0"
        self.description = "AstrBot 长期记忆插件"
        
        # 配置项
        self.config = {
            "num_pairs": 5,  # 触发总结的对话轮数阈值
            "top_k": 3,      # 检索返回的记忆数量
            "collection_name": "mnemosyne_memories",  # Milvus 集合名称
            "memory_injection_method": "user_prompt",  # 记忆注入方式
            "use_personality_filtering": True,  # 是否启用人格过滤
            "milvus_lite_path": "./data/milvus.db",  # Milvus Lite 路径
            "embedding_dimension": 768,  # 嵌入向量维度
            "api_key": None  # 管理 API 密钥
        }
        
        # Milvus 客户端
        self.milvus_client = None
        
        # 会话对话缓冲区
        self.conversation_buffer = {}
        
    async def on_load(self):
        """插件加载时执行"""
        await super().on_load()
        logger.info(f"正在加载 {self.name} 插件 v{self.version}")
        
        # 确保数据目录存在
        os.makedirs("./data", exist_ok=True)
        
        # 初始化 Milvus
        self._init_milvus()
        
        # 加载配置
        self._load_config()
        
        logger.info(f"{self.name} 插件加载完成")
    
    def _init_milvus(self):
        """初始化 Milvus 客户端"""
        try:
            # 使用 Milvus Lite
            logger.info(f"正在初始化 Milvus Lite: {self.config['milvus_lite_path']}")
            self.milvus_client = MilvusClient(self.config["milvus_lite_path"])
            logger.info(f"成功初始化 Milvus Lite")
            
            # 创建默认集合（如果不存在）
            self._create_collection()
            
        except Exception as e:
            logger.error(f"Milvus 初始化失败: {e}")
            self.milvus_client = None
    
    def _create_collection(self):
        """创建 Milvus 集合"""
        try:
            # 检查集合是否存在
            if not self.milvus_client.has_collection(self.config["collection_name"]):
                logger.info(f"创建 Milvus 集合: {self.config['collection_name']}")
                
                # 定义集合架构
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True, description="记忆ID"),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.config["embedding_dimension"], description="文本向量"),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, description="记忆文本"),
                    FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=36, description="会话ID"),
                    FieldSchema(name="persona_id", dtype=DataType.VARCHAR, max_length=50, description="人格ID"),
                    FieldSchema(name="timestamp", dtype=DataType.INT64, description="时间戳"),
                    FieldSchema(name="metadata", dtype=DataType.JSON, description="元数据"),
                ]
                
                # 创建集合
                self.milvus_client.create_collection(
                    collection_name=self.config["collection_name"],
                    schema=CollectionSchema(fields=fields, description="Mnemosyne 记忆集合"),
                    dimension=self.config["embedding_dimension"],
                    metric_type="COSINE"  # 使用余弦相似度
                )
                logger.info(f"集合创建成功: {self.config['collection_name']}")
            else:
                logger.info(f"集合已存在: {self.config['collection_name']}")
        except Exception as e:
            logger.error(f"创建 Milvus 集合失败: {e}")
    
    def _load_config(self):
        """加载配置"""
        try:
            # 这里可以从配置文件加载配置
            # 暂时使用默认配置
            pass
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    async def on_message(self, ctx: event.Context):
        """处理消息事件"""
        # 获取会话 ID
        session_id = self._get_session_id(ctx)
        persona_id = self._get_persona_id(ctx)
        
        # 存储对话到缓冲区
        await self._store_conversation(ctx, session_id)
        
        # 检查是否需要总结
        if await self._should_summarize(session_id):
            await self._summarize_and_store(ctx, session_id, persona_id)
        
        # 检索相关记忆
        relevant_memories = await self._retrieve_memories(ctx, session_id, persona_id)
        
        # 注入记忆到上下文
        await self._inject_memories(ctx, relevant_memories)
    
    def _get_session_id(self, ctx: event.Context) -> str:
        """获取会话 ID"""
        # 尝试从上下文获取会话 ID
        session_id = ctx.session.get("session_id")
        if not session_id:
            # 生成新的会话 ID
            session_id = str(uuid.uuid4())
            ctx.session["session_id"] = session_id
        return session_id
    
    def _get_persona_id(self, ctx: event.Context) -> str:
        """获取人格 ID"""
        # 从上下文获取人格 ID 或使用默认值
        return ctx.session.get("persona_id", "default")
    
    async def _store_conversation(self, ctx: event.Context, session_id: str):
        """存储对话到缓冲区"""
        if session_id not in self.conversation_buffer:
            self.conversation_buffer[session_id] = []
        
        # 添加当前消息到缓冲区
        self.conversation_buffer[session_id].append({
            "role": ctx.role,
            "content": ctx.content,
            "timestamp": time.time()
        })
    
    async def _should_summarize(self, session_id: str) -> bool:
        """检查是否需要总结对话"""
        if session_id not in self.conversation_buffer:
            return False
        
        # 计算用户-助手对话对数量
        conversation = self.conversation_buffer[session_id]
        pairs = 0
        i = 0
        while i < len(conversation) - 1:
            if conversation[i].get("role") == "user" and conversation[i+1].get("role") == "assistant":
                pairs += 1
                i += 2
            else:
                i += 1
        
        return pairs >= self.config["num_pairs"]
    
    async def _summarize_and_store(self, ctx: event.Context, session_id: str, persona_id: str):
        """总结对话并存储到向量数据库"""
        if self.milvus_client is None:
            logger.error("Milvus 客户端未初始化，无法存储记忆")
            return
        
        try:
            # 获取对话内容
            conversation = self.conversation_buffer[session_id]
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
            
            # 使用 LLM 总结对话
            summary = await self._summarize_with_llm(ctx, conversation_text)
            
            if summary:
                # 获取文本向量
                embedding = await self._get_embedding(ctx, summary)
                
                if embedding:
                    # 准备存储数据
                    memory_data = [{
                        "id": str(uuid.uuid4()),
                        "vector": embedding,
                        "text": summary,
                        "session_id": session_id,
                        "persona_id": persona_id,
                        "timestamp": int(time.time()),
                        "metadata": {
                            "source": "conversation_summary",
                            "message_count": len(conversation)
                        }
                    }]
                    
                    # 存储到 Milvus
                    self.milvus_client.insert(
                        collection_name=self.config["collection_name"],
                        data=memory_data
                    )
                    
                    logger.info(f"成功存储记忆: {summary[:50]}...")
                    
                    # 清空缓冲区
                    self.conversation_buffer[session_id] = []
        except Exception as e:
            logger.error(f"总结和存储记忆失败: {e}")
    
    async def _summarize_with_llm(self, ctx: event.Context, text: str) -> str:
        """使用 LLM 总结文本"""
        try:
            # 构建总结提示
            prompt = f"请总结以下对话内容，提取关键信息，保持简洁清晰:\n\n{text}"
            
            # 调用 LLM API
            response = await api.llm.chat_completion(
                model=ctx.session.get("model", "gpt-3.5-turbo"),
                messages=[{"role": "system", "content": "你是一个专业的对话总结助手。"},
                          {"role": "user", "content": prompt}]
            )
            
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM 总结失败: {e}")
            return ""
    
    async def _get_embedding(self, ctx: event.Context, text: str) -> List[float]:
        """获取文本向量"""
        try:
            # 调用 Embedding API
            response = await api.embedding.create(
                model=ctx.session.get("embedding_model", "text-embedding-ada-002"),
                input=text
            )
            
            # 确保向量维度正确
            embedding = response["data"][0]["embedding"]
            if len(embedding) != self.config["embedding_dimension"]:
                logger.warning(f"嵌入向量维度不匹配: {len(embedding)} vs {self.config['embedding_dimension']}")
                # 截断或填充向量
                if len(embedding) > self.config["embedding_dimension"]:
                    embedding = embedding[:self.config["embedding_dimension"]]
                else:
                    embedding = embedding + [0.0] * (self.config["embedding_dimension"] - len(embedding))
            
            return embedding
        except Exception as e:
            logger.error(f"获取文本向量失败: {e}")
            return []
    
    async def _retrieve_memories(self, ctx: event.Context, session_id: str, persona_id: str) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        if self.milvus_client is None:
            return []
        
        try:
            # 获取当前消息的向量
            embedding = await self._get_embedding(ctx, ctx.content)
            
            if not embedding:
                return []
            
            # 构建过滤条件
            filter_expr = [f"session_id == '{session_id}'"]
            
            if self.config["use_personality_filtering"]:
                filter_expr.append(f"persona_id == '{persona_id}'")
            
            filter_str = " && ".join(filter_expr)
            
            # 搜索相似向量
            search_results = self.milvus_client.search(
                collection_name=self.config["collection_name"],
                data=[embedding],
                limit=self.config["top_k"],
                search_params={"metric_type": "COSINE", "params": {}},
                filter=filter_str,
                output_fields=["text", "timestamp", "metadata"]
            )
            
            # 格式化结果
            memories = []
            for hits in search_results:
                for hit in hits:
                    memories.append({
                        "id": hit["id"],
                        "text": hit.get("entity", {}).get("text", ""),
                        "distance": hit["distance"],
                        "timestamp": hit.get("entity", {}).get("timestamp", 0),
                        "metadata": hit.get("entity", {}).get("metadata", {})
                    })
            
            # 按时间戳排序
            memories.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return memories
            
        except Exception as e:
            logger.error(f"检索记忆失败: {e}")
            return []
    
    async def _inject_memories(self, ctx: event.Context, memories: List[Dict[str, Any]]):
        """注入记忆到上下文"""
        if not memories:
            return
        
        # 根据配置选择注入方式
        if self.config["memory_injection_method"] == "user_prompt":
            # 注入到用户提示
            memory_text = "\n\n相关记忆：\n"
            for i, memory in enumerate(memories):
                memory_text += f"{i+1}. {memory['text']}\n"
            
            ctx.content += memory_text
        elif self.config["memory_injection_method"] == "system_prompt":
            # 注入到系统提示
            if "system_prompt" not in ctx.session:
                ctx.session["system_prompt"] = ""
            
            memory_text = "\n\n相关记忆：\n"
            for i, memory in enumerate(memories):
                memory_text += f"{i+1}. {memory['text']}\n"
            
            ctx.session["system_prompt"] += memory_text
    
    @plugin.command("memory list")
    async def list_collections(self, ctx: event.Context):
        """查看所有记忆集合"""
        if self.milvus_client is None:
            await ctx.reply("Milvus 客户端未初始化，无法获取集合列表")
            return
        
        try:
            collections = self.milvus_client.list_collections()
            reply = "记忆集合列表：\n"
            for collection in collections:
                reply += f"- {collection}\n"
            
            await ctx.reply(reply)
        except Exception as e:
            logger.error(f"获取集合列表失败: {e}")
            await ctx.reply(f"获取集合列表失败: {str(e)}")
    
    @plugin.command("memory list_records")
    async def list_records(self, ctx: event.Context):
        """列出指定集合的记忆记录"""
        if self.milvus_client is None:
            await ctx.reply("Milvus 客户端未初始化，无法获取记忆记录")
            return
        
        try:
            # 解析参数
            args = ctx.content.split()[2:]
            collection_name = args[0] if args else self.config["collection_name"]
            limit = int(args[1]) if len(args) > 1 else 10
            
            # 查询记录
            records = self.milvus_client.query(
                collection_name=collection_name,
                limit=limit,
                output_fields=["text", "session_id", "timestamp", "metadata"]
            )
            
            reply = f"集合 {collection_name} 的记忆记录（前{limit}条）：\n"
            for i, record in enumerate(records):
                text = record.get("text", "").replace("\n", " ")[:100]
                timestamp = datetime.fromtimestamp(record.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
                session_id = record.get("session_id", "").split("-")[0]
                reply += f"{i+1}. [{timestamp}] [{session_id}] {text}...\n"
            
            await ctx.reply(reply)
        except Exception as e:
            logger.error(f"获取记忆记录失败: {e}")
            await ctx.reply(f"获取记忆记录失败: {str(e)}")
    
    @plugin.command("memory get_session_id")
    async def get_session_id(self, ctx: event.Context):
        """获取当前会话 ID"""
        session_id = self._get_session_id(ctx)
        await ctx.reply(f"当前会话 ID: {session_id}")
    
    @plugin.command("memory reset")
    async def reset_memory(self, ctx: event.Context):
        """清除当前会话记忆"""
        # 检查是否确认
        args = ctx.content.split()[2:]
        if args and args[0].lower() == "confirm":
            session_id = self._get_session_id(ctx)
            
            # 清除缓冲区
            if session_id in self.conversation_buffer:
                del self.conversation_buffer[session_id]
            
            # 清除数据库中的会话记忆
            if self.milvus_client:
                try:
                    self.milvus_client.delete(
                        collection_name=self.config["collection_name"],
                        filter=f"session_id == '{session_id}'"
                    )
                except Exception as e:
                    logger.error(f"清除数据库记忆失败: {e}")
            
            await ctx.reply("已清除当前会话的所有记忆")
        else:
            await ctx.reply("请确认操作: /memory reset confirm")
    
    @plugin.command("memory stats")
    async def memory_stats(self, ctx: event.Context):
        """查看记忆统计信息"""
        if self.milvus_client is None:
            await ctx.reply("Milvus 客户端未初始化，无法获取统计信息")
            return
        
        try:
            # 获取集合统计信息
            stats = self.milvus_client.get_collection_stats(self.config["collection_name"])
            
            # 查询记录总数
            records = self.milvus_client.query(
                collection_name=self.config["collection_name"],
                limit=1,
                output_fields=["id"]
            )
            
            # 获取唯一会话数
            unique_sessions = self.milvus_client.query(
                collection_name=self.config["collection_name"],
                distinct_by="session_id",
                output_fields=["session_id"]
            )
            
            reply = "记忆统计信息：\n"
            reply += f"- 总记录数: {len(records)}\n"
            reply += f"- 唯一会话数: {len(unique_sessions)}\n"
            reply += f"- 集合大小: {stats.get('collection_size', '未知')}\n"
            
            await ctx.reply(reply)
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            await ctx.reply(f"获取统计信息失败: {str(e)}")
    
    async def on_unload(self):
        """插件卸载时执行"""
        logger.info(f"正在卸载 {self.name} 插件")
        
        # Milvus Lite 不需要显式关闭，但可以进行资源清理
        if self.milvus_client:
            try:
                # 清理会话缓冲区
                self.conversation_buffer.clear()
                logger.info("已清理会话缓冲区")
            except Exception as e:
                logger.error(f"资源清理失败: {e}")
        
        logger.info(f"{self.name} 插件卸载完成")

# 创建插件实例
plugin_instance = MnemosynePlugin()

# 导出插件实例
__plugin__ = plugin_instance