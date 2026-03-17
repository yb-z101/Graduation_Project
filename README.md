对话式数据分析系统## 项目简介
对话式数据分析系统是一个基于大语言模型的智能数据分析平台，支持通过自然语言对话的方式对数据进行分析和可视化。系统采用前后端分离架构，后端使用FastAPI和LangGraph构建工作流，前端使用Vue 3和Element Plus构建用户界面。

## 技术栈
### 后端
- 语言 ：Python 3.10+
- 框架 ：FastAPI
- 工作流 ：LangGraph
- ORM ：SQLAlchemy
- 数据库 ：MySQL
- 大模型 ：Qwen API
### 前端
- 语言 ：JavaScript
- 框架 ：Vue 3
- UI库 ：Element Plus
- 状态管理 ：Pinia
- 路由 ：Vue Router
- 数据可视化 ：ECharts
- HTTP客户端 ：Axios
## 功能特性
- 文件上传 ：支持CSV和Excel文件上传
- 数据预览 ：展示上传的数据内容
- 对话分析 ：通过自然语言对话进行数据分析
- 数据可视化 ：自动生成图表展示分析结果
- 会话管理 ：保存分析会话和历史记录
- 数据清洗 ：支持对数据进行清洗操作

## 环境要求
- Python ：3.10+
- Node.js ：14.0+
- MySQL ：5.7+
- ## 安装和运行
### 后端安装和运行
1. 进入后端目录 ：
2. cd backend/backend
3. 安装依赖 ：
4. pip install -r requirements.txt
   配置环境变量 ：
修改 .env 文件，配置数据库连接和大模型API密钥：
# MySQL配置
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=graduation_db

# 大模型配置
QWEN_API_KEY=your_api_key
启动后端服务 ：
uvicorn main:app --reload
后端服务将在 http://localhost:8000 运行。
### 前端安装和运行
1. 进入前端目录 ：
2. cd frontend
3. 安装依赖 ：
4. npm install
5. 配置前端代理 ：
修改 vue.config.js 文件，确保代理配置正确：
module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/': ''
        }
      }
    }
  }
}
启动前端服务 ：
npm run serve
1. 前端服务将在 http://localhost:8080 运行。
## 核心功能
### 1. 文件上传
- 支持CSV和Excel文件上传
- 自动解析文件内容
- 生成数据预览
### 2. 对话分析
- 通过自然语言对话进行数据分析
- 支持复杂的分析请求
- 保持对话上下文
### 3. 数据可视化
- 自动生成图表展示分析结果
- 支持多种图表类型
- 交互式图表操作
### 4. 会话管理
- 保存分析会话
- 支持会话切换
- 历史会话记录
### 5. 数据清洗
- 支持对数据进行清洗操作
- 自动生成清洗代码
- 展示清洗前后的对比
## API接口
### 后端主要接口
接口路径 方法 功能 /health GET 健康检查 /upload POST 文件上传 /api/v1/session/send_message POST 发送分析请求 /api/v1/session/clean POST 数据清洗 /api/v1/analysis-task/create-and-execute POST 创建并执行分析任务

### 前端API调用
- 文件上传 ： src/api/upload.js
- 会话管理 ： src/api/session.js
