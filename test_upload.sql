CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    department VARCHAR(50),
    salary DECIMAL(10, 2)
);

INSERT INTO employees (id, name, age, department, salary) VALUES
(1, '张三', 28, '技术部', 8000.00),
(2, '李四', 35, '市场部', 12000.00),
(3, '王五', 42, '管理部', 15000.00),
(4, '赵六', 25, '技术部', 6000.00),
(5, '钱七', 30, '市场部', 9000.00);