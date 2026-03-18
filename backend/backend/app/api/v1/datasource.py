from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List,Optional
from datetime import datetime

# 导入依赖
from app.core.database import get_db
from app.models.models import DataSource
from app.api.v1.schemas.datasource import DataSourceCreate, DataSourceResponse
from app.core.sql.security import SQLSecurity  # 复用之前的安全校验类

router = APIRouter(tags=["数据源管理"])


# 1. 新增数据源（核心接口，密码加密存储）
@router.post("/create", response_model=DataSourceResponse)
def create_datasource(
        data: DataSourceCreate,
        db: Session = Depends(get_db)
):
    # 1. 检查数据源名称是否重复（毕设“数据唯一性”考量）
    existing_ds = db.query(DataSource).filter(
        DataSource.source_name == data.source_name,
        DataSource.is_deleted == False
    ).first()
    if existing_ds:
        raise HTTPException(status_code=400, detail="数据源名称已存在，请更换")

    # 2. 创建数据源对象，加密密码（毕设“安全性”亮点）
    db_ds = DataSource(
        source_name=data.source_name,
        source_type=data.source_type,
        host=data.host,
        port=data.port,
        db_name=data.db_name,
        username=data.username
    )
    db_ds.set_password(data.plain_password)  # 加密密码，不存储明文

    # 3. 写入数据库
    try:
        db.add(db_ds)
        db.commit()
        db.refresh(db_ds)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建数据源失败：{str(e)}")

    # 4. 构造响应（脱敏，不返回密码）
    return DataSourceResponse(
        id=db_ds.id,
        source_name=db_ds.source_name,
        source_type=db_ds.source_type,
        host=db_ds.host,
        port=db_ds.port,
        db_name=db_ds.db_name,
        username=db_ds.username,
        create_time=db_ds.create_time.strftime("%Y-%m-%d %H:%M:%S")
    )


# 2. 查询数据源列表（脱敏返回）
@router.get("/list", response_model=List[DataSourceResponse])
def list_datasource(
        source_type: Optional[int] = None,  # 可选筛选条件
        db: Session = Depends(get_db)
):
    # 构建查询条件（软删除过滤）
    query = db.query(DataSource).filter(DataSource.is_deleted == False)
    # 可选筛选数据源类型
    if source_type:
        query = query.filter(DataSource.source_type == source_type)
    # 按创建时间倒序
    ds_list = query.order_by(DataSource.create_time.desc()).all()

    # 构造响应列表
    return [
        DataSourceResponse(
            id=ds.id,
            source_name=ds.source_name,
            source_type=ds.source_type,
            host=ds.host,
            port=ds.port,
            db_name=ds.db_name,
            username=ds.username,
            create_time=ds.create_time.strftime("%Y-%m-%d %H:%M:%S")
        ) for ds in ds_list
    ]


# 3. 查询数据源详情（用于编辑/连接测试）
@router.get("/detail/{ds_id}", response_model=DataSourceResponse)
def get_datasource_detail(
        ds_id: int,
        db: Session = Depends(get_db)
):
    db_ds = db.query(DataSource).filter(
        DataSource.id == ds_id,
        DataSource.is_deleted == False
    ).first()
    if not db_ds:
        raise HTTPException(status_code=404, detail="数据源不存在或已删除")

    return DataSourceResponse(
        id=db_ds.id,
        source_name=db_ds.source_name,
        source_type=db_ds.source_type,
        host=db_ds.host,
        port=db_ds.port,
        db_name=db_ds.db_name,
        username=db_ds.username,
        create_time=db_ds.create_time.strftime("%Y-%m-%d %H:%M:%S")
    )


# 4. 测试数据源连接（毕设“可用性校验”亮点）
# 替换原有test_datasource_connect函数
@router.post("/test-connect/{ds_id}")
def test_datasource_connect(
        ds_id: int,
        db: Session = Depends(get_db)
):
    # 1. 查询数据源信息
    db_ds = db.query(DataSource).filter(
        DataSource.id == ds_id,
        DataSource.is_deleted == False
    ).first()
    if not db_ds:
        raise HTTPException(status_code=404, detail="数据源不存在或已删除")

    # 2. 毕设简化方案：前端传入明文密码测试（临时）
    # 说明：实际项目中应前端传明文，后端验证后连接，这里先简化
    # 注意：需确保你的MySQL密码是正确的，替换下方的plain_password（仅测试用）
    plain_password = "你的MySQL明文密码"  # 临时替换为你的真实密码

    # 3. 根据数据源类型测试连接
    try:
        if db_ds.source_type == 1:  # MySQL
            import pymysql
            conn = pymysql.connect(
                host=db_ds.host,
                port=db_ds.port,
                user=db_ds.username,
                password=plain_password,  # 用明文密码连接
                db=db_ds.db_name,
                connect_timeout=5,
                charset="utf8mb4"
            )
            conn.close()

        elif db_ds.source_type == 2:  # PostgreSQL（可选）
            import psycopg2
            conn = psycopg2.connect(
                host=db_ds.host,
                port=db_ds.port,
                user=db_ds.username,
                password=plain_password,
                dbname=db_ds.db_name,
                connect_timeout=5
            )
            conn.close()

        elif db_ds.source_type == 3:  # SQLite（暂不实现）
            raise HTTPException(status_code=501, detail="SQLite连接测试暂未实现")

        return {"status": "ok", "message": "数据源连接成功"}

    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL连接失败：{str(e)}")
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL连接失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接测试失败：{str(e)}")
# 修复：MySQL连接时的密码问题（补充解密逻辑）
# 说明：上面test-connect中密码直接用了加密后的，这里修正（替换第118行左右的password参数）
# 正确写法：password=db_ds.verify_password(db_ds.password) → 错误，重新梳理：
# 补充：set_password是加密存储，verify是验证明文，连接时需要明文密码，因此需要调整：
# 方案：新增一个临时字段存储明文（仅测试用），或前端传入明文测试，毕设阶段简化：
# 临时修复test-connect中的密码逻辑（替换原password参数）：
# password=data.plain_password （需前端传入，这里先简化，后续联调时调整）