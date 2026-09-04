export interface Role {
  id: number;
  name: string;
  code: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  phone_number?: string;
  role: string | Role;
  department?: string | Department | null;
  is_active: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface SourceItem {
  source_index: number;
  document_id?: string;
  document_title: string;
  file_name: string;
  page_number: number;
  similarity_score: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender_type: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  sources: SourceItem[];
  suggest_ticket?: boolean;
  response_time_ms?: number;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface DocumentItem {
  id: string;
  title: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  department_id?: number;
  department_name?: string;
  chunk_count: number;
  is_indexed: boolean;
  created_at: string;
}

export interface TicketComment {
  id: string;
  ticket_id: string;
  user_id: string;
  user_full_name?: string;
  user_role?: string;
  content: string;
  is_internal: boolean;
  created_at: string;
}

export interface TicketItem {
  id: string;
  ticket_code: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  created_by: string;
  creator_full_name?: string;
  creator_email?: string;
  assigned_to?: string;
  assignee_full_name?: string;
  chat_session_id?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
  comment_count: number;
  comments?: TicketComment[];
}

export interface DashboardSummary {
  total_users: number;
  total_departments: number;
  total_documents: number;
  total_chunks: number;
  total_chat_sessions: number;
  total_questions: number;
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  ai_resolution_rate: number;
  avg_response_time_ms: number;
}

export interface DashboardAnalytics {
  summary: DashboardSummary;
  tickets_by_category: { category: string; count: number }[];
  tickets_by_status: { status: string; count: number }[];
  tickets_by_priority: { priority: string; count: number }[];
  recent_activities: {
    type: 'TICKET' | 'DOCUMENT' | 'CHAT';
    title: string;
    user_name: string;
    created_at: string;
  }[];
}
