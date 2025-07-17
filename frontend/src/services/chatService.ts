import api from './api';
import type { User } from '../types';

export interface Chat {
  id: number;
  title: string;
  chat_type: string;
  course_id?: number | null;
  user_id: number;
  custom_prompt?: string | null;
  created_at: string;
  updated_at: string;
  course?: {
    id: number;
    name: string;
    code: string;
  } | null;
  stats?: {
    message_count: number;
  };
}

export interface Message {
  id: number;
  chat_id: number;
  user_id: number;
  content: string;
  created_at: string;
  updated_at: string;
  ai_response?: string;
  file_ids?: number[];
  folder_ids?: number[];
}

export interface CreateChatRequest {
  chat_type: string;
  first_message: string;
  course_id?: number;
  custom_prompt?: string;
  file_ids?: number[];
  folder_ids?: number[];
}

export interface SendMessageRequest {
  content: string;
  file_ids?: number[];
  folder_ids?: number[];
}

export class ChatService {
  // 获取聊天列表
  static async getChats(): Promise<Chat[]> {
    const res = await api.get('/api/v1/chats');
    return res.data.data.chats;
  }

  // 创建聊天
  static async createChat(data: CreateChatRequest): Promise<Chat> {
    const res = await api.post('/api/v1/chats', data);
    return res.data.data;
  }

  // 获取聊天消息
  static async getMessages(chat_id: number): Promise<Message[]> {
    const res = await api.get(`/api/v1/chats/${chat_id}/messages`);
    return res.data.data.messages;
  }

  // 发送消息（带AI回复）
  static async sendMessage(chat_id: number, data: SendMessageRequest): Promise<Message> {
    const res = await api.post(`/api/v1/chats/${chat_id}/messages`, data);
    return res.data.data;
  }

  // 编辑消息
  static async editMessage(message_id: number, content: string): Promise<Message> {
    const res = await api.put(`/api/v1/messages/${message_id}`, { content });
    return res.data.data;
  }

  // 删除消息
  static async deleteMessage(message_id: number): Promise<void> {
    await api.delete(`/api/v1/messages/${message_id}`);
  }

  // 删除聊天
  static async deleteChat(chat_id: number): Promise<void> {
    await api.delete(`/api/v1/chats/${chat_id}`);
  }
}
