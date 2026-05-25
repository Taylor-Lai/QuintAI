import request from '../api/request'

// 用户分页列表
export const getUserPageApi = (params) => {
  return request.get('/admin/user/page', { params })
}

// 用户详情
export const getUserDetailApi = (id) => {
  return request.get(`/admin/user/${id}`)
}

// 删除用户
export const deleteUserApi = (id) => {
  return request.delete(`/admin/user/${id}`)
}

// 后台统计
export const getAdminStatisticsApi = () => {
  return request.get('/admin/statistics')
}

// 设置或取消管理员权限
// 对应接口：PUT /admin/user/{user_id}/role?is_admin=true
export const updateUserAdminRoleApi = (userId, isAdmin) => {
  return request.put(`/admin/user/${userId}/role`, null, {
    params: {
      is_admin: isAdmin
    }
  })
}