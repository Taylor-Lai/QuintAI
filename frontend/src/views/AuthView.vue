<template>
  <div class="auth-page">
    <div class="auth-wrapper">
      <div class="auth-card" :class="{ 'show-register': !isLoginMode }">
        <!-- 左侧表单区域 -->
        <div class="left-panel">
          <div class="form-slider">
            <!-- 登录 -->
            <div class="form-view">
              <div class="form-box">
                <h2 class="form-title">Welcome back</h2>
                <p class="form-subtitle">登录后继续使用智能文档处理服务</p>

                <div class="form-group">
                  <input
                    v-model.trim="loginForm.email"
                    type="email"
                    class="form-input"
                    placeholder="邮箱"
                    @keyup.enter="handleLogin"
                  />
                </div>

                <div class="form-group">
                  <input
                    v-model.trim="loginForm.password"
                    type="password"
                    class="form-input"
                    placeholder="密码"
                    @keyup.enter="handleLogin"
                  />
                </div>

                <div class="form-actions">
                  <button
                    class="primary-btn"
                    :disabled="userStore.loading"
                    @click="handleLogin"
                  >
                    {{ userStore.loading ? '登录中...' : '登录' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 注册 -->
            <div class="form-view">
              <div class="form-box">
                <h2 class="form-title">Create account</h2>
                <p class="form-subtitle">注册后即可体验平台全部功能</p>

                <div class="form-group">
                  <input
                    v-model.trim="registerForm.username"
                    type="text"
                    class="form-input"
                    placeholder="用户名"
                    @keyup.enter="handleRegister"
                  />
                </div>

                <div class="form-group">
                  <input
                    v-model.trim="registerForm.email"
                    type="email"
                    class="form-input"
                    placeholder="邮箱"
                    @keyup.enter="handleRegister"
                  />
                </div>

                <div class="form-group">
                  <input
                    v-model.trim="registerForm.password"
                    type="password"
                    class="form-input"
                    placeholder="密码"
                    @keyup.enter="handleRegister"
                  />
                </div>

                <div class="form-actions">
                  <button
                    class="primary-btn"
                    :disabled="userStore.loading"
                    @click="handleRegister"
                  >
                    {{ userStore.loading ? '注册中...' : '注册' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧提示区域 -->
        <div class="right-panel">
          <div class="side-slider">
            <!-- 去注册 -->
            <div class="side-view">
              <div class="side-content">
                <h2 class="side-title">New here?</h2>
                <p class="side-desc">
                  注册账号，开始体验文档智能操作、信息提取与表格处理能力
                </p>
                <button class="switch-btn" @click="switchMode(false)">
                  去注册
                </button>
              </div>
            </div>

            <!-- 去登录 -->
            <div class="side-view">
              <div class="side-content">
                <h2 class="side-title">Already have an account?</h2>
                <p class="side-desc">
                  使用已有账号登录，继续访问你的功能页面和个人中心
                </p>
                <button class="switch-btn" @click="switchMode(true)">
                  去登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="back-home" @click="goHome">← 返回首页</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const isLoginMode = ref(true)

const loginForm = reactive({
  email: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: ''
})

const switchMode = (mode) => {
  isLoginMode.value = mode
}

const goHome = () => {
  router.push('/')
}

const handleLogin = async () => {
  if (!loginForm.email) {
    alert('请输入邮箱')
    return
  }

  if (!loginForm.password) {
    alert('请输入密码')
    return
  }

  try {
    await userStore.loginAction({
      email: loginForm.email,
      password: loginForm.password
    })

    router.push('/')
  } catch (error) {
    alert(error.message || '登录失败')
  }
}

const handleRegister = async () => {
  if (!registerForm.username) {
    alert('请输入用户名')
    return
  }

  if (!registerForm.email) {
    alert('请输入邮箱')
    return
  }

  if (!registerForm.password) {
    alert('请输入密码')
    return
  }

  try {
    const res = await userStore.registerAction({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })

    alert(res.message || '注册成功')

    isLoginMode.value = true
    loginForm.email = registerForm.email
    loginForm.password = ''

    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
  } catch (error) {
    alert(error.message || '注册失败')
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #ececec;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
}

.auth-wrapper {
  width: 1120px;
  max-width: 100%;
}

.auth-card {
  width: 100%;
  min-height: 640px;
  background: #f8f8f8;
  border-radius: 28px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.08);
}

.left-panel {
  background: #fbfbfb;
  overflow: hidden;
  position: relative;
}

.form-slider {
  width: 200%;
  height: 100%;
  display: flex;
  transition: transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}

.auth-card.show-register .form-slider {
  transform: translateX(-50%);
}

.form-view {
  width: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 72px 72px;
}

.form-box {
  width: 100%;
  max-width: 420px;
}

.form-title {
  margin: 0 0 12px;
  font-size: 48px;
  line-height: 1.1;
  color: #1f1f1f;
  font-weight: 800;
}

.form-subtitle {
  margin: 0 0 42px;
  color: #9a9a9a;
  font-size: 15px;
  line-height: 1.8;
}

.form-group {
  margin-bottom: 22px;
}

.form-input {
  width: 100%;
  height: 56px;
  border: none;
  border-bottom: 1px solid #bfbfbf;
  background: transparent;
  font-size: 16px;
  color: #333;
  outline: none;
  padding: 0 4px;
  transition: border-color 0.25s ease;
}

.form-input:focus {
  border-bottom-color: #d5b076;
}

.form-input::placeholder {
  color: #c2c2c2;
}

.form-actions {
  margin-top: 36px;
}

.primary-btn {
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 26px;
  background: #d5b076;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    opacity 0.25s ease;
  box-shadow: 0 10px 24px rgba(213, 176, 118, 0.25);
}

.primary-btn:hover {
  transform: translateY(-1px);
}

.primary-btn:disabled {
  opacity: 0.72;
  cursor: not-allowed;
  transform: none;
}

.right-panel {
  background: #737373;
  overflow: hidden;
  position: relative;
}

.side-slider {
  width: 200%;
  height: 100%;
  display: flex;
  transition: transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}

.auth-card.show-register .side-slider {
  transform: translateX(-50%);
}

.side-view {
  width: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 56px 40px;
}

.side-content {
  width: 100%;
  max-width: 320px;
  text-align: center;
  color: #fff;
}

.side-title {
  margin: 0 0 18px;
  font-size: 46px;
  line-height: 1.1;
  font-weight: 700;
}

.side-desc {
  margin: 0 0 42px;
  font-size: 16px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.9);
}

.switch-btn {
  min-width: 156px;
  height: 48px;
  border-radius: 24px;
  border: 2px solid rgba(255, 255, 255, 0.88);
  background: transparent;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.25s ease,
    transform 0.25s ease;
}

.switch-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.back-home {
  margin-top: 18px;
  color: #6f6f6f;
  font-size: 14px;
  cursor: pointer;
  width: fit-content;
  transition: color 0.2s ease;
}

.back-home:hover {
  color: #d5b076;
}

@media (max-width: 900px) {
  .auth-card {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .right-panel {
    min-height: 260px;
  }

  .form-view {
    padding: 48px 28px;
  }

  .side-view {
    padding: 40px 24px;
  }

  .form-title {
    font-size: 38px;
  }

  .side-title {
    font-size: 34px;
  }
}
</style>
