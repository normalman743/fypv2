表: audit_logs
  - id: int
  - user_id: int
  - action: varchar(50)
  - entity_type: varchar(50)
  - entity_id: int
  - details: json
  - ip_address: varchar(45)
  - created_at: datetime

表: chats
  - id: int
  - title: varchar(200)
  - chat_type: varchar(20)
  - course_id: int
  - user_id: int
  - custom_prompt: text
  - rag_enabled: tinyint(1)
  - max_context_length: int
  - created_at: datetime
  - updated_at: datetime

表: courses
  - id: int
  - name: varchar(100)
  - code: varchar(20)
  - description: text
  - semester_id: int
  - user_id: int
  - created_at: datetime

表: document_chunks
  - id: int
  - physical_file_id: int
  - global_file_id: int
  - chunk_text: longtext
  - chunk_index: int
  - token_count: int
  - chroma_id: varchar(36)
  - metadata: json
  - created_at: datetime

表: files
  - id: int
  - physical_file_id: int
  - original_name: varchar(255)
  - file_type: varchar(50)
  - course_id: int
  - folder_id: int
  - user_id: int
  - is_processed: tinyint(1)
  - processing_status: varchar(20)
  - processing_error: text
  - processed_at: datetime
  - chunk_count: int
  - content_preview: text
  - created_at: datetime

表: folders
  - id: int
  - name: varchar(100)
  - folder_type: varchar(20)
  - course_id: int
  - is_default: tinyint(1)
  - created_at: datetime

表: global_files
  - id: int
  - filename: varchar(255)
  - original_name: varchar(255)
  - file_size: int
  - mime_type: varchar(100)
  - upload_path: varchar(500)
  - file_hash: varchar(64)
  - category: varchar(50)
  - tags: json
  - description: text
  - is_active: tinyint(1)
  - is_public: tinyint(1)
  - created_by: int
  - is_processed: tinyint(1)
  - processing_status: varchar(20)
  - processing_error: text
  - processed_at: datetime
  - chunk_count: int
  - content_preview: text
  - created_at: datetime
  - updated_at: datetime

表: invite_codes
  - id: int
  - code: varchar(20)
  - description: varchar(200)
  - is_used: tinyint(1)
  - used_by: int
  - used_at: datetime
  - expires_at: datetime
  - is_active: tinyint(1)
  - created_by: int
  - created_at: datetime

表: message_file_attachments
  - id: int
  - message_id: int
  - file_id: int
  - filename: varchar(256)
  - created_at: datetime

表: message_files
  - id: int
  - message_id: int
  - file_id: int

表: message_rag_sources
  - id: int
  - message_id: int
  - source_file: varchar(256)
  - chunk_id: int
  - relevance_score: varchar(32)
  - created_at: datetime

表: messages
  - id: int
  - chat_id: int
  - content: longtext
  - role: varchar(20)
  - model_name: varchar(50)
  - tokens_used: int
  - cost: decimal(10,4)
  - response_time_ms: int
  - rag_sources: json
  - created_at: datetime

表: physical_files
  - id: int
  - file_hash: varchar(64)
  - file_size: int
  - mime_type: varchar(100)
  - storage_path: varchar(500)
  - first_uploaded_at: datetime
  - reference_count: int

表: semesters
  - id: int
  - name: varchar(100)
  - code: varchar(20)
  - start_date: datetime
  - end_date: datetime
  - is_active: tinyint(1)
  - created_at: datetime
  - updated_at: datetime

表: system_config
  - id: int
  - config_key: varchar(50)
  - config_value: text
  - description: varchar(200)
  - is_public: tinyint(1)
  - updated_by: int
  - updated_at: datetime

表: users
  - id: int
  - username: varchar(50)
  - email: varchar(100)
  - password_hash: varchar(128)
  - role: varchar(20)
  - balance: decimal(10,2)
  - total_spent: decimal(10,2)
  - preferred_language: varchar(20)
  - preferred_theme: varchar(20)
  - last_opened_semester_id: int
  - is_active: tinyint(1)
  - created_at: datetime
  - updated_at: datetime