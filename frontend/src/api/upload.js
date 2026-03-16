import request from '@/utils/request';

// 上传文件到后端
export function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}