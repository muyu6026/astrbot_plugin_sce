from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger as astrbot_logger
import json
import os
import datetime
import requests
import asyncio
from pathlib import Path
import time
import random
from typing import Dict, Any, Optional
from astrbot.api.star import StarTools
from urllib.parse import urlparse
# JSON处理模块
class JsonHandler:
    @staticmethod
    def 验证文件名(文件名: str) -> bool:
        """验证文件名是否合法"""
        if not 文件名:
            print("错误: 文件名不能为空")
            return False
        
        # 检查文件名是否包含路径分隔符（防止路径遍历攻击）
        if any(c in 文件名 for c in ['/', '\\', './', '../', '.\\', '..\\']):
            print(f"错误: 文件名 '{文件名}' 包含非法字符或路径组件")
            return False
        
        # 检查文件名是否包含非法字符
        invalid_chars = '<>|?*"'
        if any(c in 文件名 for c in invalid_chars):
            print(f"错误: 文件名 '{文件名}' 包含非法字符")
            return False
        
        return True
    
    @staticmethod
    def 读取Json字典(文件名: str) -> dict:
        """从JSON文件读取数据并返回字典"""
        try:
            # 从JSON文件读取完整数据
            文件路径 = JsonHandler.获取文件路径(文件名, True)
            if os.path.exists(文件路径):
                try:
                    with open(文件路径, 'r', encoding='utf-8') as f:
                        return json.load(f) if f.read().strip() else {}
                except Exception as e:
                    logger.error(f"读取JSON文件失败: {e}")
            return {}
        except Exception as e:
            print(f"读取数据错误: {e}")
            return {}
    
    @staticmethod
    def 获取值(数据字典: dict, 键: str, 默认值: any = None) -> any:
        """安全地从字典中获取值"""
        return 数据字典.get(键, 默认值)
    
    @staticmethod
    def 获取文件路径(文件名: str, 确保目录存在: bool = False) -> str:
        """获取文件路径，将数据存储在安全的数据目录中
        
        Args:
            文件名: 要访问的JSON文件名
            确保目录存在: 是否确保目录存在，不存在则创建
            
        Returns:
            文件的绝对路径
        """
        try:
            # 获取插件数据目录
            plugin_data_path = StarTools.get_data_dir()
            # 构建完整路径: data/plugin_data/astrbot_plugin_sce/文件名
            file_path = os.path.join(plugin_data_path, 文件名)
            
            # 确保目录存在
            if 确保目录存在:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            return file_path
        except Exception as e:
            logger.error(f"获取文件路径失败: {e}")
            # 降级方案：使用当前目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, 文件名)
            if 确保目录存在:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            return file_path
    
    @staticmethod
    def 写入Json字典(文件名: str, 数据: dict) -> bool:
        """将字典数据写入JSON文件，使用UserData目录下的文件名作为模板
        
        Args:
            文件名: JSON文件名（使用UserData目录下的文件名作为模板）
            数据: 要写入的数据字典
            
        Returns:
            bool: 是否写入成功
        """
        try:
            # 获取文件路径并确保目录存在
            文件路径 = JsonHandler.获取文件路径(文件名, True)
            
            # 检查目录是否存在
            目录 = os.path.dirname(文件路径)
            if not os.path.exists(目录):
                os.makedirs(目录, exist_ok=True)
                logger.info(f"创建目录: {目录}")
            
            # 写入数据
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已成功写入: {文件路径}")
            return True
        except Exception as e:
            logger.error(f"写入JSON文件失败: {文件名}, 错误: {e}")
            return False
    
    @staticmethod
    def 读取Json字典(文件名: str) -> dict:
        """读取JSON文件为字符串字典，使用UserData目录下的文件名作为模板"""
        try:
            # 获取文件路径并确保目录存在
            文件路径 = JsonHandler.获取文件路径(文件名, True)
            
            # 检查文件是否存在
            if not os.path.exists(文件路径):
                logger.info(f"文件不存在，创建空字典: {文件路径}")
                # 创建空文件
                JsonHandler.写入Json字典(文件名, {})
                return {}
            
            # 读取文件内容
            with open(文件路径, 'r', encoding='utf-8') as f:
                json内容 = f.read().strip()
                if not json内容:
                    return {}
                字典 = json.loads(json内容)
                
                if not isinstance(字典, dict):
                    logger.warning(f"JSON文件内容格式不正确: {文件路径}")
                    return {}
                
                return 字典
        except Exception as ex:
            logger.error(f"错误: 读取JSON字典时发生错误 - {ex}")
            return {}
    
    @staticmethod
    def 获取值(字典: dict, 键: str, 默认值: str = None) -> str:
        """根据键获取值，如果键不存在返回默认值"""
        if 字典 is not None and 键 in 字典:
            return 字典[键]
        return 默认值
    
    @staticmethod
    def 添加或更新(文件名: str, 键: str, 值: str) -> bool:
        """向JSON文件添加或更新键值对"""
        try:
            if not 键:
                print("错误: 键名不能为空")
                return False
            
            # 读取现有数据
            data = JsonHandler.读取Json字典(文件名)
            
            # 更新键值对
            data[键] = str(值)
            
            # 写入文件
            return JsonHandler.写入Json字典(文件名, data)
        except Exception as ex:
            print(f"错误: 添加或更新值时发生错误 - {ex}")
            return False
    
# 创建别名方便使用
Json = JsonHandler

# 邮件服务模块
class EmailService:
    """邮件发送服务类（基于C#代码实现）"""
    
    def __init__(self, auth_token, project_id="p_95jd", max_retries=2):
        """
        初始化邮件服务
        
        Args:
            auth_token (str): 认证令牌
            project_id (str): 项目ID，默认值为"p_95jd"
            max_retries (int): 重试次数，默认值为2
        """
        self.auth_token = auth_token
        self.project_id = project_id
        self.add_email_url = "https://adminapi-pd.spark.xd.com/api/v1/table/add"
        self.send_email_url = "https://adminapi-pd.spark.xd.com/api/v1/table/row"
        self.table_id = "firm0_app_email_manager"
        self.session = requests.Session()
        self.max_retries = max_retries  # 设置重试次数
        # 设置默认请求头
        self._update_auth_headers(auth_token)
    
    def _update_auth_headers(self, token):
        """更新认证头信息"""
        self.auth_token = token
        self.session.headers.update({
            "Cookie": f"token={token}",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  # 增加Authorization头
        })
        # 同时更新session的cookies
        self.session.cookies.set('token', token)
    
    def _trigger_email_send(self, row_id):
        """
        触发邮件发送（根据C#代码和最新接口响应格式优化）
        
        Args:
            row_id: 邮件行ID
            
        Returns:
            dict: 发送结果，包含success、message和可能的附加信息
        """
        if not row_id:
            return {"success": False, "message": "行ID为空"}
        
        try:
            # 构建更完整的请求数据，确保payload包含必要信息
            request_data = {
                "firm": self.project_id,
                "functor": "send",
                "payload": {"action": "send_email"},  # 添加必要的payload参数
                "row_id": row_id,
                "table_id": self.table_id
            }
            
            print(f"准备触发邮件发送: {row_id}")
            print(f"触发请求数据: {json.dumps(request_data, ensure_ascii=False)}")
            
            # 添加超时设置
            response = self.session.post(
                self.send_email_url, 
                data=json.dumps(request_data),
                timeout=30
            )
            
            print(f"触发发送响应状态码: {response.status_code}")
            print(f"触发发送响应内容: {response.text}")
            
            # 保存原始响应，用于调试和错误处理
            raw_response = response.text
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # 根据最新接口响应格式优化：检查result=0表示成功
                    success = result.get("result") == 0
                    message = result.get("msg", "未知响应")
                    
                    # 增加详细的返回信息
                    return {
                        "success": success,
                        "message": message,
                        "raw_response": raw_response,
                        "response_data": result
                    }
                except json.JSONDecodeError:
                    print(f"触发发送响应解析失败: {raw_response}")
                    # 即使JSON解析失败，如果状态码是200，也可以尝试判断是否成功
                    # 这里我们仍然返回失败，但提供更详细的错误信息
                    return {
                        "success": False, 
                        "message": "触发发送响应不是有效的JSON",
                        "raw_response": raw_response,
                        "response_status": response.status_code
                    }
            else:
                # 非200状态码的错误处理
                error_msg = f"触发发送失败: {response.status_code} {response.reason}"
                print(error_msg)
                return {
                    "success": False, 
                    "message": error_msg,
                    "raw_response": raw_response,
                    "response_status": response.status_code
                }
                
        except requests.Timeout:
            error_msg = f"触发邮件发送超时: row_id={row_id}"
            print(error_msg)
            return {"success": False, "message": error_msg, "error_type": "TIMEOUT"}
        except requests.ConnectionError:
            error_msg = f"触发邮件发送连接错误: row_id={row_id}"
            print(error_msg)
            return {"success": False, "message": error_msg, "error_type": "CONNECTION_ERROR"}
        except Exception as e:
            error_msg = f"触发邮件发送异常: {str(e)}"
            print(error_msg)
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            return {"success": False, "message": error_msg, "error_type": "UNKNOWN_ERROR"}
    
    async def send_email(self, email_data):
        """
        异步发送邮件（根据C#代码实现）
        
        Args:
            email_data (dict): 邮件数据，包含标题、正文、收件人ID等
            
        Returns:
            dict: 发送结果
        """
        try:
            print(f"准备发送邮件: {email_data.get('标题', '无标题')}")
            print(f"目标类型: {email_data.get('目标类型', 1)}，收件人ID: {email_data.get('收件人ID', '全体')}")
            
            # 先验证token是否存在
            if not self.auth_token:
                error_msg = "认证token为空，请先设置有效的token"
                print(error_msg)
                return {"success": False, "message": error_msg, "error_code": "TOKEN_EMPTY"}
            
            # 第一步：添加邮件到系统
            add_result = await self._add_email(email_data)
            print(f"添加邮件结果: {add_result}")
            
            # 检查是否是401错误
            if add_result and "401 Unauthorized" in add_result.get("message", ""):
                print("检测到401未授权错误，可能需要刷新token")
                return {
                    "success": False, 
                    "message": add_result.get("message"),
                    "error_code": "TOKEN_EXPIRED",
                    "need_refresh": True
                }
            
            if not add_result:
                return {"success": False, "message": "添加邮件失败: 未收到响应", "error_code": "NO_RESPONSE"}
            if not add_result.get('success'):
                error_message = add_result.get('message', '添加邮件失败')
                return {"success": False, "message": error_message, "error_code": "EMAIL_ADD_FAILED"}
            
            # 第二步：触发发送
            row_id = add_result.get('row_id')
            response_structure = add_result.get('response_structure', [])
            raw_response = add_result.get('raw_response', '')
            has_dialog_box = add_result.get('has_dialog_box', False)
            
            # 处理特殊情况：根据抓包数据，即使没有row_id但有dialog_box字段，邮件实际上已经被添加并发送
            if not row_id and has_dialog_box and add_result.get('success'):
                print(f"检测到特殊响应格式（有dialog_box字段），邮件已成功添加并自动发送")
                return {
                    "success": True,
                    "message": "邮件添加成功并自动发送（特殊响应格式）",
                    "row_id": None,
                    "special_response_format": True,
                    "response_type": "dialog_box"
                }
            
            if row_id:
                # 调用触发发送方法
                trigger_result = self._trigger_email_send(row_id)
                print(f"触发发送结果: {trigger_result}")
                
                if trigger_result.get("success"):
                    # 成功情况下，返回更详细的信息
                    return {
                        "success": True,
                        "message": "邮件发送成功",
                        "row_id": row_id,
                        "trigger_result": trigger_result,
                        "raw_response": trigger_result.get('raw_response', ''),
                        "response_data": trigger_result.get('response_data', {})
                    }
                else:
                    # 触发发送失败，但邮件已添加
                    # 根据最新接口响应格式，即使触发发送返回失败，也可能邮件已经成功添加
                    error_msg = trigger_result.get('message', '未知错误')
                    error_type = trigger_result.get('error_type', 'UNKNOWN')
                    
                    # 记录详细错误信息
                    print(f"邮件添加成功但触发发送失败: {error_msg}, 错误类型: {error_type}")
                    
                    # 根据错误类型进行不同处理
                    if error_type == 'TIMEOUT':
                        # 超时情况下，邮件可能已经发送成功，我们给予警告但仍标记为可能成功
                        print(f"警告: 触发发送超时，邮件可能已经成功发送但无法确认")
                        return {
                            "success": False,
                            "message": f"邮件添加成功，但触发发送超时，邮件可能已发送: {error_msg}",
                            "row_id": row_id,
                            "email_added": True,
                            "trigger_timeout": True,
                            "warning": "超时警告：邮件可能已成功发送"
                        }
                    else:
                        # 其他错误类型
                        return {
                            "success": False,
                            "message": f"邮件添加成功但触发发送失败: {error_msg}",
                            "row_id": row_id,
                            "email_added": True,
                            "error_type": error_type,
                            "raw_response": trigger_result.get('raw_response', '')
                        }
            else:
                # 未获取到row_id时的增强错误处理
                error_msg = f"未获取到邮件行ID，响应结构: {response_structure}"
                print(f"发送邮件处理: {error_msg}")
                print(f"原始响应内容: {raw_response}")
                
                # 尝试从原始响应中直接提取row_id
                try:
                    # 如果原始响应是JSON格式，尝试直接解析
                    import json
                    if raw_response.strip().startswith('{'):
                        raw_json = json.loads(raw_response)
                        # 尝试多种可能的路径
                        if isinstance(raw_json, dict):
                            # 尝试常见的数据路径
                            if 'data' in raw_json and isinstance(raw_json['data'], dict):
                                for key in ['row_id', 'id', 'rowId']:
                                    if key in raw_json['data']:
                                        row_id = raw_json['data'][key]
                                        print(f"从原始响应中成功提取到row_id: {row_id}")
                                        # 尝试使用提取到的row_id触发发送
                                        trigger_result = self._trigger_email_send(row_id)
                                        if trigger_result.get("success"):
                                            return {
                                                "success": True,
                                                "message": "邮件发送成功(从原始响应中提取row_id)",
                                                "row_id": row_id,
                                                "trigger_result": trigger_result
                                            }
                            # 直接在根对象中查找
                            for key in ['row_id', 'id', 'rowId']:
                                if key in raw_json:
                                    row_id = raw_json[key]
                                    print(f"从原始响应根对象中成功提取到row_id: {row_id}")
                                    # 尝试使用提取到的row_id触发发送
                                    trigger_result = self._trigger_email_send(row_id)
                                    if trigger_result.get("success"):
                                        return {
                                            "success": True,
                                            "message": "邮件发送成功(从原始响应根对象中提取row_id)",
                                            "row_id": row_id,
                                            "trigger_result": trigger_result
                                        }
                except Exception as parse_error:
                    print(f"解析原始响应异常: {str(parse_error)}")
                
                # 重要修改：根据抓包数据，即使没有row_id，只要添加操作成功，也应视为成功
                # 这是因为系统实际上已经处理了邮件的添加和发送
                if add_result.get('success'):
                    print(f"虽然没有row_id，但添加操作成功，邮件可能已自动发送")
                    return {
                        "success": True,
                        "message": "邮件添加成功（系统自动处理发送）",
                        "row_id": None,
                        "auto_processed": True
                    }
                
                # 所有尝试都失败，返回详细的错误信息
                return {
                    "success": False, 
                    "message": error_msg,
                    "error_code": "NO_ROW_ID",
                    "response_structure": response_structure,
                    "raw_response_preview": raw_response[:200] + '...' if len(raw_response) > 200 else raw_response
                }
            
        except requests.RequestException as e:
            error_msg = f"网络请求异常: {str(e)}"
            print(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                # 检查是否是401错误
                if e.response.status_code == 401:
                    return {
                        "success": False,
                        "message": f"401未授权错误: {str(e)}",
                        "error_code": "TOKEN_EXPIRED",
                        "need_refresh": True
                    }
            return {"success": False, "message": error_msg, "error_code": "NETWORK_ERROR"}
        except Exception as e:
            error_msg = f"发送邮件异常: {str(e)}"
            print(error_msg)
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            return {"success": False, "message": error_msg, "error_code": "INTERNAL_ERROR"}
    
    async def quick_send(self, title, content, recipient_id, item_id=0, item_count=0, money=0, attachment=""):
        """
        异步快速发送邮件（根据C#代码实现）
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            recipient_id (str): 收件人ID
            item_id (int): 道具ID（保留兼容）
            item_count (int): 道具数量（保留兼容）
            money (int): 货币数量（保留兼容）
            attachment (str): 道具奖励字符串，如 "$p_95jd.lobby_resource.魂晶.root:999"
            
        Returns:
            dict: 发送结果
        """
        # 记录传入的参数
        print(f"quick_send方法调用参数 - 标题: '{title}', 收件人ID: '{recipient_id}', 奖励字符串: '{attachment}'")
        
        # 验证必填字段
        if not title or not str(title).strip():
            return {"success": False, "message": "邮件标题不能为空", "error_code": "EMPTY_TITLE"}
        if not content or not str(content).strip():
            return {"success": False, "message": "邮件内容不能为空", "error_code": "EMPTY_CONTENT"}
        if not recipient_id:
            return {"success": False, "message": "收件人ID不能为空", "error_code": "EMPTY_RECIPIENT"}
        
        # 验证并清理recipient_id，确保它是一个有效的数字格式用户ID
        # 清理空格和不可见字符
        cleaned_recipient_id = str(recipient_id).strip()
        # 验证是否只包含数字
        if not cleaned_recipient_id.isdigit():
            print(f"警告：收件人ID '{recipient_id}' 包含非数字字符，可能导致400错误")
            # 尝试提取数字部分（如果是混合格式）
            import re
            numbers_only = re.sub(r'\D', '', cleaned_recipient_id)
            if numbers_only:
                print(f"已提取数字部分: {numbers_only}")
                recipient_id = numbers_only
            else:
                print("无法从收件人ID中提取有效的数字，将使用原ID但可能导致错误")
                return {"success": False, "message": f"无效的收件人ID格式: {recipient_id}", "error_code": "INVALID_RECIPIENT_FORMAT"}
        else:
            recipient_id = cleaned_recipient_id
        
        print(f"清理后的收件人ID: '{recipient_id}'")
        
        # 验证奖励字符串格式（如果提供）
        if attachment:
            # 确保奖励字符串格式正确，包含必要的分隔符
            if ':' not in attachment:
                print(f"警告：奖励字符串格式可能不正确，缺少分隔符':': '{attachment}'")
                # 简单检查格式是否符合预期模式
                if not re.search(r'\$[\w\.]+:\d+', attachment):
                    print(f"奖励字符串 '{attachment}' 可能不符合预期格式")
        
        # 构建完整的邮件数据
        email_data = {
            "标题": title,
            "正文": content,
            "收件人ID": recipient_id,
            "道具奖励": attachment,  # 直接传递完整的奖励字符串
            "邮件类型": 1,
            "目标类型": 1,  # 个人邮件
            "接收方式": 0,
            "是否定时邮件": False,
            "排除新玩家": False,
            "有效天数": 90,
            "环境": "formal",
            "发件人": "系统管理员"
        }
        
        print(f"构建的邮件数据: {json.dumps(email_data, ensure_ascii=False)}")
        
        return await self.send_email(email_data)
    
    async def send_to_all(self, title, content, item_id=0, item_count=0, money=0, attachment=""):
        """
        异步发送全体邮件（根据C#代码实现）
        
        Args:
            title (str): 邮件标题
            content (str): 邮件内容
            item_id (int): 道具ID（保留兼容）
            item_count (int): 道具数量（保留兼容）
            money (int): 货币数量（保留兼容）
            attachment (str): 道具奖励字符串，如 "$p_95jd.lobby_resource.魂晶.root:999"
            
        Returns:
            dict: 发送结果
        """
        # 构建符合C#格式的邮件数据
        email_data = {
            "标题": title,
            "正文": content,
            "道具奖励": attachment,
            "邮件类型": 1,
            "目标类型": 0,  # 全体邮件
            "接收方式": 0,
            "是否定时邮件": False,
            "排除新玩家": False,
            "有效天数": 90,
            "环境": "formal",
            "发件人": "系统管理员"
        }
        
        return await self.send_email(email_data)
    
    async def _add_email(self, email_data):
        """
        添加邮件到系统（根据C#代码实现）
        
        Args:
            email_data (dict): 邮件数据
            
        Returns:
            dict: 添加结果
        """
        # 准备请求数据（提取为独立函数避免重复代码）
        def prepare_request_data():
            import time
            current_time_ms = int(time.time() * 1000)
            
            # 获取完整的奖励字符串，确保不做任何处理或分割
            full_reward_string = email_data.get("道具奖励", "")
            print(f"准备发送的完整奖励字符串: '{full_reward_string}'")
            
            # 构建payload数据
            payload = {
                "attachment": full_reward_string,  # 直接使用完整的奖励字符串
                "content": email_data.get("正文", ""),
                "content_type": email_data.get("邮件类型", 1),
                "env": email_data.get("环境", "formal"),
                "include_new_player": email_data.get("排除新玩家", False),
                "map_name": self.project_id,
                "recieve_type": email_data.get("接收方式", 0),
                "send_type": email_data.get("是否定时邮件", False),
                "sender_name": email_data.get("发件人", "系统管理员"),
                "start_time": current_time_ms,
                "target": email_data.get("收件人ID", "") if email_data.get("目标类型", 1) == 1 else "",
                "target_type": email_data.get("目标类型", 1),
                "time_limit": email_data.get("有效天数", 90),
                "title": email_data.get("标题", "系统邮件")
            }
            
            # 构建完整请求数据
            request_data = {
                "firm": self.project_id,
                "table_id": self.table_id,
                "payload": payload
            }
            
            return request_data
        
        # 执行请求（带重试逻辑）
        for attempt in range(self.max_retries + 1):
            try:
                print(f"准备添加邮件到系统 (尝试 {attempt + 1}/{self.max_retries + 1})")
                print(f"原始邮件数据: {email_data}")
                
                request_data = prepare_request_data()
                
                print(f"准备发送邮件请求到: {self.add_email_url}")
                print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")
                print(f"当前使用的token: {self.auth_token[:20]}...{self.auth_token[-8:]}")
                
                response = self.session.post(
                    self.add_email_url, 
                    data=json.dumps(request_data),
                    timeout=30  # 添加超时设置
                )
                
                print(f"邮件服务响应状态码: {response.status_code}")
                print(f"邮件服务响应内容: {response.text}")
                
                # 处理400错误（请求参数问题）
                if response.status_code == 400:
                    error_detail = f"收到400 Bad Request错误，请求参数可能有问题"
                    print(error_detail)
                    print(f"详细响应内容: {response.text}")
                    print(f"完整请求数据: {json.dumps(request_data, ensure_ascii=False)}")
                    
                    # 分析可能的问题：验证用户ID格式
                    target_id = request_data.get('payload', {}).get('target', '')
                    if target_id and not str(target_id).strip().isdigit():
                        format_warning = f"警告: 目标用户ID '{target_id}' 可能格式不正确，这可能是400错误的原因"
                        print(format_warning)
                        error_detail += "，" + format_warning
                    
                    # 获取payload中的其他关键参数信息
                    payload = request_data.get('payload', {})
                    if not payload.get('attachment'):
                        print("警告: attachment参数为空，可能导致请求失败")
                        error_detail += "，attachment参数为空"
                    if not payload.get('content'):
                        print("警告: content参数为空，可能导致请求失败")
                        error_detail += "，content参数为空"
                    
                    # 如果是最后一次尝试，直接返回详细错误
                    if attempt >= self.max_retries:
                        error_msg = f"HTTP错误: 400 Bad Request，请求参数问题: {error_detail}"
                        print(error_msg)
                        return {
                            "success": False, 
                            "message": error_msg, 
                            "response": response.text, 
                            "error_code": "BAD_REQUEST",
                            "request_data": request_data,
                            "target_id": target_id
                        }
                    
                    # 等待后重试
                    print("等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                    
                # 处理401错误（需要刷新token）
                if response.status_code == 401:
                    print(f"收到401未授权错误，token可能已过期")
                    
                    # 如果是最后一次尝试，直接返回错误
                    if attempt >= self.max_retries:
                        error_msg = f"HTTP错误: 401 Unauthorized，已尝试刷新token但仍失败"
                        print(error_msg)
                        return {"success": False, "message": error_msg, "response": response.text}
                    
                    # 立即尝试刷新token
                    print("尝试自动刷新token...")
                    refresh_result = await self._refresh_all_games()
                    
                    if refresh_result.get("success") and refresh_result.get("token"):
                        new_token = refresh_result["token"]
                        print(f"成功刷新token，后10位: {new_token[-10:]}")
                        self._update_auth_headers(new_token)
                        # 立即重试请求
                        continue
                    else:
                        print(f"token刷新失败: {refresh_result.get('message')}")
                    
                    # 尝试从cookie中获取新token（如果有）
                    if 'token' in self.session.cookies:
                        new_token = self.session.cookies['token']
                        if new_token and new_token != self.auth_token:
                            print(f"从cookie中获取到新token")
                            self._update_auth_headers(new_token)
                            continue  # 重试请求
                    
                    # 添加延迟后重试
                    print(f"等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                
                # 处理其他状态码
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"响应解析结果: {result}")
                        
                        # 返回统一格式的结果
                        success = result.get("result") == 0
                        row_id = None
                        
                        # 增强的row_id提取逻辑，尝试多种可能的结构
                        if success:
                            # 首先尝试标准路径
                            if result.get("data"):
                                row_id = result["data"].get("row_id")
                            
                            # 如果没找到，尝试直接在result中查找
                            if not row_id:
                                row_id = result.get("row_id")
                            
                            # 根据抓包数据的特殊处理：即使没有row_id，只要添加成功，也认为是成功的
                            # 在这种情况下，我们不尝试触发发送，因为没有row_id，但邮件实际上已经被添加
                            if not row_id:
                                print(f"Add接口响应中未包含row_id，但添加操作成功")
                                print(f"响应结构: {result.keys()}")
                                # 检查是否有dialog_box字段，这是抓包数据中看到的格式
                                if 'dialog_box' in result:
                                    print(f"检测到dialog_box字段，这与抓包数据格式匹配")
                            else:
                                print(f"成功提取到row_id: {row_id}")
                        
                        return {
                            "success": success,
                            "message": result.get("msg", "未知响应"),
                            "row_id": row_id,
                            "raw_response": response.text,
                            "response_structure": list(result.keys()),  # 添加响应结构信息以便调试
                            "has_dialog_box": 'dialog_box' in result  # 标记是否有dialog_box字段，用于识别特殊格式
                        }
                    except json.JSONDecodeError:
                        error_msg = f"响应解析失败: {response.text}"
                        print(error_msg)
                        return {"success": False, "message": error_msg}
                else:
                    error_msg = f"HTTP错误: {response.status_code} {response.reason}"
                    print(error_msg)
                    return {"success": False, "message": error_msg, "response": response.text}
                    
            except requests.Timeout:
                error_msg = f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待3秒后重试...")
                import time
                time.sleep(3)
            except requests.ConnectionError:
                error_msg = f"连接错误 (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待3秒后重试...")
                import time
                time.sleep(3)
            except requests.RequestException as e:
                error_msg = f"HTTP请求错误: {str(e)} (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                if hasattr(e, 'response') and e.response is not None:
                    error_msg += f", 状态码: {e.response.status_code}, 响应: {e.response.text}"
                    # 检查是否是401错误
                    if e.response.status_code == 401 and attempt < self.max_retries:
                        print("401错误，需要刷新token")
                        continue
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待2秒后重试...")
                import time
                time.sleep(2)
            except Exception as e:
                error_msg = f"添加邮件异常: {str(e)} (尝试 {attempt + 1}/{self.max_retries + 1})"
                print(error_msg)
                import traceback
                print(f"异常堆栈: {traceback.format_exc()}")
                if attempt >= self.max_retries:
                    return {"success": False, "message": error_msg}
                print("等待2秒后重试...")
                import time
                time.sleep(2)
        
        # 所有尝试都失败
        return {"success": False, "message": "所有尝试均失败，请检查token是否有效"}

# 主程序功能整合
@register("sce_spark_game", "开发者", "SCE星火游戏插件", "1.3.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化token管理，先设置token文件名
        self.token_file = "系统token存储.json"
        
        # 初始化默认token（仅作为备份使用）
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaW5mbyI6eyJ1c2VySWQiOjE0MDgxNzcxODUsIm5hbWUiOiLmmq7pm6giLCJhdmF0YXIiOiJodHRwczovL2ltZzMudGFwaW1nLmNvbS9hdmF0YXJzL2V0YWcvRnVSVnh1d1ZiM21BRTRTSWVCNkxhbkQ2UjltbC5wbmc_aW1hZ2VNb2dyMi9hdXRvLW9yaWVudC9zdHJpcC90aHVtYm5haWwvITI3MHgyNzByL2dyYXZpdHkvQ2VudGVyL2Nyb3AvMjcweDI3MC9mb3JtYXQvanBnL2ludGVybGFjZS8xL3F1YWxpdHkvODAiLCJ1bmlvbl9pZCI6IkMzNXc1YTEtaHV5akVMVzZNWXBaY0Vxd1pQMlUzM1c2RFVlbGg4blJMUWhnYXR1RCIsInRva2VuIjoiMTYzMGQ5MmQ5MmRjZWFiNDQwNGUxZTgyMTAyOWI0ODY2NjVkNWNmOWNkMDFkODM4ZWM5MzYyNjA2YzJhZjQwNSIsInRva2VuX3NlY3JldCI6Ijc2ZmMzY2QyYzA5ZGIyMzk2NTZmZDM1NjcyNzdhOTAzMTY4NGI5ZjUifSwiaWF0IjoxNzYyNzcyMjYxLCJleHAiOjE3NjI4NTg2NjF9.sMECwUYEtFEr_F4HoU1qjE9S2IvxNrw0tlqY34j2PDg"
        
        # 优先从token文件加载auth_token
        try:
            token_data = Json.读取Json字典(self.token_file)
            self.auth_token = token_data.get("token", default_token)
            logger.info(f"已从{self.token_file}加载auth_token，长度: {len(self.auth_token)} 字符")
        except Exception as e:
            logger.warning(f"从token文件加载auth_token失败: {e}，使用默认token")
            self.auth_token = default_token
        
        # 初始化游戏配置字典，包含URL
        self.game_configs = {
            "捉妖:钟馗": {
                "项目ID": "p_95jd",
                "发送的奖励": "$$p_95jd.lobby_resource.魂晶.root:999",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_2_4_1"
            },
            "游戏2": {
                "项目ID": "p_95jd",
                "发送的奖励": "$$p_95jd.lobby_resource.魂晶.root:999",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_2_4_1"
            },
            "游戏3": {
                "项目ID": "p_95jd",
                "发送的奖励": "$$p_95jd.lobby_resource.魂晶.root:999",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_2_4_1"
            },
            "游戏4": {
                "项目ID": "p_95jd",
                "发送的奖励": "$$p_95jd.lobby_resource.魂晶.root:999",
                "URL": "https://developer.spark.xd.com/dashboard/p_95jd/firm0_lv_2_4_1"
            }
        }
        self.抽奖数据列表 = {
            "捉妖:钟馗": {
                "魂晶": "$$p_95jd.lobby_resource.魂晶.root",
                "奖品2": "奖励B",
                "奖品3": "奖励C"
            },
            "游戏2": {
                "奖品1": "奖励D",
                "奖品2": "奖励E",
                "奖品3": "奖励F"
            },
            "游戏3": {
                "奖品1": "奖励G",
                "奖品2": "奖励H",
                "奖品3": "奖励I"
            },
            "游戏4": {
                "奖品1": "奖励J",
                "奖品2": "奖励K",
                "奖品3": "奖励L"
            }
           
        }
        # 加载current_token（可能与auth_token不同，用于实际请求）
        self._load_token()

    async def initialize(self):
        """初始化插件，确保数据目录存在及所有JSON文件创建"""
        try:
            # 确保UserData目录存在
            JsonHandler.获取文件路径("test.json", True)
            
            # 检查并创建所有必要的JSON文件
            self._check_and_create_json_files()
            
            # 检查并更新数据保质期
            self._check_and_update_date()
            
            # 启动定时任务，每分钟检查一次日期
            self.date_check_task = asyncio.create_task(self._schedule_date_check())
            
            # 启动定时任务，每15分钟刷新一次网页并更新token
            self.refresh_task = asyncio.create_task(self._schedule_web_refresh())
            
            logger.info("SCE星火游戏插件初始化成功")
        except Exception as e:
            logger.error(f"SCE星火游戏插件初始化失败: {e}")
    
    def _check_and_create_json_files(self):
        """检查并创建所有必要的JSON文件"""
        # 需要检查的JSON文件列表
        json_files = [
            "抽奖数据存储.json",
            "数据保质期.json",
            "玩家今天是否签到过.json",
            "玩家提醒设置.json",
            "玩家每日任务数据.json",
            "玩家活跃度数据.json",
            "玩家绑定id数据存储.json",
            "玩家连续签到数据.json",
            "系统token存储.json"
        ]
        
        for file_name in json_files:
            try:
                # 获取文件路径
                file_path = JsonHandler.获取文件路径(file_name, True)
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    # 如果文件不存在，创建空的JSON文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    logger.info(f"已创建新的JSON文件: {file_name}")
                else:
                    # 确保文件内容是有效的JSON
                    try:
                        data = JsonHandler.读取Json字典(file_name)
                        if data is None:
                            # 如果读取失败，重写为空JSON
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump({}, f, ensure_ascii=False, indent=2)
                            logger.warning(f"已修复损坏的JSON文件: {file_name}")
                    except Exception as e:
                        logger.error(f"检查JSON文件内容失败 {file_name}: {e}")
            except Exception as e:
                logger.error(f"处理JSON文件 {file_name} 时出错: {e}")
    
    def _parse_token_expiry(self, token):
        """解析JWT token中的过期时间"""
        try:
            # JWT token通常分为三部分，第二部分包含payload
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # 解码base64的payload部分
            import base64
            payload = parts[1]
            # 确保padding正确
            payload += '=' * ((4 - len(payload) % 4) % 4)
            decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
            payload_data = json.loads(decoded)
            
            # 获取过期时间戳
            if 'exp' in payload_data:
                exp_time = datetime.datetime.fromtimestamp(payload_data['exp'])
                return exp_time
            return None
        except Exception as e:
            logger.error(f"解析token过期时间失败: {e}")
            return None
    
    def _is_token_valid(self, token):
        """验证token是否有效"""
        if not token:
            return False
            
        # 检查token格式
        if len(token) < 30 or '.' not in token:
            logger.warning(f"无效的token格式: 长度不足或缺少分隔符")
            return False
            
        # 检查过期时间
        expiry = self._parse_token_expiry(token)
        if expiry:
            time_until_expiry = expiry - datetime.datetime.now()
            if time_until_expiry.total_seconds() < 0:
                logger.warning(f"token已过期: {expiry}")
                return False
            elif time_until_expiry.total_seconds() < 300:  # 5分钟内过期
                logger.info(f"token将在5分钟内过期: {expiry}")
        
        return True
    
    def _load_token(self):
        """从文件加载token"""
        try:
            token_data = Json.读取Json字典(self.token_file)
            token = token_data.get("token", self.auth_token)
            
            # 验证token有效性
            if self._is_token_valid(token):
                self.current_token = token
                logger.info(f"已加载有效token，长度: {len(token)} 字符")
                
                # 检查过期时间并提前刷新
                expiry = self._parse_token_expiry(token)
                if expiry:
                    time_until_expiry = expiry - datetime.datetime.now()
                    # 首先检查token是否已过期（防止解析时已过期但_is_token_valid检查通过的情况）
                    if time_until_expiry.total_seconds() < 0:
                        logger.warning(f"token已过期，过期时间: {expiry}，已过期时间: {-time_until_expiry}")
                        # 即使_is_token_valid通过，发现已过期也应该立即刷新
                        self._refresh_all_games()
                    else:
                        logger.info(f"token过期时间: {expiry}，剩余时间: {time_until_expiry}")
                        # 如果token将在30分钟内过期，记录警告
                        if time_until_expiry.total_seconds() < 1800:
                            logger.warning(f"token将在30分钟内过期，建议尽快刷新")
                        # 使用asyncio.create_task异步执行刷新操作
                        import asyncio
                        asyncio.create_task(self._refresh_all_games())
            else:
                logger.warning(f"加载的token无效，使用默认token")
                self.current_token = self.auth_token
        except Exception as e:
            logger.error(f"加载token失败: {e}")
            self.current_token = self.auth_token  # 使用默认token
    
    def _save_token(self, token):
        """保存token到文件，包含有效性验证"""
        # 首先验证token有效性
        if not self._is_token_valid(token):
            logger.error(f"尝试保存无效token，放弃保存")
            return False
            
        # 尝试保存token，增加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
            # 一次性读取并更新整个文件，减少文件操作次数
                token_data = Json.读取Json字典(self.token_file)
                token_data["token"] = token
                token_data["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
                # 解析并保存过期时间
                expiry = self._parse_token_expiry(token)
                if expiry:
                    token_data["expiry"] = expiry.strftime("%Y-%m-%d %H:%M:%S")
            
                # 写入文件
                # 使用JSON文件存储token数据
                JsonHandler.写入Json字典(self.token_file, token_data)
                
                # 更新当前token
                self.current_token = token
                logger.info(f"已保存新token，长度: {len(token)} 字符，后10位: {token[-10:]}，尝试次数: {attempt + 1}")
                return True

            except Exception as e:
                logger.error(f"保存token失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 等待一段时间后重试
                    time.sleep(1)
                else:
                    logger.error(f"保存token达到最大重试次数，保存失败")
            
        return False
    
    async def _check_token_expiry(self):
        """检查token是否即将过期，如果是则提前刷新"""
        try:
            # 先加载最新token
            self._load_token()
            
            # 解析token过期时间
            expiry = self._parse_token_expiry(self.current_token)
            if expiry:
                time_until_expiry = expiry - datetime.datetime.now()
                # 检查token是否已过期
                if time_until_expiry.total_seconds() < 0:
                    logger.warning(f"token已过期，过期时间: {expiry}，已过期时间: {-time_until_expiry}")
                    await self._refresh_all_games()
                    return True
                # 如果token将在10分钟内过期，立即刷新
                elif time_until_expiry.total_seconds() < 600:
                    logger.warning(f"token将在10分钟内过期，立即刷新")
                    await self._refresh_all_games()
                    return True
                else:
                    logger.info(f"token状态正常，剩余有效期: {time_until_expiry}")
            return False
        except Exception as e:
            logger.error(f"检查token过期时间失败: {e}")
            return False
    
    async def _schedule_web_refresh(self):
        """定时任务：固定时间刷新游戏网页并更新token"""
        logger.info("启动网页刷新定时任务，包含固定时间刷新和token过期检查")
        
        # 定义刷新间隔（秒）
        refresh_interval = 15 * 60  # 15分钟
        check_interval = 5 * 60     # 5分钟检查一次token过期
        last_refresh_time = datetime.datetime.now()
        last_check_time = datetime.datetime.now()
        
        try:
            while True:
                current_time = datetime.datetime.now()
                
                # 检查是否需要刷新所有游戏（每15分钟）
                if (current_time - last_refresh_time).total_seconds() >= refresh_interval:
                    logger.info(f"到达固定刷新时间，距离上次刷新: {(current_time - last_refresh_time).total_seconds():.2f}秒")
                    try:
                        await self._refresh_all_games()
                        last_refresh_time = current_time
                    except Exception as e:
                        logger.error(f"定时刷新网页时出错: {e}")
                        import traceback
                        logger.error(f"异常堆栈: {traceback.format_exc()}")
                
                # 检查token是否即将过期（每5分钟）
                if (current_time - last_check_time).total_seconds() >= check_interval:
                    await self._check_token_expiry()
                    last_check_time = current_time
                
                # 短暂休眠，避免CPU占用过高
                await asyncio.sleep(60)  # 每分钟检查一次
                
        except asyncio.CancelledError:
            logger.info("网页刷新任务已取消")
        except KeyboardInterrupt:
            logger.info("收到键盘中断，停止网页刷新任务")
        except Exception as e:
            logger.error(f"网页刷新定时任务异常: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            # 发生异常后等待一段时间再尝试恢复
            await asyncio.sleep(60)
            # 尝试重新启动任务
            logger.info("尝试重新启动网页刷新任务")
            asyncio.create_task(self._schedule_web_refresh())
    
    async def _simulate_browser_refresh(self, game_name, url, session):
        """模拟真实浏览器行为刷新游戏网页，增强token管理"""
        # 导入所需模块
        import time
        from urllib.parse import urlparse, parse_qs
        max_retries = 5  # 增加重试次数
        base_delay = 5  # 增加基础延迟时间
        
        # 更真实的浏览器headers，根据抓包数据更新
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'TE': 'trailers'
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"模拟浏览器刷新游戏: {game_name}, URL: {url}, 尝试 {attempt + 1}/{max_retries}")
                
                # 重置session的headers，确保使用最新的headers
                session.headers.clear()
                session.headers.update(headers)
                
                # 添加引用站点，更接近浏览器行为
                parsed_url = urlparse(url)
                session.headers.update({'Referer': f"https://{parsed_url.netloc}/"})
                
                # 更全面的token传递方式
                if self.current_token:
                    # 通过多种方式传递token以增加成功率
                    session.cookies.set('token', self.current_token, path='/', domain=parsed_url.netloc)
                    session.headers.update({'Authorization': f'Bearer {self.current_token}'})
                    session.headers.update({'X-Token': self.current_token})
                    logger.debug(f"已设置token: {self.current_token[:20]}...{self.current_token[-10:]}")
                
                # 特殊处理：如果是主要网站，尝试访问主页
                main_site_url = "https://developer.spark.xd.com/"
                if urlparse(url).netloc == urlparse(main_site_url).netloc:
                    try:
                        logger.info(f"访问主站: {main_site_url}")
                        main_response = session.get(main_site_url, headers=session.headers, timeout=30, allow_redirects=True)
                        logger.info(f"主站访问状态码: {main_response.status_code}")
                        
                        # 检查主站响应中是否有token
                        main_token = None
                        if 'token' in main_response.cookies:
                            main_token = main_response.cookies['token']
                            logger.info(f"从主站获取到新token，长度: {len(main_token)}")
                            return True, main_token
                    except Exception as e:
                        logger.warning(f"访问主站失败: {e}")
                
                # 1. 首先发送一个预检OPTIONS请求
                try:
                    options_response = session.options(url, timeout=15)
                    logger.debug(f"预检请求成功，状态码: {options_response.status_code}")
                    # 复制预检请求的cookies到主请求
                    for cookie in options_response.cookies:
                        session.cookies.set(cookie.name, cookie.value)
                except Exception as e:
                    logger.debug(f"预检请求失败: {e}，继续主请求")
                
                # 2. 发送主GET请求模拟网页刷新
                response = session.get(url, headers=session.headers, timeout=30, allow_redirects=True)
                
                logger.info(f"游戏{game_name}刷新状态码: {response.status_code}")
                
                # 详细记录响应信息用于调试
                logger.debug(f"响应头: {dict(response.headers)}")
                logger.debug(f"响应cookies: {dict(response.cookies)}")
                
                # 检查是否有新token
                new_token = None
                
                # 1. 从响应cookies中获取token
                if 'token' in response.cookies:
                    new_token = response.cookies['token']
                # 2. 从响应头中获取token
                elif 'Authorization' in response.headers:
                    auth_header = response.headers['Authorization']
                    if auth_header.startswith('Bearer '):
                        new_token = auth_header[7:]
                # 3. 从响应头的X-Token中获取
                elif 'X-Token' in response.headers:
                    new_token = response.headers['X-Token']
                
                # 特殊处理：尝试从重定向链中获取token
                if not new_token and response.history:
                    for hist_response in response.history:
                        if 'token' in hist_response.cookies:
                            new_token = hist_response.cookies['token']
                            logger.info(f"从历史重定向响应中获取到token")
                            break
                
                # 如果找到新token且有效，返回
                if new_token and new_token != self.current_token and len(new_token) > 50:  # 简单验证token长度
                    logger.info(f"发现新token，游戏: {game_name}, 长度: {len(new_token)}, 后10位: {new_token[-10:]}")
                    return True, new_token
                
                # 特殊处理400错误
                if response.status_code == 400:
                    logger.warning(f"游戏{game_name}返回400错误，可能是参数问题，尝试添加额外参数")
                    # 添加一些常见的查询参数
                    params = {'_t': int(time.time()), 'refresh': 'true'}
                    try:
                        response = session.get(url, headers=session.headers, params=params, timeout=30)
                        logger.info(f"带参数的刷新请求状态码: {response.status_code}")
                        
                        # 再次检查token
                        if 'token' in response.cookies:
                            param_token = response.cookies['token']
                            if param_token and param_token != self.current_token:
                                logger.info(f"从带参数请求中获取到新token")
                                return True, param_token
                        
                        if response.status_code == 200:
                            return True, new_token
                    except Exception as e:
                        logger.error(f"带参数刷新失败: {e}")
                
                # 特殊处理OAuth回调流程（根据抓包数据）
                if 'auth/callback' in url:
                    logger.info(f"处理OAuth回调URL: {url}")
                    # 提取code和state参数
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    if 'code' in query_params and 'state' in query_params:
                        logger.info(f"发现OAuth回调参数，code: {query_params['code'][0][:10]}..., state: {query_params['state'][0]}")
                        # 尝试使用回调参数获取token
                        callback_url = f"https://{parsed.netloc}/api/auth/exchange?code={query_params['code'][0]}&state={query_params['state'][0]}"
                        try:
                            exchange_response = session.get(callback_url, headers=session.headers, timeout=30)
                            logger.info(f"Token交换请求状态码: {exchange_response.status_code}")
                            
                            # 检查交换响应中的token
                            if 'token' in exchange_response.cookies:
                                exchange_token = exchange_response.cookies['token']
                                logger.info(f"从OAuth交换获取到新token")
                                return True, exchange_token
                        except Exception as e:
                            logger.warning(f"Token交换失败: {e}")
                
                # 检查响应是否表示成功
                if 200 <= response.status_code < 300:
                    # 即使没有新token，也视为成功
                    logger.info(f"游戏{game_name}刷新成功")
                    return True, None
                
                # 特殊处理认证错误
                if response.status_code in [401, 403]:
                    logger.warning(f"游戏{game_name}返回认证错误({response.status_code})，token可能已过期")
                    # 尝试清除cookie后再次请求
                    try:
                        session.cookies.clear()
                        if self.current_token:
                            session.cookies.set('token', self.current_token)
                        response = session.get(url, headers=session.headers, timeout=30)
                        logger.info(f"清除cookie后重试状态码: {response.status_code}")
                        
                        # 再次检查token
                        if 'token' in response.cookies:
                            retry_token = response.cookies['token']
                            if retry_token and retry_token != self.current_token:
                                logger.info(f"从重试请求中获取到新token")
                                return True, retry_token
                                
                        return response.status_code == 200, None
                    except Exception as e:
                        logger.error(f"清除cookie后重试失败: {e}")
                
            except requests.Timeout:
                logger.error(f"刷新游戏{game_name}超时 (尝试 {attempt + 1}/{max_retries})")
            except requests.ConnectionError:
                logger.error(f"刷新游戏{game_name}连接错误 (尝试 {attempt + 1}/{max_retries})")
                # 连接错误时重置session
                session = requests.Session()
            except requests.HTTPError as e:
                logger.error(f"刷新游戏{game_name}HTTP错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logger.error(f"刷新游戏{game_name}失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                import traceback
                logger.debug(f"异常堆栈: {traceback.format_exc()}")
            
            # 指数退避策略
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 指数增长
                jitter = random.uniform(0, 1)  # 添加随机抖动避免同步请求
                actual_delay = delay + jitter
                logger.info(f"等待 {actual_delay:.2f} 秒后重试游戏 {game_name}")
                await asyncio.sleep(actual_delay)
        
        return False, None
    
    async def _refresh_all_games(self):
        """刷新所有游戏的网页并更新token，带增强的错误处理和浏览器模拟"""
        logger.info(f"开始刷新所有游戏网页，共{len(self.game_configs)}个游戏")
        
        # 初始化变量
        success_count = 0  # 初始化成功计数
        failure_count = 0  # 初始化失败计数
        new_token = None  # 初始化新token变量
        final_token = None  # 初始化最终token变量
        
        # 检查是否有游戏配置
        if not self.game_configs:
            logger.warning("没有找到游戏配置，跳过刷新")
            return {"success": False, "message": "没有找到游戏配置"}
        
        # 对游戏配置进行随机排序，避免总是从同一个游戏开始
        sorted_games = sorted(self.game_configs.items(), key=lambda x: random.random())
        
        for game_name, config in sorted_games:
            url = config.get("URL")
            if not url:
                logger.warning(f"游戏 {game_name} 没有配置URL，跳过刷新")
                continue
            
            # 为每个游戏创建独立的session，更接近真实浏览器行为
            session = requests.Session()
            logger.info(f"开始刷新游戏: {game_name}，URL: {url}")
            
            try:
                # 使用新的浏览器模拟刷新方法
                success, game_token = await self._simulate_browser_refresh(game_name, url, session)
                
                if success:
                    success_count += 1
                    logger.info(f"游戏 {game_name} 刷新成功")
                    
                    # 如果获取到新token，更新相关变量
                    if game_token:
                        logger.info(f"从游戏 {game_name} 获取到新token")
                        new_token = game_token
                        final_token = game_token
                        # 立即保存新token
                        self.current_token = final_token
                        logger.info(f"从游戏 {game_name} 获取到新token，后10位: {final_token[-10:]}")
                        self._save_token(final_token)
                        # 获取到token后可以提前退出
                        break
                else:
                    failure_count += 1
                    logger.warning(f"游戏 {game_name} 刷新失败")
                
                # 随机延迟，模拟真实用户行为
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                failure_count += 1
                logger.error(f"刷新游戏 {game_name} 时发生异常: {e}")
                import traceback
                logger.debug(f"异常堆栈: {traceback.format_exc()}")
                
                # 发生异常后短暂休眠
                await asyncio.sleep(2)
                
                # 继续下一个游戏，不再重复刷新同一个游戏
        
        # 统计信息
        logger.info(f"游戏刷新统计: 成功 {success_count}, 失败 {failure_count}, 总计 {len(self.game_configs)}")
        
        # 如果找到新token，保存它
        if new_token:
            save_success = self._save_token(new_token)
            if save_success:
                logger.info(f"成功保存新token，后10位: {new_token[-10:]}")
                return {
                    "success": True,
                    "token": new_token,
                    "message": "成功刷新并保存新token"
                }
            else:
                logger.error(f"保存新token失败")
                return {
                    "success": False,
                    "message": "找到新token但保存失败"
                }
        else:
            logger.info("未发现新token，继续使用当前token")
            # 即使没有找到新token，如果所有游戏刷新都成功了，也算刷新成功
            if failure_count == 0:
                return {
                    "success": True,
                    "token": self.current_token,
                    "message": "所有游戏刷新成功，但未发现新token"
                }
            else:
                return {
                    "success": False,
                    "message": f"部分游戏刷新失败，成功: {success_count}, 失败: {failure_count}"
                }
           
    async def _schedule_date_check(self):
        """定时任务：每分钟检查一次数据保质期"""
        logger.info("启动每分钟数据保质期检查任务")
        try:
            while True:
                # 每分钟执行一次检查
                await asyncio.sleep(60)
                try:
                    self._check_and_update_date()
                except Exception as e:
                    logger.error(f"定时检查日期时出错: {e}")
        except asyncio.CancelledError:
            logger.info("数据保质期检查任务已取消")
        except Exception as e:
            logger.error(f"定时任务异常: {e}")
    
    def _check_and_update_date(self):
        """检查并更新数据保质期，重置签到状态"""
        try:
            # 获取当前日期的day值
            current_day = str(datetime.datetime.now().day)
            
            # 读取数据保质期
            保质期数据 = Json.读取Json字典("数据保质期.json")
            存储的日期 = Json.获取值(保质期数据, "日期", "")
            
            # 比较日期
            if current_day != 存储的日期:
                logger.info(f"日期变更: 从{存储的日期}更新到{current_day}，重置所有签到状态")
                
                # 更新数据保质期
                Json.添加或更新("数据保质期.json", "日期", current_day)
                
                # 重置所有玩家的签到状态
                签到数据 = Json.读取Json字典("玩家今天是否签到过.json")
                if 签到数据:
                    # 创建新的签到数据字典，所有值设为false
                    新签到数据 = {key: "false" for key in 签到数据.keys()}
                    # 写入文件
                    # 使用JSON文件存储签到数据
                    文件路径 = JsonHandler.获取文件路径("玩家今天是否签到过.json", True)
                    try:
                        with open(文件路径, 'w', encoding='utf-8') as f:
                            json.dump(新签到数据, f, ensure_ascii=False, indent=2)
                        logger.info(f"签到数据已保存到: {文件路径}")
                        logger.info(f"已重置{len(新签到数据)}条签到记录")
                    except Exception as e:
                        logger.error(f"保存签到数据失败: {e}")
                else:
                    # 如果签到数据为空，初始化一个空字典
                    文件路径 = JsonHandler.获取文件路径("玩家今天是否签到过.json", True)
                    try:
                        with open(文件路径, 'w', encoding='utf-8') as f:
                            json.dump({}, f, ensure_ascii=False, indent=2)
                        logger.info(f"初始化签到数据文件: {文件路径}")
                    except Exception as e:
                        logger.error(f"初始化签到数据文件失败: {e}")
        except Exception as e:
            logger.error(f"检查和更新数据保质期时出错: {e}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")

    async def 发送消息(self, event: AstrMessageEvent, 消息内容: str):
        """发送消息封装函数"""
        yield event.plain_result(消息内容)

    async def send_personal_reward_email(self, 认证令牌, 项目ID, 奖励内容, 发送的用户, 邮件标题, 邮件正文, 游戏名称=None):
        """发送个人奖励邮件（适配C#邮件格式）"""
        try:
            # 如果没有提供游戏名称，尝试从游戏配置中获取第一个
            if not 游戏名称 and self.game_configs:
                游戏名称 = list(self.game_configs.keys())[0]
            
            # 获取附件奖励
            attachment = ""
            display_name = "奖励"
            count = 1
            
            # 优先使用传入的奖励内容作为附件
            if 奖励内容 and isinstance(奖励内容, str) and 奖励内容.strip():
                # 检查奖励内容是否已经包含数量信息（格式如：xxx:数字）
                if ":" in 奖励内容:
                    # 确保奖励字符串有正确的$前缀
                    # 三重判断：如果已经有$前缀，保持不变；如果只有一个$前缀，添加一个$；如果没有$前缀，添加两个$
                    if 奖励内容.startswith("$"):
                        # 已经有两个$前缀，保持不变
                        pass
                    elif 奖励内容.startswith("$"):
                        # 只有一个$前缀，添加一个$
                        奖励内容 = "$" + 奖励内容
                    else:
                        # 没有$前缀，添加两个$
                        奖励内容 = "$" + 奖励内容
                    attachment = 奖励内容  # 使用格式化后的完整奖励字符串
                    logger.info(f"使用传入的完整奖励字符串作为附件: '{奖励内容}'")
                    
                    # 解析显示名称和数量用于邮件内容显示
                    try:
                        奖励_id, 数量_str = 奖励内容.split(":", 1)  # 只分割第一个冒号
                        # 移除可能的$前缀以便正确解析
                        奖励_id = 奖励_id.lstrip("$")
                        count = int(数量_str) if 数量_str.isdigit() else 1
                        
                        # 改进的显示名称提取逻辑
                        name_parts = 奖励_id.split(".")
                        display_name = "奖励"
                        for part in name_parts:
                            if any('\u4e00' <= char <= '\u9fff' for char in part):
                                display_name = part
                                break
                        if display_name == "奖励" and name_parts:
                            display_name = name_parts[-1]
                    except Exception as e:
                        logger.warning(f"解析奖励字符串异常（仅影响显示）: {str(e)}")
                else:
                    # 如果没有数量信息，确保有$前缀并默认为1个
                    # 三重判断：如果已经有$前缀，保持不变；如果只有一个$前缀，添加一个$；如果没有$前缀，添加两个$
                    if 奖励内容.startswith("$"):
                        # 已经有两个$前缀，保持不变
                        pass
                    elif 奖励内容.startswith("$"):
                        # 只有一个$前缀，添加一个$
                        奖励内容 = "$" + 奖励内容
                    else:
                        # 没有$前缀，添加两个$
                        奖励内容 = "$" + 奖励内容
                    attachment = 奖励内容
                    logger.info(f"使用传入的奖励ID作为附件: '{奖励内容}'")
            # 如果没有传入有效奖励内容，再尝试从游戏配置获取
            elif 游戏名称 in self.game_configs and "发送的奖励" in self.game_configs[游戏名称]:
                奖励字符串 = self.game_configs[游戏名称]["发送的奖励"]
                # 确保奖励字符串有正确的$前缀
                # 三重判断：如果已经有$前缀，保持不变；如果只有一个$前缀，添加一个$；如果没有$前缀，添加两个$
                if 奖励字符串.startswith("$"):
                    # 已经有两个$前缀，保持不变
                    pass
                elif 奖励字符串.startswith("$"):
                    # 只有一个$前缀，添加一个$
                    奖励字符串 = "$" + 奖励字符串
                else:
                    # 没有$前缀，添加两个$
                    奖励字符串 = "$" + 奖励字符串
                logger.info(f"从游戏配置获取的奖励字符串: '{奖励字符串}'")
                attachment = 奖励字符串
                
                # 解析显示名称和数量
                if ":" in 奖励字符串:
                    try:
                        奖励_id, 数量_str = 奖励字符串.split(":", 1)
                        count = int(数量_str) if 数量_str.isdigit() else 1
                        
                        name_parts = 奖励_id.split(".")
                        display_name = "奖励"
                        for part in name_parts:
                            if any('\u4e00' <= char <= '\u9fff' for char in part):
                                display_name = part
                                break
                        if display_name == "奖励" and name_parts:
                            display_name = name_parts[-1]
                    except Exception as e:
                        logger.warning(f"解析游戏配置中的奖励字符串异常: {str(e)}")
            
            # 更新邮件正文，包含奖励信息
            if display_name and count:
                # 如果邮件正文中没有包含奖励信息，则添加
                if f"{display_name} x{count}" not in 邮件正文:
                    邮件正文 = f"{邮件正文}\n\n获得奖励：{display_name} x{count}"
            
            # 先验证current_token是否有效
            token_to_use = self.current_token or 认证令牌
            if not token_to_use or len(token_to_use) < 10:  # 简单的长度验证
                print("[邮件] 警告: 当前token可能无效，尝试使用默认token")
                token_to_use = self.auth_token
            
            print(f"[邮件] 准备发送邮件 - 用户ID: {发送的用户}, 项目ID: {项目ID}")
            print(f"[邮件] 使用的token长度: {len(token_to_use)} 字符")
            print(f"[邮件] 邮件标题: {邮件标题}, 附件: {attachment}")
            
            # 创建邮件服务并发送邮件（增加重试设置）
            email_service = EmailService(
                auth_token=token_to_use,
                project_id=项目ID,
                max_retries=3
            )
            print("[邮件] 开始调用邮件服务发送邮件...")
            result = await email_service.quick_send(邮件标题, 邮件正文, 发送的用户, attachment=attachment)
            print(f"[邮件] 邮件服务返回结果: {result}")
            
            # 检查是否是token相关错误或400错误
            message = result.get('message', '')
            status_code = result.get('status_code')
            
            # 检测token错误或400/401/403错误
            if not result.get('success'):
                error_detected = False
                
                # 检测400错误（请求参数问题）
                if status_code == 400 or (message and '400' in message):
                    logger.warning(f"检测到400 Bad Request错误，可能是请求参数问题，尤其是用户ID格式")
                    logger.warning(f"详细错误信息: {message}")
                    logger.warning(f"目标用户ID: {发送的用户}")
                    error_detected = True
                # 检测token相关错误
                elif (message and ('token' in message.lower() or '认证' in message or any(code in message for code in ['401', '403']))) or status_code in [401, 403]:
                    logger.warning(f"检测到邮件发送错误: {message or status_code}，尝试刷新token")
                    error_detected = True
                
                if error_detected:
                
                    # 立即尝试刷新token（使用新的浏览器模拟方法）
                    refresh_result = await self._refresh_all_games()
                
                # 如果刷新成功且有新token
                if refresh_result and (refresh_result.get("success") or isinstance(refresh_result, str)):
                    # 获取新token
                    new_token = refresh_result.get("token") if isinstance(refresh_result, dict) else refresh_result
                    
                    if new_token and (isinstance(new_token, str) and len(new_token) > 50):
                        logger.info(f"token刷新成功，新token长度: {len(new_token)}")
                        
                        # 使用新token创建新的邮件服务实例并重新发送
                        logger.info("使用新token重新尝试发送邮件")
                        new_email_service = EmailService(
                            auth_token=new_token,
                            project_id=项目ID,
                            max_retries=2
                        )
                        # 重新发送邮件
                        retry_result = await new_email_service.quick_send(邮件标题, 邮件正文, 发送的用户, attachment=attachment)
                        
                        if retry_result.get('success'):
                            logger.info("使用新token重新发送邮件成功")
                            return True
                        else:
                            logger.error(f"使用新token重新发送邮件失败: {retry_result.get('message', '未知错误')}")
                            self._log_email_failure(发送的用户, 奖励内容, "使用新token重试失败: " + retry_result.get('message', '未知错误'))
                    else:
                        logger.warning("刷新后获取的token无效或为空")
                else:
                    logger.error(f"token刷新失败或无返回值")
                    self._log_email_failure(发送的用户, 奖励内容, "Token刷新失败或无返回值")
                    # 使用新token重新发送邮件
                    return False
            
            # 检查结果是否成功
            if result.get('success'):
                print(f"[邮件] ✅ 奖励邮件发送成功: {发送的用户}")
                logger.info(f"奖励邮件发送成功: {发送的用户}")
                return True
            else:
                # 获取错误信息，特别处理不同类型的错误
                error_msg = result.get('message')
                status_code = result.get('status_code')
                detailed_error = error_msg
                print(f"[邮件] ❌ 奖励邮件发送失败: {发送的用户}, 状态码: {status_code}, 错误信息: {error_msg}")
                
                # 如果是NO_ROW_ID错误，收集更详细的错误信息
                if result.get('error_code') == 'NO_ROW_ID':
                    response_structure = result.get('response_structure', [])
                    raw_response_preview = result.get('raw_response_preview', '')
                    detailed_error = f"{error_msg}，响应结构: {response_structure}"
                    if raw_response_preview:
                        detailed_error += f"，原始响应预览: {raw_response_preview}"
                    
                    logger.error(f"邮件行ID提取失败: {detailed_error}")
                
                # 处理触发发送超时的特殊情况
                elif result.get('trigger_timeout'):
                    # 对于触发发送超时，邮件可能已经成功发送，我们记录为警告而非错误
                    warning_msg = f"邮件添加成功，但触发发送超时，邮件可能已发送: {error_msg}"
                    logger.warning(f"奖励邮件发送状态不确定: {发送的用户}, 详情: {warning_msg}")
                    # 这里可以选择返回True，因为邮件可能已经发送成功
                    # 但为了安全起见，我们仍然返回False，但记录为警告而非错误
                    self._log_email_failure(发送的用户, 奖励内容, warning_msg + " (状态不确定)")
                    return False
                
                # 处理邮件已添加但触发发送失败的情况
                elif result.get('email_added'):
                    # 获取更多详细信息
                    error_type = result.get('error_type', 'UNKNOWN')
                    raw_response = result.get('raw_response', '')
                    
                    detailed_error = f"{error_msg}, 错误类型: {error_type}"
                    if raw_response:
                        # 只记录部分原始响应以避免日志过大
                        response_preview = raw_response[:200] + '...' if len(raw_response) > 200 else raw_response
                        detailed_error += f", 原始响应预览: {response_preview}"
                    
                    logger.error(f"邮件已添加但触发发送失败: {发送的用户}, 详情: {detailed_error}")
                
                logger.error(f"奖励邮件发送失败: {发送的用户}, 原因: {detailed_error}")
                # 记录失败信息
                self._log_email_failure(发送的用户, 奖励内容, detailed_error)
                return False
        except requests.RequestException as e:
            error_msg = f"发送奖励邮件网络异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            self._log_email_failure(发送的用户, 奖励内容, error_msg)
            return False
        except Exception as e:
            error_msg = f"发送奖励邮件异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            self._log_email_failure(发送的用户, 奖励内容, error_msg)
            return False
    
    def _log_email_failure(self, user_id, reward_info, error_msg):
        """
        记录邮件发送失败信息
        
        Args:
            user_id (str): 用户ID
            reward_info (dict): 奖励信息
            error_msg (str): 错误信息
        """
        import os
        import datetime
        
        # 创建失败日志目录
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 日志文件名
        log_file = os.path.join(log_dir, "email_failures.log")
        
        # 构建日志内容
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 用户: {user_id}, 奖励: {reward_info}, 错误: {error_msg}\n"
        
        # 写入日志文件
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"邮件发送失败信息已记录到: {log_file}")
        except Exception as e:
            print(f"记录失败日志异常: {str(e)}")

    @filter.command("签到")
    async def handle_checkin(self, event: AstrMessageEvent):
        """处理签到功能"""
        # 每次签到前检查日期，确保签到状态正确
        self._check_and_update_date()
        
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        
        # 解析游戏名称
        parts = message_str.split(" ")
        if len(parts) > 1:
            游戏名称 = parts[1]
            # 单游戏签到
            async for msg in self.handle_single_checkin(event, author_id, 游戏名称):
                yield msg
        else:
            # 批量签到
            async for msg in self.handle_batch_checkin(event, author_id):
                yield msg

    async def handle_single_checkin(self, event: AstrMessageEvent, author_id, 游戏名称):
        """处理单个游戏签到"""
        # 使用复合键格式: "玩家ID_游戏ID"
        复合键 = f"{author_id}_{游戏名称}"
        
        # 检查是否已签到
        if Json.获取值(Json.读取Json字典("玩家今天是否签到过.json"), 复合键) is None:
            Json.添加或更新("玩家今天是否签到过.json", 复合键, "false")
        
        if Json.获取值(Json.读取Json字典("玩家今天是否签到过.json"), 复合键) != "true":
            # 检查ID绑定
            玩家数据 = Json.读取Json字典("玩家绑定id数据存储.json")
            发送的用户 = Json.获取值(玩家数据, author_id)
            
            if not 发送的用户:
                async for msg in self.发送消息(event, "ID未绑定，请发送\"绑定ID xxx\"进行绑定"):
                    yield msg
                return
            
            # 发送奖励邮件
            # 从游戏配置中获取项目ID和奖励信息
            游戏配置 = self.game_configs.get(游戏名称, {})
            项目ID = 游戏配置.get("项目ID", "mock_project")
            发送的奖励 = {"items": []}
            
            # 解析奖励格式: "$p_95jd.lobby_resource.魂晶.root:999"
            奖励字符串 = 游戏配置.get("发送的奖励", "")
            if 奖励字符串:
                try:
                    # 提取奖励ID和数量
                    奖励_id, 数量 = 奖励字符串.split(":")
                    数量 = int(数量)
                    # 改进的显示名称提取逻辑
                    # 1. 尝试从奖励ID中提取中文字符作为显示名称
                    name_parts = 奖励_id.split(".")
                    display_name = "奖励"
                    for part in name_parts:
                        if any('\u4e00' <= char <= '\u9fff' for char in part):
                            display_name = part
                            break
                    # 2. 如果没有找到中文字符，回退到使用最后一部分
                    if display_name == "奖励" and name_parts:
                        display_name = name_parts[-1]
                    发送的奖励["items"].append(f"{display_name}*{数量}")
                except:
                    # 如果解析失败，使用默认奖励
                    发送的奖励["items"] = ["签到奖励"]
            else:
                发送的奖励["items"] = ["签到奖励"]
                
            邮件标题 = "签到奖励"
            邮件正文 = f"恭喜您在{游戏名称}签到成功！"

            # 先更新签到状态，确保用户签到成功
            Json.添加或更新("玩家今天是否签到过.json", 复合键, "true")
            print(f"[签到] 用户{author_id}在{游戏名称}的签到状态已更新")
            
            # 发送奖励邮件
            邮件返回值 = await self.send_personal_reward_email(self.auth_token, 项目ID, 发送的奖励, 发送的用户, 邮件标题, 邮件正文, 游戏名称)
            print(f"[签到] 邮件发送结果: {邮件返回值}")
            
            # 无论邮件是否发送成功，都处理连续签到并显示签到成功消息
            # 处理连续签到
            async for msg in self.handle_continuous_checkin(event, author_id, 游戏名称):
                yield msg
            
            # 如果邮件发送失败，添加提示信息
            if not 邮件返回值:
                print(f"[签到] 警告: 邮件发送失败，但签到已记录")
                async for msg in self.发送消息(event, "⚠️ 签到记录已保存，但奖励邮件发送失败，请稍后尝试或联系管理员"):
                    yield msg
        else:
            async for msg in self.发送消息(event, f"您今天已经在{游戏名称}签到过了，请明天再来！"):
                yield msg

    @filter.command("查看游戏列表")
    async def handle_view_games(self, event: AstrMessageEvent):
        """查看签到游戏列表，输出格式为游戏名称+奖励*数量"""
        if not self.game_configs:
            async for msg in self.发送消息(event, "当前没有配置任何签到游戏"):
                yield msg
            return
        
        # 构建游戏列表消息
        游戏列表 = []
        for 游戏名称, 配置 in self.game_configs.items():
            奖励字符串 = 配置.get("发送的奖励", "")
            if 奖励字符串 and ":" in 奖励字符串:
                try:
                    # 解析奖励ID和数量
                    奖励_id, 数量 = 奖励字符串.split(":")
                    # 尝试从奖励ID中提取显示名称
                    name_parts = 奖励_id.split(".")
                    显示名称 = "奖励"
                    for part in name_parts:
                        if any('\u4e00' <= char <= '\u9fff' for char in part):
                            显示名称 = part
                            break
                    # 如果没有找到中文字符，使用最后一部分
                    if 显示名称 == "奖励" and name_parts:
                        显示名称 = name_parts[-1]
                    游戏列表.append(f"{游戏名称}: {显示名称}*{数量}")
                except:
                    游戏列表.append(f"{游戏名称}: 奖励*1")
            else:
                游戏列表.append(f"{游戏名称}: 奖励*1")
        
        # 发送游戏列表
        消息内容 = "签到游戏列表：\n" + "\n".join(游戏列表)
        async for msg in self.发送消息(event, 消息内容):
            yield msg
    
    async def handle_continuous_checkin(self, event: AstrMessageEvent, author_id, 游戏名称):
        """处理连续签到逻辑"""
        签到统计数据 = Json.读取Json字典("玩家连续签到数据.json")
        连续签到复合键 = f"{author_id}_连续签到"
        上次签到日期键 = f"{author_id}_上次签到日期"
        
        当前日期 = datetime.datetime.now().strftime("%Y-%m-%d")
        连续签到天数 = 0
        
        # 获取上次签到日期
        上次签到日期 = Json.获取值(签到统计数据, 上次签到日期键, "")
        
        if not 上次签到日期:
            # 第一次签到
            连续签到天数 = 1
        else:
            try:
                last_date = datetime.datetime.strptime(上次签到日期, "%Y-%m-%d")
                current_date = datetime.datetime.strptime(当前日期, "%Y-%m-%d")
                if (current_date - last_date).days == 1:
                    # 连续签到
                    连续签到天数 = int(Json.获取值(签到统计数据, 连续签到复合键, "0")) + 1
                elif 上次签到日期 == 当前日期:
                    # 同一天签到
                    连续签到天数 = int(Json.获取值(签到统计数据, 连续签到复合键, "0"))
                else:
                    # 中断连续签到
                    连续签到天数 = 1
            except:
                连续签到天数 = 1
        
        # 保存签到数据
        Json.添加或更新("玩家连续签到数据.json", 连续签到复合键, str(连续签到天数))
        Json.添加或更新("玩家连续签到数据.json", 上次签到日期键, 当前日期)
        
        # 计算活跃度奖励
        基础活跃度奖励 = 5
        额外活跃度奖励 = 0
        
        if 连续签到天数 >= 7:
            额外活跃度奖励 = 10
        elif 连续签到天数 >= 3:
            额外活跃度奖励 = 3
        
        总活跃度奖励 = 基础活跃度奖励 + 额外活跃度奖励
        
        # 增加活跃度
        活跃度数据 = Json.读取Json字典("玩家活跃度数据.json")
        当前活跃度 = Json.获取值(活跃度数据, author_id, "0")
        新活跃度 = int(当前活跃度) + 总活跃度奖励
        Json.添加或更新("玩家活跃度数据.json", author_id, str(新活跃度))
        

        # 发送签到成功消息
        # 从奖励内容中提取显示信息
        奖励显示信息 = []
        if 游戏名称 in self.game_configs:

                游戏配置 = self.game_configs[游戏名称]
                奖励字符串 = 游戏配置.get("发送的奖励", "")
                if 奖励字符串:
                    try:
                        # 解析奖励格式
                        奖励_id, 数量 = 奖励字符串.split(":")
                        数量 = int(数量)
                        # 改进的显示名称提取逻辑
                        # 1. 尝试从奖励ID中提取中文字符作为显示名称
                        name_parts = 奖励_id.split(".")
                        display_name = "奖励"
                        for part in name_parts:
                            if any('\u4e00' <= char <= '\u9fff' for char in part):
                                display_name = part
                                break
                        # 2. 如果没有找到中文字符，回退到使用最后一部分
                        if display_name == "奖励" and name_parts:
                            display_name = name_parts[-1]
                        奖励显示信息.append(f"{display_name}*{数量}")
                    except:
                        pass
        奖励显示信息 = "、".join(奖励显示信息) if 奖励显示信息 else "签到奖励"
        消息内容 = f"🔥 签到成功！恭喜您在{游戏名称}获得了奖励！\n"
        消息内容 += f"🎁 获得道具：{奖励显示信息}\n"
        消息内容 += f"💯 基础活跃度奖励：{基础活跃度奖励}点\n"
        
        if 额外活跃度奖励 > 0:
            消息内容 += f"✨ 连续签到{连续签到天数}天额外奖励：{额外活跃度奖励}点\n"
        
        消息内容 += f"🎊 当前连续签到天数：{连续签到天数}天\n"
        消息内容 += f"📈 总活跃度：{新活跃度}点"
        
        async for msg in self.发送消息(event, 消息内容):
            yield msg

    async def handle_batch_checkin(self, event: AstrMessageEvent, author_id):
        """处理批量签到"""
        async for msg in self.发送消息(event, "批量签到功能正在开发中"):
            yield msg

    @filter.command("绑定ID")
    async def handle_bind_id(self, event: AstrMessageEvent):
        """处理ID绑定"""
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        
        parts = message_str.split(" ")
        if len(parts) > 1:
            游戏_id = parts[1]
            Json.添加或更新("玩家绑定id数据存储.json", author_id, 游戏_id)
            async for msg in self.发送消息(event, f"ID绑定成功！您的游戏ID是：{游戏_id}"):
                yield msg
        else:
            async for msg in self.发送消息(event, "请输入正确的格式：绑定ID xxx"):
                yield msg
    
    @filter.command("查看ID")
    async def handle_view_id(self, event: AstrMessageEvent):
        """查看已绑定的ID"""
        author_id = event.get_sender_id()
        
        # 从存储文件中读取绑定的ID
        玩家数据 = Json.读取Json字典("玩家绑定id数据存储.json")
        绑定的_id = Json.获取值(玩家数据, author_id)
        
        if 绑定的_id:
            async for msg in self.发送消息(event, f"您当前绑定的游戏ID是：{绑定的_id}"):
                yield msg
        else:
            async for msg in self.发送消息(event, "您还未绑定游戏ID，请使用'绑定ID xxx'命令进行绑定"):
                yield msg

    async def terminate(self):
        """插件销毁方法"""
        # 取消定时任务
        if hasattr(self, 'date_check_task'):
            self.date_check_task.cancel()
            try:
                await self.date_check_task
            except asyncio.CancelledError:
                pass
        
        # 取消网页刷新任务
        if hasattr(self, 'refresh_task'):
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SCE星火游戏插件已停用")
    
    @filter.command("刷新token")
    async def handle_refresh_token(self, event: AstrMessageEvent):
        """手动刷新所有游戏的token"""
        try:
            async for msg in self.发送消息(event, "正在刷新所有游戏的token，请稍候..."):
                yield msg
            
            # 执行刷新操作
            new_token = await self._refresh_all_games()
            
            if new_token:
                async for msg in self.发送消息(event, "token刷新成功！已更新到最新值"):
                    yield msg
            else:
                async for msg in self.发送消息(event, "token刷新完成，但未发现新token，继续使用当前token"):
                    yield msg
        except Exception as e:
            logger.error(f"手动刷新token失败: {e}")
            async for msg in self.发送消息(event, f"刷新token时出错: {str(e)}"):
                yield msg

    @filter.command("发起抽奖")
    async def 发起抽奖(self, event: AstrMessageEvent):
        """处理发起抽奖功能,需要管理员权限并且在群聊中使用，使用格式：发起抽奖 游戏名称 奖励名称 奖励数量 抽奖人数 开奖时间(分钟)"""
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        # 检查是否在群聊中使用
        if(event.is_private_chat()==True):
            async for msg in self.发送消息(event, "抽奖命令请在群聊中使用。"):
                yield msg
            return
        # 检查是否为管理员
        if(event.is_admin()!=True):
            async for msg in self.发送消息(event, "您没有权限使用此命令。"):
                yield msg
            return
        # 解析抽奖名称
        parts = message_str.split(" ")
        if len(parts) != 6:
            async for msg in self.发送消息(event, "请使用正确的格式：发起抽奖 游戏名称 奖励名称 奖励数量 获奖人数 开奖时间(分钟)"):
                yield msg
            return
        else:
            游戏名称 = parts[1]
            奖励名称 = parts[2]
            奖励数量 = parts[3]
            抽奖人数 = parts[4]
            开奖时间 = parts[5]
            user_name = event.get_sender_name()
            try:
                抽奖人数=int(抽奖人数)
                开奖时间=int(开奖时间)
            except:
                async for msg in self.发送消息(event, "抽奖人数和开奖时间必须为整数，请检查后重新输入。"):
                    yield msg
                return
            # 读取当前抽奖数据
            抽奖数据=JsonHandler.读取Json字典("抽奖数据存储.json")
            当前时间=datetime.datetime.now()
            开奖截止时间=当前时间+datetime.timedelta(minutes=开奖时间)
            抽奖ID=str(int(当前时间.timestamp()))
            抽奖ID=f"{游戏名称}_{抽奖ID}"
            抽奖数据[抽奖ID]={
                "游戏名称":游戏名称,
                "奖励名称":奖励名称,
                "奖励数量":奖励数量,
                "抽奖人数":抽奖人数,
                "发起人":user_name,
                "截止时间":开奖截止时间.strftime("%Y-%m-%d %H:%M:%S"),
                "参与者":[],
                "群聊ID": event.get_group_id()
            }
            # 保存抽奖数据
            # 使用JSON文件存储抽奖数据
            文件路径 = JsonHandler.获取文件路径("抽奖数据存储.json", True)
            try:
                with open(文件路径, 'w', encoding='utf-8') as f:
                    json.dump(抽奖数据, f, ensure_ascii=False, indent=2)
                logger.info(f"抽奖数据已保存到: {文件路径}")
            except Exception as e:
                logger.error(f"保存抽奖数据失败: {e}")

            async for msg in self.发送消息(event, f"🎊 抽奖发起成功！🎊\n\n抽奖ID：{抽奖ID}\n游戏名称：{游戏名称}\n奖励名称：{奖励名称}\n奖励数量：{奖励数量}\n获奖人数：{抽奖人数}\n截止时间：{开奖截止时间.strftime('%Y-%m-%d %H:%M:%S')}\n\n请使用「参与抽奖 {抽奖ID}」命令参与抽奖\n祝您好运！🎉"):
                yield msg

            # 创建并启动一个异步任务来等待开奖
            asyncio.create_task(self.等待开奖(开奖时间, 抽奖ID,event))
    
    async def 等待开奖(self,开奖时间, 抽奖ID,event:AstrMessageEvent):
        """等待开奖"""
        logger.info("开始等待开奖")
        try:
            # 等待指定的开奖时间（分钟转换为秒）
            await asyncio.sleep(60 * 开奖时间)
            try:
                # 由于开奖函数是异步生成器，需要使用async for循环来迭代结果
                async for _ in self.开奖(抽奖ID,event):
                    pass
            except Exception as e:
                logger.error(f"定时开奖出错: {e}")
            except asyncio.CancelledError:
                logger.info("开奖任务已取消")
        except Exception as e:
            logger.error(f"定时任务异常: {e}")

    async def 开奖(self, 抽奖ID,event:AstrMessageEvent):
        抽奖数据=JsonHandler.读取Json字典("抽奖数据存储.json")
        if 抽奖ID not in 抽奖数据:
            return
        数据=抽奖数据[抽奖ID]
        参与者列表=数据['参与者']
        
        # 处理参与人数为0的情况
        if len(参与者列表)==0:
            # 不开奖，直接删除抽奖数据
            del 抽奖数据[抽奖ID]
            文件路径 = JsonHandler.获取文件路径("抽奖数据存储.json", True)
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(抽奖数据, f, ensure_ascii=False, indent=2)
            # 发送未有人参与的消息
            群聊ID=数据.get('群聊ID')
            if 群聊ID:
                try:
                    # 安全地处理事件对象，避免'dict' object has no attribute 'id'错误
                    try:
                        # 直接在平台元数据中设置群聊ID，避免调用可能失败的方法
                        if hasattr(event, 'platform_meta'):
                            if isinstance(event.platform_meta, dict):
                                event.platform_meta['group_id'] = 群聊ID
                        
                        # 尝试设置群聊ID，但使用try-except保护
                        if hasattr(event, 'set_group_id') and callable(event.set_group_id):
                            try:
                                event.set_group_id(群聊ID)
                            except Exception as set_error:
                                logger.warning(f"设置群聊ID时出错但继续: {set_error}")
                                # 不中断，继续尝试发送消息
                    except Exception as e:
                        logger.warning(f"处理事件对象时出错: {e}")
                        # 如果出错，创建新的事件对象
                        event = AstrMessageEvent(
                            message_str='',
                            message_obj=None,
                            platform_meta={'group_id': 群聊ID},  # 直接设置群聊ID
                            session_id=f'lottery_{抽奖ID}'
                        )
                    
                    游戏名称 = 数据.get('游戏名称', '未知游戏')
                    消息内容=f"📢 抽奖结果通知 📢\n\n✨ 抽奖ID：{抽奖ID}\n🎮 游戏名称：{游戏名称}\n\n很遗憾，本次抽奖活动无人参与，活动已自动取消。"
                    async for msg in self.发送消息(event, 消息内容):
                        yield msg
                except Exception as e:
                    logger.error(f"发送无人参与消息时出错: {e}")
            return
        
        # 处理参与人数大于0的情况
        设定获奖人数 = 数据['抽奖人数']
        if len(参与者列表) <= 设定获奖人数:
            # 参与人数小于等于获奖人数，全员获奖
            获奖者 = 参与者列表.copy()
            实际获奖人数 = len(获奖者)
        else:
            # 参与人数大于获奖人数，随机抽取
            获奖者 = random.sample(参与者列表, 设定获奖人数)
            实际获奖人数 = 设定获奖人数

        #发送获奖消息
        # 使用get方法安全访问字典键
        游戏名称 = 数据.get('游戏名称', '未知游戏')
        奖励名称 = 数据.get('奖励名称', '未知奖励')
        奖励数量 = 数据.get('奖励数量', '未知数量')
        消息内容=f"🎊 抽奖活动已结束！ 🎊\n\n✨ 抽奖ID：{抽奖ID}\n🎮 游戏名称：{游戏名称}\n🏆 奖励名称：{奖励名称}\n💎 奖励数量：{奖励数量}\n👥 获奖人数：{实际获奖人数}\n\n🎉 获奖者名单：\n{', '.join(获奖者)}\n\n恭喜以上获奖者！🎊"
        #假设有一个群聊ID存储在数据中
        群聊ID=数据.get('群聊ID')
        if 群聊ID:
            # 使用传入的event对象，并设置群聊ID
            try:
                # 安全地处理事件对象，避免'dict' object has no attribute 'id'错误
                try:
                    # 直接在平台元数据中设置群聊ID，避免调用可能失败的方法
                    if hasattr(event, 'platform_meta'):
                        if isinstance(event.platform_meta, dict):
                            event.platform_meta['group_id'] = 群聊ID
                    
                    # 尝试设置群聊ID，但使用try-except保护
                    if hasattr(event, 'set_group_id') and callable(event.set_group_id):
                        try:
                            event.set_group_id(群聊ID)
                        except Exception as set_error:
                            logger.warning(f"设置群聊ID时出错但继续: {set_error}")
                            # 不中断，继续尝试发送消息
                except Exception as e:
                    logger.warning(f"处理事件对象时出错: {e}")
                    # 如果出错，创建新的事件对象
                    event = AstrMessageEvent(
                        message_str='',
                        message_obj=None,
                        platform_meta={'group_id': 群聊ID},  # 直接设置群聊ID
                        session_id=f'lottery_{抽奖ID}'
                    )
                async for msg in self.发送消息(event, 消息内容):
                    yield msg
            except Exception as e:
                logger.error(f"发送获奖消息时出错: {e}")
                # 尝试使用全新的事件对象作为最后的备用方案
                try:
                    # 创建更安全的备份事件对象
                    backup_event = AstrMessageEvent(
                        message_str='',
                        message_obj=None,
                        platform_meta={'group_id': 群聊ID},  # 直接在平台元数据中设置群聊ID
                        session_id=f'lottery_backup_{抽奖ID}'
                    )
                    
                    # 避免直接调用set_group_id，改为使用更安全的方式
                    # 尝试发送消息，不依赖set_group_id方法
                    try:
                        async for msg in self.发送消息(backup_event, 消息内容):
                            yield msg
                    except Exception as msg_error:
                        logger.error(f"发送备份消息时出错: {msg_error}")
                        # 最后尝试不使用事件对象发送消息
                        logger.warning("尝试直接发送消息，不依赖事件对象")
                except Exception as backup_error:
                    logger.error(f"备用方案也失败: {backup_error}")

        # 安全获取项目ID和奖励字符串
        项目ID = self.game_configs.get(数据.get('游戏名称', ''), {}).get('项目ID', '')

        # 安全获取奖励字符串，避免'发送的奖励'键不存在的错误
        游戏名称 = 数据.get('游戏名称', '')
        奖励数量 = 数据.get('奖励数量', 1)
        
        # 优化奖励字符串构建：优先从抽奖数据列表中根据奖励名称获取对应的ID
        奖励基础字符串 = ""
        奖励名称 = 数据.get('奖励名称', '')
        
        # 首先从抽奖数据列表获取对应游戏和奖励名称的ID
        if hasattr(self, '抽奖数据列表') and isinstance(self.抽奖数据列表, dict):
            游戏配置 = self.抽奖数据列表.get(游戏名称, {})
            if 游戏配置 and 奖励名称 in 游戏配置:
                奖励基础字符串 = 游戏配置[奖励名称]
        
        # 正确构建奖励字符串，确保格式为"$$p_95jd.lobby_resource.魂晶.root:999"（根据实际数量）
        # 确保奖励基础字符串有正确的$$前缀
        if 奖励基础字符串:
             # 检查前缀情况并添加正确的$$前缀
            if 奖励基础字符串.startswith("$"):
                # 已经有两个$前缀，保持不变
                pass
            elif 奖励基础字符串.startswith("$"):
                # 已有一个$前缀，添加一个$
                奖励基础字符串 = "$" + 奖励基础字符串
            else:
                # 没有$前缀，添加两个$
                奖励基础字符串 = "$" + 奖励基础字符串
        奖励字符串 = f"{奖励基础字符串}:{奖励数量}" if 奖励基础字符串 else ""

        for 获奖者ID in 获奖者:
            #发送奖励邮件
            # 修复Json类调用错误，使用正确的JsonHandler类
            玩家数据 = JsonHandler.读取Json字典("玩家绑定id数据存储.json")
            发送的用户 = JsonHandler.获取值(玩家数据, 获奖者ID)
            if not 发送的用户:
                logger.warning(f"未找到获奖者{获奖者ID}的绑定信息，跳过发送奖励")
                continue
            
            发送的奖励 = {"items": []}
            if 奖励字符串:
                try:
                    # 提取奖励ID和数量
                    奖励_id, 数量 = 奖励字符串.split(":")
                    数量 = int(数量)
                    # 改进的显示名称提取逻辑
                    # 1. 尝试从奖励ID中提取中文字符作为显示名称
                    name_parts = 奖励_id.split(".")
                    display_name = "奖励"
                    for part in name_parts:
                        if any('\u4e00' <= char <= '\u9fff' for char in part):
                            display_name = part
                            break
                    # 2. 如果没有找到中文字符，回退到使用最后一部分
                    if display_name == "奖励" and name_parts:
                        display_name = name_parts[-1]
                    发送的奖励["items"].append(f"{display_name}*{数量}")
                except:
                    发送的奖励["items"] = ["抽奖奖励"]
            else:
                发送的奖励["items"] = ["抽奖奖励"]
            邮件标题 = "抽奖奖励"
            游戏名称 = 数据.get('游戏名称', '未知游戏')
            邮件正文 = f"恭喜您在{游戏名称}的抽奖活动中获奖！"
            # 检查send_personal_reward_email是否返回异步生成器
            try:
                logger.info(f"准备发送邮件给用户 {发送的用户}，奖励: {奖励字符串}")
                result = self.send_personal_reward_email(self.auth_token, 项目ID, 奖励字符串, 发送的用户, 邮件标题, 邮件正文, 数据.get('游戏名称', '未知游戏'))
                # 检查返回值是否是协程或异步生成器
                if hasattr(result, '__await__'):
                    # 是协程，直接await
                    await result
                    logger.info(f"邮件发送完成给用户 {发送的用户}")
                elif hasattr(result, '__aiter__'):
                    # 是异步生成器，使用async for
                    async for _ in result:
                        pass
                else:
                    # 是普通值，直接忽略
                    pass
            except Exception as email_error:
                logger.error(f"发送奖励邮件时出错: {email_error}")
        #删除抽奖数据
        del 抽奖数据[抽奖ID]
        文件路径 = JsonHandler.获取文件路径("抽奖数据存储.json", True)
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(抽奖数据, f, ensure_ascii=False, indent=2)

    @filter.command("查看游戏抽奖")
    async def 查询游戏抽奖(self, event: AstrMessageEvent):
        """处理查看指定游戏的抽奖活动，格式为：查看游戏抽奖 游戏名称"""
        message_str = event.message_str.strip()
        parts = message_str.split(" ")
        
        # 检查参数格式
        if len(parts) != 2:
            async for msg in self.发送消息(event, "📝 使用说明 📝\n\n查看指定游戏的抽奖活动：查看游戏抽奖 游戏名称"):
                yield msg
            return
        
        游戏名称 = parts[1]
        抽奖数据 = JsonHandler.读取Json字典("抽奖数据存储.json")
        
        # 筛选该游戏的所有抽奖
        游戏抽奖列表 = []
        for 抽奖ID, 数据 in 抽奖数据.items():
            if 数据.get('游戏名称') == 游戏名称:
                游戏抽奖列表.append((抽奖ID, 数据))
        
        # 处理没有找到该游戏抽奖的情况
        if not 游戏抽奖列表:
            async for msg in self.发送消息(event, f"📢 通知 📢\n\n未找到与「{游戏名称}」相关的抽奖活动\n请检查游戏名称是否正确"):
                yield msg
            return
        
        # 构建消息内容
        消息内容 = f"🎮 「{游戏名称}」的抽奖活动列表 🎮\n\n"
        for 抽奖ID, 数据 in 游戏抽奖列表:
            # 使用get方法安全访问字典键，提供默认值
            奖励名称 = 数据.get('奖励名称', '未知奖励')
            奖励数量 = 数据.get('奖励数量', '未知数量')
            获奖人数 = 数据.get('抽奖人数', '0')
            截止时间 = 数据.get('截止时间', '未知时间')
            参与者列表 = 数据.get('参与者', [])
            参与人数 = len(参与者列表)
            消息内容 += f"📌 抽奖详情 📌\n抽奖ID：{抽奖ID}\n奖励名称：{奖励名称}\n奖励数量：{奖励数量}\n获奖人数：{获奖人数}\n截止时间：{截止时间}\n参与人数：{参与人数}\n\n------------------------------\n"
        
        # 发送消息
        async for msg in self.发送消息(event, 消息内容):
            yield msg

    @filter.command("查看抽奖")
    async def 查看抽奖(self, event: AstrMessageEvent):
        """处理查看已发起的抽奖，如果不指定就是查看所有的抽奖,格式为：查看抽奖 抽奖ID"""
        message_str = event.message_str.strip()
        parts = message_str.split(" ")
        抽奖数据=JsonHandler.读取Json字典("抽奖数据存储.json")
        if len(parts)==1:
            #查看所有抽奖
            if len(抽奖数据)==0:
                async for msg in self.发送消息(event, "📢 通知 📢\n\n当前没有任何抽奖活动\n请稍后再来查看吧~"):
                    yield msg
                return
            消息内容="🎯 当前抽奖活动列表 🎯\n\n"
            for 抽奖ID,数据 in 抽奖数据.items():
                # 使用get方法安全访问字典键，提供默认值
                游戏名称 = 数据.get('游戏名称', '未知游戏')
                奖励名称 = 数据.get('奖励名称', '未知奖励')
                奖励数量 = 数据.get('奖励数量', '未知数量')
                获奖人数 = 数据.get('抽奖人数', '0')
                截止时间 = 数据.get('截止时间', '未知时间')
                参与者列表 = 数据.get('参与者', [])
                参与人数 = len(参与者列表)
                消息内容+=f"📌 抽奖详情 📌\n抽奖ID：{抽奖ID}\n游戏名称：{游戏名称}\n奖励名称：{奖励名称}\n奖励数量：{奖励数量}\n获奖人数：{获奖人数}\n截止时间：{截止时间}\n参与人数：{参与人数}\n\n------------------------------\n"
            async for msg in self.发送消息(event, 消息内容):
                yield msg
        elif len(parts)==2:
            #查看指定抽奖
            抽奖ID=parts[1]
            if 抽奖ID not in 抽奖数据:
                async for msg in self.发送消息(event, f"❌ 错误提示 ❌\n\n未找到ID为{抽奖ID}的抽奖活动\n请检查抽奖ID是否正确"):
                        yield msg
                return
            数据=抽奖数据[抽奖ID]
            # 使用get方法安全访问字典键，提供默认值
            游戏名称 = 数据.get('游戏名称', '未知游戏')
            奖励名称 = 数据.get('奖励名称', '未知奖励')
            奖励数量 = 数据.get('奖励数量', '未知数量')
            获奖人数 = 数据.get('抽奖人数', '0')
            截止时间 = 数据.get('截止时间', '未知时间')
            参与者列表 = 数据.get('参与者', [])
            参与人数 = len(参与者列表)
            消息内容=f"📋 抽奖详情 📋\n\n抽奖ID：{抽奖ID}\n游戏名称：{游戏名称}\n奖励名称：{奖励名称}\n奖励数量：{奖励数量}\n获奖人数：{获奖人数}\n截止时间：{截止时间}\n参与人数：{参与人数}\n\n👥 参与者列表：\n{', '.join(参与者列表) if 参与者列表 else '暂无参与者'}"
            async for msg in self.发送消息(event, 消息内容):
                yield msg
        else:
            async for msg in self.发送消息(event, "📝 使用说明 📝\n\n查看所有抽奖：查看抽奖\n查看指定抽奖：查看抽奖 抽奖ID"):
                        yield msg
    
    @filter.command("参与抽奖")
    async def 参与抽奖(self, event: AstrMessageEvent):
        """参与已发起的某个抽奖，格式为：参与抽奖 抽奖ID"""
        message_str = event.message_str.strip()
        author_id = event.get_sender_id()
        parts = message_str.split(" ")
        if len(parts)!=2:
            async for msg in self.发送消息(event, "📝 使用说明 📝\n\n参与抽奖：参与抽奖 抽奖ID"):
                yield msg
            return
        抽奖ID=parts[1]
        
        # 检查是否已绑定ID
        玩家绑定数据 = JsonHandler.读取Json字典("玩家绑定id数据存储.json")
        if author_id not in 玩家绑定数据 or not 玩家绑定数据[author_id].strip():
            async for msg in self.发送消息(event, "❌ 参与失败 ❌\n\n参与抽奖必须已经绑定ID\n请先完成ID绑定后再参与抽奖\n\n绑定ID格式：绑定ID 游戏名称 玩家ID"):
                yield msg
            return
            
        抽奖数据=JsonHandler.读取Json字典("抽奖数据存储.json")
        if 抽奖ID not in 抽奖数据:
            async for msg in self.发送消息(event, f"❌ 错误提示 ❌\n\n未找到ID为{抽奖ID}的抽奖活动\n请检查抽奖ID是否正确\n\n如果确认抽奖ID正确，请联系管理员处理"):
                        yield msg
            return
        数据=抽奖数据[抽奖ID]
        # 使用get方法安全访问参与者列表
        参与者列表 = 数据.get('参与者', [])
        if author_id in 参与者列表:
            async for msg in self.发送消息(event, "🔔 提示 🔔\n\n您已参与该抽奖\n无需重复参与\n耐心等待开奖吧~"):
                    yield msg
            return
        参与者列表.append(author_id)
        # 更新数据字典中的参与者列表
        数据['参与者'] = 参与者列表
        # 使用直接的文件操作保存数据，与其他部分保持一致
        文件路径 = JsonHandler.获取文件路径("抽奖数据存储.json", True)
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(抽奖数据, f, ensure_ascii=False, indent=2)
        async for msg in self.发送消息(event, f"✅ 参与成功！\n\n您已成功参与抽奖ID为{抽奖ID}的抽奖活动\n\n现在您的参与人数：{len(数据.get('参与者', []))}\n\n🎁 祝您好运！🎁"):
                yield msg
