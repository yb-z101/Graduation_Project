import request from '@/utils/request';

// 示例：调用FastAPI的用户列表接口（假设后端接口为 /api/user/list）
export function getUserList(params) {
  return request({
    url: '/api/user/list', // FastAPI的接口路径（拼接后为 http://localhost:8000/api/user/list）
    method: 'get',
    params // GET参数（FastAPI通过Query接收）
  });
}

// 示例：调用FastAPI的新增用户接口（POST请求，JSON参数）
export function addUser(data) {
  return request({
    url: '/api/user/add',
    method: 'post',
    data // POST参数（FastAPI通过Body接收JSON）
  });
}