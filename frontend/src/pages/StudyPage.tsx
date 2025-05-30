import React, { useState } from 'react';
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
  DatePicker,
  Switch,
  Tabs,
  Upload,
  message,
  Table,
  Space,
  Typography,
  Tooltip,
  Divider,
  TimePicker,
  Calendar,
  Badge,
  Dropdown,
  MenuProps,
  Popconfirm,
  Progress,
  Statistic,
  InputNumber,
} from 'antd';
import {
  BookOutlined,
  CalendarOutlined,
  FileTextOutlined,
  BulbOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  EyeOutlined,
  DownloadOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  UserOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  MoreOutlined,
  QuestionCircleOutlined,
  PlayCircleOutlined,
  FolderOpenOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  SettingOutlined,
  StarOutlined,
  RocketOutlined,
  TrophyOutlined,
  FireOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import dayjs, { Dayjs } from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import QuickActionCard from '../components/common/QuickActionCard';
import LoadingSpinner from '../components/common/LoadingSpinner';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Dragger } = Upload;
const { TabPane } = Tabs;

// 数据接口定义
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
  code: string;
  instructor: string;
  location: string;
  credits: number;
  semesterId: string;
  color: string;
}

interface Schedule {
  id: string;
  courseId: string;
  dayOfWeek: number; // 0-6 (周日到周六)
  startTime: string; // HH:mm
  endTime: string; // HH:mm
  frequency: 'weekly' | 'biweekly';
  weeks: number[]; // 哪些周有课
}

interface CourseMaterial {
  id: string;
  courseId: string;
  name: string;
  type: 'outline' | 'ppt' | 'textbook' | 'assignment' | 'exam';
  fileUrl: string;
  uploadDate: string;
  size: number;
}

interface AITool {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  type: 'concept' | 'practice' | 'exam';
}

const StudyPage: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('schedule');
  
  // 学期管理状态
  const [semesters, setSemesters] = useState<Semester[]>([
    {
      id: '1',
      name: '2024-2025 第一学期',
      startDate: '2024-09-01',
      endDate: '2025-01-15',
      isActive: true,
    },
    {
      id: '2',
      name: '2024-2025 第二学期',
      startDate: '2025-02-15',
      endDate: '2025-06-30',
      isActive: false,
    },
  ]);
  
  const [activeSemester, setActiveSemester] = useState<string>('1');
  
  // 课程管理状态
  const [courses, setCourses] = useState<Course[]>([
    {
      id: '1',
      name: '人工智能导论',
      code: 'CS101',
      instructor: '张教授',
      location: '教学楼A-101',
      credits: 3,
      semesterId: '1',
      color: '#1890ff',
    },
    {
      id: '2',
      name: '数据结构与算法',
      code: 'CS102',
      instructor: '李教授',
      location: '教学楼B-201',
      credits: 4,
      semesterId: '1',
      color: '#52c41a',
    },
    {
      id: '3',
      name: '高等数学',
      code: 'MATH101',
      instructor: '王教授',
      location: '教学楼C-301',
      credits: 4,
      semesterId: '1',
      color: '#fa8c16',
    },
  ]);
  
  // 课程安排状态
  const [schedules, setSchedules] = useState<Schedule[]>([
    {
      id: '1',
      courseId: '1',
      dayOfWeek: 1, // 周一
      startTime: '08:00',
      endTime: '09:40',
      frequency: 'weekly',
      weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
      id: '2',
      courseId: '2',
      dayOfWeek: 2, // 周二
      startTime: '10:00',
      endTime: '11:40',
      frequency: 'weekly',
      weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
      id: '3',
      courseId: '3',
      dayOfWeek: 3, // 周三
      startTime: '14:00',
      endTime: '15:40',
      frequency: 'weekly',
      weeks: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    },
  ]);
  
  // 课程材料状态
  const [materials, setMaterials] = useState<CourseMaterial[]>([
    {
      id: '1',
      courseId: '1',
      name: '人工智能导论课程大纲',
      type: 'outline',
      fileUrl: '/files/ai-outline.pdf',
      uploadDate: '2024-09-01',
      size: 1024000,
    },
    {
      id: '2',
      courseId: '1',
      name: '第一章：人工智能概述',
      type: 'ppt',
      fileUrl: '/files/ai-chapter1.pptx',
      uploadDate: '2024-09-05',
      size: 2048000,
    },
  ]);
  
  // AI工具定义
  const aiTools: AITool[] = [
    {
      id: '1',
      name: '概念解释器',
      description: '输入任何学习概念，AI将为您提供详细解释和实例',
      icon: <BulbOutlined />,
      type: 'concept',
    },
    {
      id: '2',
      name: '练习题生成器',
      description: '基于课程内容自动生成相似的练习题',
      icon: <EditOutlined />,
      type: 'practice',
    },
    {
      id: '3',
      name: '模拟考试',
      description: '创建模拟考试，测试您的学习成果',
      icon: <FileTextOutlined />,
      type: 'exam',
    },
  ];
  
  // 模态框状态
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'semester' | 'course' | 'schedule' | 'material'>('course');
  const [editingItem, setEditingItem] = useState<any>(null);
  const [form] = Form.useForm();
  
  // 获取当前学期的课程
  const getCurrentSemesterCourses = () => {
    return courses.filter(course => course.semesterId === activeSemester);
  };
  
  // 获取时间表数据
  const getTimeTableData = () => {
    const timeSlots = [
      '08:00-09:40',
      '10:00-11:40',
      '14:00-15:40',
      '16:00-17:40',
      '19:00-20:40',
    ];
    
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    const tableData = timeSlots.map(timeSlot => {
      const row: any = { timeSlot };
      
      days.forEach((day, dayIndex) => {
        const schedule = schedules.find(s => {
          const course = courses.find(c => c.id === s.courseId);
          if (!course) return false;
          
          const [startTime] = timeSlot.split('-');
          return s.dayOfWeek === (dayIndex + 1) % 7 && s.startTime === startTime;
        });
        
        if (schedule) {
          const course = courses.find(c => c.id === schedule.courseId);
          row[day] = course ? {
            courseName: course.name,
            location: course.location,
            instructor: course.instructor,
            color: course.color,
          } : null;
        } else {
          row[day] = null;
        }
      });
      
      return row;
    });
    
    return tableData;
  };
  
  // 时间表列定义
  const timeTableColumns: ColumnsType<any> = [
    {
      title: '时间',
      dataIndex: 'timeSlot',
      key: 'timeSlot',
      width: 120,
      fixed: 'left',
    },
    ...['周一', '周二', '周三', '周四', '周五', '周六', '周日'].map(day => ({
      title: day,
      dataIndex: day,
      key: day,
      width: 180,
      render: (cellData: any) => {
        if (!cellData) return null;
        
        return (
          <div
            style={{
              background: cellData.color,
              color: 'white',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '12px',
              lineHeight: '16px',
            }}
          >
            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
              {cellData.courseName}
            </div>
            <div>{cellData.location}</div>
            <div>{cellData.instructor}</div>
          </div>
        );
      },
    })),
  ];
  
  // 文件类型图标
  const getFileIcon = (type: string) => {
    switch (type) {
      case 'outline':
        return <FileTextOutlined style={{ color: '#1890ff' }} />;
      case 'ppt':
        return <FilePdfOutlined style={{ color: '#fa8c16' }} />;
      case 'textbook':
        return <BookOutlined style={{ color: '#52c41a' }} />;
      case 'assignment':
        return <EditOutlined style={{ color: '#722ed1' }} />;
      case 'exam':
        return <FileTextOutlined style={{ color: '#eb2f96' }} />;
      default:
        return <FileTextOutlined />;
    }
  };
  
  // 文件大小格式化
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // 打开模态框
  const openModal = (type: typeof modalType, item?: any) => {
    setModalType(type);
    setEditingItem(item);
    setIsModalVisible(true);
    
    if (item) {
      form.setFieldsValue(item);
    } else {
      form.resetFields();
    }
  };
  
  // 关闭模态框
  const closeModal = () => {
    setIsModalVisible(false);
    setEditingItem(null);
    form.resetFields();
  };
  
  // 处理表单提交
  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingItem) {
        // 编辑模式
        switch (modalType) {
          case 'semester':
            setSemesters(prev => prev.map(item => 
              item.id === editingItem.id ? { ...item, ...values } : item
            ));
            break;
          case 'course':
            setCourses(prev => prev.map(item => 
              item.id === editingItem.id ? { ...item, ...values } : item
            ));
            break;
          case 'schedule':
            setSchedules(prev => prev.map(item => 
              item.id === editingItem.id ? { ...item, ...values } : item
            ));
            break;
        }
      } else {
        // 新增模式
        const newId = Date.now().toString();
        switch (modalType) {
          case 'semester':
            setSemesters(prev => [...prev, { ...values, id: newId }]);
            break;
          case 'course':
            setCourses(prev => [...prev, { 
              ...values, 
              id: newId, 
              semesterId: activeSemester,
              color: '#' + Math.floor(Math.random()*16777215).toString(16),
            }]);
            break;
          case 'schedule':
            setSchedules(prev => [...prev, { ...values, id: newId }]);
            break;
        }
      }
      
      message.success(editingItem ? '更新成功' : '添加成功');
      closeModal();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };
  
  // 删除项目
  const handleDelete = (type: string, id: string) => {
    switch (type) {
      case 'semester':
        setSemesters(prev => prev.filter(item => item.id !== id));
        break;
      case 'course':
        setCourses(prev => prev.filter(item => item.id !== id));
        // 同时删除相关的课程安排
        setSchedules(prev => prev.filter(item => item.courseId !== id));
        break;
      case 'schedule':
        setSchedules(prev => prev.filter(item => item.id !== id));
        break;
      case 'material':
        setMaterials(prev => prev.filter(item => item.id !== id));
        break;
    }
    message.success('删除成功');
  };
  
  // 文件上传配置
  const uploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/upload',
    onChange(info: any) {
      const { status } = info.file;
      if (status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (status === 'done') {
        message.success(`${info.file.name} 文件上传成功`);
      } else if (status === 'error') {
        message.error(`${info.file.name} 文件上传失败`);
      }
    },
    onDrop(e: any) {
      console.log('拖放文件', e.dataTransfer.files);
    },
  };

  // 渲染课程安排标签页
  const renderScheduleTab = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Title level={4}>课程时间表</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Select
              value={activeSemester}
              onChange={setActiveSemester}
              style={{ width: 200 }}
            >
              {semesters.map(semester => (
                <Option key={semester.id} value={semester.id}>
                  {semester.name}
                </Option>
              ))}
            </Select>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => openModal('schedule')}
            >
              添加课程安排
            </Button>
          </Space>
        </Col>
      </Row>
      
      <Card>
        <Table
          columns={timeTableColumns}
          dataSource={getTimeTableData()}
          pagination={false}
          scroll={{ x: 1200 }}
          bordered
        />
      </Card>
    </div>
  );

  // 渲染课程管理标签页
  const renderCourseTab = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Title level={4}>课程管理</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button 
              icon={<PlusOutlined />}
              onClick={() => openModal('semester')}
            >
              添加学期
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => openModal('course')}
            >
              添加课程
            </Button>
          </Space>
        </Col>
      </Row>
      
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="学期管理" size="small">
            <List
              dataSource={semesters}
              renderItem={semester => (
                <List.Item
                  actions={[
                    <Button 
                      type="text" 
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => openModal('semester', semester)}
                    />,
                    <Popconfirm
                      title="确定删除此学期吗？"
                      onConfirm={() => handleDelete('semester', semester.id)}
                    >
                      <Button 
                        type="text" 
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                      />
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        {semester.name}
                        {semester.isActive && <Tag color="green">当前学期</Tag>}
                      </Space>
                    }
                    description={`${semester.startDate} - ${semester.endDate}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        
        <Col span={16}>
          <Card title="当前学期课程" size="small">
            <Row gutter={[16, 16]}>
              {getCurrentSemesterCourses().map(course => (
                <Col span={12} key={course.id}>
                  <Card
                    size="small"
                    style={{ borderLeft: `4px solid ${course.color}` }}
                    actions={[
                      <EditOutlined onClick={() => openModal('course', course)} />,
                      <Popconfirm
                        title="确定删除此课程吗？"
                        onConfirm={() => handleDelete('course', course.id)}
                      >
                        <DeleteOutlined />
                      </Popconfirm>,
                    ]}
                  >
                    <Card.Meta
                      title={course.name}
                      description={
                        <div>
                          <div>课程代码: {course.code}</div>
                          <div>授课教师: {course.instructor}</div>
                          <div>上课地点: {course.location}</div>
                          <div>学分: {course.credits}</div>
                        </div>
                      }
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );

  // 渲染课程材料标签页
  const renderMaterialsTab = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Title level={4}>课程材料</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Select
            value={activeSemester}
            onChange={setActiveSemester}
            style={{ width: 200 }}
          >
            {semesters.map(semester => (
              <Option key={semester.id} value={semester.id}>
                {semester.name}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {getCurrentSemesterCourses().map(course => (
          <Col span={24} key={course.id}>
            <Card
              title={
                <Space>
                  <BookOutlined style={{ color: course.color }} />
                  {course.name}
                </Space>
              }
              extra={
                <Button
                  type="primary"
                  size="small"
                  icon={<UploadOutlined />}
                  onClick={() => openModal('material', { courseId: course.id })}
                >
                  上传材料
                </Button>
              }
            >
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Dragger {...uploadProps}>
                    <p className="ant-upload-drag-icon">
                      <UploadOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      支持单个或批量上传。支持 PDF、PPT、Word 等格式
                    </p>
                  </Dragger>
                </Col>
              </Row>
              
              <Divider />
              
              <List
                dataSource={materials.filter(m => m.courseId === course.id)}
                renderItem={material => (
                  <List.Item
                    actions={[
                      <Button type="text" icon={<EyeOutlined />} size="small" />,
                      <Button type="text" icon={<DownloadOutlined />} size="small" />,
                      <Popconfirm
                        title="确定删除此材料吗？"
                        onConfirm={() => handleDelete('material', material.id)}
                      >
                        <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={getFileIcon(material.type)}
                      title={material.name}
                      description={
                        <Space>
                          <Tag>{material.type}</Tag>
                          <Text type="secondary">{formatFileSize(material.size)}</Text>
                          <Text type="secondary">{material.uploadDate}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );

  // 渲染AI工具标签页
  const renderAIToolsTab = () => (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>AI学习工具</Title>
      
      <Row gutter={[24, 24]}>
        {aiTools.map(tool => (
          <Col span={8} key={tool.id}>
            <Card
              hoverable
              style={{ height: 200 }}
              actions={[
                <Button type="primary" icon={<PlayCircleOutlined />}>
                  使用工具
                </Button>
              ]}
            >
              <Card.Meta
                avatar={
                  <div style={{ 
                    fontSize: 32, 
                    color: '#1890ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 64,
                    height: 64,
                    background: '#f0f9ff',
                    borderRadius: 8,
                  }}>
                    {tool.icon}
                  </div>
                }
                title={tool.name}
                description={tool.description}
              />
            </Card>
          </Col>
        ))}
      </Row>
      
      <Divider />
      
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="学习统计" size="small">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="已完成作业"
                  value={12}
                  suffix="/ 20"
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="学习时长"
                  value={45.5}
                  suffix="小时"
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<ClockCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均成绩"
                  value={87.3}
                  suffix="分"
                  valueStyle={{ color: '#fa8c16' }}
                  prefix={<StarOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="使用AI次数"
                  value={156}
                  valueStyle={{ color: '#722ed1' }}
                  prefix={<ToolOutlined />}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );

  return (
    <div style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
      <PageHeader
        title="智能学习助手"
        subtitle="AI驱动的个性化学习管理平台，让学习更高效、更智能"
        icon={<BookOutlined />}
        gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        actions={[
          {
            text: '添加课程',
            icon: <PlusOutlined />,
            onClick: () => openModal('course'),
            type: 'primary'
          }
        ]}
      />

      {/* 统计概览 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ marginTop: '24px' }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="本学期课程"
              value={getCurrentSemesterCourses().length}
              suffix="门"
              icon={<BookOutlined />}
              color="#667eea"
              trend={{ value: 12, isPositive: true }}
              description="较上学期增长"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="学习材料"
              value={materials.length}
              suffix="个"
              icon={<FileTextOutlined />}
              color="#52c41a"
              trend={{ value: 8, isPositive: true }}
              description="本周新增"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="本周课时"
              value={schedules.length * 2}
              suffix="小时"
              icon={<ClockCircleOutlined />}
              color="#fa8c16"
              trend={{ value: 5, isPositive: false }}
              description="较上周减少"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <StatCard
              title="学习进度"
              value={85}
              suffix="%"
              icon={<TrophyOutlined />}
              color="#f759ab"
              trend={{ value: 15, isPositive: true }}
              description="本月提升"
            />
          </Col>
        </Row>
      </motion.div>

      {/* 快速操作卡片 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{ marginTop: '24px' }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="AI学习助手"
              description="智能概念解释、练习生成"
              icon={<RocketOutlined />}
              onClick={() => setActiveTab('ai-tools')}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              stats={{ label: "今日使用", value: "12次" }}
              badge="HOT"
            />
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="课程安排"
              description="查看今日课程和时间表"
              icon={<CalendarOutlined />}
              onClick={() => setActiveTab('schedule')}
              gradient="linear-gradient(135deg, #52c41a 0%, #389e0d 100%)"
              stats={{ label: "今日课程", value: "3门" }}
            />
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <QuickActionCard
              title="学习材料"
              description="管理课件、作业和资源"
              icon={<FolderOpenOutlined />}
              onClick={() => setActiveTab('materials')}
              gradient="linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)"
              stats={{ label: "待复习", value: "5份" }}
            />
          </Col>
        </Row>
      </motion.div>

      {/* 主要内容区域 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        style={{ marginTop: '24px' }}
      >
        <Card
          style={{ 
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            border: '1px solid rgba(102, 126, 234, 0.1)'
          }}
          bodyStyle={{ padding: 0 }}
        >
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            size="large"
            style={{ margin: 0 }}
            tabBarStyle={{ 
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
              margin: 0,
              padding: '0 24px'
            }}
          >
            <TabPane
              tab={
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CalendarOutlined />
                  课程安排
                </span>
              }
              key="schedule"
            >
              <div style={{ padding: '24px' }}>
                {renderScheduleTab()}
              </div>
            </TabPane>
            
            <TabPane
              tab={
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookOutlined />
                  课程管理
                </span>
              }
              key="courses"
            >
              <div style={{ padding: '24px' }}>
                {renderCourseTab()}
              </div>
            </TabPane>
            
            <TabPane
              tab={
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FolderOpenOutlined />
                  课程材料
                </span>
              }
              key="materials"
            >
              <div style={{ padding: '24px' }}>
                {renderMaterialsTab()}
              </div>
            </TabPane>
            
            <TabPane
              tab={
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ToolOutlined />
                  <Badge dot style={{ backgroundColor: '#f759ab' }}>
                    AI工具
                  </Badge>
                </span>
              }
              key="ai-tools"
            >
              <div style={{ padding: '24px' }}>
                {renderAIToolsTab()}
              </div>
            </TabPane>
          </Tabs>
        </Card>
      </motion.div>

      {/* 通用模态框 */}
      <Modal
        title={
          modalType === 'semester' ? (editingItem ? '编辑学期' : '添加学期') :
          modalType === 'course' ? (editingItem ? '编辑课程' : '添加课程') :
          modalType === 'schedule' ? (editingItem ? '编辑课程安排' : '添加课程安排') :
          '添加材料'
        }
        open={isModalVisible}
        onOk={handleFormSubmit}
        onCancel={closeModal}
        width={600}
      >
        <Form form={form} layout="vertical">
          {modalType === 'semester' && (
            <>
              <Form.Item
                name="name"
                label="学期名称"
                rules={[{ required: true, message: '请输入学期名称' }]}
              >
                <Input placeholder="例如：2024-2025 第一学期" />
              </Form.Item>
              <Form.Item
                name="startDate"
                label="开始日期"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                name="endDate"
                label="结束日期"
                rules={[{ required: true, message: '请选择结束日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                name="isActive"
                label="是否为当前学期"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </>
          )}
          
          {modalType === 'course' && (
            <>
              <Form.Item
                name="name"
                label="课程名称"
                rules={[{ required: true, message: '请输入课程名称' }]}
              >
                <Input placeholder="例如：人工智能导论" />
              </Form.Item>
              <Form.Item
                name="code"
                label="课程代码"
                rules={[{ required: true, message: '请输入课程代码' }]}
              >
                <Input placeholder="例如：CS101" />
              </Form.Item>
              <Form.Item
                name="instructor"
                label="授课教师"
                rules={[{ required: true, message: '请输入授课教师' }]}
              >
                <Input placeholder="例如：张教授" />
              </Form.Item>
              <Form.Item
                name="location"
                label="上课地点"
                rules={[{ required: true, message: '请输入上课地点' }]}
              >
                <Input placeholder="例如：教学楼A-101" />
              </Form.Item>
              <Form.Item
                name="credits"
                label="学分"
                rules={[{ required: true, message: '请输入学分' }]}
              >
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}
          
          {modalType === 'schedule' && (
            <>
              <Form.Item
                name="courseId"
                label="课程"
                rules={[{ required: true, message: '请选择课程' }]}
              >
                <Select placeholder="选择课程">
                  {getCurrentSemesterCourses().map(course => (
                    <Option key={course.id} value={course.id}>
                      {course.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item
                name="dayOfWeek"
                label="星期"
                rules={[{ required: true, message: '请选择星期' }]}
              >
                <Select placeholder="选择星期">
                  <Option value={1}>周一</Option>
                  <Option value={2}>周二</Option>
                  <Option value={3}>周三</Option>
                  <Option value={4}>周四</Option>
                  <Option value={5}>周五</Option>
                  <Option value={6}>周六</Option>
                  <Option value={0}>周日</Option>
                </Select>
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="startTime"
                    label="开始时间"
                    rules={[{ required: true, message: '请选择开始时间' }]}
                  >
                    <TimePicker format="HH:mm" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="endTime"
                    label="结束时间"
                    rules={[{ required: true, message: '请选择结束时间' }]}
                  >
                    <TimePicker format="HH:mm" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item
                name="frequency"
                label="频率"
                rules={[{ required: true, message: '请选择频率' }]}
              >
                <Select placeholder="选择频率">
                  <Option value="weekly">每周</Option>
                  <Option value="biweekly">双周</Option>
                </Select>
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default StudyPage;
