import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Row,
  Col,
  Card,
  Button,
  List,
  Tag,
  Select,
  Input,
  Modal,
  Form,
  TimePicker,
  Upload,
  message,
  Space,
  Typography,
  Breadcrumb,
  Popconfirm,
  Tooltip,
  Tabs,
  Tree,
  Avatar,
} from 'antd';
import {
  BookOutlined,
  CalendarOutlined,
  FileTextOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  EyeOutlined,
  DownloadOutlined,
  ClockCircleOutlined,
  UserOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FolderOpenOutlined,
  ArrowLeftOutlined,
  InboxOutlined,
  HomeOutlined,
  MessageOutlined,
  FolderOutlined,
  SendOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import dayjs, { Dayjs } from 'dayjs';
import TopNavigation from '../components/common/TopNavigation';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const { Dragger } = Upload;

// Interfaces
interface Semester {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  isActive: boolean;
}

interface Course {
  id: string;
  name: string;
  code?: string;
  instructor?: string;
  startTime?: string;
  endTime?: string;
  semesterId: string;
  fileCount: number;
}

interface StudyFile {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadDate: string;
  courseId: string;
  url?: string;
}

interface NavigationState {
  level: 'semester' | 'course' | 'files' | 'courseDetail'; // 添加 courseDetail 级别
  selectedSemester?: string;
  selectedCourse?: string;
}

interface CourseFolder {
  id: string;
  courseId: string;
  name: string;
  type: 'outline' | 'tutorial' | 'lecture' | 'note' | 'custom';
  parentId?: string;
  icon?: string;
  color?: string;
}

interface CourseMaterial {
  id: string;
  courseId: string;
  folderId: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  uploadDate: Date;
  filePath: string;
}

const StudyPage: React.FC = () => {
  const { t } = useTranslation();

  // State management
  const [semesters] = useState<Semester[]>([
    {
      id: '1',
      name: '2024-25学年 第二学期',
      startDate: '2025-01-20',
      endDate: '2025-06-15',
      isActive: true,
    },
    {
      id: '2',
      name: '2024-25学年 第三学期',
      startDate: '2025-06-16',
      endDate: '2025-08-31',
      isActive: true,
    },
    {
      id: '3',
      name: '2025-26学年 第一学期',
      startDate: '2025-09-01',
      endDate: '2026-01-19',
      isActive: true,
    },
    {
      id: 'other',
      name: '其他',
      startDate: '',
      endDate: '',
      isActive: false,
    },
  ]);

  const [courses, setCourses] = useState<Course[]>([
    {
      id: '1',
      name: '高级数据结构与算法',
      code: 'CS301',
      instructor: '张教授',
      startTime: '09:30',
      endTime: '11:15',
      semesterId: '1',
      fileCount: 12,
    },
    {
      id: '2',
      name: '机器学习基础',
      code: 'CS402',
      instructor: '李教授',
      startTime: '14:00',
      endTime: '15:45',
      semesterId: '1',
      fileCount: 8,
    },
    {
      id: '3',
      name: '软件工程实践',
      code: 'CS350',
      instructor: '王教授',
      semesterId: '2',
      fileCount: 5,
    },
  ]);

  const [files, setFiles] = useState<StudyFile[]>([
    {
      id: '1',
      name: '算法分析讲义.pdf',
      type: 'application/pdf',
      size: 2048000,
      uploadDate: '2025-01-15',
      courseId: '1',
    },
    {
      id: '2',
      name: '数据结构实验报告.docx',
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      size: 1024000,
      uploadDate: '2025-01-12',
      courseId: '1',
    },
    {
      id: '3',
      name: '机器学习笔记.md',
      type: 'text/markdown',
      size: 512000,
      uploadDate: '2025-01-10',
      courseId: '2',
    },
  ]);

  // 自动计算当前学期
  const getCurrentSemesterByDate = (): string => {
    const now = new Date();
    const month = now.getMonth() + 1; // getMonth() 返回 0-11，需要 +1
    
    // 根据月份判断学期
    if (month >= 9 || month <= 1) {
      // 9月-1月：第一学期
      return '3'; // 2025-26学年 第一学期
    } else if (month >= 2 && month <= 6) {
      // 2月-6月：第二学期  
      return '1'; // 2024-25学年 第二学期
    } else {
      // 7月-8月：第三学期
      return '2'; // 2024-25学年 第三学期
    }
  };

  const [navigation, setNavigation] = useState<NavigationState>({
    level: 'course', // 默认进入课程选择页面
    selectedSemester: getCurrentSemesterByDate(), // 自动选择当前学期
  });

  const [loading, setLoading] = useState(false);
  const [modals, setModals] = useState({
    course: false,
    file: false,
    filePreview: false,
    folder: false, // 添加文件夹创建模态框
  });
  const [selectedFile, setSelectedFile] = useState<StudyFile | null>(null);
  const [form] = Form.useForm();
  const [folderForm] = Form.useForm(); // 文件夹表单
  
  // 新增：课程详情页面状态
  const [activeTab, setActiveTab] = useState<'materials' | 'chat'>('materials');
  const [courseFolders, setCourseFolders] = useState<CourseFolder[]>([
    // 预设文件夹
    { id: '1', courseId: '1', name: 'Outline', type: 'outline', icon: '📋', color: '#1890ff' },
    { id: '2', courseId: '1', name: 'Tutorial', type: 'tutorial', icon: '📚', color: '#52c41a' },
    { id: '3', courseId: '1', name: 'Lecture', type: 'lecture', icon: '🎯', color: '#722ed1' },
    { id: '4', courseId: '1', name: 'Note', type: 'note', icon: '📝', color: '#fa8c16' },
    { id: '5', courseId: '2', name: 'Outline', type: 'outline', icon: '📋', color: '#1890ff' },
    { id: '6', courseId: '2', name: 'Tutorial', type: 'tutorial', icon: '📚', color: '#52c41a' },
    { id: '7', courseId: '2', name: 'Lecture', type: 'lecture', icon: '🎯', color: '#722ed1' },
    { id: '8', courseId: '2', name: 'Note', type: 'note', icon: '📝', color: '#fa8c16' },
  ]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);

  // Helper functions
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
    if (type.includes('word') || type.includes('document')) return <FileWordOutlined style={{ color: '#1890ff' }} />;
    return <FileTextOutlined style={{ color: '#52c41a' }} />;
  };

  const getActiveSemesters = () => semesters.filter(s => s.isActive);

  const getCurrentCourses = () => {
    if (!navigation.selectedSemester) return [];
    return courses.filter(c => c.semesterId === navigation.selectedSemester);
  };

  const getCurrentFiles = () => {
    if (!navigation.selectedCourse) return [];
    return files.filter(f => f.courseId === navigation.selectedCourse);
  };

  const getCurrentSemester = () => semesters.find(s => s.id === navigation.selectedSemester);
  const getCurrentCourse = () => courses.find(c => c.id === navigation.selectedCourse);

  // Event handlers
  const handleNavigate = (level: NavigationState['level'], id?: string) => {
    if (level === 'semester') {
      setNavigation({ level: 'semester' });
    } else if (level === 'course' && id) {
      setNavigation({ level: 'course', selectedSemester: id });
    } else if (level === 'files' && id) {
      setNavigation({ ...navigation, level: 'files', selectedCourse: id });
    } else if (level === 'courseDetail' && id) {
      setNavigation({ ...navigation, level: 'courseDetail', selectedCourse: id });
      setActiveTab('materials'); // 默认显示资料管理
    }
  };

  // 获取当前课程的文件夹
  const getCurrentCourseFolders = () => {
    if (!navigation.selectedCourse) return [];
    return courseFolders.filter(f => f.courseId === navigation.selectedCourse);
  };

  // 创建自定义文件夹
  const handleCreateFolder = async (values: any) => {
    try {
      setLoading(true);
      const newFolder: CourseFolder = {
        id: Date.now().toString(),
        courseId: navigation.selectedCourse!,
        name: values.name,
        type: 'custom',
        icon: values.icon || '📁',
        color: values.color || '#1890ff',
      };
      setCourseFolders(prev => [...prev, newFolder]);
      folderForm.resetFields();
      setModals({ ...modals, folder: false });
      message.success('文件夹创建成功');
    } catch (error) {
      message.error('创建文件夹失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = useCallback(async (values: any) => {
    try {
      setLoading(true);
      const newCourse: Course = {
        id: Date.now().toString(),
        name: values.name,
        code: values.code,
        instructor: values.instructor,
        startTime: values.time?.[0]?.format('HH:mm'),
        endTime: values.time?.[1]?.format('HH:mm'),
        semesterId: navigation.selectedSemester!,
        fileCount: 0,
      };
      setCourses(prev => [...prev, newCourse]);
      form.resetFields();
      setModals({ ...modals, course: false });
      message.success('课程创建成功');
    } catch (error) {
      message.error('创建失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [navigation.selectedSemester, modals, form]);

  const handleDeleteCourse = useCallback(async (courseId: string) => {
    try {
      setCourses(prev => prev.filter(c => c.id !== courseId));
      setFiles(prev => prev.filter(f => f.courseId !== courseId));
      message.success('课程删除成功');
    } catch (error) {
      message.error('删除失败，请重试');
    }
  }, []);

  const handleFileUpload = useCallback(async (info: any) => {
    const { file } = info;
    
    if (file.size > 10 * 1024 * 1024) {
      message.error('文件大小不能超过10MB');
      return false;
    }

    try {
      setLoading(true);
      const newFile: StudyFile = {
        id: Date.now().toString(),
        name: file.name,
        type: file.type,
        size: file.size,
        uploadDate: dayjs().format('YYYY-MM-DD'),
        courseId: navigation.selectedCourse!,
        url: URL.createObjectURL(file),
      };
      
      setFiles(prev => [...prev, newFile]);
      setCourses(prev => prev.map(c => 
        c.id === navigation.selectedCourse 
          ? { ...c, fileCount: c.fileCount + 1 }
          : c
      ));
      
      setModals({ ...modals, file: false });
      message.success('文件上传成功');
    } catch (error) {
      message.error('上传失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [navigation.selectedCourse, modals]);

  const handleDeleteFile = useCallback(async (fileId: string) => {
    try {
      setFiles(prev => prev.filter(f => f.id !== fileId));
      setCourses(prev => prev.map(c => 
        c.id === navigation.selectedCourse 
          ? { ...c, fileCount: Math.max(0, c.fileCount - 1) }
          : c
      ));
      message.success('文件删除成功');
    } catch (error) {
      message.error('删除失败，请重试');
    }
  }, [navigation.selectedCourse]);

  const handlePreviewFile = (file: StudyFile) => {
    setSelectedFile(file);
    setModals({ ...modals, filePreview: true });
  };

  // Render functions
  const renderBreadcrumb = () => {
    const items = [
      {
        title: (
          <Button 
            type="link" 
            icon={<HomeOutlined />} 
            onClick={() => handleNavigate('semester')}
          >
            学期管理
          </Button>
        ),
      },
    ];

    if (navigation.selectedSemester) {
      const semester = getCurrentSemester();
      items.push({
        title: navigation.level === 'course' ? (
          <span>{semester?.name}</span>
        ) : (
          <Button 
            type="link" 
            onClick={() => handleNavigate('course', navigation.selectedSemester)}
          >
            {semester?.name}
          </Button>
        ),
      });
    }

    if (navigation.selectedCourse) {
      const course = getCurrentCourse();
      items.push({
        title: navigation.level === 'courseDetail' ? (
          <span>{course?.name}</span>
        ) : (
          <Button 
            type="link" 
            onClick={() => handleNavigate('courseDetail', navigation.selectedCourse)}
          >
            {course?.name}
          </Button>
        ),
      });
    }

    return <Breadcrumb items={items} style={{ marginBottom: 16 }} />;
  };

  const renderSemesterView = () => (
    <Row gutter={[16, 16]}>
      {getActiveSemesters().map(semester => (
        <Col xs={24} sm={12} lg={8} key={semester.id}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card
              hoverable
              onClick={() => handleNavigate('course', semester.id)}
              actions={[
                <BookOutlined key="courses" />,
                <Text key="count">
                  {courses.filter(c => c.semesterId === semester.id).length} 门课程
                </Text>,
              ]}
            >
              <Card.Meta
                avatar={<CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={semester.name}
                description={`${semester.startDate} - ${semester.endDate}`}
              />
              <Tag color="green" style={{ marginTop: 8 }}>
                当前学期
              </Tag>
            </Card>
          </motion.div>
        </Col>
      ))}
    </Row>
  );

  const renderCourseView = () => {
    const currentCourses = getCurrentCourses();
    
    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModals({ ...modals, course: true })}
            >
              添加课程
            </Button>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          {currentCourses.map(course => (
            <Col xs={24} sm={12} lg={8} key={course.id}>
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card
                  hoverable
                  onClick={() => handleNavigate('courseDetail', course.id)}
                  actions={[
                    <FileTextOutlined key="files" />,
                    <Text key="count">{course.fileCount} 个文件</Text>,
                    <Popconfirm
                      title="确定要删除这门课程吗？"
                      onConfirm={() => handleDeleteCourse(course.id)}
                    >
                      <Button 
                        type="text" 
                        icon={<DeleteOutlined />} 
                        danger 
                        onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      />
                    </Popconfirm>,
                  ]}
                >
                  <Card.Meta
                    avatar={<BookOutlined style={{ fontSize: 24, color: '#52c41a' }} />}
                    title={course.name}
                    description={
                      <Space direction="vertical" size="small">
                        {course.code && <Text type="secondary">课程编号: {course.code}</Text>}
                        {course.instructor && (
                          <Text type="secondary">
                            <UserOutlined /> {course.instructor}
                          </Text>
                        )}
                        {course.startTime && course.endTime && (
                          <Text type="secondary">
                            <ClockCircleOutlined /> {course.startTime} - {course.endTime}
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </Card>
              </motion.div>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  const renderFilesView = () => {
    const currentFiles = getCurrentFiles();
    
    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setModals({ ...modals, file: true })}
            >
              上传文件
            </Button>
          </Col>
        </Row>

        <List
          itemLayout="horizontal"
          dataSource={currentFiles}
          renderItem={(file) => (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <List.Item
                actions={[
                  <Tooltip title="预览">
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={() => handlePreviewFile(file)}
                    />
                  </Tooltip>,
                  <Tooltip title="下载">
                    <Button
                      type="text"
                      icon={<DownloadOutlined />}
                      onClick={() => {
                        if (file.url) {
                          const a = document.createElement('a');
                          a.href = file.url;
                          a.download = file.name;
                          a.click();
                        }
                      }}
                    />
                  </Tooltip>,
                  <Popconfirm
                    title="确定要删除这个文件吗？"
                    onConfirm={() => handleDeleteFile(file.id)}
                  >
                    <Button type="text" icon={<DeleteOutlined />} danger />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  avatar={getFileIcon(file.type)}
                  title={file.name}
                  description={
                    <Space>
                      <Text type="secondary">{formatFileSize(file.size)}</Text>
                      <Text type="secondary">上传于 {file.uploadDate}</Text>
                    </Space>
                  }
                />
              </List.Item>
            </motion.div>
          )}
        />
      </div>
    );
  };

  // 渲染课程详情页面（资料管理 + 聊天）
  const renderCourseDetailView = () => {
    const currentCourse = getCurrentCourse();
    const currentFolders = getCurrentCourseFolders();
    
    const tabItems = [
      {
        key: 'materials',
        label: (
          <span>
            <FolderOutlined />
            课程资料
          </span>
        ),
        children: renderMaterialsTab(currentFolders),
      },
      {
        key: 'chat',
        label: (
          <span>
            <MessageOutlined />
            课程问答
          </span>
        ),
        children: renderChatTab(currentCourse),
      },
    ];

    return (
      <div>
        {/* 课程信息头部 */}
        <Card style={{ marginBottom: 16 }}>
          <Row align="middle" justify="space-between">
            <Col>
              <Space>
                <BookOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <div>
                  <Title level={3} style={{ margin: 0 }}>
                    {currentCourse?.name}
                  </Title>
                  <Text type="secondary">
                    {currentCourse?.code} • {currentCourse?.instructor}
                  </Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => handleNavigate('course', navigation.selectedSemester)}
              >
                返回课程列表
              </Button>
            </Col>
          </Row>
        </Card>

        {/* 标签页内容 */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as 'materials' | 'chat')}
            items={tabItems}
            size="large"
          />
        </Card>
      </div>
    );
  };

  // 渲染资料管理标签页
  const renderMaterialsTab = (folders: CourseFolder[]) => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModals({ ...modals, folder: true })}
          >
            创建文件夹
          </Button>
        </Col>
        <Col>
          <Button
            icon={<UploadOutlined />}
            onClick={() => setModals({ ...modals, file: true })}
            disabled={!selectedFolder}
          >
            上传文件
          </Button>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 文件夹列表 */}
        <Col xs={24} lg={8}>
          <Card title="文件夹" size="small">
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {folders.map(folder => (
                <div
                  key={folder.id}
                  style={{
                    padding: '12px',
                    margin: '8px 0',
                    backgroundColor: selectedFolder === folder.id ? '#e6f7ff' : '#fafafa',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    border: selectedFolder === folder.id ? '2px solid #1890ff' : '1px solid #d9d9d9',
                    transition: 'all 0.3s ease'
                  }}
                  onClick={() => setSelectedFolder(selectedFolder === folder.id ? null : folder.id)}
                >
                  <Space>
                    <span style={{ fontSize: '18px' }}>{folder.icon}</span>
                    <Text strong={selectedFolder === folder.id}>
                      {folder.name}
                    </Text>
                    <Tag color={folder.color}>
                      {folder.type}
                    </Tag>
                  </Space>
                </div>
              ))}
            </div>
          </Card>
        </Col>

        {/* 文件列表 */}
        <Col xs={24} lg={16}>
          <Card 
            title={selectedFolder ? `文件列表 - ${folders.find(f => f.id === selectedFolder)?.name}` : '请选择文件夹'} 
            size="small"
          >
            {selectedFolder ? (
              <div style={{ minHeight: '300px' }}>
                {getCurrentFiles().length > 0 ? (
                  <List
                    itemLayout="horizontal"
                    dataSource={getCurrentFiles()}
                    renderItem={(file) => (
                      <List.Item
                        actions={[
                          <Button type="text" icon={<EyeOutlined />} />,
                          <Button type="text" icon={<DownloadOutlined />} />,
                          <Button type="text" icon={<DeleteOutlined />} danger />,
                        ]}
                      >
                        <List.Item.Meta
                          avatar={getFileIcon(file.type)}
                          title={file.name}
                          description={`${formatFileSize(file.size)} • ${file.uploadDate}`}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '50px',
                    color: '#999'
                  }}>
                    <InboxOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>该文件夹暂无文件</div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '50px',
                color: '#999'
              }}>
                <FolderOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>请先选择一个文件夹</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );

  // 渲染聊天标签页
  const renderChatTab = (course: Course | undefined) => (
    <div style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
      {/* 聊天消息区域 */}
      <div style={{ 
        flex: 1, 
        padding: '16px',
        backgroundColor: '#fafafa',
        borderRadius: '8px',
        marginBottom: '16px',
        overflowY: 'auto'
      }}>
        {/* 欢迎消息 */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <Avatar size={64} icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
          <Title level={4} style={{ marginTop: '8px' }}>
            {course?.name} AI助手
          </Title>
          <Text type="secondary">
            我可以帮您解答关于这门课程的任何问题，包括课程内容、作业要求、学习建议等。
          </Text>
        </div>

        {/* 快速问题按钮 */}
        <Row gutter={[8, 8]} style={{ marginBottom: '20px' }}>
          {[
            '这门课的学习目标是什么？',
            '有哪些重要的作业和考试？',
            '推荐的学习资料有哪些？',
            '如何更好地掌握课程内容？'
          ].map((question, index) => (
            <Col key={index}>
              <Button 
                size="small" 
                style={{ borderRadius: '16px' }}
                onClick={() => {
                  // 这里可以添加快速问题的处理逻辑
                  message.info(`您问了：${question}`);
                }}
              >
                {question}
              </Button>
            </Col>
          ))}
        </Row>
      </div>

      {/* 消息输入区域 */}
      <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '16px' }}>
        <Row gutter={8}>
          <Col flex={1}>
            <Input.TextArea
              placeholder={`向 ${course?.name} AI助手提问...`}
              autoSize={{ minRows: 1, maxRows: 3 }}
              style={{ borderRadius: '8px' }}
            />
          </Col>
          <Col>
            <Button 
              type="primary" 
              icon={<SendOutlined />}
              style={{ height: '100%', borderRadius: '8px' }}
            >
              发送
            </Button>
          </Col>
        </Row>
        
        {/* 资料引用区域 */}
        <div style={{ marginTop: '8px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            💡 提示：您可以在问题中引用课程资料，AI助手会基于这些资料为您提供更准确的答案
          </Text>
        </div>
      </div>
    </div>
  );

  const renderMainContent = () => {
    if (navigation.level === 'semester') {
      return renderSemesterView();
    } else if (navigation.level === 'course') {
      return renderCourseView();
    } else if (navigation.level === 'courseDetail') {
      return renderCourseDetailView();
    } else {
      return renderFilesView();
    }
  };

  const getPageTitle = () => {
    if (navigation.level === 'semester') return '学习助手';
    if (navigation.level === 'course') return '课程管理';
    if (navigation.level === 'courseDetail') return getCurrentCourse()?.name || '课程详情';
    return '文件管理';
  };

  const getStatsData = () => {
    const totalCourses = courses.length;
    const totalFiles = files.length;
    const activeSemesters = getActiveSemesters().length;
    
    return [
      {
        title: '活跃学期',
        value: activeSemesters,
        icon: <CalendarOutlined />,
        color: '#1890ff',
      },
      {
        title: '总课程数',
        value: totalCourses,
        icon: <BookOutlined />,
        color: '#52c41a',
      },
      {
        title: '总文件数',
        value: totalFiles,
        icon: <FileTextOutlined />,
        color: '#faad14',
      },
    ];
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f5f5f5' }}>
      <TopNavigation 
        title={getPageTitle()}
        subtitle="管理您的学习资料和课程安排"
        icon={<BookOutlined />}
      />
      
      <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
        {/* Stats Cards */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {getStatsData().map((stat, index) => (
            <Col xs={24} sm={8} key={index}>
              <StatCard {...stat} />
            </Col>
          ))}
        </Row>

        {/* Breadcrumb */}
        {navigation.level !== 'semester' && renderBreadcrumb()}

        {/* Main Content */}
        <motion.div
          key={navigation.level}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderMainContent()}
        </motion.div>
      </div>

      {/* Course Creation Modal */}
      <Modal
        title="添加课程"
        open={modals.course}
        onCancel={() => setModals({ ...modals, course: false })}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateCourse}
        >
          <Form.Item
            name="name"
            label="课程名称"
            rules={[{ required: true, message: '请输入课程名称' }]}
          >
            <Input placeholder="请输入课程名称" />
          </Form.Item>

          <Form.Item name="code" label="课程编号">
            <Input placeholder="请输入课程编号（可选）" />
          </Form.Item>

          <Form.Item name="instructor" label="任课教师">
            <Input placeholder="请输入任课教师（可选）" />
          </Form.Item>

          <Form.Item name="time" label="上课时间">
            <TimePicker.RangePicker
              format="HH:mm"
              placeholder={['开始时间', '结束时间']}
              minuteStep={15}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建课程
              </Button>
              <Button onClick={() => setModals({ ...modals, course: false })}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* File Upload Modal */}
      <Modal
        title="上传文件"
        open={modals.file}
        onCancel={() => setModals({ ...modals, file: false })}
        footer={null}
      >
        <Dragger
          multiple
          maxCount={5}
          beforeUpload={() => false}
          onChange={handleFileUpload}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传，文件大小限制为10MB
          </p>
        </Dragger>
      </Modal>

      {/* Folder Creation Modal */}
      <Modal
        title="创建文件夹"
        open={modals.folder}
        onCancel={() => setModals({ ...modals, folder: false })}
        footer={null}
      >
        <Form
          form={folderForm}
          layout="vertical"
          onFinish={handleCreateFolder}
        >
          <Form.Item
            name="name"
            label="文件夹名称"
            rules={[{ required: true, message: '请输入文件夹名称' }]}
          >
            <Input placeholder="请输入文件夹名称" />
          </Form.Item>

          <Form.Item name="icon" label="文件夹图标">
            <Select placeholder="选择图标（可选）" allowClear>
              <Option value="📁">📁 默认文件夹</Option>
              <Option value="📚">📚 书籍</Option>
              <Option value="📝">📝 笔记</Option>
              <Option value="🎯">🎯 重点</Option>
              <Option value="📋">📋 列表</Option>
              <Option value="🔬">🔬 实验</Option>
              <Option value="📊">📊 图表</Option>
              <Option value="🎨">🎨 创意</Option>
            </Select>
          </Form.Item>

          <Form.Item name="color" label="文件夹颜色">
            <Select placeholder="选择颜色（可选）" allowClear>
              <Option value="#1890ff">🔵 蓝色</Option>
              <Option value="#52c41a">🟢 绿色</Option>
              <Option value="#722ed1">🟣 紫色</Option>
              <Option value="#fa8c16">🟠 橙色</Option>
              <Option value="#f5222d">🔴 红色</Option>
              <Option value="#13c2c2">🟡 青色</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                创建文件夹
              </Button>
              <Button onClick={() => setModals({ ...modals, folder: false })}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* File Preview Modal */}
      <Modal
        title="文件预览"
        open={modals.filePreview}
        onCancel={() => setModals({ ...modals, filePreview: false })}
        footer={null}
        width={800}
      >
        {selectedFile && (
          <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Title level={4}>{selectedFile.name}</Title>
                <Text type="secondary">
                  大小: {formatFileSize(selectedFile.size)} | 
                  上传时间: {selectedFile.uploadDate}
                </Text>
              </div>
              
              {selectedFile.type.includes('image') && selectedFile.url ? (
                <img 
                  src={selectedFile.url} 
                  alt={selectedFile.name}
                  style={{ maxWidth: '100%', maxHeight: '500px' }}
                />
              ) : selectedFile.type.includes('pdf') ? (
                <div style={{ 
                  height: '500px', 
                  border: '1px solid #d9d9d9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Space direction="vertical" align="center">
                    <FilePdfOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
                    <Text>PDF文件预览暂不支持，请下载查看</Text>
                  </Space>
                </div>
              ) : (
                <div style={{ 
                  height: '300px', 
                  border: '1px solid #d9d9d9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Space direction="vertical" align="center">
                    {getFileIcon(selectedFile.type)}
                    <Text>此文件类型暂不支持预览，请下载查看</Text>
                  </Space>
                </div>
              )}
            </Space>
          </div>
        )}
      </Modal>

      {loading && <LoadingSpinner />}
    </div>
  );
};

export default StudyPage;
