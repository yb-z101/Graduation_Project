-- 创建员工表
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    department VARCHAR(50) NOT NULL
);

-- 插入测试数据
INSERT INTO employees (name, age, department) VALUES
('张三', 28, '技术部'),
('李四', 32, '市场部'),
('王五', 24, '产品部');

-- 查询所有员工
SELECT * FROM employees;

-- 查询年龄大于25的员工
SELECT * FROM employees WHERE age > 25;

-- 按部门分组统计员工数量
SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department;
