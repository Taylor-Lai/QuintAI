import request from './request'

export function loginApi(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export function registerApi(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}

export function getProfileApi() {
  return request({
    url: '/user/profile',
    method: 'get'
  })
}

export function updateProfileApi(data) {
  return request({
    url: '/user/profile',
    method: 'put',
    data
  })
}

export function logoutApi(data) {
  return request({
    url: '/auth/logout',
    method: 'post',
    data
  })
}