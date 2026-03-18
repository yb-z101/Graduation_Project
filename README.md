# 对话式数据分析系统

## 项目简介

对话式数据分析系统是一个基于大模型和数据分析技术的智能系统，允许用户通过自然语言对话的方式上传数据文件、进行数据分析和可视化。

### 主要功能

- 文件上传：支持 CSV 和 Excel 文件的上传和解析
- 数据分析：通过自然语言查询进行数据分析
- 图表生成：根据分析结果自动生成图表
- 会话管理：支持多会话管理和历史会话恢复
- 多模型支持：集成阿里云 Qwen、DeepSeek 和火山引擎等主流大模型

## 技术栈

### 后端
- Python 3.10+
- FastAPI：高性能 API 框架
- SQLAlchemy：ORM 数据库框架
- Pandas：数据处理库
- LangGraph：工作流管理

### 前端
- Vue 3：前端框架
- Element Plus：UI 组件库
- ECharts：图表库
- Axios：HTTP 客户端

## 项目结构

```
graduation-project/
├── backend/          # 后端代码
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/         # API 路由
│   │   │   ├── core/        # 核心配置
│   │   │   ├── models/      # 数据库模型
│   │   │   ├── repositories/ # 数据访问层
│   │   │   ├── services/    # 业务逻辑层
│   │   │   ├── utils/       # 工具函数
│   │   │   └── workflows/   # 工作流
│   │   ├── tests/           # 测试代码
│   │   ├── .env             # 环境变量
│   │   ├── main.py          # 主入口
│   │   └── requirements.txt # 依赖包
├── frontend/         # 前端代码
│   ├── public/       # 静态资源
│   ├── src/
│   │   ├── api/       # API 服务
│   │   ├── components/ # 组件
│   │   ├── router/    # 路由
│   │   ├── store/     # 状态管理
│   │   ├── utils/     # 工具函数
│   │   ├── views/     # 页面
│   │   ├── App.vue    # 根组件
│   │   └── main.js    # 主入口
│   ├── .env.development # 开发环境配置
│   ├── .env.production  # 生产环境配置
│   ├── package.json   # 依赖包
│   └── vue.config.js  # Vue 配置
└── README.md          # 项目说明
```

## 安装与运行

### 后端安装

1. 进入后端目录
   ```bash
   cd backend/backend
   ```

2. 创建虚拟环境
   ```bash
   python -m venv .venv
   ```

3. 激活虚拟环境
   - Windows: `.venvcriptsctivate`
   - Linux/Mac: `source .venv/bin/activate`

4. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

5. 配置环境变量
   编辑 `.env` 文件，添加以下配置：
   ```
   # 数据库配置
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_DB=chat_analysis_db

   # 大模型配置
   QWEN_API_KEY=your_qwen_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   VOLCENGINE_API_KEY=your_volcengine_api_key
   ```

6. 启动后端服务
   ```bash
   uvicorn main:app --reload
   ```

### 前端安装

1. 进入前端目录
   ```bash
   cd frontend
   ```

2. 安装依赖
   ```bash
   npm install
   ```

3. 启动前端服务
   ```bash
   npm run serve
   ```

## API 文档

后端启动后，可以通过以下地址访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心模块

### 1. 文件上传模块
- 支持 CSV 和 Excel 文件上传
- 自动解析文件内容，生成数据预览
- 创建会话并存储数据

### 2. 会话管理模块
- 支持多会话管理
- 会话历史记录和恢复
- 会话数据清理和操作

### 3. 数据分析模块
- 通过自然语言查询进行数据分析
- 自动生成 pandas 代码执行分析
- 生成分析结果和图表

### 4. 聊天模块
- 支持普通聊天功能
- 集成多个大模型
- 智能回复和上下文理解

## 测试

### 运行后端测试

```bash
cd backend/backend
pytest tests/
```

## 部署

### 后端部署

1. 构建 Docker 镜像
   ```bash
   docker build -t chat-analysis-backend .
   ```

2. 运行容器
   ```bash
   docker run -p 8000:8000 --env-file .env chat-analysis-backend
   ```

### 前端部署

1. 构建生产版本
   ```bash
   npm run build
   ```

2. 部署到静态文件服务器
   将 `dist` 目录部署到 Nginx、Apache 等静态文件服务器。

## 注意事项

1. 确保数据库服务已启动，并且创建了相应的数据库
2. 配置正确的大模型 API 密钥
3. 前端服务默认运行在 8080 端口，后端服务默认运行在 8000 端口
4. 上传的文件大小限制为 10MB

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 许可证

MIT License
