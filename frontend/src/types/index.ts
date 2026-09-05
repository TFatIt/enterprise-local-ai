export type UserStatus = 'ACTIVE' | 'INACTIVE' | 'LOCKED' | 'SUSPENDED' | 'PENDING';

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_system_role?: boolean;
  permissions?: PermissionItem[];
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description?: string;
  user_count?: number;
}

export interface PermissionItem {
  id: number;
  code: string;
  name: string;
  description?: string;
  category: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  employee_code?: string;
  phone?: string;
  phone_number?: string;
  position?: string;
  role: string | Role;
  role_name?: string;
  department_id?: number;
  department?: string | Department | null;
  status?: UserStatus;
  is_active: boolean;
  avatar?: string;
  last_login_at?: string;
  created_at?: string;
  updated_at?: string;
  permissions?: string[];
  force_password_change?: boolean;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  locked_users: number;
  pending_users: number;
  total_departments: number;
  it_users: number;
  admin_users: number;
}

export interface UserActivityItem {
  id: number;
  action: string;
  resource: string;
  result: string;
  details: Record<string, any>;
  ip_address?: string;
  created_at: string;
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

export type SecurityLevel = 'PUBLIC' | 'INTERNAL' | 'DEPARTMENT' | 'CONFIDENTIAL';
export type DocumentType = 'SOP' | 'POLICY' | 'PROCEDURE' | 'GUIDE' | 'MANUAL' | 'REPORT' | 'FORM' | 'SPECIFICATION' | 'OTHER';

export interface DocumentPermissionItem {
  id: string;
  document_id: string;
  user_id?: string;
  user_name?: string;
  user_email?: string;
  role_id?: number;
  role_code?: string;
  role_name?: string;
  permission_type: 'VIEW' | 'EDIT' | 'MANAGE';
  created_at: string;
}

export interface DocumentVersionItem {
  id: string;
  document_id: string;
  version_number: string;
  file_name: string;
  file_size: number;
  change_notes?: string;
  created_by?: string;
  creator_name?: string;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  file_name: string;
  file_type?: string;
  file_size?: number;
  file_size_bytes?: number;
  mime_type?: string;
  department_id?: number;
  department_name?: string;
  department_code?: string;
  document_type?: string;
  category?: string;
  owner_id?: string;
  owner_name?: string;
  uploaded_by?: string;
  uploader_name?: string;
  security_level?: SecurityLevel;
  visibility?: boolean;
  version?: string;
  status?: string;
  rag_status?: string;
  total_chunks?: number;
  chunk_count?: number;
  error_message?: string;
  approved_at?: string;
  approved_by?: string;
  approved_by_name?: string;
  created_at: string;
  updated_at?: string;
  can_edit?: boolean;
  can_delete?: boolean;
  can_manage_permissions?: boolean;
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

export interface KnowledgeGapItem {
  id: string;
  topic: string;
  sample_query: string;
  department_code: string;
  department_name: string;
  query_count: number;
  last_queried_at: string;
  suggested_action: string;
  status: 'OPEN' | 'RESOLVED';
  has_matching_doc: boolean;
}

export interface KnowledgeGapResponse {
  total_gaps: number;
  open_gaps: number;
  resolved_gaps: number;
  items: KnowledgeGapItem[];
}
