# 🏫 Campus LLM Database Analysis Report

- **Database**: campus_llm_db
- **Host**: 39.108.113.103
- **Analysis Time**: 2025-07-16 02:49:23

## 📋 1. TABLE STRUCTURES

### 🔹 Table: audit_logs
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| user_id | int | YES | MUL |  |  |
| action | varchar(50) | NO |  |  |  |
| entity_type | varchar(50) | NO | MUL |  |  |
| entity_id | int | YES |  |  |  |
| details | json | YES |  |  |  |
| ip_address | varchar(45) | YES |  |  |  |
| created_at | datetime | YES | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: chats
- **Engine**: InnoDB
- **Rows**: 3
- **Auto_increment**: 4

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| title | varchar(200) | NO |  |  |  |
| chat_type | varchar(20) | NO | MUL |  |  |
| course_id | int | YES | MUL |  |  |
| user_id | int | NO | MUL |  |  |
| custom_prompt | text | YES |  |  |  |
| rag_enabled | tinyint(1) | YES |  | 1 |  |
| max_context_length | int | YES |  | 4000 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | datetime | YES | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 🔹 Table: courses
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 3

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| name | varchar(100) | NO |  |  |  |
| code | varchar(20) | NO | MUL |  |  |
| description | text | YES |  |  |  |
| semester_id | int | NO | MUL |  |  |
| user_id | int | NO | MUL |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: document_chunks
- **Engine**: InnoDB
- **Rows**: 6
- **Auto_increment**: 9

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| chunk_text | longtext | NO |  |  |  |
| chunk_index | int | YES |  |  |  |
| token_count | int | YES |  |  |  |
| chroma_id | varchar(36) | NO | UNI |  |  |
| chunk_metadata | json | YES |  |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| file_id | int | YES | MUL |  |  |

### 🔹 Table: document_chunks_backup_20250714
- **Engine**: InnoDB
- **Rows**: 18
- **Auto_increment**: None

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO |  | 0 |  |
| physical_file_id | int | YES |  |  |  |
| global_file_id | int | YES |  |  |  |
| chunk_text | longtext | NO |  |  |  |
| chunk_index | int | YES |  |  |  |
| token_count | int | YES |  |  |  |
| chroma_id | varchar(36) | NO |  |  |  |
| Chunk_Metadata | json | YES |  |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| file_id | int | YES |  |  |  |

### 🔹 Table: file_access_logs
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 5

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| file_id | int | NO | MUL |  |  |
| user_id | int | NO | MUL |  |  |
| action | varchar(20) | NO |  |  |  |
| access_via | varchar(20) | YES |  | direct |  |
| ip_address | varchar(45) | YES |  |  |  |
| user_agent | text | YES |  |  |  |
| accessed_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: file_group_members
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| group_id | int | NO | MUL |  |  |
| user_id | int | NO | MUL |  |  |
| role | varchar(20) | YES |  |  |  |
| added_by | int | NO | MUL |  |  |
| joined_at | datetime | YES |  | now() | DEFAULT_GENERATED |

### 🔹 Table: file_groups
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| name | varchar(100) | NO |  |  |  |
| description | text | YES |  |  |  |
| group_type | varchar(20) | YES |  |  |  |
| created_by | int | NO | MUL |  |  |
| course_id | int | YES | MUL |  |  |
| is_active | tinyint(1) | YES |  |  |  |
| auto_manage | tinyint(1) | YES |  |  |  |
| created_at | datetime | YES |  | now() | DEFAULT_GENERATED |
| updated_at | datetime | YES |  | now() | DEFAULT_GENERATED |

### 🔹 Table: file_shares
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 2

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| file_id | int | NO | MUL |  |  |
| shared_with_type | varchar(20) | NO | MUL |  |  |
| shared_with_id | int | YES |  |  |  |
| permission_level | varchar(20) | YES |  | read |  |
| can_reshare | tinyint(1) | YES |  | 0 |  |
| download_allowed | tinyint(1) | YES |  | 1 |  |
| expires_at | datetime | YES |  |  |  |
| shared_by | int | NO | MUL |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| last_accessed | datetime | YES |  |  |  |
| access_count | int | YES |  | 0 |  |

### 🔹 Table: files
- **Engine**: InnoDB
- **Rows**: 3
- **Auto_increment**: 6

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| physical_file_id | int | NO | MUL |  |  |
| original_name | varchar(255) | NO |  |  |  |
| file_type | varchar(50) | NO | MUL |  |  |
| course_id | int | YES | MUL |  |  |
| folder_id | int | YES | MUL |  |  |
| user_id | int | NO | MUL |  |  |
| is_processed | tinyint(1) | YES |  | 0 |  |
| processing_status | varchar(20) | YES |  | pending |  |
| processing_error | text | YES |  |  |  |
| processed_at | datetime | YES |  |  |  |
| chunk_count | int | YES |  | 0 |  |
| content_preview | text | YES |  |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| scope | varchar(20) | YES | MUL | course |  |
| visibility | varchar(20) | YES |  | private |  |
| is_shareable | tinyint(1) | YES |  | 1 |  |
| share_settings | json | YES |  |  |  |
| tags | json | YES |  |  |  |
| description | text | YES |  |  |  |
| file_size | int | YES |  |  |  |
| mime_type | varchar(100) | YES |  |  |  |
| file_hash | varchar(64) | YES | MUL |  |  |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 🔹 Table: folders
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 3

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| name | varchar(100) | NO | MUL |  |  |
| folder_type | varchar(20) | NO | MUL |  |  |
| course_id | int | NO | MUL |  |  |
| is_default | tinyint(1) | YES |  | 0 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: invite_codes
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 4

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| code | varchar(20) | NO | UNI |  |  |
| description | varchar(200) | YES |  |  |  |
| is_used | tinyint(1) | YES | MUL | 0 |  |
| used_by | int | YES | MUL |  |  |
| used_at | datetime | YES |  |  |  |
| expires_at | datetime | YES | MUL |  |  |
| is_active | tinyint(1) | YES | MUL | 1 |  |
| created_by | int | NO | MUL |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: message_file_references
- **Engine**: InnoDB
- **Rows**: 9
- **Auto_increment**: 10

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| message_id | int | NO | MUL |  |  |
| file_id | int | NO | MUL |  |  |
| reference_type | enum('file','folder') | NO |  | file |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: message_rag_sources
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| message_id | int | NO | MUL |  |  |
| source_file | varchar(256) | NO |  |  |  |
| chunk_id | int | NO |  |  |  |
| relevance_score | decimal(5,4) | YES |  |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### 🔹 Table: messages
- **Engine**: InnoDB
- **Rows**: 12
- **Auto_increment**: 13

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| chat_id | int | NO | MUL |  |  |
| content | longtext | NO |  |  |  |
| role | varchar(20) | NO | MUL |  |  |
| model_name | varchar(50) | YES | MUL |  |  |
| tokens_used | int | YES |  |  |  |
| cost | decimal(10,4) | YES |  |  |  |
| response_time_ms | int | YES |  |  |  |
| rag_sources | json | YES |  |  |  |
| created_at | datetime | YES | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| context_size | int | YES |  |  |  |
| direct_file_count | int | YES |  | 0 |  |
| rag_source_count | int | YES |  | 0 |  |

### 🔹 Table: permissions
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| resource_type | varchar(50) | NO | MUL |  |  |
| resource_id | varchar(100) | NO |  |  |  |
| subject_type | varchar(50) | NO | MUL |  |  |
| subject_id | varchar(100) | NO |  |  |  |
| action | varchar(50) | NO | MUL |  |  |
| effect | enum('allow','deny') | YES |  | allow |  |
| conditions | json | YES |  |  |  |
| metadata | json | YES |  |  |  |
| granted_by | int | YES | MUL |  |  |
| granted_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| expires_at | datetime | YES |  |  |  |
| is_active | tinyint(1) | YES | MUL | 1 |  |

### 🔹 Table: physical_files
- **Engine**: InnoDB
- **Rows**: 3
- **Auto_increment**: 5

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| file_hash | varchar(64) | NO | UNI |  |  |
| file_size | int | NO |  |  |  |
| mime_type | varchar(100) | NO |  |  |  |
| storage_path | varchar(500) | NO |  |  |  |
| first_uploaded_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| reference_count | int | YES |  | 0 |  |

### 🔹 Table: roles
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| name | varchar(100) | NO | UNI |  |  |
| description | text | YES |  |  |  |
| scope_type | varchar(50) | YES | MUL | global |  |
| scope_id | varchar(100) | YES |  |  |  |
| is_system | tinyint(1) | YES |  | 0 |  |
| is_active | tinyint(1) | YES |  | 1 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 🔹 Table: semesters
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 3

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| name | varchar(100) | NO |  |  |  |
| code | varchar(20) | NO | UNI |  |  |
| start_date | datetime | YES |  |  |  |
| end_date | datetime | YES |  |  |  |
| is_active | tinyint(1) | YES | MUL | 1 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 🔹 Table: subject_roles
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| subject_type | varchar(50) | NO | MUL |  |  |
| subject_id | varchar(100) | NO |  |  |  |
| role_id | int | NO | MUL |  |  |
| scope_type | varchar(50) | YES | MUL |  |  |
| scope_id | varchar(100) | YES |  |  |  |
| assigned_by | int | YES | MUL |  |  |
| assigned_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| expires_at | datetime | YES |  |  |  |
| is_active | tinyint(1) | YES | MUL | 1 |  |

### 🔹 Table: system_config
- **Engine**: InnoDB
- **Rows**: 0
- **Auto_increment**: 1

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| config_key | varchar(50) | NO | UNI |  |  |
| config_value | text | NO |  |  |  |
| description | varchar(200) | YES |  |  |  |
| is_public | tinyint(1) | YES |  | 0 |  |
| updated_by | int | YES | MUL |  |  |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### 🔹 Table: users
- **Engine**: InnoDB
- **Rows**: 2
- **Auto_increment**: 3

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| username | varchar(50) | NO | UNI |  |  |
| email | varchar(100) | NO | UNI |  |  |
| password_hash | varchar(128) | YES |  |  |  |
| role | varchar(20) | YES | MUL | user |  |
| balance | decimal(10,2) | YES |  | 1.00 |  |
| total_spent | decimal(10,2) | YES |  | 0.00 |  |
| preferred_language | varchar(20) | YES |  | zh_CN |  |
| preferred_theme | varchar(20) | YES |  | light |  |
| last_opened_semester_id | int | YES | MUL |  |  |
| is_active | tinyint(1) | YES |  | 1 |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

## 🔗 2. FOREIGN KEY RELATIONSHIPS

| Child Table | Child Column | Parent Table | Parent Column | Constraint Name |
|-------------|--------------|--------------|---------------|-----------------|
| audit_logs | user_id | users | id | audit_logs_ibfk_1 |
| chats | course_id | courses | id | chats_ibfk_1 |
| chats | user_id | users | id | chats_ibfk_2 |
| courses | semester_id | semesters | id | courses_ibfk_1 |
| courses | user_id | users | id | courses_ibfk_2 |
| document_chunks | file_id | files | id | document_chunks_ibfk_1 |
| file_access_logs | file_id | files | id | file_access_logs_ibfk_1 |
| file_access_logs | user_id | users | id | file_access_logs_ibfk_2 |
| file_group_members | group_id | file_groups | id | file_group_members_ibfk_1 |
| file_group_members | user_id | users | id | file_group_members_ibfk_2 |
| file_group_members | added_by | users | id | file_group_members_ibfk_3 |
| file_groups | created_by | users | id | file_groups_ibfk_1 |
| file_groups | course_id | courses | id | file_groups_ibfk_2 |
| file_shares | file_id | files | id | file_shares_ibfk_1 |
| file_shares | shared_by | users | id | file_shares_ibfk_2 |
| files | physical_file_id | physical_files | id | files_ibfk_1 |
| files | course_id | courses | id | files_ibfk_2 |
| files | folder_id | folders | id | files_ibfk_3 |
| files | user_id | users | id | files_ibfk_4 |
| folders | course_id | courses | id | folders_ibfk_1 |
| invite_codes | created_by | users | id | invite_codes_ibfk_1 |
| invite_codes | used_by | users | id | invite_codes_ibfk_2 |
| message_file_references | message_id | messages | id | message_file_references_ibfk_1 |
| message_rag_sources | message_id | messages | id | message_rag_sources_ibfk_1 |
| messages | chat_id | chats | id | messages_ibfk_1 |
| permissions | granted_by | users | id | permissions_ibfk_1 |
| subject_roles | role_id | roles | id | subject_roles_ibfk_1 |
| subject_roles | assigned_by | users | id | subject_roles_ibfk_2 |
| system_config | updated_by | users | id | system_config_ibfk_1 |
| users | last_opened_semester_id | semesters | id | users_ibfk_1 |

## 📊 3. INDEXES

### Table: audit_logs

- **INDEX** `idx_created_at` (created_at) [BTREE]
- **INDEX** `idx_entity` (entity_type, entity_id) [BTREE]
- **INDEX** `idx_user_action` (user_id, action) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: chats

- **INDEX** `idx_chat_type` (chat_type) [BTREE]
- **INDEX** `idx_chats_course_updated` (course_id, updated_at) [BTREE]
- **INDEX** `idx_chats_user_updated` (user_id, updated_at) [BTREE]
- **INDEX** `idx_course_id` (course_id) [BTREE]
- **INDEX** `idx_updated_at` (updated_at) [BTREE]
- **INDEX** `idx_user_id` (user_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: courses

- **INDEX** `idx_courses_user_semester` (user_id, semester_id, created_at) [BTREE]
- **INDEX** `idx_semester_id` (semester_id) [BTREE]
- **INDEX** `idx_user_id` (user_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **UNIQUE** `unique_course_per_user_semester` (code, semester_id, user_id) [BTREE]

### Table: document_chunks

- **UNIQUE** `chroma_id` (chroma_id) [BTREE]
- **INDEX** `idx_chroma_id` (chroma_id) [BTREE]
- **INDEX** `idx_document_chunks_file_id` (file_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: file_access_logs

- **INDEX** `idx_file_access` (file_id, accessed_at) [BTREE]
- **INDEX** `idx_user_access` (user_id, accessed_at) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: file_group_members

- **INDEX** `added_by` (added_by) [BTREE]
- **INDEX** `idx_group_member` (group_id, user_id) [BTREE]
- **INDEX** `ix_file_group_members_id` (id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **UNIQUE** `uq_group_member` (group_id, user_id) [BTREE]
- **INDEX** `user_id` (user_id) [BTREE]

### Table: file_groups

- **INDEX** `course_id` (course_id) [BTREE]
- **INDEX** `created_by` (created_by) [BTREE]
- **INDEX** `ix_file_groups_id` (id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: file_shares

- **INDEX** `idx_file_permissions` (file_id, permission_level) [BTREE]
- **INDEX** `idx_share_target` (shared_with_type, shared_with_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **INDEX** `shared_by` (shared_by) [BTREE]

### Table: files

- **INDEX** `idx_course_id` (course_id) [BTREE]
- **INDEX** `idx_file_type` (file_type) [BTREE]
- **INDEX** `idx_files_folder_status` (folder_id, processing_status) [BTREE]
- **INDEX** `idx_files_hash` (file_hash) [BTREE]
- **INDEX** `idx_files_owner_course` (user_id, course_id) [BTREE]
- **INDEX** `idx_files_scope_visibility` (scope, visibility) [BTREE]
- **INDEX** `idx_files_user_course` (user_id, course_id, created_at) [BTREE]
- **INDEX** `idx_physical_file_id` (physical_file_id) [BTREE]
- **INDEX** `idx_user_id` (user_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: folders

- **INDEX** `idx_course_id` (course_id) [BTREE]
- **INDEX** `idx_folder_type` (folder_type) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **UNIQUE** `unique_folder_per_course` (name, course_id) [BTREE]

### Table: invite_codes

- **UNIQUE** `code` (code) [BTREE]
- **INDEX** `created_by` (created_by) [BTREE]
- **INDEX** `idx_code` (code) [BTREE]
- **INDEX** `idx_expires_at` (expires_at) [BTREE]
- **INDEX** `idx_is_active` (is_active) [BTREE]
- **INDEX** `idx_is_used` (is_used) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **INDEX** `used_by` (used_by) [BTREE]

### Table: message_file_references

- **INDEX** `idx_file_refs` (file_id, reference_type) [BTREE]
- **INDEX** `idx_message_refs` (message_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: message_rag_sources

- **INDEX** `ix_message_rag_sources_id` (id) [BTREE]
- **INDEX** `ix_message_rag_sources_message_id` (message_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: messages

- **INDEX** `idx_chat_id` (chat_id) [BTREE]
- **INDEX** `idx_created_at` (created_at) [BTREE]
- **INDEX** `idx_messages_chat_created` (chat_id, created_at) [BTREE]
- **INDEX** `idx_model_name` (model_name) [BTREE]
- **INDEX** `idx_role` (role) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: permissions

- **INDEX** `granted_by` (granted_by) [BTREE]
- **INDEX** `idx_action` (action) [BTREE]
- **INDEX** `idx_active_permissions` (is_active, expires_at) [BTREE]
- **INDEX** `idx_resource` (resource_type, resource_id) [BTREE]
- **INDEX** `idx_subject` (subject_type, subject_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: physical_files

- **UNIQUE** `file_hash` (file_hash) [BTREE]
- **INDEX** `idx_file_hash` (file_hash) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: roles

- **INDEX** `idx_name` (name) [BTREE]
- **INDEX** `idx_scope` (scope_type, scope_id) [BTREE]
- **UNIQUE** `name` (name) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: semesters

- **UNIQUE** `code` (code) [BTREE]
- **INDEX** `idx_code` (code) [BTREE]
- **INDEX** `idx_is_active` (is_active) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]

### Table: subject_roles

- **INDEX** `assigned_by` (assigned_by) [BTREE]
- **INDEX** `idx_active` (is_active, expires_at) [BTREE]
- **INDEX** `idx_scope` (scope_type, scope_id) [BTREE]
- **INDEX** `idx_subject_role` (subject_type, subject_id, role_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **INDEX** `role_id` (role_id) [BTREE]

### Table: system_config

- **UNIQUE** `config_key` (config_key) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **INDEX** `updated_by` (updated_by) [BTREE]

### Table: users

- **UNIQUE** `email` (email) [BTREE]
- **INDEX** `idx_email` (email) [BTREE]
- **INDEX** `idx_role` (role) [BTREE]
- **INDEX** `idx_username` (username) [BTREE]
- **INDEX** `last_opened_semester_id` (last_opened_semester_id) [BTREE]
- **UNIQUE** `PRIMARY` (id) [BTREE]
- **UNIQUE** `username` (username) [BTREE]

## 🔒 4. CONSTRAINTS

### Table: audit_logs

- **FOREIGN KEY**: audit_logs_ibfk_1
- **PRIMARY KEY**: PRIMARY

### Table: chats

- **FOREIGN KEY**: chats_ibfk_1
- **FOREIGN KEY**: chats_ibfk_2
- **PRIMARY KEY**: PRIMARY

### Table: courses

- **FOREIGN KEY**: courses_ibfk_1
- **FOREIGN KEY**: courses_ibfk_2
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: unique_course_per_user_semester

### Table: document_chunks

- **FOREIGN KEY**: document_chunks_ibfk_1
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: chroma_id

### Table: file_access_logs

- **FOREIGN KEY**: file_access_logs_ibfk_1
- **FOREIGN KEY**: file_access_logs_ibfk_2
- **PRIMARY KEY**: PRIMARY

### Table: file_group_members

- **FOREIGN KEY**: file_group_members_ibfk_1
- **FOREIGN KEY**: file_group_members_ibfk_2
- **FOREIGN KEY**: file_group_members_ibfk_3
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: uq_group_member

### Table: file_groups

- **FOREIGN KEY**: file_groups_ibfk_1
- **FOREIGN KEY**: file_groups_ibfk_2
- **PRIMARY KEY**: PRIMARY

### Table: file_shares

- **FOREIGN KEY**: file_shares_ibfk_1
- **FOREIGN KEY**: file_shares_ibfk_2
- **PRIMARY KEY**: PRIMARY

### Table: files

- **FOREIGN KEY**: files_ibfk_1
- **FOREIGN KEY**: files_ibfk_2
- **FOREIGN KEY**: files_ibfk_3
- **FOREIGN KEY**: files_ibfk_4
- **PRIMARY KEY**: PRIMARY

### Table: folders

- **FOREIGN KEY**: folders_ibfk_1
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: unique_folder_per_course

### Table: invite_codes

- **FOREIGN KEY**: invite_codes_ibfk_1
- **FOREIGN KEY**: invite_codes_ibfk_2
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: code

### Table: message_file_references

- **FOREIGN KEY**: message_file_references_ibfk_1
- **PRIMARY KEY**: PRIMARY

### Table: message_rag_sources

- **FOREIGN KEY**: message_rag_sources_ibfk_1
- **PRIMARY KEY**: PRIMARY

### Table: messages

- **FOREIGN KEY**: messages_ibfk_1
- **PRIMARY KEY**: PRIMARY

### Table: permissions

- **FOREIGN KEY**: permissions_ibfk_1
- **PRIMARY KEY**: PRIMARY

### Table: physical_files

- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: file_hash

### Table: roles

- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: name

### Table: semesters

- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: code

### Table: subject_roles

- **FOREIGN KEY**: subject_roles_ibfk_1
- **FOREIGN KEY**: subject_roles_ibfk_2
- **PRIMARY KEY**: PRIMARY

### Table: system_config

- **FOREIGN KEY**: system_config_ibfk_1
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: config_key

### Table: users

- **FOREIGN KEY**: users_ibfk_1
- **PRIMARY KEY**: PRIMARY
- **UNIQUE**: email
- **UNIQUE**: username

## 📈 5. DATA SAMPLES

| Table | Rows | Sample Fields |
|-------|------|---------------|
| audit_logs | 0 |  |
| chats | 3 | id, title, chat_type, course_id, user_id |
| courses | 2 | id, name, code, description, semester_id |
| document_chunks | 6 | id, chunk_text, chunk_index, token_count, chroma_id |
| document_chunks_backup_20250714 | 18 | id, physical_file_id, global_file_id, chunk_text, chunk_index |
| file_access_logs | 2 | id, file_id, user_id, action, access_via |
| file_group_members | 0 |  |
| file_groups | 0 |  |
| file_shares | 0 |  |
| files | 3 | id, physical_file_id, original_name, file_type, course_id |
| folders | 2 | id, name, folder_type, course_id, is_default |
| invite_codes | 3 | id, code, description, is_used, used_by |
| message_file_references | 9 | id, message_id, file_id, reference_type, created_at |
| message_rag_sources | 0 |  |
| messages | 12 | id, chat_id, content, role, model_name |
| permissions | 0 |  |
| physical_files | 3 | id, file_hash, file_size, mime_type, storage_path |
| roles | 0 |  |
| semesters | 2 | id, name, code, start_date, end_date |
| subject_roles | 0 |  |
| system_config | 0 |  |
| users | 2 | id, username, email, password_hash, role |

## 🌐 6. DEPENDENCY GRAPH

Tables dependency order (for safe deletion):

- **Level 0 (Independent)**: document_chunks_backup_20250714, physical_files, roles, semesters
- **Level 1**: users
- **Level 2**: audit_logs, courses, invite_codes, permissions, subject_roles, system_config
- **Level 3**: chats, file_groups, folders
- **Level 4**: file_group_members, files, messages
- **Level 5**: document_chunks, file_access_logs, file_shares, message_file_references, message_rag_sources

## 📏 7. FIELD LENGTH LIMITS

Password and hash fields:

- **files.file_hash**: varchar(64)
- **physical_files.file_hash**: varchar(64)
- **users.password_hash**: varchar(128)

---
✅ **Analysis Complete!**