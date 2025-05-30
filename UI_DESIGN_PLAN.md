# 🎯 UI设计方案 - 基于具体需求

## A. Campus Life Q&A 模块设计

### 简化设计要求
- ✅ 只显示一个title  
- ✅ 一个关于title的简单搜索
- ✅ AI交互交给后端处理

### UI设计方案

```tsx
// 简化的ChatPage设计
<PageHeader title="校园生活助手" />

<Row gutter={[16, 16]}>
  {/* 左侧 - 会话列表 */}
  <Col xs={24} md={8}>
    <Card title="对话历史">
      <Input.Search 
        placeholder="搜索对话..." 
        style={{ marginBottom: 16 }}
      />
      <List>
        {sessions.map(session => (
          <List.Item key={session.id}>
            <List.Item.Meta 
              title={session.title}
              description={`${session.messageCount}条消息`}
            />
          </List.Item>
        ))}
      </List>
    </Card>
  </Col>
  
  {/* 右侧 - 聊天界面 */}
  <Col xs={24} md={16}>
    <Card title="AI助手对话">
      <div className="chat-messages">
        {/* 消息列表 */}
      </div>
      <Input.TextArea 
        placeholder="输入你的问题..."
        autoSize={{ minRows: 2, maxRows: 4 }}
      />
    </Card>
  </Col>
</Row>
```

---

## B. Study Assistant 模块设计

### 学期管理设计

#### 1. 默认学期配置
```typescript
const DEFAULT_TERMS = [
  { id: '2024-25-2', name: '2024-25 Term 2', isActive: true },
  { id: '2024-25-3', name: '2024-25 Term 3', isActive: true },
  { id: '2025-26-1', name: '2025-26 Term 1', isActive: true },
  { id: 'other', name: '其他学期', isActive: false }
];
```

#### 2. 学期选择界面UI
```tsx
<Card title="选择学期" style={{ marginBottom: 24 }}>
  <Row gutter={[16, 16]}>
    {DEFAULT_TERMS.map(term => (
      <Col xs={24} sm={12} md={8} key={term.id}>
        <Card
          hoverable={term.isActive}
          onClick={() => term.isActive && selectTerm(term)}
          style={{
            cursor: term.isActive ? 'pointer' : 'not-allowed',
            opacity: term.isActive ? 1 : 0.5,
            border: selectedTerm === term.id ? '2px solid #1890ff' : '1px solid #d9d9d9'
          }}
        >
          <Card.Meta 
            title={term.name}
            description={term.isActive ? '点击选择' : '暂不支持'}
          />
          {!term.isActive && <Tag color="orange">暂不支持</Tag>}
        </Card>
      </Col>
    ))}
  </Row>
</Card>
```

### 课程创建表单UI

```tsx
<Card title="创建新课程">
  <Form layout="vertical">
    {/* 必填字段 */}
    <Form.Item 
      label="课程名称" 
      name="courseName" 
      rules={[{ required: true }]}
    >
      <Input placeholder="例：高等数学" />
    </Form.Item>
    
    {/* 选填字段 */}
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item label="课程代码" name="courseCode">
          <Input placeholder="例：MATH101" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item label="授课教师" name="instructor">
          <Input placeholder="例：张教授" />
        </Form.Item>
      </Col>
    </Row>
    
    {/* 时间设置 */}
    <Card title="上课时间" size="small" style={{ marginBottom: 16 }}>
      <Form.List name="scheduleTimes">
        {(fields, { add, remove }) => (
          <>
            {fields.map(field => (
              <Row gutter={8} key={field.key} align="middle">
                <Col span={6}>
                  <Form.Item name={[field.name, 'dayOfWeek']}>
                    <Select placeholder="星期">
                      <Option value="1">星期一</Option>
                      <Option value="2">星期二</Option>
                      <Option value="3">星期三</Option>
                      <Option value="4">星期四</Option>
                      <Option value="5">星期五</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={7}>
                  <Form.Item name={[field.name, 'startTime']}>
                    <TimePicker 
                      format="HH:30" 
                      minuteStep={30}
                      placeholder="开始时间"
                    />
                  </Form.Item>
                </Col>
                <Col span={7}>
                  <Form.Item name={[field.name, 'endTime']}>
                    <TimePicker 
                      format="HH:15" 
                      minuteStep={45}
                      placeholder="结束时间"
                    />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Button 
                    type="link" 
                    danger 
                    onClick={() => remove(field.name)}
                  >
                    删除
                  </Button>
                </Col>
              </Row>
            ))}
            <Button type="dashed" onClick={() => add()} block>
              + 添加上课时间
            </Button>
          </>
        )}
      </Form.List>
    </Card>
    
    {/* 课程大纲上传 */}
    <Form.Item label="课程大纲" name="outline">
      <Upload.Dragger>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p>点击或拖拽上传课程大纲</p>
        <p className="ant-upload-hint">支持PDF、DOC格式，不超过10MB</p>
      </Upload.Dragger>
    </Form.Item>
  </Form>
</Card>
```

### 三级目录结构UI

```tsx
// 层级结构：学期 → 课程 → 课程内容
<Breadcrumb style={{ marginBottom: 16 }}>
  <Breadcrumb.Item>
    <Select value={selectedTerm} onChange={setSelectedTerm}>
      {terms.map(term => (
        <Option key={term.id} value={term.id}>{term.name}</Option>
      ))}
    </Select>
  </Breadcrumb.Item>
  {selectedCourse && (
    <Breadcrumb.Item>{selectedCourse.name}</Breadcrumb.Item>
  )}
</Breadcrumb>

{/* 学期级别 - 显示该学期的所有课程 */}
{!selectedCourse && (
  <Row gutter={[16, 16]}>
    {courses.map(course => (
      <Col xs={24} sm={12} md={8} lg={6} key={course.id}>
        <Card
          hoverable
          onClick={() => setSelectedCourse(course)}
          cover={<div style={{ height: 120, background: course.color || '#f0f0f0' }} />}
        >
          <Card.Meta 
            title={course.name}
            description={
              <Space direction="vertical" size="small">
                <Text type="secondary">{course.code}</Text>
                <Text type="secondary">{course.instructor}</Text>
                <Tag color="blue">{course.fileCount || 0} 个文件</Tag>
              </Space>
            }
          />
        </Card>
      </Col>
    ))}
    <Col xs={24} sm={12} md={8} lg={6}>
      <Card 
        hoverable
        style={{ border: '2px dashed #d9d9d9' }}
        onClick={() => setCreateCourseModal(true)}
      >
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <PlusOutlined style={{ fontSize: 24, color: '#ccc' }} />
          <div style={{ marginTop: 8 }}>创建新课程</div>
        </div>
      </Card>
    </Col>
  </Row>
)}

{/* 课程级别 - 显示课程内的所有材料 */}
{selectedCourse && (
  <Row gutter={[16, 16]}>
    <Col span={24}>
      <Card 
        title={selectedCourse.name}
        extra={
          <Space>
            <Button icon={<UploadOutlined />}>上传文件</Button>
            <Button icon={<ArrowLeftOutlined />} onClick={() => setSelectedCourse(null)}>
              返回课程列表
            </Button>
          </Space>
        }
      >
        {/* 课程材料分类展示 */}
        <Tabs defaultActiveKey="all">
          <TabPane tab="全部文件" key="all">
            <FileList files={selectedCourse.files} />
          </TabPane>
          <TabPane tab="课程大纲" key="outline">
            <FileList files={selectedCourse.files?.filter(f => f.category === 'outline')} />
          </TabPane>
          <TabPane tab="课件PPT" key="slides">
            <FileList files={selectedCourse.files?.filter(f => f.category === 'slides')} />
          </TabPane>
          <TabPane tab="作业" key="assignments">
            <FileList files={selectedCourse.files?.filter(f => f.category === 'assignments')} />
          </TabPane>
          <TabPane tab="其他" key="other">
            <FileList files={selectedCourse.files?.filter(f => f.category === 'other')} />
          </TabPane>
        </Tabs>
      </Card>
    </Col>
  </Row>
)}
```

---

## C. 文件管理UI设计

### 文件上传组件

```tsx
const FileUploadComponent = ({ courseId, onUploadSuccess }) => {
  const handleUpload = (file) => {
    // 检查文件大小
    if (file.size > 10 * 1024 * 1024) {
      message.error('文件大小不能超过10MB');
      return false;
    }
    
    // 模拟上传，只记录文件信息
    const fileInfo = {
      id: Date.now(),
      name: file.name,
      size: file.size,
      path: file.path || file.webkitRelativePath || file.name, // 绝对路径
      type: file.type,
      uploadTime: new Date(),
      courseId: courseId
    };
    
    // 存储到本地状态或localStorage
    onUploadSuccess(fileInfo);
    message.success('文件上传成功');
    return false; // 阻止默认上传
  };
  
  return (
    <Upload.Dragger
      accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.jpg,.png"
      beforeUpload={handleUpload}
      showUploadList={false}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持PDF、DOC、PPT、图片等格式，单个文件不超过10MB
      </p>
    </Upload.Dragger>
  );
};
```

### 文件列表和预览UI

```tsx
const FileList = ({ files }) => {
  const [previewFile, setPreviewFile] = useState(null);
  
  const handlePreview = (file) => {
    // 使用绝对路径尝试预览
    setPreviewFile(file);
  };
  
  return (
    <>
      <List
        dataSource={files}
        renderItem={file => (
          <List.Item
            actions={[
              <Button 
                type="link" 
                icon={<EyeOutlined />}
                onClick={() => handlePreview(file)}
              >
                预览
              </Button>,
              <Button 
                type="link" 
                icon={<DownloadOutlined />}
                onClick={() => window.open(file.path)}
              >
                下载
              </Button>,
              <Button 
                type="link" 
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            ]}
          >
            <List.Item.Meta
              avatar={<FileTextOutlined style={{ fontSize: 24 }} />}
              title={file.name}
              description={
                <Space direction="vertical" size="small">
                  <Text type="secondary">
                    大小: {(file.size / 1024 / 1024).toFixed(2)} MB
                  </Text>
                  <Text type="secondary">
                    上传时间: {file.uploadTime?.toLocaleString()}
                  </Text>
                  <Text type="secondary" copyable>
                    路径: {file.path}
                  </Text>
                </Space>
              }
            />
          </List.Item>
        )}
      />
      
      {/* 文件预览模态框 */}
      <Modal
        title={`预览: ${previewFile?.name}`}
        open={!!previewFile}
        onCancel={() => setPreviewFile(null)}
        footer={null}
        width="80%"
        style={{ top: 20 }}
      >
        {previewFile && (
          <div style={{ textAlign: 'center' }}>
            {/* 根据文件类型显示不同的预览 */}
            {previewFile.type?.includes('image') ? (
              <img 
                src={previewFile.path} 
                alt={previewFile.name}
                style={{ maxWidth: '100%', maxHeight: '600px' }}
              />
            ) : previewFile.type?.includes('pdf') ? (
              <iframe
                src={previewFile.path}
                style={{ width: '100%', height: '600px', border: 'none' }}
                title={previewFile.name}
              />
            ) : (
              <div style={{ padding: '40px' }}>
                <FileTextOutlined style={{ fontSize: 64, color: '#ccc' }} />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    暂不支持此文件类型的预览
                  </Text>
                  <br />
                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />}
                    onClick={() => window.open(previewFile.path)}
                    style={{ marginTop: 16 }}
                  >
                    下载文件
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
};
```

---

## UI设计总结

### 1. Campus Life Q&A
- ✅ **极简设计**: 只有标题和搜索
- ✅ **美观布局**: 左右分栏，清晰的对话界面
- ✅ **后端友好**: 简单的数据结构，易于实现

### 2. Study Assistant
- ✅ **学期管理**: 默认3个可用学期，其他显示为不可用
- ✅ **三级结构**: 学期→课程→文件，层次清晰
- ✅ **课程创建**: 名称必填，其他选填，时间精确到小时
- ✅ **文件分类**: 使用Tabs进行分类展示

### 3. 文件管理
- ✅ **大小限制**: 前端验证10MB限制
- ✅ **路径记录**: 记录绝对路径用于预览
- ✅ **预览功能**: 支持图片和PDF预览
- ✅ **美观展示**: 使用List和Modal组件

### 4. 技术实现要点
- 📱 **响应式设计**: 使用Ant Design的Grid系统
- 🎨 **统一风格**: 延续现有的渐变和动画设计
- 💾 **数据管理**: 使用localStorage暂存数据
- 🔍 **用户体验**: 清晰的导航和反馈机制

这个设计方案专注于UI美观性，同时确保后端实现简单可行。所有功能都可以先用前端模拟数据实现，后续轻松对接真实API。
